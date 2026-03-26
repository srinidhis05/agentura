"""Execute a skill locally via Pydantic AI + Anthropic API."""

import json
import logging
import os
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
    from uuid import uuid4
    execution_id = f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}"
    skill_path = f"{ctx.domain}/{ctx.skill_name}"
    if result.approval_required:
        outcome = "pending_approval"
    elif result.success:
        outcome = "accepted"
    else:
        outcome = "error"
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
        "triggered_by": ctx.input_data.get("_triggered_by", ""),
    }

    try:
        from agentura_sdk.memory import get_memory_store
        store = get_memory_store()
        store.log_execution(skill_path, entry)

        # Approval engine: store pending tool calls for post-approval execution
        pending = result.output.get("pending_approvals") if isinstance(result.output, dict) else None
        if pending:
            try:
                store.update_execution_pending_approvals(execution_id, pending)
            except Exception:
                pass

        # MemRL: track which reflexions were injected (DEC-066)
        if ctx.injected_reflexion_ids:
            try:
                store.record_reflexion_injection(execution_id, ctx.injected_reflexion_ids)
            except Exception:
                pass
        # MemRL: record success for utility scoring
        if result.success and ctx.injected_reflexion_ids:
            try:
                store.record_execution_success(execution_id)
            except Exception:
                pass
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


def _is_anthropic_model(model: str) -> bool:
    """Check if the model is an Anthropic Claude model."""
    return model.startswith("anthropic/") or "claude" in model.lower()


# Anthropic pricing per million tokens (input, output)
_ANTHROPIC_PRICING = {
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-opus-4-20250514": (15.0, 75.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
}


def _estimate_anthropic_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD from token counts and model pricing."""
    # Try exact match, then prefix match
    pricing = _ANTHROPIC_PRICING.get(model_name)
    if not pricing:
        for prefix, p in _ANTHROPIC_PRICING.items():
            if model_name.startswith(prefix):
                pricing = p
                break
    if not pricing:
        # Default to Sonnet pricing as safe estimate
        pricing = (3.0, 15.0)
    input_cost = (input_tokens / 1_000_000) * pricing[0]
    output_cost = (output_tokens / 1_000_000) * pricing[1]
    return round(input_cost + output_cost, 6)


def _post_execution_hook(ctx: SkillContext, result: SkillResult) -> None:
    """Fire-and-forget post-execution actions (incident-to-eval, etc.)."""
    try:
        from agentura_sdk.testing.incident_eval import maybe_generate_failure_tests

        skills_dir = Path(os.environ.get("SKILLS_DIR", "/skills"))
        # Also try walking up from CWD
        if not skills_dir.exists():
            cwd = Path.cwd()
            for parent in [cwd, *cwd.parents]:
                candidate = parent / "skills"
                if candidate.is_dir():
                    skills_dir = candidate
                    break

        maybe_generate_failure_tests(ctx, result, skills_dir)
    except Exception:
        pass


async def execute_skill(ctx: SkillContext) -> SkillResult:
    """Execute a skill using Pydantic AI (Anthropic) or OpenRouter."""
    if ctx.role == SkillRole.AGENT:
        from agentura_sdk.runner.ptc_executor import _should_use_ptc
        if _should_use_ptc(ctx):
            from agentura_sdk.runner.ptc_executor import execute_ptc
            logger.info("Routing agent skill %s to PTC executor", ctx.skill_name)
            result = await execute_ptc(ctx)
            log_execution(ctx, result)
            _post_execution_hook(ctx, result)
            return result
        from agentura_sdk.runner.claude_code_executor import _should_use_claude_code
        if _should_use_claude_code(ctx):
            from agentura_sdk.runner.claude_code_executor import execute_claude_code
            logger.info("Routing agent skill %s to Claude Code SDK", ctx.skill_name)
            result = await execute_claude_code(ctx)
            log_execution(ctx, result)
            _post_execution_hook(ctx, result)
            return result
        from agentura_sdk.runner.agent_executor import execute_agent
        return await execute_agent(ctx)
    # Prefer Anthropic direct for Claude models (accurate cost tracking, no proxy)
    if os.environ.get("ANTHROPIC_API_KEY") and _is_anthropic_model(ctx.model):
        return await _execute_via_pydantic_ai(ctx)
    if os.environ.get("OPENROUTER_API_KEY"):
        return await _execute_via_openrouter(ctx)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return await _execute_via_pydantic_ai(ctx)
    return SkillResult(
        skill_name=ctx.skill_name,
        success=False,
        output={"error": "Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY. Use --dry-run to skip."},
    )


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
        _post_execution_hook(ctx, skill_result)
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
        _post_execution_hook(ctx, skill_result)
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
            "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
            "claude-haiku-4.5": "claude-haiku-4-5-20251001",
            "claude-haiku-4-5": "claude-haiku-4-5-20251001",
            "claude-opus-4.6": "claude-opus-4-6",
            # claude-opus-4-6 is already the canonical ID — no alias needed
        }
        model_name = _MODEL_ALIASES.get(model_name, model_name)
        provider = AnthropicProvider(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        model = AnthropicModel(model_name, provider=provider)

        agent = Agent(
            model=model,
            system_prompt=ctx.system_prompt,
        )

        user_prompt = json.dumps(ctx.input_data, indent=2)
        max_tokens = 16384
        if ctx.sandbox_config and ctx.sandbox_config.max_tokens:
            max_tokens = ctx.sandbox_config.max_tokens
        result = await agent.run(
            user_prompt,
            model_settings={"max_tokens": max_tokens},
        )

        latency_ms = (time.monotonic() - start) * 1000

        output_text = result.output
        try:
            output = json.loads(output_text)
        except (json.JSONDecodeError, TypeError):
            output = {"raw_output": str(output_text)}

        # Extract token usage and calculate cost
        cost_usd = 0.0
        usage = result.usage()
        input_tokens = getattr(usage, 'input_tokens', 0) or 0
        output_tokens = getattr(usage, 'output_tokens', 0) or 0
        cost_usd = _estimate_anthropic_cost(model_name, input_tokens, output_tokens)
        trace_msg = "Executed via Anthropic (%s, in=%d out=%d tokens, $%.4f)" % (
            model_name, input_tokens, output_tokens, cost_usd)

        skill_result = SkillResult(
            skill_name=ctx.skill_name,
            success=True,
            output=output,
            reasoning_trace=[trace_msg],
            model_used=ctx.model,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
        execution_id = log_execution(ctx, skill_result)
        skill_result.reasoning_trace.append(f"Logged as {execution_id}")
        _post_execution_hook(ctx, skill_result)
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
        _post_execution_hook(ctx, skill_result)
        return skill_result
