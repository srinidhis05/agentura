"""Sandbox runtime — FastAPI server running inside isolated pods/containers.

Exposes /execute, /code, /files, /health endpoints for the agent executor
to drive tool calls against. Runs arbitrary user code — must be isolated.

Also supports file-based IPC: if /ipc/ directory exists at startup, a background
thread watches for request files and writes response files.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import time
from io import StringIO
from pathlib import Path

from fastapi import FastAPI, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
app = FastAPI(title="sandbox-runtime")


class CommandRequest(BaseModel):
    command: str


class CommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


class CodeRequest(BaseModel):
    code: str


class CodeResponse(BaseModel):
    output: str
    error: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class FileWriteResponse(BaseModel):
    message: str


class FileReadResponse(BaseModel):
    content: str


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ready")


@app.post("/execute", response_model=CommandResponse)
def execute(req: CommandRequest):
    try:
        result = subprocess.run(
            req.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/home/sandbox",
        )
    except subprocess.TimeoutExpired:
        return CommandResponse(stdout="", stderr="[error] Command timed out after 120s", exit_code=124)
    except Exception as e:
        return CommandResponse(stdout="", stderr=f"[error] {type(e).__name__}: {e}", exit_code=1)
    return CommandResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )


@app.post("/code", response_model=CodeResponse)
def run_code(req: CodeRequest):
    old_stdout = sys.stdout
    sys.stdout = captured = StringIO()
    error = ""
    try:
        exec(req.code, {"__builtins__": __builtins__})
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    finally:
        sys.stdout = old_stdout
    return CodeResponse(output=captured.getvalue(), error=error)


WRITABLE_ROOTS = ("/home/sandbox", "/home/user", "/tmp")


@app.post("/files", response_model=FileWriteResponse)
def write_file(req: FileWriteRequest):
    p = Path(req.path).resolve()
    if not any(str(p).startswith(root) for root in WRITABLE_ROOTS):
        return FileWriteResponse(
            message=f"[error] Cannot write to {req.path} — use /home/sandbox/ as your working directory"
        )
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(req.content)
        return FileWriteResponse(message=f"Written {len(req.content)} bytes to {req.path}")
    except PermissionError:
        return FileWriteResponse(
            message=f"[error] Permission denied writing to {req.path} — use /home/sandbox/ instead"
        )
    except Exception as e:
        return FileWriteResponse(message=f"[error] {type(e).__name__}: {e}")


@app.get("/files", response_model=FileReadResponse)
def read_file(path: str = Query(..., description="Absolute file path to read")):
    p = Path(path)
    if not p.exists():
        return FileReadResponse(content=f"[error] File not found: {path}")
    return FileReadResponse(content=p.read_text())


# --- File-based IPC watcher ---

IPC_ROOT = Path("/ipc")
IPC_REQUESTS = IPC_ROOT / "requests"
IPC_RESPONSES = IPC_ROOT / "responses"
IPC_POLL_INTERVAL = 0.1  # 100ms


def _handle_ipc_request(req_path: Path) -> None:
    """Process a single IPC request file and write the response."""
    try:
        data = json.loads(req_path.read_text())
        req_id = data["id"]
        tool = data["tool"]
        args = data.get("args", {})
    except Exception as e:
        logger.error("IPC: failed to parse request %s: %s", req_path, e)
        req_path.unlink(missing_ok=True)
        return

    req_path.unlink(missing_ok=True)

    result = None
    error = None

    try:
        if tool == "execute":
            resp = execute(CommandRequest(command=args.get("command", "")))
            parts = []
            if resp.stdout:
                parts.append(resp.stdout)
            if resp.stderr:
                parts.append(f"[stderr] {resp.stderr}")
            if resp.exit_code != 0:
                parts.append(f"[exit_code] {resp.exit_code}")
            result = "\n".join(parts) or "(no output)"

        elif tool == "code":
            resp = run_code(CodeRequest(code=args.get("code", "")))
            parts = []
            if resp.output:
                parts.append(resp.output)
            if resp.error:
                parts.append(f"[error] {resp.error}")
            result = "\n".join(parts) or "(no output)"

        elif tool == "files_write":
            resp = write_file(FileWriteRequest(path=args.get("path", ""), content=args.get("content", "")))
            result = resp.message

        elif tool == "files_read":
            resp = read_file(path=args.get("path", ""))
            result = resp.content

        else:
            error = f"unknown IPC tool: {tool}"

    except Exception as e:
        error = f"{type(e).__name__}: {e}"

    IPC_RESPONSES.mkdir(parents=True, exist_ok=True)
    response = {"id": req_id, "result": result, "error": error}
    (IPC_RESPONSES / f"{req_id}.json").write_text(json.dumps(response))


def _ipc_watcher() -> None:
    """Background thread that polls /ipc/requests/ for new request files."""
    logger.info("IPC watcher started, watching %s", IPC_REQUESTS)
    IPC_REQUESTS.mkdir(parents=True, exist_ok=True)
    IPC_RESPONSES.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            for req_path in sorted(IPC_REQUESTS.glob("*.json")):
                _handle_ipc_request(req_path)
        except Exception as e:
            logger.error("IPC watcher error: %s", e)
        time.sleep(IPC_POLL_INTERVAL)


@app.on_event("startup")
def _start_ipc_watcher() -> None:
    """Start file-based IPC watcher if /ipc/ directory exists."""
    if IPC_ROOT.exists():
        thread = threading.Thread(target=_ipc_watcher, daemon=True)
        thread.start()
        logger.info("IPC file watcher thread started")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
