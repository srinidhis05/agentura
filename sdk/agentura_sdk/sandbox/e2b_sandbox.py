"""Thin wrapper over E2B Code Interpreter SDK.

All public methods return plain strings (stdout/stderr combined).
No complex objects cross this boundary.
"""

from __future__ import annotations

from agentura_sdk.types import SandboxConfig

try:
    from e2b_code_interpreter import Sandbox
except ImportError:
    Sandbox = None  # type: ignore[assignment,misc]


def _require_sdk() -> None:
    if Sandbox is None:
        raise ImportError(
            "e2b-code-interpreter is not installed. "
            "Install with: pip install -e '.[agent]'"
        )


async def create(config: SandboxConfig, env_vars: dict[str, str] | None = None) -> "Sandbox":
    """Create and return an E2B sandbox instance."""
    _require_sdk()
    kwargs: dict = {
        "template": config.template,
        "timeout": config.timeout,
    }
    if env_vars:
        kwargs["envs"] = env_vars
    sandbox = Sandbox(**kwargs)
    return sandbox


def run_code(sandbox: "Sandbox", code: str) -> str:
    """Execute Python code in the sandbox, return combined output."""
    execution = sandbox.run_code(code)
    parts: list[str] = []
    for result in execution.results:
        if result.text:
            parts.append(result.text)
    if execution.logs.stdout:
        parts.append(execution.logs.stdout)
    if execution.logs.stderr:
        parts.append(f"[stderr] {execution.logs.stderr}")
    if execution.error:
        parts.append(f"[error] {execution.error.name}: {execution.error.value}")
    return "\n".join(parts) or "(no output)"


def run_command(sandbox: "Sandbox", cmd: str) -> str:
    """Run a shell command in the sandbox, return combined output."""
    result = sandbox.commands.run(cmd)
    parts: list[str] = []
    if result.stdout:
        parts.append(result.stdout)
    if result.stderr:
        parts.append(f"[stderr] {result.stderr}")
    return "\n".join(parts) or "(no output)"


def write_file(sandbox: "Sandbox", path: str, content: str) -> str:
    """Write content to a file in the sandbox."""
    sandbox.files.write(path, content)
    return f"Written {len(content)} bytes to {path}"


def read_file(sandbox: "Sandbox", path: str) -> str:
    """Read a file from the sandbox."""
    return sandbox.files.read(path)


def close(sandbox: "Sandbox") -> None:
    """Terminate the sandbox."""
    try:
        sandbox.kill()
    except Exception:
        pass
