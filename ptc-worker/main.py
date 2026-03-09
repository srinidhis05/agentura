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
    approval_tools: list[str] = Field(default_factory=list)
    verify_criteria: list[str] = Field(default_factory=list)
    verify_max_retries: int = 1


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# MCP tool discovery and dispatch — supports both REST and MCP Streamable HTTP
# ---------------------------------------------------------------------------

# Servers using MCP Streamable HTTP protocol (detected at discovery time)
_mcp_protocol_servers: set[str] = set()
# Session IDs for MCP Streamable HTTP servers (from initialize response)
_mcp_session_ids: dict[str, str] = {}
# Auth headers per server URL
_mcp_server_headers: dict[str, dict[str, str]] = {}


def _parse_sse_data(text: str) -> dict:
    """Extract JSON from an SSE 'data:' frame."""
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(text)


def _mcp_headers(server_url: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Build headers for an MCP request, including auth and session."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    # Auth headers from server config
    if server_url in _mcp_server_headers:
        headers.update(_mcp_server_headers[server_url])
    # Session ID from initialize response
    if server_url in _mcp_session_ids:
        headers["Mcp-Session-Id"] = _mcp_session_ids[server_url]
    if extra:
        headers.update(extra)
    return headers


def _mcp_initialize(server_url: str) -> bool:
    """Send MCP initialize and store session ID. Returns True on success."""
    try:
        resp = httpx.post(
            server_url,
            json={
                "jsonrpc": "2.0", "id": 0, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "agentura-ptc", "version": "1.0"},
                },
            },
            headers=_mcp_headers(server_url),
            timeout=MCP_FETCH_TIMEOUT,
        )
        resp.raise_for_status()
        session_id = resp.headers.get("Mcp-Session-Id", "")
        if session_id:
            _mcp_session_ids[server_url] = session_id
        return True
    except Exception as exc:
        logger.error("MCP initialize failed for %s: %s", server_url, exc)
        return False


def _fetch_tools_rest(server_url: str) -> list[dict] | None:
    """Try REST API: GET {url}/tools → [{name, description, input_schema}]."""
    try:
        resp = httpx.get(f"{server_url}/tools", timeout=MCP_FETCH_TIMEOUT)
        if resp.status_code in (405, 406):
            return None  # Not REST — signal to try MCP protocol
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _fetch_tools_mcp(server_url: str) -> list[dict] | None:
    """Try MCP Streamable HTTP: initialize → tools/list."""
    try:
        # Initialize first to get session ID
        if not _mcp_initialize(server_url):
            return None

        resp = httpx.post(
            server_url,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers=_mcp_headers(server_url),
            timeout=MCP_FETCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = _parse_sse_data(resp.text)
        tools = data.get("result", {}).get("tools", [])
        # Normalize MCP tool defs → Anthropic API format
        # Only keep: name, description, input_schema (strip all other fields)
        cleaned: list[dict] = []
        for tool in tools:
            schema = tool.get("input_schema") or tool.get("inputSchema") or {"type": "object", "properties": {}}
            cleaned.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": schema,
            })
        tools = cleaned
        return tools
    except Exception as exc:
        logger.error("MCP Streamable HTTP tools/list failed for %s: %s", server_url, exc)
        return None


def _fetch_mcp_tools(
    mcp_servers: dict[str, dict],
    allowed_tools: list[str],
) -> tuple[list[dict], dict[str, str]]:
    """Discover tools from MCP servers. Returns (tool_defs, name->url map)."""
    all_tools: list[dict] = []
    tool_server_map: dict[str, str] = {}
    _mcp_protocol_servers.clear()
    _mcp_session_ids.clear()
    _mcp_server_headers.clear()

    for server_name, server_cfg in mcp_servers.items():
        server_url = server_cfg.get("url", "")
        if not server_url:
            continue

        # Store auth headers for this server
        if server_cfg.get("headers"):
            _mcp_server_headers[server_url] = server_cfg["headers"]

        # Try REST first (backward compat with k8s-mcp), fall back to MCP protocol
        remote_tools = _fetch_tools_rest(server_url)
        if remote_tools is None:
            remote_tools = _fetch_tools_mcp(server_url)
            if remote_tools is not None:
                _mcp_protocol_servers.add(server_url)
                logger.info("MCP Streamable HTTP: %s (%s) — %d tools", server_name, server_url, len(remote_tools))

        if remote_tools is None:
            logger.error("Failed to fetch tools from %s (%s) via both REST and MCP", server_name, server_url)
            continue

        for tool_def in remote_tools:
            name = tool_def["name"]
            if allowed_tools and "*" not in allowed_tools:
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


def _call_mcp_tool_rest(server_url: str, tool_name: str, arguments: dict) -> str:
    """Call tool via REST API: POST {url}/tools/call."""
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


def _call_mcp_tool_protocol(server_url: str, tool_name: str, arguments: dict) -> str:
    """Call tool via MCP Streamable HTTP: POST {url} with JSON-RPC tools/call."""
    resp = httpx.post(
        server_url,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
        headers=_mcp_headers(server_url),
        timeout=MCP_CALL_TIMEOUT,
    )
    resp.raise_for_status()
    data = _parse_sse_data(resp.text)
    result = data.get("result", {})
    if result.get("isError"):
        texts = [c.get("text", "") for c in result.get("content", [])]
        return f"[error] {' '.join(texts)}"
    texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
    return "\n".join(texts)


_pending_approvals: list[dict] = []


def _call_mcp_tool(
    tool_name: str,
    arguments: dict,
    tool_server_map: dict[str, str],
    *,
    tools_called: set[str] | None = None,
    approval_tools: list[str] | None = None,
) -> str:
    """Dispatch a tool call to its MCP server (auto-detects protocol)."""
    # Intercept tools that require human approval
    if approval_tools and tool_name in approval_tools:
        _pending_approvals.append({
            "tool": tool_name,
            "arguments": arguments,
            "server": tool_server_map.get(tool_name, ""),
        })
        return (
            f"[APPROVAL REQUIRED] The action '{tool_name}' requires human approval. "
            f"The request has been captured and will be included in your output for the user to review. "
            f"Do NOT retry this tool. Continue with other tasks or call task_complete."
        )

    if tool_name == "task_complete":
        called = tools_called or set()
        # Only enforce write-tool check when write tools are actually available
        write_tools = {"kubectl_apply", "write_file", "run_command"}
        available_write_tools = write_tools & set(tool_server_map.keys())
        if available_write_tools and not (called & available_write_tools):
            return "[error] You have not called any mutating tools yet. You MUST apply changes before completing."
        return json.dumps(arguments)

    server_url = tool_server_map.get(tool_name)
    if not server_url:
        return f"[error] Unknown tool: {tool_name}"

    try:
        if server_url in _mcp_protocol_servers:
            return _call_mcp_tool_protocol(server_url, tool_name, arguments)
        return _call_mcp_tool_rest(server_url, tool_name, arguments)
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

        # Clear pending approvals from prior runs
        _pending_approvals.clear()

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
                        approval_tools=request.approval_tools,
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

        # Self-critique verification (DEC-069)
        verified = None
        verify_issues: list[str] = []
        if task_completed and request.verify_criteria:
            try:
                yield _sse("verify_start", {"criteria": request.verify_criteria})

                output_text = json.dumps(final_output, indent=2)
                criteria_block = "\n".join(f"- {c}" for c in request.verify_criteria)
                verify_prompt = (
                    f"## Post-Execution Verification\n\nReview the output below against these criteria:\n\n"
                    f"{criteria_block}\n\n### Output to Verify\n\n{output_text[:4000]}\n\n"
                    f"If ALL criteria are satisfied, respond with:\nVERIFIED: <confirmation>\n\n"
                    f"If ANY criteria are NOT satisfied, respond with:\nISSUES: <numbered list>"
                )
                messages.append({"role": "user", "content": verify_prompt})
                verify_response = anthropic.messages.create(
                    model=request.model,
                    max_tokens=1024,
                    system=request.system_prompt,
                    messages=messages,
                    temperature=0.0,
                )
                total_in += verify_response.usage.input_tokens
                total_out += verify_response.usage.output_tokens
                verify_text = verify_response.content[0].text if verify_response.content else ""

                if verify_text.strip().upper().startswith("VERIFIED"):
                    verified = True
                    yield _sse("verify_pass", {"message": verify_text})
                else:
                    verified = False
                    verify_issues = [verify_text[:500]]
                    yield _sse("verify_fail", {"issues": verify_issues})
            except Exception as vexc:
                logger.debug("Verification failed: %s", vexc)

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = (total_in * 3.0 + total_out * 15.0) / 1_000_000

        # Attach pending approvals to output so they surface to the user
        if _pending_approvals:
            final_output["pending_approvals"] = list(_pending_approvals)

        yield _sse("result", {
            "success": task_completed or bool(final_output),
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "iterations_count": iteration_count,
            "task_result": final_output,
            "summary": final_output.get("summary", ""),
            "verified": verified,
            "verify_issues": verify_issues,
            "pending_approvals": list(_pending_approvals),
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
