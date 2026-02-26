"""K8s-native sandbox — creates ephemeral pods running sandbox-runtime.

Same 6-function sandbox interface:
  create, run_code, run_command, write_file, read_file, close
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx

from agentura_sdk.types import SandboxConfig

try:
    from kubernetes import client, config, watch
except ImportError:
    client = None  # type: ignore[assignment]
    config = None  # type: ignore[assignment]
    watch = None  # type: ignore[assignment]

NAMESPACE = os.environ.get("SANDBOX_NAMESPACE", "agentura")
IMAGE = os.environ.get("SANDBOX_IMAGE", "agentura/sandbox-runtime:latest")
RUNTIME_CLASS = os.environ.get("SANDBOX_RUNTIME_CLASS", "")
IMAGE_PULL_POLICY = os.environ.get("SANDBOX_IMAGE_PULL_POLICY", "Never")
POD_READY_TIMEOUT = 120


@dataclass
class K8sSandbox:
    pod_name: str
    pod_ip: str
    namespace: str


def _require_sdk() -> None:
    if client is None:
        raise ImportError(
            "kubernetes is not installed. "
            "Install with: pip install -e '.[sandbox]'"
        )


def _load_k8s_config() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def _build_pod_manifest(name: str, sandbox_cfg: SandboxConfig, env_vars: dict[str, str] | None) -> client.V1Pod:
    env = []
    if env_vars:
        env = [client.V1EnvVar(name=k, value=v) for k, v in env_vars.items()]

    container = client.V1Container(
        name="sandbox",
        image=IMAGE,
        image_pull_policy=IMAGE_PULL_POLICY,
        ports=[client.V1ContainerPort(container_port=8080)],
        env=env or None,
        resources=client.V1ResourceRequirements(
            requests={"cpu": f"{sandbox_cfg.cpu}", "memory": f"{sandbox_cfg.memory}Mi"},
            limits={"cpu": f"{sandbox_cfg.cpu}", "memory": f"{sandbox_cfg.memory}Mi"},
        ),
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
    )

    if RUNTIME_CLASS:
        spec.runtime_class_name = RUNTIME_CLASS

    return client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=NAMESPACE,
            labels={"app": "sandbox-runtime", "managed-by": "agentura-executor"},
        ),
        spec=spec,
    )


def _wait_for_ready(api: client.CoreV1Api, name: str, namespace: str) -> str:
    """Watch pod until Ready, return pod IP."""
    w = watch.Watch()
    deadline = time.monotonic() + POD_READY_TIMEOUT
    for event in w.stream(api.list_namespaced_pod, namespace=namespace, field_selector=f"metadata.name={name}"):
        pod = event["object"]
        if pod.status.pod_ip and pod.status.conditions:
            for cond in pod.status.conditions:
                if cond.type == "Ready" and cond.status == "True":
                    w.stop()
                    return pod.status.pod_ip
        if time.monotonic() > deadline:
            w.stop()
            raise TimeoutError(f"Sandbox pod {name} not ready within {POD_READY_TIMEOUT}s")
    raise TimeoutError(f"Watch stream ended for pod {name}")


async def create(cfg: SandboxConfig, env_vars: dict[str, str] | None = None) -> K8sSandbox:
    """Create a sandbox pod and wait for it to become ready."""
    _require_sdk()
    _load_k8s_config()

    pod_name = f"sandbox-{int(time.time() * 1000) % 10_000_000:07d}"
    api = client.CoreV1Api()

    manifest = _build_pod_manifest(pod_name, cfg, env_vars)
    api.create_namespaced_pod(namespace=NAMESPACE, body=manifest)

    pod_ip = _wait_for_ready(api, pod_name, NAMESPACE)
    return K8sSandbox(pod_name=pod_name, pod_ip=pod_ip, namespace=NAMESPACE)


def _url(sandbox: K8sSandbox, path: str) -> str:
    return f"http://{sandbox.pod_ip}:8080{path}"


def _safe_json(resp: httpx.Response) -> dict:
    """Parse JSON response, returning error dict on failure."""
    try:
        return resp.json()
    except Exception:
        return {"error": f"[sandbox HTTP {resp.status_code}] {resp.text[:500]}"}


def run_code(sandbox: K8sSandbox, code: str) -> str:
    resp = httpx.post(_url(sandbox, "/code"), json={"code": code}, timeout=120)
    data = _safe_json(resp)
    parts = []
    if data.get("output"):
        parts.append(data["output"])
    if data.get("error"):
        parts.append(f"[error] {data['error']}")
    return "\n".join(parts) or "(no output)"


def run_command(sandbox: K8sSandbox, cmd: str) -> str:
    resp = httpx.post(_url(sandbox, "/execute"), json={"command": cmd}, timeout=120)
    data = _safe_json(resp)
    parts = []
    if data.get("stdout"):
        parts.append(data["stdout"])
    if data.get("stderr"):
        parts.append(f"[stderr] {data['stderr']}")
    if data.get("exit_code", 0) != 0:
        parts.append(f"[exit_code] {data['exit_code']}")
    return "\n".join(parts) or "(no output)"


def write_file(sandbox: K8sSandbox, path: str, content: str) -> str:
    resp = httpx.post(_url(sandbox, "/files"), json={"path": path, "content": content}, timeout=30)
    data = _safe_json(resp)
    return data.get("message", data.get("error", "written"))


def read_file(sandbox: K8sSandbox, path: str) -> str:
    resp = httpx.get(_url(sandbox, "/files"), params={"path": path}, timeout=30)
    data = _safe_json(resp)
    return data.get("content", data.get("error", ""))


def close(sandbox: K8sSandbox) -> None:
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
