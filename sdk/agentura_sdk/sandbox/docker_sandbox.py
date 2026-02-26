"""Docker sandbox — local dev fallback using Docker containers.

Same 6-function sandbox interface:
  create, run_code, run_command, write_file, read_file, close
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from agentura_sdk.types import SandboxConfig

try:
    import docker
except ImportError:
    docker = None  # type: ignore[assignment]

IMAGE = "agentura/sandbox-runtime:latest"
CONTAINER_PORT = 8080
READY_TIMEOUT = 30


@dataclass
class DockerSandbox:
    container_id: str
    host_port: int


def _require_sdk() -> None:
    if docker is None:
        raise ImportError(
            "docker is not installed. "
            "Install with: pip install -e '.[sandbox]'"
        )


def _wait_for_healthy(port: int) -> None:
    """Poll /health until the container is ready."""
    deadline = time.monotonic() + READY_TIMEOUT
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"http://localhost:{port}/health", timeout=2)
            if resp.status_code == 200:
                return
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Sandbox container not ready on port {port} within {READY_TIMEOUT}s")


async def create(cfg: SandboxConfig, env_vars: dict[str, str] | None = None) -> DockerSandbox:
    """Run a sandbox-runtime container and wait for it to become healthy."""
    _require_sdk()
    client = docker.from_env()
    environment = env_vars or {}
    container = client.containers.run(
        IMAGE,
        detach=True,
        ports={f"{CONTAINER_PORT}/tcp": None},
        environment=environment,
        mem_limit=f"{cfg.memory}m",
        nano_cpus=cfg.cpu * 1_000_000_000,
        name=f"sandbox-{int(time.time() * 1000) % 10_000_000:07d}",
    )

    container.reload()
    host_port = int(
        container.attrs["NetworkSettings"]["Ports"][f"{CONTAINER_PORT}/tcp"][0]["HostPort"]
    )

    _wait_for_healthy(host_port)
    return DockerSandbox(container_id=container.id, host_port=host_port)


def _url(sandbox: DockerSandbox, path: str) -> str:
    return f"http://localhost:{sandbox.host_port}{path}"


def run_code(sandbox: DockerSandbox, code: str) -> str:
    resp = httpx.post(_url(sandbox, "/code"), json={"code": code}, timeout=120)
    data = resp.json()
    parts = []
    if data.get("output"):
        parts.append(data["output"])
    if data.get("error"):
        parts.append(f"[error] {data['error']}")
    return "\n".join(parts) or "(no output)"


def run_command(sandbox: DockerSandbox, cmd: str) -> str:
    resp = httpx.post(_url(sandbox, "/execute"), json={"command": cmd}, timeout=120)
    data = resp.json()
    parts = []
    if data.get("stdout"):
        parts.append(data["stdout"])
    if data.get("stderr"):
        parts.append(f"[stderr] {data['stderr']}")
    if data.get("exit_code", 0) != 0:
        parts.append(f"[exit_code] {data['exit_code']}")
    return "\n".join(parts) or "(no output)"


def write_file(sandbox: DockerSandbox, path: str, content: str) -> str:
    resp = httpx.post(_url(sandbox, "/files"), json={"path": path, "content": content}, timeout=30)
    return resp.json().get("message", "written")


def read_file(sandbox: DockerSandbox, path: str) -> str:
    resp = httpx.get(_url(sandbox, "/files"), params={"path": path}, timeout=30)
    return resp.json().get("content", "")


def close(sandbox: DockerSandbox) -> None:
    """Remove the sandbox container."""
    try:
        _require_sdk()
        client = docker.from_env()
        container = client.containers.get(sandbox.container_id)
        container.remove(force=True)
    except Exception:
        pass
