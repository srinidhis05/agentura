"""Execute a skill locally via Pydantic AI + Anthropic API."""

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from agentura_sdk.types import SkillContext, SkillResult, SkillRole

# Load .env — walk up from CWD to find the project root .env
def _find_dotenv() -> Path | None:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None

_dotenv_path = _find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)

# Default knowledge layer directory (overridable via AGENTURA_KNOWLEDGE_DIR)
_KNOWLEDGE_DIR = Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str(Path.cwd() / ".agentura"))


def _get_knowledge_dir() -> Path:
    """Return the knowledge layer directory, creating if needed."""
    d = _KNOWLEDGE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_execution(ctx: SkillContext, result: SkillResult) -> str:
    """Log execution to the memory store (JSON fallback or mem0)."""
    execution_id = f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    skill_path = f"{ctx.domain}/{ctx.skill_name}"
    outcome = "accepted" if result.success else "error"
    entry = {
        "execution_id": execution_id,
        "skill": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_summary": ctx.input_data,
        "output_summary": result.output,
        "outcome": outcome,
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
        "model_used": result.model_used,
    }

    try:
        from agentura_sdk.memory import get_memory_store
        store = get_memory_store()
        store.log_execution(skill_path, entry)
    except Exception:
        # Fallback: write directly to JSON
        memory_file = _get_knowledge_dir() / "episodic_memory.json"
        if memory_file.exists():
            data = json.loads(memory_file.read_text())
        else:
            data = {"entries": []}
        data["entries"].append(entry)
        memory_file.write_text(json.dumps(data, indent=2))

    return execution_id


logger = logging.getLogger(__name__)


def _run_deploy(result: SkillResult) -> SkillResult:
    """Post-processor: write Dockerfile and run deploy commands from skill output."""
    artifacts_dir = result.output.get("artifacts_dir") or ""
    dockerfile = result.output.get("dockerfile")
    commands = result.output.get("deploy_commands", [])

    if not commands:
        return result

    if dockerfile and artifacts_dir:
        (Path(artifacts_dir) / "Dockerfile").write_text(dockerfile)

    for cmd in commands:
        logger.info("deploy: %s", cmd)
        subprocess.run(cmd, shell=True, check=True, cwd=artifacts_dir or ".")

    result.output["deployed"] = True
    return result


async def execute_skill(ctx: SkillContext) -> SkillResult:
    """Execute a skill using Pydantic AI (Anthropic) or OpenRouter."""
    if ctx.role == SkillRole.AGENT:
        from agentura_sdk.runner.agent_executor import execute_agent
        result = await execute_agent(ctx)
    elif os.environ.get("OPENROUTER_API_KEY"):
        result = await _execute_via_openrouter(ctx)
    elif os.environ.get("ANTHROPIC_API_KEY"):
        result = await _execute_via_pydantic_ai(ctx)
    else:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY. Use --dry-run to skip."},
        )

    # Post-processor: run deploy commands if present in output
    if result.success and result.output.get("deploy_commands"):
        try:
            result = _run_deploy(result)
        except Exception as e:
            logger.error("deploy post-processor failed: %s", e)
            result.output["deploy_error"] = str(e)

    return result


async def _execute_via_openrouter(ctx: SkillContext) -> SkillResult:
    """Execute via OpenRouter — supports 200+ models with fallback chains."""
    start = time.monotonic()
    try:
        from agentura_sdk.runner.openrouter import chat_completion

        user_prompt = json.dumps(ctx.input_data, indent=2)
        response = chat_completion(
            model=ctx.model,
            system_prompt=ctx.system_prompt,
            user_message=user_prompt,
        )

        try:
            output = json.loads(response.content)
        except (json.JSONDecodeError, TypeError):
            output = {"raw_output": response.content}

        skill_result = SkillResult(
            skill_name=ctx.skill_name,
            success=True,
            output=output,
            reasoning_trace=[f"Executed via OpenRouter ({response.model})"],
            model_used=response.model,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
        )
        execution_id = log_execution(ctx, skill_result)
        skill_result.reasoning_trace.append(f"Logged as {execution_id}")
        return skill_result

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        skill_result = SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
        log_execution(ctx, skill_result)
        return skill_result


async def _execute_via_pydantic_ai(ctx: SkillContext) -> SkillResult:
    """Execute via Pydantic AI + Anthropic API (direct)."""
    start = time.monotonic()

    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        model_name = ctx.model.removeprefix("anthropic/")
        _MODEL_ALIASES = {
            "claude-sonnet-4.5": "claude-sonnet-4-5-latest",
            "claude-haiku-4.5": "claude-haiku-4-5-latest",
        }
        model_name = _MODEL_ALIASES.get(model_name, model_name)
        provider = AnthropicProvider(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        model = AnthropicModel(model_name, provider=provider)

        agent = Agent(
            model=model,
            system_prompt=ctx.system_prompt,
        )

        user_prompt = json.dumps(ctx.input_data, indent=2)
        result = await agent.run(user_prompt)

        latency_ms = (time.monotonic() - start) * 1000

        output_text = result.output
        try:
            output = json.loads(output_text)
        except (json.JSONDecodeError, TypeError):
            output = {"raw_output": str(output_text)}

        skill_result = SkillResult(
            skill_name=ctx.skill_name,
            success=True,
            output=output,
            reasoning_trace=[f"Executed via {ctx.model}"],
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
        execution_id = log_execution(ctx, skill_result)
        skill_result.reasoning_trace.append(f"Logged as {execution_id}")
        return skill_result

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        skill_result = SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
        log_execution(ctx, skill_result)
        return skill_result
