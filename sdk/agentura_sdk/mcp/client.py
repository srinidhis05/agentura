"""MCP HTTP client — thin wrapper for calling MCP tool servers over HTTP."""

from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY = 2  # seconds


def fetch_tool_definitions(server_url: str) -> list[dict]:
    """GET /tools from an MCP server, return list of Anthropic-format tool defs."""
    for attempt in range(_MAX_RETRIES):
        try:
            resp = httpx.get(f"{server_url}/tools", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, OSError) as exc:
            if attempt < _MAX_RETRIES - 1:
                logger.warning("MCP fetch retry %d/%d for %s: %s", attempt + 1, _MAX_RETRIES, server_url, exc)
                time.sleep(_RETRY_DELAY)
            else:
                raise


def call_tool(server_url: str, tool_name: str, arguments: dict) -> str:
    """POST /tools/call on an MCP server, return the content string."""
    for attempt in range(_MAX_RETRIES):
        try:
            resp = httpx.post(
                f"{server_url}/tools/call",
                json={"name": tool_name, "arguments": arguments},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("is_error"):
                return f"[error] {data['content']}"
            return data["content"]
        except (httpx.ConnectError, OSError) as exc:
            if attempt < _MAX_RETRIES - 1:
                logger.warning("MCP call retry %d/%d for %s/%s: %s", attempt + 1, _MAX_RETRIES, server_url, tool_name, exc)
                time.sleep(_RETRY_DELAY)
            else:
                raise
