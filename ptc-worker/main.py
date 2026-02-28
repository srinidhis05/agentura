"""PTC Worker — isolated FastAPI server running Anthropic tool-calling loop.

Each worker pod handles a single agent execution, streaming SSE events
back to the executor. Created/destroyed per-request by ptc_worker.py.

Lighter than claude-code-worker: Python-only, no Node.js, no sandbox filesystem.
Tools are dispatched to MCP servers over HTTP.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PTC Worker", version="0.1.0")

MCP_CALL_TIMEOUT = int(os.environ.get("MCP_CALL_TIMEOUT", "60"))
MCP_FETCH_TIMEOUT = int(os.environ.get("MCP_FETCH_TIMEOUT", "10"))


class PTCRequest(BaseModel):
    prompt: str
    system_prompt: str
    model: str = "claude-sonnet-4-5-20250929"
    max_turns: int = 15
    max_tokens: int = 16384
    mcp_servers: dict[str, dict] = Field(default_factory=dict)
    allowed_mcp_tools: list[str] = Field(default_factory=list)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# MCP tool discovery and dispatch
# ---------------------------------------------------------------------------

def _fetch_mcp_tools(
    mcp_servers: dict[str, dict],
    allowed_tools: list[str],
) -> tuple[list[dict], dict[str, str]]:
    """Discover tools from MCP servers. Returns (tool_defs, name->url map)."""
    all_tools: list[dict] = []
    tool_server_map: dict[str, str] = {}

    for server_name, server_cfg in mcp_servers.items():
        server_url = server_cfg.get("url", "")
        if not server_url:
            continue
        try:
            resp = httpx.get(f"{server_url}/tools", timeout=MCP_FETCH_TIMEOUT)
            resp.raise_for_status()
            remote_tools = resp.json()
        except Exception as exc:
            logger.error("Failed to fetch tools from %s: %s", server_url, exc)
            continue

        for tool_def in remote_tools:
            name = tool_def["name"]
            if allowed_tools:
                # Check both raw name and mcp__server__name format
                qualified = f"mcp__{server_name}__{name}"
                if name not in allowed_tools and qualified not in allowed_tools:
                    continue
            all_tools.append(tool_def)
            tool_server_map[name] = server_url

    # Always include task_complete
    all_tools.append({
        "name": "task_complete",
        "description": "Signal that the task is finished. Provide a summary and any output URLs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Summary of what was accomplished"},
                "url": {"type": "string", "description": "Access URL if applicable"},
                "port": {"type": "integer", "description": "Port number if applicable"},
                "deployed": {"type": "boolean", "description": "Whether deployment succeeded"},
            },
            "required": ["summary"],
        },
    })

    return all_tools, tool_server_map


def _call_mcp_tool(
    tool_name: str,
    arguments: dict,
    tool_server_map: dict[str, str],
    *,
    tools_called: set[str] | None = None,
) -> str:
    """Dispatch a tool call to its MCP server."""
    if tool_name == "task_complete":
        called = tools_called or set()
        # Require at least one write/mutating tool call — reads alone don't count
        write_tools = {"kubectl_apply", "write_file", "run_command"}
        if not called & write_tools:
            return "[error] You have not called any mutating tools (e.g. kubectl_apply). Reading state with kubectl_get is NOT enough. You MUST apply the manifest before completing. Generate the K8s YAML from the artifacts dict and call kubectl_apply NOW."
        return json.dumps(arguments)

    server_url = tool_server_map.get(tool_name)
    if not server_url:
        return f"[error] Unknown tool: {tool_name}"

    try:
        resp = httpx.post(
            f"{server_url}/tools/call",
            json={"name": tool_name, "arguments": arguments},
            timeout=MCP_CALL_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("is_error"):
            return f"[error] {data['content']}"
        return data["content"]
    except Exception as exc:
        return f"[error] MCP call failed: {exc}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/execute-stream")
async def execute_stream(request: PTCRequest):
    """Run PTC agent loop and stream SSE events."""

    async def event_generator():
        start = time.monotonic()
        iteration_count = 0

        # Discover MCP tools
        tools, tool_server_map = _fetch_mcp_tools(
            request.mcp_servers, request.allowed_mcp_tools,
        )

        if not tool_server_map:
            yield _sse("error", {"error": "No MCP tools discovered. Check MCP server URLs."})
            return

        logger.info("Discovered MCP tools: %s", list(tool_server_map.keys()))

        # Set up Anthropic client
        try:
            from anthropic import Anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                yield _sse("error", {"error": "ANTHROPIC_API_KEY not set"})
                return

            anthropic = Anthropic(api_key=api_key)
        except ImportError:
            yield _sse("error", {"error": "anthropic SDK not installed"})
            return

        messages: list[dict] = [
            {"role": "user", "content": request.prompt},
        ]
        total_in = 0
        total_out = 0
        final_output: dict = {}
        task_completed = False
        tools_called: set[str] = set()

        try:
            for _turn in range(request.max_turns):
                resp = anthropic.messages.create(
                    model=request.model,
                    max_tokens=request.max_tokens,
                    system=request.system_prompt,
                    tools=tools,
                    messages=messages,
                )

                messages.append({"role": "assistant", "content": resp.content})
                total_in += resp.usage.input_tokens
                total_out += resp.usage.output_tokens

                if resp.stop_reason == "max_tokens":
                    logger.warning("Response truncated (max_tokens hit at %d output tokens). Continuing.", resp.usage.output_tokens)
                    # Provide tool_results for any partial tool_use blocks so the API accepts the next turn
                    partial_tool_ids = [b.id for b in resp.content if b.type == "tool_use"]
                    if partial_tool_ids:
                        messages.append({"role": "user", "content": [
                            {"type": "tool_result", "tool_use_id": tid, "content": "[truncated] Your previous response was cut off. Please call the tool again with the complete input."}
                            for tid in partial_tool_ids
                        ]})
                    else:
                        messages.append({"role": "user", "content": "Your response was truncated. Please call the required tools now."})
                    continue

                if resp.stop_reason != "tool_use":
                    text_parts = [b.text for b in resp.content if b.type == "text"]
                    final_output = {"summary": "\n".join(text_parts)}
                    break

                # Process tool calls
                tool_results = []
                for block in resp.content:
                    if block.type != "tool_use":
                        continue

                    iteration_count += 1
                    yield _sse("iteration", {
                        "iteration": iteration_count,
                        "tool_name": block.name,
                        "tool_input": block.input,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                    tool_output = _call_mcp_tool(
                        block.name, block.input, tool_server_map,
                        tools_called=tools_called,
                    )

                    if block.name != "task_complete":
                        tools_called.add(block.name)

                    yield _sse("tool_result", {
                        "tool_use_id": block.id,
                        "output": tool_output[:2000],
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output[:4000],
                    })

                    # Only accept task_complete if it wasn't rejected
                    if block.name == "task_complete" and not tool_output.startswith("[error]"):
                        final_output = block.input
                        task_completed = True
                        break

                messages.append({"role": "user", "content": tool_results})

                if task_completed:
                    break

        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.error("PTC agent loop failed: %s", exc)
            yield _sse("error", {
                "error": str(exc),
                "latency_ms": latency_ms,
            })
            return

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = (total_in * 3.0 + total_out * 15.0) / 1_000_000

        yield _sse("result", {
            "success": task_completed or bool(final_output),
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "iterations_count": iteration_count,
            "task_result": final_output,
            "summary": final_output.get("summary", ""),
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
