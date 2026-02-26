"""Build-deploy pipeline: app-builder (agent) -> deployer (specialist).

Chains skills by injecting context_for_next from step N into input_data of step N+1.
The async generator variant yields SSE events for real-time progress.
"""

import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from agentura_sdk.runner.local_runner import execute_skill, log_execution
from agentura_sdk.runner.skill_loader import load_skill_md
from agentura_sdk.types import SandboxConfig, SkillContext, SkillRole

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "/skills"))

# Pipeline steps: (domain/skill, required)
PIPELINE_STEPS = [
    ("dev/app-builder", True),
    ("dev/deployer", True),
]


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
    prompt_parts.append(loaded.system_prompt)
    system_prompt = "\n\n---\n\n".join(prompt_parts)

    sandbox_config = None
    if loaded.metadata.role == SkillRole.AGENT:
        sandbox_config = SandboxConfig()
        config_path = skill_dir / "agentura.config.yaml"
        if config_path.exists():
            try:
                cfg = yaml.safe_load(config_path.read_text()) or {}
                sandbox_raw = cfg.get("sandbox", {})
                if sandbox_raw:
                    sandbox_config = SandboxConfig(**sandbox_raw)
            except Exception:
                pass

    return SkillContext(
        skill_name=loaded.metadata.name,
        domain=loaded.metadata.domain,
        role=loaded.metadata.role,
        model=loaded.metadata.model,
        system_prompt=system_prompt,
        input_data=input_data,
        sandbox_config=sandbox_config,
    )


async def run_build_deploy(pipeline_input: dict[str, Any]) -> dict[str, Any]:
    """Run the build-deploy pipeline synchronously, return aggregated result."""
    skills_dir = SKILLS_DIR
    start = time.monotonic()
    step_results: list[dict] = []
    carry_forward: dict[str, Any] = {}

    for step_idx, (skill_path, required) in enumerate(PIPELINE_STEPS, 1):
        step_start = time.monotonic()
        step_input = dict(pipeline_input)
        step_input.update(carry_forward)

        try:
            ctx = _build_skill_context(skill_path, step_input, skills_dir)
            if ctx is None:
                raise FileNotFoundError(f"Skill {skill_path} not found")

            result = await execute_skill(ctx)
            step_latency = (time.monotonic() - step_start) * 1000
            exec_id = log_execution(ctx, result)

            step_results.append({
                "step": step_idx,
                "skill": skill_path,
                "status": "success" if result.success else "error",
                "execution_id": exec_id,
                "latency_ms": step_latency,
                "cost_usd": result.cost_usd,
                "output": result.output,
            })

            if result.context_for_next:
                carry_forward.update(result.context_for_next)

            if not result.success and required:
                break

        except Exception as e:
            step_latency = (time.monotonic() - step_start) * 1000
            logger.error("step %d (%s) failed: %s", step_idx, skill_path, e)
            step_results.append({
                "step": step_idx,
                "skill": skill_path,
                "status": "error",
                "execution_id": "N/A",
                "latency_ms": step_latency,
                "cost_usd": 0.0,
                "output": {"error": str(e)},
            })
            if required:
                break

    total_latency = (time.monotonic() - start) * 1000
    all_success = all(s["status"] == "success" for s in step_results)
    final_output = step_results[-1].get("output", {}) if step_results else {}

    return {
        "success": all_success,
        "steps": step_results,
        "steps_completed": len(step_results),
        "total_latency_ms": total_latency,
        "total_cost_usd": sum(s.get("cost_usd", 0) for s in step_results),
        "url": f"http://localhost:{final_output.get('port', '')}" if all_success else None,
    }


async def run_build_deploy_stream(
    pipeline_input: dict[str, Any],
) -> AsyncGenerator[str, None]:
    """SSE streaming variant — yields newline-delimited JSON events."""
    from agentura_sdk.runner.agent_executor import execute_agent_streaming
    from agentura_sdk.types import AgentIteration as AgentIterationType
    from agentura_sdk.types import SkillResult

    skills_dir = SKILLS_DIR
    start = time.monotonic()
    carry_forward: dict[str, Any] = {}
    steps_completed = 0
    total_cost = 0.0

    for step_idx, (skill_path, required) in enumerate(PIPELINE_STEPS, 1):
        step_start = time.monotonic()
        step_input = dict(pipeline_input)
        step_input.update(carry_forward)

        yield _sse("step_started", {
            "step": step_idx,
            "skill": skill_path,
            "status": "running",
        })

        try:
            ctx = _build_skill_context(skill_path, step_input, skills_dir)
            if ctx is None:
                raise FileNotFoundError(f"Skill {skill_path} not found")

            # Agent-role skills: stream per-iteration events
            if ctx.role == SkillRole.AGENT:
                result = None
                async for event in execute_agent_streaming(ctx):
                    if isinstance(event, AgentIterationType):
                        yield _sse("iteration", {
                            "step": step_idx,
                            **event.model_dump(),
                        })
                    elif isinstance(event, SkillResult):
                        result = event

                if result is None:
                    raise RuntimeError(f"Agent {skill_path} yielded no result")
            else:
                result = await execute_skill(ctx)

            step_latency = (time.monotonic() - step_start) * 1000
            exec_id = log_execution(ctx, result)
            total_cost += result.cost_usd

            if result.context_for_next:
                carry_forward.update(result.context_for_next)

            yield _sse("step_completed", {
                "step": step_idx,
                "skill": skill_path,
                "success": result.success,
                "execution_id": exec_id,
                "latency_ms": step_latency,
                "cost_usd": result.cost_usd,
                "artifacts_dir": result.context_for_next.get("artifacts_dir", ""),
                "deployed": result.output.get("deployed", False),
                "port": result.output.get("port"),
            })

            steps_completed = step_idx

            if not result.success and required:
                break

        except Exception as e:
            step_latency = (time.monotonic() - step_start) * 1000
            logger.error("step %d (%s) failed: %s", step_idx, skill_path, e)
            yield _sse("step_completed", {
                "step": step_idx,
                "skill": skill_path,
                "success": False,
                "error": str(e),
                "latency_ms": step_latency,
            })
            if required:
                break

    total_latency = (time.monotonic() - start) * 1000
    port = pipeline_input.get("port", "")

    yield _sse("pipeline_done", {
        "success": steps_completed == len(PIPELINE_STEPS),
        "steps_completed": steps_completed,
        "total_latency_ms": total_latency,
        "total_cost_usd": total_cost,
        "url": f"http://localhost:{port}" if port and steps_completed == len(PIPELINE_STEPS) else None,
    })


def _sse(event_type: str, data: dict) -> str:
    """Format a single SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
