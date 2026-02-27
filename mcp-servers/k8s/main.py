"""K8s MCP Server — exposes kubectl operations as MCP tools.

FastAPI server providing /health, /tools, /tools/call endpoints.
Runs inside the cluster with a scoped ServiceAccount.
"""

from __future__ import annotations

import subprocess
import tempfile

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="k8s-mcp")


# --- Request/Response models ---

class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class ToolCallResponse(BaseModel):
    content: str
    is_error: bool = False


class HealthResponse(BaseModel):
    status: str


# --- Tool definitions (Anthropic schema format) ---

TOOLS = [
    {
        "name": "kubectl_apply",
        "description": "Apply a Kubernetes manifest YAML to the cluster.",
        "input_schema": {
            "type": "object",
            "properties": {
                "manifest": {
                    "type": "string",
                    "description": "Complete YAML manifest to apply",
                },
                "namespace": {
                    "type": "string",
                    "description": "Target namespace (default: agentura)",
                },
            },
            "required": ["manifest"],
        },
    },
    {
        "name": "kubectl_get",
        "description": "Get Kubernetes resources. Returns kubectl output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "description": "Resource type (e.g. pods, deployments, services)",
                },
                "name": {
                    "type": "string",
                    "description": "Specific resource name (optional)",
                },
                "namespace": {
                    "type": "string",
                    "description": "Target namespace (default: agentura)",
                },
            },
            "required": ["resource"],
        },
    },
    {
        "name": "kubectl_delete",
        "description": "Delete Kubernetes resources by manifest or by resource type/name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "manifest": {
                    "type": "string",
                    "description": "YAML manifest to delete (optional)",
                },
                "resource": {
                    "type": "string",
                    "description": "Resource type (e.g. deployment)",
                },
                "name": {
                    "type": "string",
                    "description": "Resource name to delete",
                },
                "namespace": {
                    "type": "string",
                    "description": "Target namespace (default: agentura)",
                },
            },
        },
    },
]


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ready")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call", response_model=ToolCallResponse)
def call_tool(req: ToolCallRequest):
    handlers = {
        "kubectl_apply": _kubectl_apply,
        "kubectl_get": _kubectl_get,
        "kubectl_delete": _kubectl_delete,
    }
    handler = handlers.get(req.name)
    if not handler:
        return ToolCallResponse(content=f"Unknown tool: {req.name}", is_error=True)
    try:
        output = handler(req.arguments)
        return ToolCallResponse(content=output)
    except Exception as e:
        return ToolCallResponse(content=str(e), is_error=True)


# --- Tool implementations ---

def _run_kubectl(args: list[str], stdin: str | None = None) -> str:
    """Run kubectl with args, return combined stdout+stderr."""
    result = subprocess.run(
        ["kubectl", *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout
    if result.stderr:
        output += "\n" + result.stderr if output else result.stderr
    if result.returncode != 0:
        raise RuntimeError(output.strip() or f"kubectl exited {result.returncode}")
    return output.strip()


def _kubectl_apply(args: dict) -> str:
    manifest = args["manifest"]
    ns = args.get("namespace", "agentura")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(manifest)
        f.flush()
        return _run_kubectl(["apply", "-f", f.name, "-n", ns])


def _kubectl_get(args: dict) -> str:
    resource = args["resource"]
    ns = args.get("namespace", "agentura")
    cmd = ["get", resource, "-n", ns]
    name = args.get("name")
    if name:
        cmd.append(name)
    return _run_kubectl(cmd)


def _kubectl_delete(args: dict) -> str:
    ns = args.get("namespace", "agentura")
    manifest = args.get("manifest")
    if manifest:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(manifest)
            f.flush()
            return _run_kubectl(["delete", "-f", f.name, "-n", ns])
    resource = args.get("resource", "")
    name = args.get("name", "")
    if resource and name:
        return _run_kubectl(["delete", resource, name, "-n", ns])
    return "Must provide either manifest or resource+name"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
