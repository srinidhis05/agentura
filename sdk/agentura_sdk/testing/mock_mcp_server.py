"""In-process mock MCP server for workflow evals (DEC-070).

Starts a FastAPI server on a random port that responds to /tools and /tools/call
with canned responses. Tracks all tool invocations for assertion checking.
"""

from __future__ import annotations

import socket
import threading
from dataclasses import dataclass, field

import uvicorn
from fastapi import FastAPI

from agentura_sdk.testing.eval_types import MockToolConfig


@dataclass
class ToolCall:
    tool_name: str
    arguments: dict


class MockMCPServer:
    """In-process mock MCP server for testing skill behavior without live K8s."""

    def __init__(self, mock_tools: dict[str, MockToolConfig]):
        self._mock_tools = mock_tools
        self._calls: list[ToolCall] = []
        self._port = _find_free_port()
        self._app = self._build_app()
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    @property
    def calls(self) -> list[ToolCall]:
        return list(self._calls)

    @property
    def call_names(self) -> list[str]:
        return [c.tool_name for c in self._calls]

    def _build_app(self) -> FastAPI:
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ready"}

        @app.get("/tools")
        def list_tools():
            tools = []
            for name in self._mock_tools:
                tools.append({
                    "name": name,
                    "description": f"Mock tool: {name}",
                    "inputSchema": {"type": "object", "properties": {}},
                })
            return tools

        @app.post("/tools/call")
        def call_tool(request: dict):
            tool_name = request.get("name", "")
            arguments = request.get("arguments", {})
            self._calls.append(ToolCall(tool_name=tool_name, arguments=arguments))

            config = self._mock_tools.get(tool_name)
            if config:
                return {"content": [{"type": "text", "text": config.response}]}
            return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

        return app

    def start(self) -> None:
        """Start the mock server in a background thread."""
        config = uvicorn.Config(
            self._app,
            host="127.0.0.1",
            port=self._port,
            log_level="error",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        # Wait for server to be ready
        import time
        for _ in range(50):
            try:
                import urllib.request
                urllib.request.urlopen(f"{self.url}/health", timeout=1)
                return
            except Exception:
                time.sleep(0.1)

    def stop(self) -> None:
        """Stop the mock server."""
        if self._server:
            self._server.should_exit = True
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
