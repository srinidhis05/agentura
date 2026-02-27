"""K8s sandbox with file-based IPC — uses kubectl exec to write/read files.

Same 6-function interface as k8s_sandbox.py but replaces HTTP round-trips
with file-based IPC via K8s exec API for sandbox tools. MCP tools still
use HTTP to their respective servers.

The executor creates the sandbox pod normally, then uses kubectl exec to
write request files and read response files inside the pod's /ipc/ directory.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

from agentura_sdk.sandbox.ipc_protocol import (
    DEFAULT_TIMEOUT,
    POLL_INTERVAL,
    IPCRequest,
    IPCResponse,
)
from agentura_sdk.types import SandboxConfig

try:
    from kubernetes import client, config, stream, watch
except ImportError:
    client = None  # type: ignore[assignment]
    config = None  # type: ignore[assignment]
    stream = None  # type: ignore[assignment]
    watch = None  # type: ignore[assignment]

NAMESPACE = os.environ.get("SANDBOX_NAMESPACE", "agentura")
IMAGE = os.environ.get("SANDBOX_IMAGE", "agentura/sandbox-runtime:latest")
RUNTIME_CLASS = os.environ.get("SANDBOX_RUNTIME_CLASS", "")
IMAGE_PULL_POLICY = os.environ.get("SANDBOX_IMAGE_PULL_POLICY", "Never")
POD_READY_TIMEOUT = 120


@dataclass
class K8sFileSandbox:
    pod_name: str
    namespace: str
    api: object  # CoreV1Api


def _require_sdk() -> None:
    if client is None:
        raise ImportError("kubernetes is not installed")


def _load_k8s_config() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def _build_pod_manifest(name: str, sandbox_cfg: SandboxConfig) -> client.V1Pod:
    container = client.V1Container(
        name="sandbox",
        image=IMAGE,
        image_pull_policy=IMAGE_PULL_POLICY,
        ports=[client.V1ContainerPort(container_port=8080)],
        resources=client.V1ResourceRequirements(
            requests={"cpu": f"{sandbox_cfg.cpu}", "memory": f"{sandbox_cfg.memory}Mi"},
            limits={"cpu": f"{sandbox_cfg.cpu}", "memory": f"{sandbox_cfg.memory}Mi"},
        ),
        volume_mounts=[
            client.V1VolumeMount(name="ipc", mount_path="/ipc"),
        ],
        readiness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path="/health", port=8080),
            initial_delay_seconds=2,
            period_seconds=2,
        ),
    )

    spec = client.V1PodSpec(
        containers=[container],
        restart_policy="Never",
        automount_service_account_token=False,
        volumes=[
            client.V1Volume(
                name="ipc",
                empty_dir=client.V1EmptyDirVolumeSource(medium="Memory", size_limit="10Mi"),
            ),
        ],
    )

    if RUNTIME_CLASS:
        spec.runtime_class_name = RUNTIME_CLASS

    return client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=NAMESPACE,
            labels={"app": "sandbox-runtime", "managed-by": "agentura-executor", "ipc": "file"},
        ),
        spec=spec,
    )


def _wait_for_ready(api: client.CoreV1Api, name: str, namespace: str) -> None:
    """Watch pod until Ready."""
    w = watch.Watch()
    deadline = time.monotonic() + POD_READY_TIMEOUT
    for event in w.stream(api.list_namespaced_pod, namespace=namespace, field_selector=f"metadata.name={name}"):
        pod = event["object"]
        if pod.status.conditions:
            for cond in pod.status.conditions:
                if cond.type == "Ready" and cond.status == "True":
                    w.stop()
                    return
        if time.monotonic() > deadline:
            w.stop()
            raise TimeoutError(f"Sandbox pod {name} not ready within {POD_READY_TIMEOUT}s")
    raise TimeoutError(f"Watch stream ended for pod {name}")


def _exec_in_pod(sandbox: K8sFileSandbox, command: list[str]) -> str:
    """Execute a command in the sandbox pod and return stdout."""
    resp = stream.stream(
        sandbox.api.connect_get_namespaced_pod_exec,
        sandbox.pod_name,
        sandbox.namespace,
        command=command,
        container="sandbox",
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    return resp


def _write_file_in_pod(sandbox: K8sFileSandbox, path: str, content: str) -> None:
    """Write a file inside the sandbox pod via exec."""
    _exec_in_pod(sandbox, ["sh", "-c", f"mkdir -p $(dirname {path}) && cat > {path}"])
    # Use base64 to safely transfer content
    import base64
    encoded = base64.b64encode(content.encode()).decode()
    _exec_in_pod(sandbox, [
        "sh", "-c",
        f"mkdir -p $(dirname {path}) && echo '{encoded}' | base64 -d > {path}",
    ])


def _read_file_in_pod(sandbox: K8sFileSandbox, path: str) -> str | None:
    """Read a file from the sandbox pod via exec. Returns None if not found."""
    result = _exec_in_pod(sandbox, ["sh", "-c", f"cat {path} 2>/dev/null || echo '__IPC_NOT_FOUND__'"])
    if "__IPC_NOT_FOUND__" in result:
        return None
    return result


def _send_ipc_request(sandbox: K8sFileSandbox, tool: str, args: dict) -> str:
    """Send an IPC request and wait for response."""
    req = IPCRequest.create(tool=tool, args=args)
    req_path = f"/ipc/requests/{req.id}.json"
    resp_path = f"/ipc/responses/{req.id}.json"

    _write_file_in_pod(sandbox, req_path, req.to_json())

    deadline = time.monotonic() + DEFAULT_TIMEOUT
    while time.monotonic() < deadline:
        content = _read_file_in_pod(sandbox, resp_path)
        if content is not None:
            resp = IPCResponse.from_json(content)
            _exec_in_pod(sandbox, ["rm", "-f", resp_path])
            if resp.error:
                return f"[error] {resp.error}"
            return resp.result or "(no output)"
        time.sleep(POLL_INTERVAL)
    return f"[error] IPC timeout after {DEFAULT_TIMEOUT}s"


async def create(cfg: SandboxConfig, env_vars: dict[str, str] | None = None) -> K8sFileSandbox:
    """Create a sandbox pod with file IPC support."""
    _require_sdk()
    _load_k8s_config()

    pod_name = f"sandbox-ipc-{int(time.time() * 1000) % 10_000_000:07d}"
    api = client.CoreV1Api()

    manifest = _build_pod_manifest(pod_name, cfg)
    api.create_namespaced_pod(namespace=NAMESPACE, body=manifest)

    _wait_for_ready(api, pod_name, NAMESPACE)

    sandbox = K8sFileSandbox(pod_name=pod_name, namespace=NAMESPACE, api=api)

    # Initialize IPC directories inside the pod
    _exec_in_pod(sandbox, ["mkdir", "-p", "/ipc/requests", "/ipc/responses"])

    return sandbox


def run_code(sandbox: K8sFileSandbox, code: str) -> str:
    return _send_ipc_request(sandbox, "code", {"code": code})


def run_command(sandbox: K8sFileSandbox, cmd: str) -> str:
    return _send_ipc_request(sandbox, "execute", {"command": cmd})


def write_file(sandbox: K8sFileSandbox, path: str, content: str) -> str:
    return _send_ipc_request(sandbox, "files_write", {"path": path, "content": content})


def read_file(sandbox: K8sFileSandbox, path: str) -> str:
    return _send_ipc_request(sandbox, "files_read", {"path": path})


def close(sandbox: K8sFileSandbox) -> None:
    """Delete the sandbox pod."""
    try:
        _load_k8s_config()
        api = client.CoreV1Api()
        api.delete_namespaced_pod(
            name=sandbox.pod_name,
            namespace=sandbox.namespace,
            grace_period_seconds=0,
        )
    except Exception:
        pass
