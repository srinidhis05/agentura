"""Programmatic Tool Calling executor — agent loop via isolated worker pods.

Creates a lightweight PTC worker pod per agent execution, sends the agent
config via HTTP POST to the worker's /execute-stream endpoint, and streams
SSE events back. Worker pods are cleaned up after execution completes.

Lighter than claude-code-worker: Python-only, no Node.js, ~200MB image.
Tools are dispatched to MCP servers inside the worker pod.

Config: set ``executor: ptc`` in agentura.config.yaml to route here.
Requires: SANDBOX_BACKEND=k8s, ANTHROPIC_API_KEY set.
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

WORKER_TIMEOUT = int(os.environ.get("PTC_WORKER_TIMEOUT", "300"))


def _should_use_ptc(ctx: SkillContext | None = None) -> bool:
    """Use PTC when skill opts in via ``executor: ptc`` in config."""
    if not (ctx and ctx.sandbox_config and ctx.sandbox_config.executor == "ptc"):
        return False
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    if os.environ.get("SANDBOX_BACKEND") != "k8s":
        return False
    return True


def _resolve_model(model: str) -> str:
    """Resolve model string to Anthropic model ID."""
    name = model.removeprefix("anthropic/")
    return {
        "claude-sonnet-4.5": "claude-sonnet-4-5-latest",
        "claude-haiku-4.5": "claude-haiku-4-5-latest",
    }.get(name, name)


def _build_worker_env(ctx: SkillContext) -> dict[str, str]:
    """Build env vars to pass to the PTC worker pod."""
    env: dict[str, str] = {}
    if os.environ.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    return env


def _build_ptc_request(ctx: SkillContext) -> dict:
    """Build the HTTP request body for the worker's /execute-stream endpoint."""
    max_turns = 15
    if ctx.sandbox_config and ctx.sandbox_config.max_iterations:
        max_turns = ctx.sandbox_config.max_iterations

    # MCP server mapping — pass URLs so the worker can call them directly
    mcp_servers: dict = {}
    allowed_mcp_tools: list[str] = []
    for binding in ctx.mcp_bindings:
        server_name = binding.get("server", "")
        server_url = binding.get("url", "")
        if not server_name or not server_url:
            continue
        mcp_servers[server_name] = {"url": server_url}
        for tool_name in binding.get("tools", []):
            allowed_mcp_tools.append(tool_name)

    from agentura_sdk.runner.agent_executor import _build_prompt_with_memory

    system_prompt = _build_prompt_with_memory(ctx)

    return {
        "prompt": json.dumps(ctx.input_data, indent=2),
        "system_prompt": system_prompt,
        "model": _resolve_model(ctx.model),
        "max_turns": max_turns,
        "mcp_servers": mcp_servers,
        "allowed_mcp_tools": allowed_mcp_tools,
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


# ---------------------------------------------------------------------------
# One-shot execution
# ---------------------------------------------------------------------------

async def execute_ptc(ctx: SkillContext) -> SkillResult:
    """One-shot PTC execution via worker pod."""
    from agentura_sdk.sandbox import ptc_worker

    start = time.monotonic()
    sandbox_cfg = ctx.sandbox_config or SandboxConfig()
    env_vars = _build_worker_env(ctx)

    worker = await ptc_worker.create(sandbox_cfg, env_vars)
    try:
        request_body = _build_ptc_request(ctx)
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
                                iterations.append(AgentIteration(
                                    iteration=data.get("iteration", len(iterations) + 1),
                                    tool_name=data.get("tool_name", ""),
                                    tool_input=data.get("tool_input", {}),
                                    tool_output="",
                                    timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                                ))
                            elif event_type == "result":
                                result_data = data
                            elif event_type == "error":
                                result_data = {"success": False, "error": data.get("error", "unknown")}

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = result_data.get("cost_usd", 0.0)
        task_result = result_data.get("task_result", {})

        output = task_result or {"summary": result_data.get("summary", "")}
        output["iterations_count"] = len(iterations)

        return SkillResult(
            skill_name=ctx.skill_name,
            success=result_data.get("success", False),
            output=output,
            reasoning_trace=[
                f"PTC Worker: {len(iterations)} tool calls",
                f"Worker pod: {worker.pod_name}",
            ],
            model_used=ctx.model,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        logger.error("PTC worker execution failed: %s", e)
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
    finally:
        ptc_worker.close(worker)


# ---------------------------------------------------------------------------
# Streaming execution
# ---------------------------------------------------------------------------

async def execute_ptc_streaming(
    ctx: SkillContext,
) -> AsyncGenerator[AgentIteration | SkillResult, None]:
    """Streaming variant — yields AgentIteration events then SkillResult."""
    from agentura_sdk.sandbox import ptc_worker

    start = time.monotonic()
    sandbox_cfg = ctx.sandbox_config or SandboxConfig()
    env_vars = _build_worker_env(ctx)

    worker = await ptc_worker.create(sandbox_cfg, env_vars)
    try:
        request_body = _build_ptc_request(ctx)
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
                                iteration = AgentIteration(
                                    iteration=data.get("iteration", len(iterations) + 1),
                                    tool_name=data.get("tool_name", ""),
                                    tool_input=data.get("tool_input", {}),
                                    tool_output="",
                                    timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                                )
                                iterations.append(iteration)
                                yield iteration
                            elif event_type == "tool_result":
                                if iterations:
                                    iterations[-1].tool_output = data.get("output", "")[:2000]
                            elif event_type == "result":
                                result_data = data
                            elif event_type == "error":
                                result_data = {"success": False, "error": data.get("error", "unknown")}

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = result_data.get("cost_usd", 0.0)
        task_result = result_data.get("task_result", {})

        output = task_result or {"summary": result_data.get("summary", "")}
        output["iterations_count"] = len(iterations)

        yield SkillResult(
            skill_name=ctx.skill_name,
            success=result_data.get("success", False),
            output=output,
            reasoning_trace=[
                f"PTC Worker: {len(iterations)} tool calls",
                f"Worker pod: {worker.pod_name}",
            ],
            model_used=ctx.model,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        logger.error("PTC worker streaming failed: %s", e)
        yield SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
            model_used=ctx.model,
            latency_ms=latency_ms,
        )
    finally:
        ptc_worker.close(worker)
