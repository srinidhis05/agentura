"""File-based IPC protocol for sandbox tool calls.

Protocol:
- Agent writes /ipc/requests/{uuid}.json with {"tool": "...", "args": {...}}
- Sandbox watches /ipc/requests/ and executes tools
- Sandbox writes /ipc/responses/{uuid}.json with {"result": "...", "error": null}
- Agent polls /ipc/responses/{uuid}.json with timeout
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

IPC_ROOT = Path("/ipc")
REQUESTS_DIR = IPC_ROOT / "requests"
RESPONSES_DIR = IPC_ROOT / "responses"

POLL_INTERVAL = 0.1  # 100ms
DEFAULT_TIMEOUT = 30.0  # 30s


@dataclass(frozen=True)
class IPCRequest:
    id: str
    tool: str
    args: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({"id": self.id, "tool": self.tool, "args": self.args})

    @classmethod
    def create(cls, tool: str, args: dict[str, Any]) -> IPCRequest:
        return cls(id=str(uuid.uuid4()), tool=tool, args=args)


@dataclass(frozen=True)
class IPCResponse:
    id: str
    result: str | None
    error: str | None

    @classmethod
    def from_json(cls, data: str) -> IPCResponse:
        parsed = json.loads(data)
        return cls(
            id=parsed["id"],
            result=parsed.get("result"),
            error=parsed.get("error"),
        )

    def to_json(self) -> str:
        return json.dumps({"id": self.id, "result": self.result, "error": self.error})


def write_request(req: IPCRequest, base: Path = REQUESTS_DIR) -> Path:
    """Write a request JSON file. Returns the file path."""
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{req.id}.json"
    path.write_text(req.to_json())
    return path


def poll_response(
    request_id: str,
    base: Path = RESPONSES_DIR,
    timeout: float = DEFAULT_TIMEOUT,
) -> IPCResponse:
    """Poll for a response file, blocking until found or timeout."""
    path = base / f"{request_id}.json"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            data = path.read_text()
            path.unlink(missing_ok=True)
            return IPCResponse.from_json(data)
        time.sleep(POLL_INTERVAL)
    return IPCResponse(id=request_id, result=None, error=f"IPC timeout after {timeout}s")


def write_response(resp: IPCResponse, base: Path = RESPONSES_DIR) -> Path:
    """Write a response JSON file (used by sandbox side)."""
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{resp.id}.json"
    path.write_text(resp.to_json())
    return path


def read_pending_requests(base: Path = REQUESTS_DIR) -> list[IPCRequest]:
    """Read and consume all pending request files (used by sandbox side)."""
    if not base.exists():
        return []
    requests = []
    for path in sorted(base.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            requests.append(IPCRequest(
                id=data["id"],
                tool=data["tool"],
                args=data.get("args", {}),
            ))
            path.unlink()
        except Exception:
            continue
    return requests
