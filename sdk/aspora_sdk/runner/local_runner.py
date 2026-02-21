"""Execute a skill locally via Pydantic AI + Anthropic API."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from aspora_sdk.types import SkillContext, SkillResult

# Load .env from project root
load_dotenv(Path.cwd() / ".env")

# Default knowledge layer directory (overridable via ASPORA_KNOWLEDGE_DIR)
_KNOWLEDGE_DIR = Path(os.environ.get("ASPORA_KNOWLEDGE_DIR", Path.cwd() / ".aspora"))


def _get_knowledge_dir() -> Path:
    """Return the knowledge layer directory, creating if needed."""
    d = _KNOWLEDGE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_execution(ctx: SkillContext, result: SkillResult) -> str:
    """Log execution to memory store (mem0 or JSON fallback). Returns execution_id."""
    execution_id = f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    skill_path = f"{ctx.domain}/{ctx.skill_name}"
    entry = {
        "execution_id": execution_id,
        "skill": skill_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_summary": ctx.input_data,
        "output_summary": result.output,
        "outcome": "pending_review",
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
        "model_used": result.model_used,
    }

    try:
        from aspora_sdk.memory import get_memory_store
        store = get_memory_store()
        return store.log_execution(skill_path, entry)
    except Exception:
        pass

    # Fallback: write directly to JSON
    memory_file = _get_knowledge_dir() / "episodic_memory.json"
    if memory_file.exists():
        data = json.loads(memory_file.read_text())
    else:
        data = {"entries": []}

    data["entries"].append(entry)
    memory_file.write_text(json.dumps(data, indent=2))
    return execution_id


async def execute_skill(ctx: SkillContext) -> SkillResult:
    """Execute a skill using Pydantic AI with OpenRouter."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "ANTHROPIC_API_KEY not set. Use --dry-run or set the env var."},
        )

    start = time.monotonic()

    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        # Strip OpenRouter prefix and resolve shorthand model names
        model_name = ctx.model.removeprefix("anthropic/")
        _MODEL_ALIASES = {
            "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
            "claude-haiku-4.5": "claude-haiku-4-5-20251001",
        }
        model_name = _MODEL_ALIASES.get(model_name, model_name)
        provider = AnthropicProvider(api_key=api_key)
        model = AnthropicModel(model_name, provider=provider)

        agent = Agent(
            model=model,
            system_prompt=ctx.system_prompt,
        )

        import json
        user_prompt = json.dumps(ctx.input_data, indent=2)
        result = await agent.run(user_prompt)

        latency_ms = (time.monotonic() - start) * 1000

        # Try to parse output as JSON
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
