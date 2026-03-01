"""Parallel PR pipeline — spawns testing, SLT, and docs agents concurrently.

Orchestrates fleet session tracking, GitHub Checks API, and result aggregation.
"""

import asyncio
import logging
import os
import time
from typing import Any

from agentura_sdk.pipelines.engine import (
    SKILLS_DIR,
    PipelinePhase,
    _build_skill_context,
    _sse,
    load_pipeline,
)
from agentura_sdk.pipelines.github_client import (
    create_check_run,
    fetch_pr_diff,
    fetch_pr_files,
    post_comment,
    update_check_run,
)
from agentura_sdk.runner.local_runner import execute_skill, log_execution

logger = logging.getLogger(__name__)

CHECK_NAME_MAP = {
    "testing": "Agentura / Testing",
    "slt": "Agentura / SLT",
    "docs": "Agentura / Docs",
}


def _get_fleet_store():
    """Lazy-load FleetStore to avoid import at module level."""
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        return None
    from agentura_sdk.memory.fleet_store import FleetStore
    return FleetStore(dsn)


async def run_pr_parallel_pipeline(pr_event: dict[str, Any]) -> dict[str, Any]:
    """Main orchestrator: fan-out parallel agents, fan-in results, post to GitHub."""
    pipeline = load_pipeline("github-pr-parallel")
    repo = pr_event.get("repo", "")
    pr_number = pr_event.get("pr_number", 0)
    pr_url = pr_event.get("pr_url", "")
    head_sha = pr_event.get("head_sha", "")

    # 1. Create fleet session
    store = _get_fleet_store()
    session_id = ""
    if store:
        analyze_phase = next((p for p in pipeline.phases if p.name == "analyze"), None)
        total = len(analyze_phase.steps) if analyze_phase else 0
        session_id = store.create_session(
            pipeline_name="github-pr-parallel",
            trigger_type="github_pr",
            repo=repo,
            pr_number=pr_number,
            pr_url=pr_url,
            head_sha=head_sha,
            total_agents=total,
            input_data=pr_event,
        )
        store.update_session_status(session_id, "running")

    # 2. Fetch PR data
    diff = ""
    changed_files: list[dict] = []
    try:
        diff, changed_files = await asyncio.gather(
            fetch_pr_diff(repo, pr_number),
            fetch_pr_files(repo, pr_number),
        )
    except Exception as e:
        logger.error("failed to fetch PR data: %s", e)

    base_input = {
        **pr_event,
        "diff": diff,
        "changed_files": changed_files,
    }

    # 3. Create GitHub check runs per agent
    check_runs: dict[str, int] = {}
    for agent_id, check_name in CHECK_NAME_MAP.items():
        try:
            cr = await create_check_run(repo, head_sha, check_name, status="in_progress")
            check_runs[agent_id] = cr.get("id", 0)
        except Exception as e:
            logger.warning("failed to create check run %s: %s", check_name, e)

    # 4. Fan out: execute analyze phase in parallel
    analyze_phase = next((p for p in pipeline.phases if p.name == "analyze"), None)
    agent_results: list[dict] = []
    if analyze_phase:
        # Register agents in fleet store
        if store and session_id:
            for step in analyze_phase.steps:
                aid = step.agent_id or step.skill.replace("/", "-")
                store.create_agent(session_id, aid, step.skill)

        agent_results = await _fan_out(analyze_phase, base_input, store, session_id, check_runs, repo)

    # 5. Fan in: aggregate and post results
    completed = sum(1 for r in agent_results if r.get("success"))
    failed = sum(1 for r in agent_results if not r.get("success"))
    total_cost = sum(r.get("cost_usd", 0) for r in agent_results)

    # 6. Post summary comment
    summary = _build_summary(agent_results, pr_url, session_id)
    try:
        await post_comment(repo, pr_number, summary)
        if store and session_id:
            store.update_session_status(session_id, github_check_posted=True,
                                        status="completed" if failed == 0 else "failed",
                                        completed_agents=completed, failed_agents=failed,
                                        total_cost_usd=total_cost)
    except Exception as e:
        logger.error("failed to post summary comment: %s", e)
        if store and session_id:
            store.update_session_status(session_id, status="completed" if failed == 0 else "failed",
                                        completed_agents=completed, failed_agents=failed,
                                        total_cost_usd=total_cost)

    return {
        "session_id": session_id,
        "pipeline": "github-pr-parallel",
        "success": failed == 0,
        "agents": agent_results,
        "total_cost_usd": total_cost,
    }


async def _fan_out(
    phase: PipelinePhase,
    base_input: dict[str, Any],
    store: Any,
    session_id: str,
    check_runs: dict[str, int],
    repo: str,
) -> list[dict]:
    """Execute all agents in a phase concurrently."""

    async def _run_one(step) -> dict:
        agent_id = step.agent_id or step.skill.replace("/", "-")
        start = time.monotonic()
        if store and session_id:
            store.update_agent_status(agent_id, "running")
        try:
            ctx = _build_skill_context(step.skill, base_input, SKILLS_DIR)
            if ctx is None:
                raise FileNotFoundError(f"Skill {step.skill} not found")
            result = await execute_skill(ctx)
            latency = (time.monotonic() - start) * 1000
            exec_id = log_execution(ctx, result)

            # Update fleet store
            if store and session_id:
                store.update_agent_status(
                    agent_id, "completed",
                    execution_id=exec_id, success=result.success,
                    output=result.output, cost_usd=result.cost_usd,
                    latency_ms=latency,
                )

            # Update GitHub check run
            cr_id = check_runs.get(agent_id)
            if cr_id:
                conclusion = "success" if result.success else "failure"
                try:
                    await update_check_run(repo, cr_id, status="completed",
                                           conclusion=conclusion, output={
                                               "title": f"{agent_id} — {'passed' if result.success else 'failed'}",
                                               "summary": result.output.get("summary", str(result.output)[:500]),
                                           })
                except Exception as e:
                    logger.warning("failed to update check run %s: %s", agent_id, e)

            return {
                "agent_id": agent_id,
                "skill": step.skill,
                "success": result.success,
                "execution_id": exec_id,
                "latency_ms": latency,
                "cost_usd": result.cost_usd,
                "output": result.output,
            }
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            if store and session_id:
                store.update_agent_status(agent_id, "failed", error_message=str(e), latency_ms=latency)

            cr_id = check_runs.get(agent_id)
            if cr_id:
                try:
                    await update_check_run(repo, cr_id, status="completed",
                                           conclusion="failure", output={
                                               "title": f"{agent_id} — error",
                                               "summary": str(e)[:500],
                                           })
                except Exception:
                    pass

            return {
                "agent_id": agent_id,
                "skill": step.skill,
                "success": False,
                "execution_id": "N/A",
                "latency_ms": latency,
                "cost_usd": 0.0,
                "output": {"error": str(e)},
            }

    tasks = [_run_one(step) for step in phase.steps]
    return list(await asyncio.gather(*tasks))


def _build_summary(results: list[dict], pr_url: str, session_id: str) -> str:
    """Build a markdown summary comment for the PR."""
    lines = ["## Agentura Fleet Review", ""]
    all_pass = all(r.get("success") for r in results)
    status = "All checks passed" if all_pass else "Some checks failed"
    lines.append(f"**Status**: {status}")
    lines.append("")
    lines.append("| Agent | Status | Cost | Latency |")
    lines.append("|-------|--------|------|---------|")
    for r in results:
        icon = "pass" if r.get("success") else "fail"
        lines.append(
            f"| {r['agent_id']} | {icon} | ${r.get('cost_usd', 0):.3f} | {r.get('latency_ms', 0):.0f}ms |"
        )
    lines.append("")
    if session_id:
        lines.append(f"Fleet session: `{session_id}`")
    return "\n".join(lines)
