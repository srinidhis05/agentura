"""Thin GitHub API wrapper for PR pipeline operations.

All functions take an explicit token parameter — no global state.
Uses httpx (already a project dependency).
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0


def build_diff_position_map(diff_text: str) -> dict[str, dict[int, int]]:
    """Parse a unified diff and build a mapping of (file, new_line) → diff position.

    GitHub's review API requires a 'position' (1-based offset within the diff hunk)
    rather than an absolute file line number. This function builds that mapping.

    Returns:
        dict mapping file path → {new_line_number: diff_position}
    """
    import re
    result: dict[str, dict[int, int]] = {}
    current_file: str | None = None
    position = 0  # 1-based position within the current file's diff

    for line in diff_text.split("\n"):
        # Detect file header
        if line.startswith("diff --git"):
            # Extract b-side path: "diff --git a/foo b/bar" → "bar"
            match = re.search(r" b/(.+)$", line)
            if match:
                current_file = match.group(1)
                result[current_file] = {}
                position = 0
            continue

        if current_file is None:
            continue

        # Skip non-diff metadata lines (index, ---, +++, mode changes, renames etc.)
        if (line.startswith("index ") or line.startswith("--- ") or line.startswith("+++ ")
                or line.startswith("new file mode") or line.startswith("deleted file mode")
                or line.startswith("old mode") or line.startswith("new mode")
                or line.startswith("similarity index") or line.startswith("rename ")
                or line.startswith("copy ")):
            continue

        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            position += 1
            continue

        # Within a hunk — every line (context, add, delete) increments position
        position += 1

        if line.startswith("+"):
            # Added line — map its new-file line number to this diff position
            result[current_file][new_line] = position
            new_line += 1
        elif line.startswith("-"):
            # Deleted line — no new-file line number
            pass
        else:
            # Context line — present in both old and new
            new_line += 1

    return result


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _diff_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_token() -> str:
    """Read GITHUB_TOKEN from environment."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.warning("GITHUB_TOKEN not set — GitHub API calls will fail")
    return token


async def fetch_pr_diff(repo: str, pr_number: int, token: str | None = None) -> str:
    """Fetch the unified diff for a PR via GitHub API."""
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, headers=_diff_headers(token))
        resp.raise_for_status()
        return resp.text


async def fetch_pr_files(repo: str, pr_number: int, token: str | None = None) -> list[dict]:
    """Fetch the list of changed files for a PR."""
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, headers=_headers(token))
        resp.raise_for_status()
        return resp.json()


async def post_review(
    repo: str,
    pr_number: int,
    comments: list[dict],
    body: str,
    event: str = "COMMENT",
    commit_id: str | None = None,
    token: str | None = None,
    diff_text: str | None = None,
) -> dict:
    """Post a PR review with inline comments.

    Args:
        repo: "owner/repo" format
        pr_number: PR number
        comments: List of {"path": str, "line": int, "body": str}
        body: Review summary body
        event: APPROVE | REQUEST_CHANGES | COMMENT
        commit_id: HEAD SHA for the review (required by GitHub)
        token: GitHub API token
        diff_text: Unified diff text for position mapping (fetched if not provided)
    """
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews"

    # Build diff position map for accurate inline comments
    position_map: dict[str, dict[int, int]] = {}
    if comments:
        if not diff_text:
            try:
                diff_text = await fetch_pr_diff(repo, pr_number, token)
            except Exception as e:
                logger.warning("Failed to fetch diff for position mapping: %s", e)
        if diff_text:
            position_map = build_diff_position_map(diff_text)

    # Map absolute line numbers to diff positions
    enriched_comments = []
    skipped = 0
    for c in comments:
        path = c["path"]
        line = c["line"]
        file_positions = position_map.get(path, {})
        position = file_positions.get(line)

        if position is not None:
            enriched_comments.append({
                "path": path,
                "position": position,
                "body": c["body"],
            })
        else:
            # Fallback: try line+side=RIGHT (works for new files / simple diffs)
            enriched_comments.append({
                "path": path,
                "line": line,
                "body": c["body"],
                "side": "RIGHT",
            })
            skipped += 1

    if skipped:
        logger.info("%d/%d comments used line fallback (no diff position found)", skipped, len(comments))

    payload: dict = {
        "body": body,
        "event": event,
        "comments": enriched_comments,
    }
    if commit_id:
        payload["commit_id"] = commit_id

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, headers=_headers(token), json=payload)
        if resp.status_code == 422 and enriched_comments:
            # Retry: drop comments that failed position mapping, keep positioned ones
            positioned_only = [c for c in enriched_comments if "position" in c]
            if positioned_only and len(positioned_only) < len(enriched_comments):
                logger.warning(
                    "GitHub rejected some comments (422), retrying with %d positioned-only comments",
                    len(positioned_only),
                )
                payload["comments"] = positioned_only
                resp = await client.post(url, headers=_headers(token), json=payload)

            if resp.status_code == 422:
                # Final fallback: post review without inline comments
                logger.warning("GitHub rejected inline comments (422), posting review without them: %s", resp.text)
                payload["comments"] = []
                resp = await client.post(url, headers=_headers(token), json=payload)
        resp.raise_for_status()
        return resp.json()


async def post_comment(
    repo: str,
    pr_number: int,
    body: str,
    token: str | None = None,
) -> dict:
    """Post an issue comment on a PR (summary comment)."""
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, headers=_headers(token), json={"body": body})
        resp.raise_for_status()
        return resp.json()


async def get_comment_reactions(
    repo: str,
    comment_id: int,
    token: str | None = None,
) -> dict:
    """Get reactions on an issue comment. Returns reaction counts."""
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/issues/comments/{comment_id}/reactions"

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, headers=_headers(token))
        resp.raise_for_status()
        reactions = resp.json()

    counts: dict[str, int] = {}
    for r in reactions:
        content = r.get("content", "unknown")
        counts[content] = counts.get(content, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# GitHub Checks API — per-agent status on PRs
# ---------------------------------------------------------------------------


async def create_check_run(
    repo: str,
    head_sha: str,
    name: str,
    status: str = "queued",
    token: str | None = None,
) -> dict:
    """Create a check run on a commit. Returns the check run object."""
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/check-runs"
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": status,
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, headers=_headers(token), json=payload)
        resp.raise_for_status()
        return resp.json()


async def update_check_run(
    repo: str,
    check_run_id: int,
    status: str | None = None,
    conclusion: str | None = None,
    output: dict | None = None,
    token: str | None = None,
) -> dict:
    """Update a check run. conclusion: success|failure|neutral|cancelled|timed_out."""
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/check-runs/{check_run_id}"
    payload: dict = {}
    if status:
        payload["status"] = status
    if conclusion:
        payload["conclusion"] = conclusion
    if output:
        payload["output"] = output
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.patch(url, headers=_headers(token), json=payload)
        resp.raise_for_status()
        return resp.json()
