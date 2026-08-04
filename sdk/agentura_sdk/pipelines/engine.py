"""Generic pipeline engine — loads YAML configs and executes skill chains.

New pipeline = new YAML file in pipelines/. Zero code changes.
Supports both flat `steps:` (sequential) and `phases:` (parallel/sequential mix).
"""

import asyncio
import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agentura_sdk.runner.local_runner import execute_skill, log_execution
from agentura_sdk.runner.skill_loader import load_skill_md
from agentura_sdk.types import SandboxConfig, SkillContext, SkillRole

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "/skills"))
PIPELINES_DIR = Path(os.environ.get("PIPELINES_DIR", str(Path(__file__).parents[3] / "pipelines")))


@dataclass
class PipelineStep:
    skill: str
    agent_id: str = ""
    required: bool = True


@dataclass
class PipelinePhase:
    name: str
    type: str = "sequential"  # "sequential" | "parallel"
    steps: list[PipelineStep] = field(default_factory=list)
    fan_out_from: str | None = None
    fan_in_from: str | None = None


@dataclass
class PipelineDef:
    name: str
    description: str = ""
    input_mapping: dict[str, str] = field(default_factory=dict)
    steps: list[PipelineStep] = field(default_factory=list)
    phases: list[PipelinePhase] = field(default_factory=list)
    trigger: dict[str, Any] = field(default_factory=dict)


def _parse_steps(raw_steps: list[dict]) -> list[PipelineStep]:
    return [
        PipelineStep(
            skill=s["skill"],
            agent_id=s.get("agent_id", ""),
            required=s.get("required", True),
        )
        for s in raw_steps
    ]


def load_pipeline(name: str) -> PipelineDef:
    """Load a pipeline definition from pipelines/{name}.yaml."""
    path = PIPELINES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Pipeline not found: {name} (looked in {path})")

    raw = yaml.safe_load(path.read_text()) or {}

    # Parse phases if present (new format), else wrap flat steps in a single phase
    phases: list[PipelinePhase] = []
    if "phases" in raw:
        for p in raw["phases"]:
            phases.append(PipelinePhase(
                name=p.get("name", ""),
                type=p.get("type", "sequential"),
                steps=_parse_steps(p.get("steps", [])),
                fan_out_from=p.get("fan_out_from"),
                fan_in_from=p.get("fan_in_from"),
            ))

    # Flat steps (backward compat)
    flat_steps = _parse_steps(raw.get("steps", []))

    return PipelineDef(
        name=raw.get("name", name),
        description=raw.get("description", ""),
        input_mapping=raw.get("input_mapping", {}),
        steps=flat_steps,
        phases=phases,
        trigger=raw.get("trigger", {}),
    )


def list_pipelines() -> list[PipelineDef]:
    """List all available pipeline definitions."""
    if not PIPELINES_DIR.exists():
        return []
    return [
        load_pipeline(p.stem)
        for p in sorted(PIPELINES_DIR.glob("*.yaml"))
    ]


def _apply_input_mapping(input_data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """Apply input_mapping: if source key exists and target doesn't, copy it."""
    result = dict(input_data)
    for source, target in mapping.items():
        if source in result and target not in result:
            result[target] = result[source]
    return result


def _build_skill_context(
    skill_path_str: str,
    input_data: dict[str, Any],
    skills_dir: Path,
) -> SkillContext | None:
    """Load a skill and build its SkillContext with sandbox config if agent."""
    parts = skill_path_str.split("/")
    if len(parts) != 2:
        logger.error("invalid skill path: %s", skill_path_str)
        return None

    domain, skill_name = parts
    skill_dir = skills_dir / domain / skill_name
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_md_path.exists():
        logger.warning("skill not found: %s", skill_md_path)
        return None

    loaded = load_skill_md(skill_md_path)

    prompt_parts = []
    if loaded.workspace_context:
        prompt_parts.append(loaded.workspace_context)
    if loaded.domain_context:
        prompt_parts.append(loaded.domain_context)
    if loaded.reflexion_context:
        prompt_parts.append(loaded.reflexion_context)
    # Inject project configs (ClickUp IDs, assignees, channels)
    configs_dir = skill_dir.parent / "project-configs"
    if configs_dir.is_dir():
        cfg_parts: list[str] = []
        ws_file = configs_dir / "_workspace.md"
        if ws_file.exists():
            cfg_parts.append(ws_file.read_text().strip())
        for cf in sorted(configs_dir.glob("*.md")):
            if not cf.name.startswith("_"):
                cfg_parts.append(cf.read_text().strip())
        if cfg_parts:
            header = "## Project Configurations\n\nUse these configs for workspace IDs, list IDs, assignee mappings, and channel references. Do NOT ask the user for IDs that are listed here.\n"
            prompt_parts.append(header + "\n\n---\n\n".join(cfg_parts))
    prompt_parts.append(loaded.system_prompt)
    system_prompt = "\n\n---\n\n".join(prompt_parts)

    sandbox_config = None
    mcp_bindings: list[dict] = []

    # Bind MCP tools for ANY skill that declares them (not just agents).
    # Specialists like pr-context-enricher need Datadog/Jira MCP access.
    if loaded.metadata.role == SkillRole.AGENT:
        sandbox_config = SandboxConfig()

    config_path = skill_dir / "agentura.config.yaml"
    if config_path.exists():
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
            sandbox_raw = cfg.get("sandbox", {}) or cfg.get("agent", {})
            if sandbox_raw and sandbox_config is not None:
                sandbox_config = SandboxConfig(**sandbox_raw)
            gateway_api_key = os.environ.get("MCP_GATEWAY_API_KEY", "")
            # mcp_tools can be at top level OR inside skills[].mcp_tools
            mcp_tools = cfg.get("mcp_tools", [])
            if not mcp_tools:
                for skill_cfg in cfg.get("skills", []):
                    if skill_cfg.get("name") == loaded.metadata.name:
                        mcp_tools = skill_cfg.get("mcp_tools", [])
                        break
            for mcp_ref in mcp_tools:
                server_name = mcp_ref.get("server", "")
                tools = mcp_ref.get("tools", [])
                binding: dict | None = None

                # 1. Explicit env var
                env_key = f"MCP_{server_name.upper().replace('-', '_')}_URL"
                server_url = os.environ.get(env_key, "")
                if server_url:
                    binding = {"server": server_name, "url": server_url, "tools": tools}
                    auth_key = f"MCP_{server_name.upper().replace('-', '_')}_API_KEY"
                    api_key = os.environ.get(auth_key, "")
                    if api_key:
                        binding["headers"] = {"Authorization": f"Bearer {api_key}"}

                # 2. MCP registry fallback (Obot auto-discovery)
                if binding is None:
                    try:
                        from agentura_sdk.mcp.registry import get_registry
                        reg = get_registry()
                        srv = reg.get(server_name)
                        if srv and srv.url:
                            binding = {"server": server_name, "url": srv.url, "tools": tools}
                            if gateway_api_key:
                                binding["headers"] = {"Authorization": f"Bearer {gateway_api_key}"}
                            logger.debug("MCP server %s resolved via registry: %s", server_name, srv.url)
                    except Exception:
                        pass

                if binding is None:
                    if not mcp_ref.get("optional"):
                        logger.warning("MCP server %s: no URL found (env var %s not set, registry empty)", server_name, env_key)
                    continue

                if mcp_ref.get("approval_required"):
                    binding["approval_required"] = mcp_ref["approval_required"]
                mcp_bindings.append(binding)
                logger.info("MCP tool bound: %s → %s (%d tools)", server_name, binding["url"], len(tools))
        except Exception:
            pass

    return SkillContext(
        skill_name=loaded.metadata.name,
        domain=loaded.metadata.domain,
        role=loaded.metadata.role,
        model=loaded.metadata.model,
        system_prompt=system_prompt,
        input_data=input_data,
        mcp_bindings=mcp_bindings,
        sandbox_config=sandbox_config,
    )


def _sse(event_type: str, data: dict) -> str:
    """Format a single SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _run_flat_steps(
    steps: list[PipelineStep],
    normalized: dict[str, Any],
    carry_forward: dict[str, Any],
    skills_dir: Path,
) -> list[dict]:
    """Execute flat steps sequentially, returning step result dicts."""
    step_results: list[dict] = []
    for step_idx, step in enumerate(steps, 1):
        step_start = time.monotonic()
        step_input = dict(normalized)
        step_input.update(carry_forward)

        try:
            ctx = _build_skill_context(step.skill, step_input, skills_dir)
            if ctx is None:
                raise FileNotFoundError(f"Skill {step.skill} not found")

            result = await execute_skill(ctx)
            step_latency = (time.monotonic() - step_start) * 1000
            exec_id = log_execution(ctx, result)

            step_results.append({
                "step": step_idx,
                "skill": step.skill,
                "status": "success" if result.success else "error",
                "execution_id": exec_id,
                "latency_ms": step_latency,
                "cost_usd": result.cost_usd,
                "output": result.output,
            })

            if result.context_for_next:
                carry_forward.update(result.context_for_next)

            if not result.success and step.required:
                break

        except Exception as e:
            step_latency = (time.monotonic() - step_start) * 1000
            logger.error("step %d (%s) failed: %s", step_idx, step.skill, e)
            step_results.append({
                "step": step_idx,
                "skill": step.skill,
                "status": "error",
                "execution_id": "N/A",
                "latency_ms": step_latency,
                "cost_usd": 0.0,
                "output": {"error": str(e)},
            })
            if step.required:
                break
    return step_results


def _get_fleet_store():
    """Lazy-load FleetStore to avoid import at module level."""
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        return None
    try:
        from agentura_sdk.memory.fleet_store import FleetStore
        return FleetStore(dsn)
    except Exception:
        return None


MAX_AGENT_OUTPUT_CHARS = int(os.environ.get("MAX_AGENT_OUTPUT_CHARS", "50000"))


def _compact_agent_results(results: list[dict]) -> list[dict]:
    """Strip large fields from agent results for fan-in phases.

    Specialist skills wrap JSON output in markdown code blocks (```json ... ```).
    Parse these to clean structured data to avoid blowing the context window.
    Per-agent output is capped at MAX_AGENT_OUTPUT_CHARS to prevent exceeding
    the 200K token limit on downstream skills (verifier, reporter).
    """
    import re

    compacted = []
    for r in results:
        entry = {
            "agent_id": r.get("agent_id", ""),
            "skill": r.get("skill", ""),
            "success": r.get("success", False),
            "execution_id": r.get("execution_id", ""),
            "cost_usd": r.get("cost_usd", 0),
            "latency_ms": r.get("latency_ms", 0),
        }
        output = r.get("output", {})
        if isinstance(output, dict):
            raw = output.get("raw_output", "")
            if isinstance(raw, str) and raw.strip().startswith("```"):
                # Parse JSON from markdown code block
                match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
                if match:
                    try:
                        entry["output"] = json.loads(match.group(1))
                    except json.JSONDecodeError:
                        entry["output"] = output
                else:
                    entry["output"] = output
            else:
                entry["output"] = output
        else:
            entry["output"] = output

        # Cap output size to prevent blowing context window on downstream fan-in
        serialized = json.dumps(entry["output"], default=str)
        if len(serialized) > MAX_AGENT_OUTPUT_CHARS:
            agent_id = entry["agent_id"]
            original_len = len(serialized)
            truncated = serialized[:MAX_AGENT_OUTPUT_CHARS]
            entry["output"] = {
                "truncated": True,
                "original_chars": original_len,
                "content": truncated,
                "note": f"Output truncated from {original_len} to {MAX_AGENT_OUTPUT_CHARS} chars for fan-in",
            }
            logger.warning(
                "agent %s output truncated: %d -> %d chars",
                agent_id, original_len, MAX_AGENT_OUTPUT_CHARS,
            )
        compacted.append(entry)
    return compacted


def _truncate_diff(diff: str, changed_files: list[dict],
                   max_chars: int = 500_000) -> tuple[str, list[str]]:
    """Truncate diff to max_chars, prioritizing files with most changes.

    Returns (truncated_diff, skipped_file_names).
    """
    if len(diff) <= max_chars:
        return diff, []

    sorted_files = sorted(
        changed_files,
        key=lambda f: f.get("changes", 0),
        reverse=True,
    )

    included_files: set[str] = set()
    budget = max_chars
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

    parts = []
    for f in sorted_files:
        fname = f.get("filename", "")
        if fname in included_files:
            parts.append("diff --git a/%s b/%s\n%s" % (fname, fname, f.get("patch", "")))

    return "\n".join(parts)[:max_chars], skipped


async def _prefetch_pr_data(input_data: dict[str, Any]) -> dict[str, Any]:
    """For GitHub PR pipelines, fetch diff and changed files before fan-out.

    Truncates the diff to 500K chars (~125K tokens) to stay within context
    limits. Opus 4.6 (1M ctx) handles this easily; Sonnet 4.5 (200K ctx)
    needs the headroom for system prompt + output.
    """
    repo = input_data.get("Repo") or input_data.get("repo")
    pr_number = input_data.get("PRNumber") or input_data.get("pr_number")
    if not repo or not pr_number:
        return input_data

    enriched = dict(input_data)
    try:
        from agentura_sdk.pipelines.github_client import fetch_pr_diff, fetch_pr_files
        # Prefer fresh token from gateway input over stale env var
        token = input_data.get("github_token") or None
        diff = await fetch_pr_diff(repo=repo, pr_number=int(pr_number), token=token)
        files = await fetch_pr_files(repo=repo, pr_number=int(pr_number), token=token)
        original_len = len(diff)
        diff, skipped = _truncate_diff(diff, files)
        enriched["diff"] = diff
        enriched["changed_files"] = files
        if skipped:
            enriched["skipped_files"] = skipped
            logger.info("prefetched PR diff (%d->%d chars, skipped %d files) for %s#%s",
                        original_len, len(diff), len(skipped), repo, pr_number)
        else:
            logger.info("prefetched PR diff (%d chars) and %d changed files for %s#%s",
                        len(diff), len(files), repo, pr_number)
    except Exception as e:
        logger.error("failed to prefetch PR data for %s#%s: %s", repo, pr_number, e)
    return enriched


def _extract_reviewer_output(all_results: list[dict]) -> dict[str, Any]:
    """Find the pr-code-reviewer output from pipeline results."""
    logger.debug("searching %d results for pr-code-reviewer output: skills=%s",
                 len(all_results), [r.get("skill") for r in all_results])
    for r in all_results:
        skill = r.get("skill", "")
        success = r.get("success") or r.get("status") == "success"
        logger.debug("checking result: skill=%s success=%s has_output=%s", skill, success, bool(r.get("output")))
        if skill in ("dev/pr-code-reviewer", "dev/pr-deep-reviewer") and success:
            output = r.get("output", {})
            # Output may be nested under raw_output as JSON in a markdown code block
            if isinstance(output, dict) and "findings" in output:
                return output
            raw = output.get("raw_output", "") if isinstance(output, dict) else ""
            if isinstance(raw, str) and "```" in raw:
                import re
                match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        pass
            return output
    return {}


def _format_review_comments(review_output: dict[str, Any]) -> list[dict]:
    """Format findings as GitHub inline review comments."""
    comments = []
    severity_icon = {
        "BLOCKER": "rotating_light",
        "WARNING": "warning",
        "SUGGESTION": "bulb",
    }

    for finding in review_output.get("findings", []):
        severity = finding.get("severity", "").upper()
        if severity == "PRAISE" or not finding.get("file") or not finding.get("line"):
            continue

        icon = severity_icon.get(severity, "memo")
        body_parts = [f":{icon}: **{severity}**: {finding.get('title', '')}"]
        if finding.get("reason"):
            body_parts.append(f"\n{finding['reason']}")
        if finding.get("snippet"):
            body_parts.append(f"\n```\n{finding['snippet']}\n```")
        if finding.get("suggestion"):
            body_parts.append(f"\n> **Suggestion**: {finding['suggestion']}")

        comments.append({
            "path": finding["file"],
            "line": finding["line"],
            "body": "\n".join(body_parts),
        })

    return comments


def _record_reflexion_feedback(all_results: list[dict], input_data: dict) -> None:
    """Feed verifier verdicts back into the reflexion store.

    When the verifier marks a finding as false_positive, create a negative
    reflexion so the reviewer is less confident on that pattern next time.
    When findings are verified, boost the injected reflexions' utility scores.
    """
    try:
        from agentura_sdk.memory import get_memory_store
        store = get_memory_store()
    except Exception:
        return

    repo = input_data.get("Repo") or input_data.get("repo", "")

    # Find verifier output
    verifier_output = None
    reviewer_reflexion_ids = []
    for r in all_results:
        skill = r.get("skill", "")
        if "verifier" in skill:
            verifier_output = r.get("output", {})
        if "reviewer" in skill and r.get("injected_reflexion_ids"):
            reviewer_reflexion_ids = r.get("injected_reflexion_ids", [])

    if not verifier_output:
        return

    # Parse verifier findings
    findings = verifier_output.get("findings", [])
    false_positives = [f for f in findings if f.get("status") == "false_positive"]
    verified = [f for f in findings if f.get("status") == "verified"]

    # Create negative reflexions for false positives
    for fp in false_positives:
        title = fp.get("title", "")
        severity = fp.get("severity", "")
        reason = fp.get("reason", "")
        if title:
            content = (
                f"FALSE POSITIVE on {repo}: '{title}' ({severity}) was flagged "
                f"but verifier determined: {reason}. Lower confidence on this pattern."
            )
            try:
                store.create_reflexion(
                    execution_id="",
                    rule=content,
                    skill_path="dev/pr-code-reviewer",
                    scope=f"repo:{repo}",
                )
                logger.info("Created false-positive reflexion for repo=%s finding=%s", repo, title[:50])
            except Exception as e:
                logger.debug("Failed to create reflexion: %s", e)

    # Boost utility scores for reflexions that led to verified findings
    if verified and reviewer_reflexion_ids:
        for rid in reviewer_reflexion_ids:
            try:
                store.record_execution_success(rid)
                logger.info("Boosted reflexion %s (verified findings found)", rid)
            except Exception as e:
                logger.debug("Failed to boost reflexion: %s", e)

    if false_positives or (verified and reviewer_reflexion_ids):
        logger.info(
            "Reflexion feedback: %d false positives logged, %d reflexions boosted for repo=%s",
            len(false_positives), len(reviewer_reflexion_ids) if verified else 0, repo,
        )


async def _maybe_post_pr_review(
    pipeline_name: str,
    input_data: dict[str, Any],
    all_results: list[dict],
) -> None:
    """Post inline review comments and summary comment for PR pipelines."""
    if not pipeline_name.startswith("github-pr"):
        logger.debug("skipping PR review posting — pipeline %r is not a github-pr pipeline", pipeline_name)
        return

    repo = input_data.get("Repo") or input_data.get("repo")
    pr_number = input_data.get("PRNumber") or input_data.get("pr_number")
    head_sha = input_data.get("HeadSHA") or input_data.get("head_sha")
    logger.info("PR review posting: repo=%s pr_number=%s head_sha=%s input_keys=%s",
                repo, pr_number, head_sha, list(input_data.keys()))
    if not repo or not pr_number:
        logger.warning("skipping PR review posting — missing repo=%s or pr_number=%s", repo, pr_number)
        return

    from agentura_sdk.pipelines import github_client
    # Prefer fresh token from gateway input over stale env var
    token = input_data.get("github_token") or github_client.get_token()
    if not token:
        logger.warning("GITHUB_TOKEN not set — skipping PR review posting")
        return

    # Post inline review from code reviewer findings
    review_output = _extract_reviewer_output(all_results)
    logger.info("reviewer output extracted: has_findings=%s, verdict=%s, keys=%s",
                bool(review_output.get("findings")),
                review_output.get("verdict", "<none>"),
                list(review_output.keys()) if review_output else [])
    if review_output:
        try:
            inline_comments = _format_review_comments(review_output)
            summary = review_output.get("summary", "Automated review by Agentura")

            # Always use COMMENT — never REQUEST_CHANGES during beta rollout.
            # REQUEST_CHANGES blocks merge, which is too aggressive before
            # severity calibration is complete. Graduate to REQUEST_CHANGES
            # after false positive rate < 10% across 50+ reviews.
            event = "COMMENT"

            await github_client.post_review(
                repo=repo,
                pr_number=int(pr_number),
                comments=inline_comments,
                body=summary,
                event=event,
                commit_id=head_sha,
                token=token,
            )
            logger.info("posted PR inline review on %s#%s (%d comments, event=%s)",
                        repo, pr_number, len(inline_comments), event)
        except Exception as e:
            logger.error("failed to post PR inline review on %s#%s: %s", repo, pr_number, e, exc_info=True)
    else:
        logger.warning("no reviewer output found — skipping inline review on %s#%s", repo, pr_number)

    # Post reporter summary as a PR comment — but skip if findings unchanged
    final_output = all_results[-1].get("output", {}) if all_results else {}
    logger.debug("reporter final_output keys=%s", list(final_output.keys()) if isinstance(final_output, dict) else type(final_output))
    body = final_output.get("raw_output") or final_output.get("output", "")
    if body:
        # Dedup: check if the last Shipwright comment has the same findings
        if await _is_duplicate_review_comment(repo, int(pr_number), body, token):
            logger.info("skipping duplicate review comment on %s#%s — findings unchanged", repo, pr_number)
        else:
            try:
                await github_client.post_comment(repo=repo, pr_number=int(pr_number), body=body, token=token)
                logger.info("posted PR summary comment on %s#%s", repo, pr_number)
            except Exception as e:
                logger.error("failed to post PR summary comment on %s#%s: %s", repo, pr_number, e)


async def _is_duplicate_review_comment(repo: str, pr_number: int, new_body: str, token: str) -> bool:
    """Check if posting this review would be noise.

    Two conditions that skip posting:
    1. Same findings — the last Shipwright comment has identical verdict+findings
       (cost/duration change every run, so we ignore those)
    2. Recent review — a Shipwright comment was posted in the last 24 hours and
       findings are the same (batching: avoid reviewing unchanged code repeatedly)

    If the code changed and findings are different → always post.
    """
    import hashlib
    from datetime import datetime, timezone, timedelta
    try:
        comments = await github_client.get_pr_comments(repo, pr_number, token)
        bot_comments = [
            c for c in comments
            if c.get("user", {}).get("login") == "shipwright-crew[bot]"
            and ("Shipwright Review" in c.get("body", "") or "Deep Review" in c.get("body", ""))
        ]
        if not bot_comments:
            return False

        last_comment = bot_comments[-1]
        last_body = last_comment["body"]
        last_created = last_comment.get("created_at", "")

        # Hash the substantive part (verdict + findings) — ignore run-specific metadata
        def findings_hash(body: str) -> str:
            lines = []
            for line in body.split("\n"):
                if any(skip in line.lower() for skip in [
                    "total cost:", "cost:", "duration:", "fleet session:",
                    "exec-", "generated:", "| duration", "| cost"
                ]):
                    continue
                lines.append(line.strip())
            return hashlib.md5("\n".join(lines).encode()).hexdigest()

        old_hash = findings_hash(last_body)
        new_hash = findings_hash(new_body)

        # Same findings → always skip (regardless of time)
        if old_hash == new_hash:
            logger.info("skipping duplicate review on %s#%d — findings unchanged (hash: %s)",
                        repo, pr_number, old_hash[:8])
            return True

        # Different findings but recent review → post (code actually changed)
        # This ensures new pushes with real changes get a fresh review
        logger.info("findings changed on %s#%d — posting new review (old: %s, new: %s)",
                    repo, pr_number, old_hash[:8], new_hash[:8])
        return False
    except Exception as e:
        logger.debug("duplicate check failed (allowing post): %s", e)
        return False


async def run_pipeline(name: str, pipeline_input: dict[str, Any]) -> dict[str, Any]:
    """Run a named pipeline synchronously, return aggregated result.

    Supports both flat ``steps:`` (sequential) and ``phases:`` (parallel/sequential mix).
    When ``phases:`` is present it takes precedence over flat ``steps:``.
    """
    pipeline = load_pipeline(name)
    skills_dir = SKILLS_DIR
    start = time.monotonic()
    all_results: list[dict] = []
    carry_forward: dict[str, Any] = {}
    total_expected = 0
    session_id = ""

    normalized = _apply_input_mapping(pipeline_input, pipeline.input_mapping)

    # Prefetch PR diff + changed files for GitHub PR pipelines
    if name.startswith("github-pr"):
        normalized = await _prefetch_pr_data(normalized)

    if pipeline.phases:
        # --- Fleet session tracking for phase-based pipelines ---
        store = _get_fleet_store()
        total_agents = sum(len(p.steps) for p in pipeline.phases)
        if store:
            session_id = store.create_session(
                pipeline_name=name,
                trigger_type=pipeline.trigger.get("type", "manual"),
                total_agents=total_agents,
                input_data=pipeline_input,
            )
            store.update_session_status(session_id, "running")

        # --- Phase-based execution (parallel + sequential mix) ---
        for phase in pipeline.phases:
            total_expected += len(phase.steps)

            # Strip diff from downstream fan-in phases (verify, report) that
            # only need agent_results. Keep diff for phases that consume it
            # (analyze, deep-analyze). Heuristic: strip only if the fan-in
            # source was the analyze/deep-analyze phase (not triage).
            strip_diff = (
                phase.fan_in_from
                and phase.fan_in_from in ("analyze", "deep-analyze")
            )
            if strip_diff:
                phase_input = {
                    k: v for k, v in normalized.items()
                    if k not in ("diff", "changed_files")
                }
            else:
                phase_input = dict(normalized)
            phase_input.update(carry_forward)

            if phase.type == "parallel":
                # Skip agents from: .shipwright.yaml (in input_data) > triage output (in carry_forward)
                skip_agents = set(normalized.get("skip_agents", []))
                skip_agents.update(carry_forward.get("skip_agents", []))
                active_steps = [
                    s for s in phase.steps
                    if (s.agent_id or s.skill.split("/")[-1]) not in skip_agents
                ]
                if skip_agents and len(active_steps) < len(phase.steps):
                    skipped = [s.agent_id or s.skill for s in phase.steps if s not in active_steps]
                    logger.info("triage skip_agents: skipping %s (saving ~$%.2f)",
                                skipped, len(skipped) * 0.7)
                skipped_phase = PipelinePhase(
                    name=phase.name, type=phase.type, steps=active_steps,
                    fan_in_from=phase.fan_in_from,
                )

                # Register agents in fleet store
                if store and session_id:
                    for step in active_steps:
                        aid = step.agent_id or step.skill.replace("/", "-")
                        try:
                            store.create_agent(session_id, f"{session_id}-{aid}", step.skill)
                        except Exception:
                            pass

                phase_results = await execute_parallel_phase(skipped_phase, phase_input, skills_dir)
                all_results.extend(phase_results)

                # Update fleet store with per-agent results
                if store and session_id:
                    for r in phase_results:
                        aid = r.get("agent_id", "")
                        try:
                            store.update_agent_status(
                                f"{session_id}-{aid}",
                                "completed" if r.get("success") else "failed",
                                execution_id=r.get("execution_id", ""),
                                success=r.get("success", False),
                                output=r.get("output"),
                                cost_usd=r.get("cost_usd", 0),
                                latency_ms=r.get("latency_ms", 0),
                            )
                        except Exception:
                            pass

                # Merge context_for_next from all parallel agents
                for r in phase_results:
                    cfn = r.pop("context_for_next", {})
                    if cfn:
                        carry_forward.update(cfn)
                # Inject agent_results for downstream fan-in phases.
                # Parse raw_output (JSON wrapped in ```json ... ```) to clean
                # structured data so downstream phases don't get bloated strings.
                carry_forward["agent_results"] = _compact_agent_results(phase_results)
            else:
                # Register agents in fleet store for sequential phases too
                if store and session_id:
                    for step in phase.steps:
                        aid = step.agent_id or step.skill.replace("/", "-")
                        try:
                            store.create_agent(session_id, f"{session_id}-{aid}", step.skill)
                        except Exception:
                            pass

                seq_results = await _run_flat_steps(phase.steps, phase_input, carry_forward, skills_dir)
                all_results.extend(seq_results)

                # Update fleet store with per-agent results for sequential phases
                if store and session_id:
                    for r in seq_results:
                        aid = r.get("agent_id", "")
                        try:
                            store.update_agent_status(
                                f"{session_id}-{aid}",
                                "completed" if r.get("success") else "failed",
                                execution_id=r.get("execution_id", ""),
                                success=r.get("success", False),
                                output=r.get("output"),
                                cost_usd=r.get("cost_usd", 0),
                                latency_ms=r.get("latency_ms", 0),
                            )
                        except Exception:
                            pass

                # Propagate agent_results for downstream fan-in phases
                carry_forward["agent_results"] = _compact_agent_results(seq_results)

                # Extract triage directives (skip_agents, model_override) into carry_forward
                for r in seq_results:
                    output = r.get("output") or {}
                    if isinstance(output, str):
                        try:
                            output = json.loads(output)
                        except (json.JSONDecodeError, TypeError):
                            output = {}
                    if "skip_agents" in output:
                        carry_forward["skip_agents"] = output["skip_agents"]
                        logger.info("triage directive: skip_agents=%s", output["skip_agents"])

            # Check for required-step failures — abort remaining phases
            has_required_failure = any(
                r.get("success") is False and r.get("required", True)
                for r in all_results
            )
            if has_required_failure:
                break
    else:
        # --- Flat steps (backward compat) ---
        total_expected = len(pipeline.steps)
        all_results = await _run_flat_steps(pipeline.steps, normalized, carry_forward, skills_dir)

    total_latency = (time.monotonic() - start) * 1000
    all_success = all(
        r.get("status") == "success" or r.get("success") is True
        for r in all_results
    )
    total_cost = sum(r.get("cost_usd", 0) for r in all_results)
    final_output = all_results[-1].get("output", {}) if all_results else {}

    # Update fleet session final status
    if session_id:
        store = _get_fleet_store()
        if store:
            completed = sum(1 for r in all_results if r.get("success") or r.get("status") == "success")
            failed = sum(1 for r in all_results if not (r.get("success") or r.get("status") == "success"))
            store.update_session_status(
                session_id,
                status="completed" if all_success else "failed",
                completed_agents=completed,
                failed_agents=failed,
                total_cost_usd=total_cost,
            )

    # Post inline review + summary comment for GitHub PR pipelines
    await _maybe_post_pr_review(name, normalized, all_results)

    # Feed verifier verdicts back to reflexion store (closes the learning loop)
    _record_reflexion_feedback(all_results, normalized)

    return {
        "pipeline": name,
        "session_id": session_id,
        "success": all_success,
        "steps": all_results,
        "steps_completed": len(all_results),
        "total_steps": total_expected,
        "total_latency_ms": total_latency,
        "total_cost_usd": total_cost,
        "url": (
            final_output.get("url")
            or (f"http://localhost:{final_output.get('port')}" if final_output.get("port") else None)
        ) if all_success else None,
    }


async def _stream_flat_steps(
    steps: list[PipelineStep],
    normalized: dict[str, Any],
    carry_forward: dict[str, Any],
    skills_dir: Path,
    total_cost_ref: list[float],
) -> AsyncGenerator[str, None]:
    """SSE stream for flat sequential steps."""
    from agentura_sdk.runner.claude_code_executor import _should_use_claude_code
    from agentura_sdk.types import AgentIteration as AgentIterationType
    from agentura_sdk.types import SkillResult

    for step_idx, step in enumerate(steps, 1):
        step_start = time.monotonic()
        step_input = dict(normalized)
        step_input.update(carry_forward)

        yield _sse("step_started", {
            "step": step_idx,
            "skill": step.skill,
            "status": "running",
        })

        try:
            ctx = _build_skill_context(step.skill, step_input, skills_dir)
            if ctx is None:
                raise FileNotFoundError(f"Skill {step.skill} not found")

            if ctx.role == SkillRole.AGENT:
                result = None
                from agentura_sdk.runner.ptc_executor import _should_use_ptc
                if _should_use_ptc(ctx):
                    from agentura_sdk.runner.ptc_executor import execute_ptc_streaming
                    stream_fn = execute_ptc_streaming
                elif _should_use_claude_code(ctx):
                    from agentura_sdk.runner.claude_code_executor import execute_claude_code_streaming
                    stream_fn = execute_claude_code_streaming
                else:
                    from agentura_sdk.runner.agent_executor import execute_agent_streaming
                    stream_fn = execute_agent_streaming
                async for event in stream_fn(ctx):
                    if isinstance(event, AgentIterationType):
                        yield _sse("iteration", {
                            "step": step_idx,
                            **event.model_dump(),
                        })
                    elif isinstance(event, SkillResult):
                        result = event

                if result is None:
                    raise RuntimeError(f"Agent {step.skill} yielded no result")
            else:
                result = await execute_skill(ctx)

            step_latency = (time.monotonic() - step_start) * 1000
            exec_id = log_execution(ctx, result)
            total_cost_ref[0] += result.cost_usd

            if result.context_for_next:
                carry_forward.update(result.context_for_next)
            if result.output.get("url"):
                carry_forward["url"] = result.output["url"]
            if result.output.get("port"):
                carry_forward["port"] = result.output["port"]

            yield _sse("step_completed", {
                "step": step_idx,
                "skill": step.skill,
                "success": result.success,
                "execution_id": exec_id,
                "latency_ms": step_latency,
                "cost_usd": result.cost_usd,
                "artifacts_dir": result.context_for_next.get("artifacts_dir", ""),
                "deployed": result.output.get("deployed", False),
                "port": result.output.get("port"),
                "url": result.output.get("url"),
            })

            if not result.success and step.required:
                break

        except Exception as e:
            step_latency = (time.monotonic() - step_start) * 1000
            logger.error("step %d (%s) failed: %s", step_idx, step.skill, e)
            yield _sse("step_completed", {
                "step": step_idx,
                "skill": step.skill,
                "success": False,
                "error": str(e),
                "latency_ms": step_latency,
            })
            if step.required:
                break


async def run_pipeline_stream(
    name: str,
    pipeline_input: dict[str, Any],
) -> AsyncGenerator[str, None]:
    """SSE streaming variant — yields newline-delimited JSON events.

    Supports both flat ``steps:`` and ``phases:`` (parallel/sequential mix).
    """
    pipeline = load_pipeline(name)
    skills_dir = SKILLS_DIR
    start = time.monotonic()
    carry_forward: dict[str, Any] = {}
    total_cost_ref = [0.0]
    total_expected = 0

    normalized = _apply_input_mapping(pipeline_input, pipeline.input_mapping)

    if pipeline.phases:
        # --- Phase-based streaming ---
        for phase in pipeline.phases:
            total_expected += len(phase.steps)
            phase_input = dict(normalized)
            phase_input.update(carry_forward)

            if phase.type == "parallel":
                async for event in stream_parallel_phase(phase, phase_input, skills_dir):
                    yield event
                    # Track cost from agent_completed events
                    if '"cost_usd"' in event:
                        try:
                            data = json.loads(event.split("data: ", 1)[1].split("\n", 1)[0])
                            total_cost_ref[0] += data.get("cost_usd", 0)
                        except Exception:
                            pass
            else:
                async for event in _stream_flat_steps(phase.steps, phase_input, carry_forward, skills_dir, total_cost_ref):
                    yield event
    else:
        # --- Flat steps (backward compat) ---
        total_expected = len(pipeline.steps)
        async for event in _stream_flat_steps(pipeline.steps, normalized, carry_forward, skills_dir, total_cost_ref):
            yield event

    total_latency = (time.monotonic() - start) * 1000

    final_url = (
        carry_forward.get("url")
        or (f"http://localhost:{carry_forward.get('port')}" if carry_forward.get("port") else None)
        or (f"http://localhost:{normalized.get('port')}" if normalized.get("port") else None)
    )

    yield _sse("pipeline_done", {
        "pipeline": name,
        "success": True,
        "total_steps": total_expected,
        "total_latency_ms": total_latency,
        "total_cost_usd": total_cost_ref[0],
        "url": final_url,
    })


# ---------------------------------------------------------------------------
# Parallel phase execution
# ---------------------------------------------------------------------------


async def _execute_single_agent(
    step: PipelineStep,
    input_data: dict[str, Any],
    skills_dir: Path,
) -> dict[str, Any]:
    """Execute a single agent step, return result dict."""
    agent_id = step.agent_id or step.skill.replace("/", "-")
    step_start = time.monotonic()
    try:
        ctx = _build_skill_context(step.skill, input_data, skills_dir)
        if ctx is None:
            raise FileNotFoundError(f"Skill {step.skill} not found")
        result = await execute_skill(ctx)
        latency = (time.monotonic() - step_start) * 1000
        exec_id = log_execution(ctx, result)
        return {
            "agent_id": agent_id,
            "skill": step.skill,
            "success": result.success,
            "execution_id": exec_id,
            "latency_ms": latency,
            "cost_usd": result.cost_usd,
            "output": result.output,
            "context_for_next": result.context_for_next,
        }
    except Exception as e:
        latency = (time.monotonic() - step_start) * 1000
        logger.error("agent %s (%s) failed: %s", agent_id, step.skill, e)
        return {
            "agent_id": agent_id,
            "skill": step.skill,
            "success": False,
            "execution_id": "N/A",
            "latency_ms": latency,
            "cost_usd": 0.0,
            "output": {"error": str(e)},
            "context_for_next": {},
        }


async def execute_parallel_phase(
    phase: PipelinePhase,
    base_input: dict[str, Any],
    skills_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Execute all steps in a phase concurrently via asyncio.gather."""
    skills_dir = skills_dir or SKILLS_DIR
    tasks = [
        _execute_single_agent(step, base_input, skills_dir)
        for step in phase.steps
    ]
    return list(await asyncio.gather(*tasks))


async def stream_parallel_phase(
    phase: PipelinePhase,
    base_input: dict[str, Any],
    skills_dir: Path | None = None,
) -> AsyncGenerator[str, None]:
    """SSE multiplexer — streams events from parallel agents tagged with agent_id."""
    from agentura_sdk.runner.claude_code_executor import _should_use_claude_code
    from agentura_sdk.types import AgentIteration as AgentIterationType
    from agentura_sdk.types import SkillResult

    skills_dir = skills_dir or SKILLS_DIR
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    agent_count = len(phase.steps)
    done_count = 0

    yield _sse("phase_started", {
        "phase": phase.name,
        "type": phase.type,
        "agents": [s.agent_id or s.skill.replace("/", "-") for s in phase.steps],
    })

    async def _run_agent(step: PipelineStep) -> None:
        agent_id = step.agent_id or step.skill.replace("/", "-")
        step_start = time.monotonic()
        await queue.put(_sse("agent_started", {"agent_id": agent_id, "skill": step.skill}))

        try:
            ctx = _build_skill_context(step.skill, base_input, skills_dir)
            if ctx is None:
                raise FileNotFoundError(f"Skill {step.skill} not found")

            if ctx.role == SkillRole.AGENT:
                result = None
                from agentura_sdk.runner.ptc_executor import _should_use_ptc
                if _should_use_ptc(ctx):
                    from agentura_sdk.runner.ptc_executor import execute_ptc_streaming
                    stream_fn = execute_ptc_streaming
                elif _should_use_claude_code(ctx):
                    from agentura_sdk.runner.claude_code_executor import execute_claude_code_streaming
                    stream_fn = execute_claude_code_streaming
                else:
                    from agentura_sdk.runner.agent_executor import execute_agent_streaming
                    stream_fn = execute_agent_streaming
                async for event in stream_fn(ctx):
                    if isinstance(event, AgentIterationType):
                        await queue.put(_sse("iteration", {
                            "agent_id": agent_id,
                            **event.model_dump(),
                        }))
                    elif isinstance(event, SkillResult):
                        result = event
                if result is None:
                    raise RuntimeError(f"Agent {step.skill} yielded no result")
            else:
                result = await execute_skill(ctx)

            latency = (time.monotonic() - step_start) * 1000
            exec_id = log_execution(ctx, result)
            await queue.put(_sse("agent_completed", {
                "agent_id": agent_id,
                "skill": step.skill,
                "success": result.success,
                "execution_id": exec_id,
                "latency_ms": latency,
                "cost_usd": result.cost_usd,
            }))
        except Exception as e:
            latency = (time.monotonic() - step_start) * 1000
            await queue.put(_sse("agent_completed", {
                "agent_id": agent_id,
                "skill": step.skill,
                "success": False,
                "error": str(e),
                "latency_ms": latency,
            }))
        finally:
            await queue.put(None)  # signal this agent is done

    # Launch all agents concurrently
    for step in phase.steps:
        asyncio.create_task(_run_agent(step))

    # Drain the queue until all agents are done
    while done_count < agent_count:
        msg = await queue.get()
        if msg is None:
            done_count += 1
        else:
            yield msg

    yield _sse("phase_completed", {"phase": phase.name})
