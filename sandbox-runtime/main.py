"""Sandbox runtime — FastAPI server running inside isolated pods/containers.

Exposes /execute, /code, /files, /health endpoints for the agent executor
to drive tool calls against. Runs arbitrary user code — must be isolated.
"""

from __future__ import annotations

import subprocess
import sys
from io import StringIO
from pathlib import Path

from fastapi import FastAPI, Query
from pydantic import BaseModel

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
    result = subprocess.run(
        req.command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
        cwd="/home/sandbox",
    )
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


@app.post("/files", response_model=FileWriteResponse)
def write_file(req: FileWriteRequest):
    p = Path(req.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(req.content)
    return FileWriteResponse(message=f"Written {len(req.content)} bytes to {req.path}")


@app.get("/files", response_model=FileReadResponse)
def read_file(path: str = Query(..., description="Absolute file path to read")):
    p = Path(path)
    if not p.exists():
        return FileReadResponse(content=f"[error] File not found: {path}")
    return FileReadResponse(content=p.read_text())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
