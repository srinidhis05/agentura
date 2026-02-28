"""Agent executor using Claude Code Worker pods.

Creates an isolated worker pod per agent execution, sends the agent config
via HTTP POST to the worker's /execute-stream endpoint, and streams SSE
events back. Worker pods are cleaned up after execution completes.

Falls back to legacy agent_executor.py when SANDBOX_BACKEND != k8s or
ANTHROPIC_API_KEY is not set.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import httpx

from agentura_sdk.types import AgentIteration, SandboxConfig, SkillContext, SkillResult

logger = logging.getLogger(__name__)

WORKER_TIMEOUT = int(os.environ.get("CLAUDE_CODE_WORKER_TIMEOUT", "600"))


def _should_use_claude_code(ctx: SkillContext | None = None) -> bool:
    """Use Claude Code when skill opts in via executor: claude-code in config."""
    if ctx and ctx.sandbox_config and ctx.sandbox_config.executor == "claude-code":
        pass
    else:
        return False

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False

    if os.environ.get("SANDBOX_BACKEND") != "k8s":
        return False

    return True


def _parse_cost_budget(budget_str: str) -> float | None:
    """Parse '$1.00' → 1.0, return None if unparseable."""
    try:
        return float(budget_str.replace("$", "").strip())
    except (ValueError, AttributeError):
        return None


def _build_system_prompt(ctx: SkillContext) -> str:
    """Compose system prompt with memory recall injected."""
    from agentura_sdk.runner.agent_executor import _build_prompt_with_memory

    return _build_prompt_with_memory(ctx)


# Map Claude Code tool names → legacy sandbox tool names for UI rendering
_TOOL_NAME_MAP = {
    "Write": "write_file",
    "Read": "read_file",
    "Edit": "write_file",
    "Bash": "run_command",
    "Glob": "read_file",
    "Grep": "read_file",
}


def _map_tool_for_ui(tool_name: str, tool_input: dict) -> tuple[str, dict]:
    """Map Claude Code tool names/inputs to legacy format for UI rendering."""
    mapped_name = _TOOL_NAME_MAP.get(tool_name, tool_name)
    mapped_input = dict(tool_input)

    if tool_name == "Write":
        mapped_input = {
            "path": tool_input.get("file_path", ""),
            "content": tool_input.get("content", ""),
        }
    elif tool_name == "Edit":
        mapped_input = {
            "path": tool_input.get("file_path", ""),
            "content": f"Edit: {tool_input.get('old_string', '')[:50]} → {tool_input.get('new_string', '')[:50]}",
        }
    elif tool_name == "Read":
        mapped_input = {"path": tool_input.get("file_path", "")}
    elif tool_name == "Bash":
        mapped_input = {"command": tool_input.get("command", "")}

    return mapped_name, mapped_input


def _resolve_model(model: str) -> str:
    """Resolve model string to one the SDK understands."""
    name = model.removeprefix("anthropic/")
    aliases = {
        "claude-sonnet-4.5": "claude-sonnet-4-5-latest",
        "claude-haiku-4.5": "claude-haiku-4-5-latest",
    }
    return aliases.get(name, name)


def _build_worker_env(ctx: SkillContext) -> dict[str, str]:
    """Build env vars to pass to the worker pod."""
    env: dict[str, str] = {}
    if os.environ.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("OPENROUTER_API_KEY"):
        env["OPENROUTER_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
    return env


def _build_agent_request(ctx: SkillContext) -> dict:
    """Build the HTTP request body for the worker's /execute-stream endpoint."""
    max_turns = 25
    if ctx.sandbox_config and ctx.sandbox_config.max_iterations:
        max_turns = ctx.sandbox_config.max_iterations

    max_budget = _parse_cost_budget(
        getattr(ctx, "cost_budget_per_execution", "$1.00") or "$1.00"
    )

    # MCP server mapping
    mcp_servers: dict = {}
    allowed_mcp_tools: list[str] = []
    for binding in ctx.mcp_bindings:
        server_name = binding.get("server", "")
        server_url = binding.get("url", "")
        if not server_name or not server_url:
            continue
        mcp_servers[server_name] = {"type": "http", "url": server_url}
        for tool_name in binding.get("tools", []):
            allowed_mcp_tools.append(f"mcp__{server_name}__{tool_name}")

    allowed_tools = [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        *allowed_mcp_tools,
    ]

    system_prompt = _build_system_prompt(ctx)

    return {
        "prompt": json.dumps(ctx.input_data, indent=2),
        "system_prompt": system_prompt,
        "model": _resolve_model(ctx.model),
        "max_turns": max_turns,
        "max_budget_usd": max_budget,
        "mcp_servers": mcp_servers,
        "allowed_tools": allowed_tools,
    }


def _parse_sse_events(text: str) -> list[tuple[str, dict]]:
    """Parse SSE text into (event_type, data) tuples."""
    events = []
    for frame in text.split("\n\n"):
        frame = frame.strip()
        if not frame:
            continue
        event_type = ""
        data_str = ""
        for line in frame.split("\n"):
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data_str = line[6:]
        if event_type and data_str:
            try:
                events.append((event_type, json.loads(data_str)))
            except json.JSONDecodeError:
                pass
    return events


async def execute_claude_code(ctx: SkillContext) -> SkillResult:
    """One-shot agent execution via Claude Code worker pod."""
    from agentura_sdk.sandbox import claude_code_worker

    start = time.monotonic()
    sandbox_cfg = ctx.sandbox_config or SandboxConfig()
    env_vars = _build_worker_env(ctx)

    worker = await claude_code_worker.create(sandbox_cfg, env_vars)
    try:
        request_body = _build_agent_request(ctx)
        worker_url = f"http://{worker.pod_ip}:8080/execute-stream"

        iterations: list[AgentIteration] = []
        result_data: dict = {}

        async with httpx.AsyncClient(timeout=httpx.Timeout(WORKER_TIMEOUT)) as client:
            async with client.stream("POST", worker_url, json=request_body) as resp:
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        frame, buffer = buffer.split("\n\n", 1)
                        events = _parse_sse_events(frame + "\n\n")
                        for event_type, data in events:
                            if event_type == "iteration":
                                ui_name, ui_input = _map_tool_for_ui(
                                    data.get("tool_name", ""), data.get("tool_input", {})
                                )
                                iterations.append(AgentIteration(
                                    iteration=data.get("iteration", len(iterations) + 1),
                                    tool_name=ui_name,
                                    tool_input=ui_input,
                                    tool_output="",
                                    timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                                ))
                            elif event_type == "result":
                                result_data = data
                            elif event_type == "error":
                                result_data = {"success": False, "error": data.get("error", "unknown")}

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = result_data.get("cost_usd", 0.0)
        session_id = result_data.get("session_id", "")
        task_result = result_data.get("task_result", {})
        artifacts = result_data.get("artifacts", {})

        output = task_result or {"summary": result_data.get("summary", "")}
        output["iterations_count"] = len(iterations)

        context_for_next: dict = {}
        if artifacts:
            context_for_next["artifacts"] = artifacts

        return SkillResult(
            skill_name=ctx.skill_name,
            success=result_data.get("success", False),
            output=output,
            reasoning_trace=[
                f"Claude Code Worker: {len(iterations)} tool calls",
                f"Session: {session_id}",
                f"Worker pod: {worker.pod_name}",
            ],
            model_used=ctx.model,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            context_for_next=context_for_next,
        )

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        logger.error("Claude Code worker execution failed: %s", e)
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
    finally:
        claude_code_worker.close(worker)


async def execute_claude_code_streaming(
    ctx: SkillContext,
) -> AsyncGenerator[AgentIteration | SkillResult, None]:
    """Streaming variant — yields AgentIteration events then SkillResult."""
    from agentura_sdk.sandbox import claude_code_worker

    start = time.monotonic()
    sandbox_cfg = ctx.sandbox_config or SandboxConfig()
    env_vars = _build_worker_env(ctx)

    worker = await claude_code_worker.create(sandbox_cfg, env_vars)
    try:
        request_body = _build_agent_request(ctx)
        worker_url = f"http://{worker.pod_ip}:8080/execute-stream"

        iterations: list[AgentIteration] = []
        result_data: dict = {}

        async with httpx.AsyncClient(timeout=httpx.Timeout(WORKER_TIMEOUT)) as client:
            async with client.stream("POST", worker_url, json=request_body) as resp:
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        frame, buffer = buffer.split("\n\n", 1)
                        events = _parse_sse_events(frame + "\n\n")
                        for event_type, data in events:
                            if event_type == "iteration":
                                ui_name, ui_input = _map_tool_for_ui(
                                    data.get("tool_name", ""), data.get("tool_input", {})
                                )
                                iteration = AgentIteration(
                                    iteration=data.get("iteration", len(iterations) + 1),
                                    tool_name=ui_name,
                                    tool_input=ui_input,
                                    tool_output="",
                                    timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                                )
                                iterations.append(iteration)
                                yield iteration
                            elif event_type == "tool_result":
                                tool_use_id = data.get("tool_use_id", "")
                                output = data.get("output", "")
                                # Match tool result to pending iteration (best effort)
                                if iterations:
                                    iterations[-1].tool_output = output[:2000]
                            elif event_type == "result":
                                result_data = data
                            elif event_type == "error":
                                result_data = {"success": False, "error": data.get("error", "unknown")}

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = result_data.get("cost_usd", 0.0)
        task_result = result_data.get("task_result", {})
        artifacts = result_data.get("artifacts", {})

        output = task_result or {"summary": result_data.get("summary", "")}
        output["iterations_count"] = len(iterations)

        context_for_next: dict = {}
        if artifacts:
            context_for_next["artifacts"] = artifacts

        yield SkillResult(
            skill_name=ctx.skill_name,
            success=result_data.get("success", False),
            output=output,
            reasoning_trace=[
                f"Claude Code Worker: {len(iterations)} tool calls",
                f"Worker pod: {worker.pod_name}",
            ],
            model_used=ctx.model,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            context_for_next=context_for_next,
        )

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        logger.error("Claude Code worker streaming failed: %s", e)
        yield SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
    finally:
        claude_code_worker.close(worker)
