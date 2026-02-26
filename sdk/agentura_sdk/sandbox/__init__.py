"""Sandbox backend factory.

Selects sandbox implementation via SANDBOX_BACKEND env var:
  docker (default) | k8s
"""

from __future__ import annotations

import os
from types import ModuleType


def get_sandbox_module() -> ModuleType:
    """Return the sandbox module matching SANDBOX_BACKEND env var."""
    backend = os.environ.get("SANDBOX_BACKEND", "docker")
    if backend == "k8s":
        from agentura_sdk.sandbox import k8s_sandbox
        return k8s_sandbox
    from agentura_sdk.sandbox import docker_sandbox
    return docker_sandbox
