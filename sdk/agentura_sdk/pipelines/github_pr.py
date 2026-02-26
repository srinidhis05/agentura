"""PR pipeline orchestrator: fetch diff -> sequence skills -> post to GitHub.

Invoked by the Go gateway via POST /api/v1/pipelines/github-pr after receiving
a GitHub pull_request webhook. Runs skills sequentially so each step can
reference prior step output.
"""

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentura_sdk.indexer.skill_mapper import map_skills_for_stage
from agentura_sdk.pipelines import github_client
from agentura_sdk.runner.local_runner import execute_skill, log_execution
from agentura_sdk.runner.skill_loader import load_skill_md
from agentura_sdk.types import SkillContext, SkillResult, SkillRole

logger = logging.getLogger(__name__)

MAX_DIFF_CHARS = 50_000
SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "/skills"))

# Pipeline steps: (domain/skill, required)
PIPELINE_STEPS = [
    ("dev/github-pr-reviewer", True),
    ("dev/pr-doc-generator", False),
    ("dev/e2e-test-generator", False),
    ("dev/service-agent", False),
    ("dev/pr-release-checks", False),
]

# Map pipeline skill path → SDLC stage name from sdlc.yaml
_STEP_STAGE_MAP: dict[str, str] = {
    "dev/github-pr-reviewer": "review",
    "dev/pr-doc-generator": "docs",
    "dev/e2e-test-generator": "test",
    "dev/pr-release-checks": "release",
}

# File extension → language name
_EXT_LANG_MAP: dict[str, str] = {
    ".go": "go",
    ".java": "java",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".rs": "rust",
    ".kt": "kotlin",
    ".rb": "ruby",
}


def _detect_language(file_names: list[str]) -> str:
    """Detect primary language from changed file extensions."""
    counts: dict[str, int] = {}
    for name in file_names:
        ext = Path(name).suffix.lower()
        lang = _EXT_LANG_MAP.get(ext)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1

    if not counts:
        return ""
    return max(counts, key=counts.get)  # type: ignore[arg-type]


def _find_skills_dir() -> Path:
    """Find the skills directory, checking env var then walking up from CWD."""
    env_dir = os.environ.get("SKILLS_DIR") or os.environ.get("AGENTURA_SKILLS_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p

    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "skills"
        if candidate.is_dir():
            return candidate

    return SKILLS_DIR


def _truncate_diff(diff: str, changed_files: list[dict]) -> tuple[str, list[str]]:
    """Truncate diff to MAX_DIFF_CHARS, prioritizing files with most changes.

    Returns (truncated_diff, skipped_file_names).
    """
    if len(diff) <= MAX_DIFF_CHARS:
        return diff, []

    # Sort files by changes (additions + deletions), descending
    sorted_files = sorted(
        changed_files,
        key=lambda f: f.get("changes", 0),
        reverse=True,
    )

    included_files = set()
    budget = MAX_DIFF_CHARS
    for f in sorted_files:
        patch = f.get("patch", "")
        if budget - len(patch) > 0:
            included_files.add(f.get("filename", ""))
            budget -= len(patch)
        else:
            break

    skipped = [
        f.get("filename", "")
        for f in sorted_files
        if f.get("filename", "") not in included_files
    ]

    # Rebuild diff from patches of included files
    parts = []
    for f in sorted_files:
        fname = f.get("filename", "")
        if fname in included_files:
            parts.append(f"diff --git a/{fname} b/{fname}\n{f.get('patch', '')}")

    truncated = "\n".join(parts)
    return truncated[:MAX_DIFF_CHARS], skipped


def _build_skill_context(
    skill_path_str: str,
    input_data: dict[str, Any],
    skills_dir: Path,
) -> SkillContext | None:
    """Load a skill and build its SkillContext."""
    parts = skill_path_str.split("/")
    if len(parts) != 2:
        logger.error("invalid skill path: %s", skill_path_str)
        return None

    domain, skill_name = parts
    skill_md_path = skills_dir / domain / skill_name / "SKILL.md"

    if not skill_md_path.exists():
        logger.warning("skill not found: %s", skill_md_path)
        return None

    loaded = load_skill_md(skill_md_path)

    # Compose 4-layer system prompt
    prompt_parts = []
    if loaded.workspace_context:
        prompt_parts.append(loaded.workspace_context)
    if loaded.domain_context:
        prompt_parts.append(loaded.domain_context)
    if loaded.reflexion_context:
        prompt_parts.append(loaded.reflexion_context)
    prompt_parts.append(loaded.system_prompt)
    system_prompt = "\n\n---\n\n".join(prompt_parts)

    return SkillContext(
        skill_name=loaded.metadata.name,
        domain=loaded.metadata.domain,
        role=loaded.metadata.role,
        model=loaded.metadata.model,
        system_prompt=system_prompt,
        input_data=input_data,
    )


def _format_inline_comments(
    review_result: dict,
    doc_result: dict,
) -> list[dict]:
    """Extract inline review comments from code review and doc suggestions."""
    comments = []

    # From code review: blocking issues + suggestions
    for issue in review_result.get("blocking_issues", []):
        if issue.get("file") and issue.get("line"):
            comments.append({
                "path": issue["file"],
                "line": issue["line"],
                "body": f"**{issue.get('severity', 'issue').upper()}** ({issue.get('category', '')}): {issue.get('description', '')}\n\n> {issue.get('suggestion', '')}",
            })

    for suggestion in review_result.get("suggestions", []):
        if suggestion.get("file") and suggestion.get("line"):
            comments.append({
                "path": suggestion["file"],
                "line": suggestion["line"],
                "body": f"**Suggestion** ({suggestion.get('category', '')}): {suggestion.get('description', '')}\n\n> {suggestion.get('suggestion', '')}",
            })

    # From doc generator: documentation suggestions
    for sugg in doc_result.get("suggestions", []):
        if sugg.get("file") and sugg.get("line"):
            comments.append({
                "path": sugg["file"],
                "line": sugg["line"],
                "body": f"**{sugg.get('severity', 'recommended').upper()} Doc**: {sugg.get('reason', '')}\n\n```\n{sugg.get('content', '')}\n```",
            })

    return comments


def _format_summary_comment(
    step_results: list[dict],
    skipped_files: list[str],
    pipeline_id: str,
) -> str:
    """Format the summary GitHub comment with collapsible sections per skill."""
    lines = [
        "## Agentura PR Pipeline Report",
        "",
        f"Pipeline ID: `{pipeline_id}`",
        "",
    ]

    for step in step_results:
        skill = step["skill"]
        status = step["status"]
        exec_id = step.get("execution_id", "N/A")
        icon = "white_check_mark" if status == "success" else "x"

        lines.append(f"<details>")
        lines.append(f"<summary>:{icon}: <strong>{skill}</strong> — {status} ({step.get('latency_ms', 0):.0f}ms, ${step.get('cost_usd', 0):.4f})</summary>")
        lines.append("")

        output = step.get("output", {})
        if status == "error":
            lines.append(f"**Error**: {output.get('error', 'Unknown error')}")
        elif skill == "dev/github-pr-reviewer":
            lines.append(f"**Verdict**: {output.get('verdict', 'N/A')}")
            lines.append(f"\n{output.get('summary', '')}")
            blocking = output.get("blocking_issues", [])
            if blocking:
                lines.append(f"\n**Blocking Issues**: {len(blocking)}")
        elif skill == "dev/pr-doc-generator":
            coverage = output.get("doc_coverage", {})
            lines.append(f"**Coverage**: {coverage.get('documented', 0)}/{coverage.get('new_public_apis', 0)} public APIs documented")
            lines.append(f"\n{output.get('summary', '')}")
        elif skill == "dev/e2e-test-generator":
            lines.append(f"**Test Cases**: {output.get('total_test_cases', 0)}")
        elif skill == "dev/service-agent":
            lines.append(f"**Test Execution**: {output.get('summary', 'See details')}")
        elif skill == "dev/pr-release-checks":
            checks = output.get("checks", [])
            for check in checks:
                check_icon = {"pass": "white_check_mark", "warn": "warning", "fail": "x"}.get(check.get("status", ""), "question")
                lines.append(f"- :{check_icon}: **{check.get('name', '')}**: {check.get('detail', '')}")
            lines.append(f"\n**Release Ready**: {output.get('release_ready', 'N/A')}")

        lines.append("")
        lines.append(f"<!-- agentura:exec:{exec_id}:{skill} -->")
        lines.append("</details>")
        lines.append("")

    if skipped_files:
        lines.append("<details>")
        lines.append("<summary>:scissors: Skipped files (diff too large)</summary>")
        lines.append("")
        for f in skipped_files:
            lines.append(f"- `{f}`")
        lines.append("</details>")
        lines.append("")

    # Totals
    total_cost = sum(s.get("cost_usd", 0) for s in step_results)
    total_latency = sum(s.get("latency_ms", 0) for s in step_results)
    lines.append(f"---")
    lines.append(f"**Total**: ${total_cost:.4f} | {total_latency:.0f}ms")
    lines.append("")
    lines.append("*Powered by [Agentura](https://github.com/agentura-ai/agentura)*")

    return "\n".join(lines)


async def run_pr_pipeline(pr_event: dict) -> dict:
    """Main pipeline entry point. Called by the executor endpoint."""
    start = time.monotonic()
    pipeline_id = f"PIPE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    repo = pr_event.get("repo", "")
    pr_number = pr_event.get("pr_number", 0)
    head_sha = pr_event.get("head_sha", "")

    logger.info(
        "starting PR pipeline",
        extra={"pipeline_id": pipeline_id, "repo": repo, "pr": pr_number},
    )

    # 1. Fetch diff + file list from GitHub
    token = github_client.get_token()
    try:
        diff = await github_client.fetch_pr_diff(repo, pr_number, token)
        changed_files = await github_client.fetch_pr_files(repo, pr_number, token)
    except Exception as e:
        logger.error("failed to fetch PR data: %s", e)
        return {
            "pipeline_id": pipeline_id,
            "pr_number": pr_number,
            "repo": repo,
            "error": f"Failed to fetch PR data: {e}",
            "steps": [],
        }

    # 2. Truncate diff if needed
    file_names = [f.get("filename", "") for f in changed_files]
    diff, skipped_files = _truncate_diff(diff, changed_files)

    # 3. Build common context
    common_input = {
        "pr_url": pr_event.get("pr_url", ""),
        "pr_title": pr_event.get("pr_title", ""),
        "pr_description": pr_event.get("pr_body", ""),
        "diff": diff,
        "changed_files": file_names,
        "head_branch": pr_event.get("head_branch", ""),
        "base_branch": pr_event.get("base_branch", ""),
    }

    skills_dir = _find_skills_dir()
    step_results: list[dict] = []

    # Detect primary language from changed files for expertise loading
    pr_language = _detect_language(file_names)

    # Track outputs for cross-step dependencies
    review_output: dict = {}
    doc_output: dict = {}
    test_gen_output: dict = {}

    # 4. Execute pipeline steps sequentially
    for skill_path, required in PIPELINE_STEPS:
        step_start = time.monotonic()

        # Build per-skill input (common + step-specific context)
        step_input = dict(common_input)

        # Inject prior step outputs where relevant
        if skill_path == "dev/service-agent" and test_gen_output:
            step_input["task"] = "Run the generated tests and report coverage"
            step_input["generated_tests"] = test_gen_output.get("code_snippet", "")
            step_input["test_suites"] = test_gen_output.get("test_suites", [])
        elif skill_path == "dev/pr-release-checks":
            step_input["labels"] = pr_event.get("labels", [])

        # Inject expertise from sdlc.yaml (skip service-agent — gets its own)
        stage = _STEP_STAGE_MAP.get(skill_path)
        if stage:
            expertise_skills = map_skills_for_stage(stage, pr_language)
            if expertise_skills:
                step_input["expertise"] = "\n\n---\n\n".join(
                    s.content for s in expertise_skills
                )
                logger.info(
                    "loaded %d expertise skill(s) for stage %s: %s",
                    len(expertise_skills),
                    stage,
                    ", ".join(s.name for s in expertise_skills),
                )

        try:
            ctx = _build_skill_context(skill_path, step_input, skills_dir)
            if ctx is None:
                raise FileNotFoundError(f"Skill {skill_path} not found")

            result = await execute_skill(ctx)
            step_latency = (time.monotonic() - step_start) * 1000
            exec_id = log_execution(ctx, result)

            step_record = {
                "skill": skill_path,
                "status": "success" if result.success else "error",
                "execution_id": exec_id,
                "latency_ms": step_latency,
                "cost_usd": result.cost_usd,
                "output": result.output,
            }

            # Track outputs for downstream steps
            if skill_path == "dev/github-pr-reviewer":
                review_output = result.output
            elif skill_path == "dev/pr-doc-generator":
                doc_output = result.output
            elif skill_path == "dev/e2e-test-generator":
                test_gen_output = result.output

        except Exception as e:
            step_latency = (time.monotonic() - step_start) * 1000
            logger.error("skill %s failed: %s", skill_path, e)
            step_record = {
                "skill": skill_path,
                "status": "error",
                "execution_id": "N/A",
                "latency_ms": step_latency,
                "cost_usd": 0.0,
                "output": {"error": str(e)},
            }

        step_results.append(step_record)

    # 5. Post results to GitHub
    github_review_posted = False
    github_comment_posted = False

    if token:
        # Post inline review
        try:
            inline_comments = _format_inline_comments(review_output, doc_output)
            review_body = review_output.get("summary", "Automated review by Agentura PR Pipeline")

            if inline_comments or review_body:
                # Determine review event based on blocking issues
                has_blocking = bool(review_output.get("blocking_issues"))
                event = "REQUEST_CHANGES" if has_blocking else "COMMENT"

                await github_client.post_review(
                    repo=repo,
                    pr_number=pr_number,
                    comments=inline_comments,
                    body=review_body,
                    event=event,
                    commit_id=head_sha,
                    token=token,
                )
                github_review_posted = True
        except Exception as e:
            logger.error("failed to post GitHub review: %s", e)

        # Post summary comment
        try:
            summary = _format_summary_comment(step_results, skipped_files, pipeline_id)
            await github_client.post_comment(
                repo=repo,
                pr_number=pr_number,
                body=summary,
                token=token,
            )
            github_comment_posted = True
        except Exception as e:
            logger.error("failed to post GitHub summary comment: %s", e)

    total_latency = (time.monotonic() - start) * 1000
    total_cost = sum(s.get("cost_usd", 0) for s in step_results)

    result = {
        "pipeline_id": pipeline_id,
        "pr_number": pr_number,
        "repo": repo,
        "steps": [
            {k: v for k, v in s.items() if k != "output"}
            for s in step_results
        ],
        "github_review_posted": github_review_posted,
        "github_comment_posted": github_comment_posted,
        "total_cost_usd": total_cost,
        "total_latency_ms": total_latency,
    }

    logger.info(
        "PR pipeline completed",
        extra={
            "pipeline_id": pipeline_id,
            "repo": repo,
            "pr": pr_number,
            "cost": total_cost,
            "latency_ms": total_latency,
        },
    )

    return result


async def collect_pr_feedback(
    repo: str,
    comment_id: int,
    execution_ids: dict[str, str],
    token: str | None = None,
) -> list[dict]:
    """Poll reactions on a bot comment and create corrections for thumbs-down.

    Called by a cron job or manually via the CLI.

    Args:
        repo: "owner/repo"
        comment_id: GitHub comment ID
        execution_ids: mapping of skill path -> execution ID from the comment markers
        token: GitHub API token

    Returns:
        List of corrections created.
    """
    token = token or github_client.get_token()
    reactions = await github_client.get_comment_reactions(repo, comment_id, token)

    corrections = []
    thumbs_down = reactions.get("-1", 0)
    if thumbs_down > 0:
        for skill_path, exec_id in execution_ids.items():
            corrections.append({
                "execution_id": exec_id,
                "skill": skill_path,
                "correction": "Developer indicated review was unhelpful (thumbs-down reaction)",
                "source": "github_reaction",
            })

    return corrections
