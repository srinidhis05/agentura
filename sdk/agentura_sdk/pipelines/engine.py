"""Generic pipeline engine — loads YAML configs and executes skill chains.

New pipeline = new YAML file in pipelines/. Zero code changes.
"""

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
    required: bool = True


@dataclass
class PipelineDef:
    name: str
    description: str = ""
    input_mapping: dict[str, str] = field(default_factory=dict)
    steps: list[PipelineStep] = field(default_factory=list)


def load_pipeline(name: str) -> PipelineDef:
    """Load a pipeline definition from pipelines/{name}.yaml."""
    path = PIPELINES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Pipeline not found: {name} (looked in {path})")

    raw = yaml.safe_load(path.read_text()) or {}
    steps = [
        PipelineStep(skill=s["skill"], required=s.get("required", True))
        for s in raw.get("steps", [])
    ]
    return PipelineDef(
        name=raw.get("name", name),
        description=raw.get("description", ""),
        input_mapping=raw.get("input_mapping", {}),
        steps=steps,
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
    prompt_parts.append(loaded.system_prompt)
    system_prompt = "\n\n---\n\n".join(prompt_parts)

    sandbox_config = None
    mcp_bindings: list[dict] = []
    if loaded.metadata.role == SkillRole.AGENT:
        sandbox_config = SandboxConfig()
        config_path = skill_dir / "agentura.config.yaml"
        if config_path.exists():
            try:
                cfg = yaml.safe_load(config_path.read_text()) or {}
                sandbox_raw = cfg.get("sandbox", {})
                if sandbox_raw:
                    sandbox_config = SandboxConfig(**sandbox_raw)
                for mcp_ref in cfg.get("mcp_tools", []):
                    server_name = mcp_ref.get("server", "")
                    env_key = f"MCP_{server_name.upper().replace('-', '_')}_URL"
                    server_url = os.environ.get(env_key, "")
                    if server_url:
                        mcp_bindings.append({
                            "server": server_name,
                            "url": server_url,
                            "tools": mcp_ref.get("tools", []),
                        })
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


async def run_pipeline(name: str, pipeline_input: dict[str, Any]) -> dict[str, Any]:
    """Run a named pipeline synchronously, return aggregated result."""
    pipeline = load_pipeline(name)
    skills_dir = SKILLS_DIR
    start = time.monotonic()
    step_results: list[dict] = []
    carry_forward: dict[str, Any] = {}

    normalized = _apply_input_mapping(pipeline_input, pipeline.input_mapping)

    for step_idx, step in enumerate(pipeline.steps, 1):
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

    total_latency = (time.monotonic() - start) * 1000
    all_success = all(s["status"] == "success" for s in step_results)
    final_output = step_results[-1].get("output", {}) if step_results else {}

    return {
        "pipeline": name,
        "success": all_success,
        "steps": step_results,
        "steps_completed": len(step_results),
        "total_steps": len(pipeline.steps),
        "total_latency_ms": total_latency,
        "total_cost_usd": sum(s.get("cost_usd", 0) for s in step_results),
        "url": (
            final_output.get("url")
            or (f"http://localhost:{final_output.get('port')}" if final_output.get("port") else None)
        ) if all_success else None,
    }


async def run_pipeline_stream(
    name: str,
    pipeline_input: dict[str, Any],
) -> AsyncGenerator[str, None]:
    """SSE streaming variant — yields newline-delimited JSON events."""
    from agentura_sdk.runner.agent_executor import execute_agent_streaming
    from agentura_sdk.types import AgentIteration as AgentIterationType
    from agentura_sdk.types import SkillResult

    pipeline = load_pipeline(name)
    skills_dir = SKILLS_DIR
    start = time.monotonic()
    carry_forward: dict[str, Any] = {}
    steps_completed = 0
    total_cost = 0.0

    normalized = _apply_input_mapping(pipeline_input, pipeline.input_mapping)

    for step_idx, step in enumerate(pipeline.steps, 1):
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
                async for event in execute_agent_streaming(ctx):
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
            total_cost += result.cost_usd

            if result.context_for_next:
                carry_forward.update(result.context_for_next)
            # Propagate url/port from task_complete output for downstream use
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

            steps_completed = step_idx

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

    total_latency = (time.monotonic() - start) * 1000
    all_success = steps_completed == len(pipeline.steps)

    # Prefer URL from carry_forward (deployer output), fall back to port
    final_url = (
        carry_forward.get("url")
        or (f"http://localhost:{carry_forward.get('port')}" if carry_forward.get("port") else None)
        or (f"http://localhost:{normalized.get('port')}" if normalized.get("port") else None)
    ) if all_success else None

    yield _sse("pipeline_done", {
        "pipeline": name,
        "success": all_success,
        "steps_completed": steps_completed,
        "total_steps": len(pipeline.steps),
        "total_latency_ms": total_latency,
        "total_cost_usd": total_cost,
        "url": final_url,
    })
