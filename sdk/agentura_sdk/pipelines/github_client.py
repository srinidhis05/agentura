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
    """
    token = token or get_token()
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews"

    payload: dict = {
        "body": body,
        "event": event,
        "comments": comments,
    }
    if commit_id:
        payload["commit_id"] = commit_id

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
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
