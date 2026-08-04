"""No-op sandbox backend.

Used when SANDBOX_BACKEND=none — skips Docker container creation entirely.
Only non-sandbox tools (e.g. git_codebase, MCP tools) will work.
Sandbox tools (write_file, run_command, etc.) return a clear error message.
"""

from __future__ import annotations

from agentura_sdk.types import SandboxConfig


class _NoopSandbox:
    """Placeholder sandbox object — no container, no network port."""


async def create(cfg: SandboxConfig, env_vars: dict[str, str] | None = None) -> _NoopSandbox:
    return _NoopSandbox()


def close(sandbox: _NoopSandbox) -> None:
    pass


def _not_available(tool: str) -> str:
    return (
        f"[error] '{tool}' requires a Docker sandbox (SANDBOX_BACKEND=docker). "
        "This skill runs with SANDBOX_BACKEND=none — only git_codebase and MCP tools are available."
    )


def write_file(sandbox: _NoopSandbox, path: str, content: str) -> str:
    return _not_available("write_file")


def read_file(sandbox: _NoopSandbox, path: str) -> str:
    return _not_available("read_file")


def run_command(sandbox: _NoopSandbox, command: str) -> str:
    return _not_available("run_command")


def run_code(sandbox: _NoopSandbox, code: str) -> str:
    return _not_available("run_code")
