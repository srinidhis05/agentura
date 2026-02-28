"""Claude Code Worker — isolated FastAPI server wrapping claude-agent-sdk.

Each worker pod handles a single agent execution, streaming SSE events
back to the executor. Created/destroyed per-request by claude_code_worker.py.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

WORK_DIR = os.environ.get("WORK_DIR", "/home/worker/workspace")

app = FastAPI(title="Claude Code Worker", version="0.1.0")


class AgentRequest(BaseModel):
    prompt: str
    system_prompt: str
    model: str = "claude-sonnet-4-5-20250929"
    max_turns: int = 25
    max_budget_usd: float | None = None
    mcp_servers: dict = Field(default_factory=dict)
    allowed_tools: list[str] = Field(default_factory=list)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/execute-stream")
async def execute_stream(request: AgentRequest):
    """Run Claude Code agent and stream SSE events."""
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
        query,
    )

    async def event_generator():
        start = time.monotonic()
        iteration_count = 0

        # Write input to workspace
        Path(WORK_DIR).mkdir(parents=True, exist_ok=True)

        allowed_tools = request.allowed_tools or [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        ]

        options = ClaudeAgentOptions(
            system_prompt=request.system_prompt,
            allowed_tools=allowed_tools,
            mcp_servers=request.mcp_servers or {},
            permission_mode="bypassPermissions",
            cwd=WORK_DIR,
            max_turns=request.max_turns,
            max_budget_usd=request.max_budget_usd,
            model=request.model,
        )

        result_msg = None
        final_text_parts: list[str] = []

        try:
            async for message in query(prompt=request.prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            iteration_count += 1
                            yield _sse("iteration", {
                                "iteration": iteration_count,
                                "tool_name": block.name,
                                "tool_input": block.input,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                        elif isinstance(block, TextBlock):
                            final_text_parts.append(block.text)

                elif isinstance(message, UserMessage):
                    if isinstance(message.content, list):
                        for block in message.content:
                            if isinstance(block, ToolResultBlock) and block.tool_use_id:
                                content = block.content
                                output = ""
                                if isinstance(content, str):
                                    output = content[:2000]
                                elif isinstance(content, list):
                                    text_parts = [
                                        c.get("text", "") for c in content
                                        if isinstance(c, dict) and c.get("type") == "text"
                                    ]
                                    output = "\n".join(text_parts)[:2000]
                                yield _sse("tool_result", {
                                    "tool_use_id": block.tool_use_id,
                                    "output": output,
                                })

                elif isinstance(message, ResultMessage):
                    result_msg = message

            # Read TASK_RESULT.json if exists
            task_result = {}
            result_path = Path(WORK_DIR) / "TASK_RESULT.json"
            if result_path.exists():
                try:
                    task_result = json.loads(result_path.read_text())
                except (json.JSONDecodeError, OSError):
                    pass

            # Collect artifacts from workspace
            artifacts: dict[str, str] = {}
            work_path = Path(WORK_DIR)
            for fpath in work_path.rglob("*"):
                if fpath.is_file() and fpath.name not in ("INPUT.json", "TASK_RESULT.json"):
                    rel = str(fpath.relative_to(work_path))
                    try:
                        artifacts[rel] = fpath.read_text()
                    except (UnicodeDecodeError, OSError):
                        artifacts[rel] = f"<binary: {fpath.stat().st_size} bytes>"

            latency_ms = (time.monotonic() - start) * 1000
            cost_usd = result_msg.total_cost_usd if result_msg and result_msg.total_cost_usd else 0.0
            session_id = result_msg.session_id if result_msg else ""
            is_error = result_msg.is_error if result_msg else False

            yield _sse("result", {
                "success": not is_error,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "session_id": session_id,
                "iterations_count": iteration_count,
                "task_result": task_result,
                "summary": "\n".join(final_text_parts),
                "artifacts": artifacts,
            })

        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.error("Agent execution failed: %s", exc)
            yield _sse("error", {
                "error": str(exc),
                "latency_ms": latency_ms,
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
