"""Claude Code Worker pod lifecycle — create/close.

Same pattern as k8s_sandbox.py but uses the claude-code-worker image
with higher resource limits (2Gi RAM, 2 CPU) for agent workloads.
"""

from __future__ import annotations

import logging
import os
import time

from agentura_sdk.sandbox.k8s_sandbox import (
    K8sSandbox,
    NAMESPACE,
    IMAGE_PULL_POLICY,
    POD_READY_TIMEOUT,
    _load_k8s_config,
    _require_sdk,
    _wait_for_ready,
)
from agentura_sdk.types import SandboxConfig

try:
    from kubernetes import client
except ImportError:
    client = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

WORKER_IMAGE = os.environ.get(
    "CLAUDE_CODE_WORKER_IMAGE", "agentura/claude-code-worker:latest"
)
WORKER_CPU = os.environ.get("CLAUDE_CODE_WORKER_CPU", "2")
WORKER_MEMORY = os.environ.get("CLAUDE_CODE_WORKER_MEMORY", "2048Mi")


def _build_worker_manifest(
    name: str,
    env_vars: dict[str, str] | None = None,
) -> client.V1Pod:
    """Build K8s pod manifest for a Claude Code worker."""
    env = []
    if env_vars:
        env = [client.V1EnvVar(name=k, value=v) for k, v in env_vars.items()]

    container = client.V1Container(
        name="worker",
        image=WORKER_IMAGE,
        image_pull_policy=IMAGE_PULL_POLICY,
        ports=[client.V1ContainerPort(container_port=8080)],
        env=env or None,
        resources=client.V1ResourceRequirements(
            requests={"cpu": WORKER_CPU, "memory": WORKER_MEMORY},
            limits={"cpu": WORKER_CPU, "memory": WORKER_MEMORY},
        ),
        readiness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path="/health", port=8080),
            initial_delay_seconds=3,
            period_seconds=2,
        ),
    )

    spec = client.V1PodSpec(
        containers=[container],
        restart_policy="Never",
        automount_service_account_token=False,
    )

    return client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=NAMESPACE,
            labels={
                "app": "claude-code-worker",
                "managed-by": "agentura-executor",
            },
        ),
        spec=spec,
    )


async def create(
    cfg: SandboxConfig,
    env_vars: dict[str, str] | None = None,
) -> K8sSandbox:
    """Create a Claude Code worker pod and wait for ready."""
    _require_sdk()
    _load_k8s_config()

    pod_name = f"cc-worker-{int(time.time() * 1000) % 10_000_000:07d}"
    api = client.CoreV1Api()

    manifest = _build_worker_manifest(pod_name, env_vars)
    api.create_namespaced_pod(namespace=NAMESPACE, body=manifest)
    logger.info("Created worker pod %s", pod_name)

    pod_ip = _wait_for_ready(api, pod_name, NAMESPACE)
    logger.info("Worker pod %s ready at %s", pod_name, pod_ip)
    return K8sSandbox(pod_name=pod_name, pod_ip=pod_ip, namespace=NAMESPACE)


def close(sandbox: K8sSandbox) -> None:
    """Delete the worker pod."""
    try:
        _load_k8s_config()
        api = client.CoreV1Api()
        api.delete_namespaced_pod(
            name=sandbox.pod_name,
            namespace=sandbox.namespace,
            grace_period_seconds=0,
        )
        logger.info("Deleted worker pod %s", sandbox.pod_name)
    except Exception as exc:
        logger.warning("Failed to delete worker pod %s: %s", sandbox.pod_name, exc)
