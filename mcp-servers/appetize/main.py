"""Appetize MCP Server — exposes Appetize.io operations as MCP tools.

FastAPI server providing /health, /tools, /tools/call endpoints.
Proxies requests to the Appetize.io REST API.
"""

from __future__ import annotations

import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="appetize-mcp")

APPETIZE_API = "https://api.appetize.io/v1"


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class ToolCallResponse(BaseModel):
    content: str
    is_error: bool = False


class HealthResponse(BaseModel):
    status: str


TOOLS = [
    {
        "name": "appetize_upload",
        "description": "Upload an APK/IPA to Appetize.io via URL. Returns publicKey and embed URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Publicly accessible URL to the APK or IPA file",
                },
                "platform": {
                    "type": "string",
                    "description": "Platform: 'android' or 'ios'",
                    "enum": ["android", "ios"],
                },
                "public_key": {
                    "type": "string",
                    "description": "Existing app publicKey to update (optional, omit to create new)",
                },
            },
            "required": ["url", "platform"],
        },
    },
    {
        "name": "appetize_delete",
        "description": "Delete an app from Appetize.io by publicKey.",
        "input_schema": {
            "type": "object",
            "properties": {
                "public_key": {
                    "type": "string",
                    "description": "The publicKey of the app to delete",
                },
            },
            "required": ["public_key"],
        },
    },
]


@app.get("/health", response_model=HealthResponse)
def health():
    api_key = os.environ.get("APPETIZE_API_KEY", "")
    return HealthResponse(status="ready" if api_key else "no_api_key")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call", response_model=ToolCallResponse)
def call_tool(req: ToolCallRequest):
    handlers = {
        "appetize_upload": _appetize_upload,
        "appetize_delete": _appetize_delete,
    }
    handler = handlers.get(req.name)
    if not handler:
        return ToolCallResponse(content=f"Unknown tool: {req.name}", is_error=True)
    try:
        output = handler(req.arguments)
        return ToolCallResponse(content=output)
    except Exception as e:
        return ToolCallResponse(content=str(e), is_error=True)


def _get_api_key() -> str:
    key = os.environ.get("APPETIZE_API_KEY", "")
    if not key:
        raise RuntimeError("APPETIZE_API_KEY environment variable is not set")
    return key


def _appetize_upload(args: dict) -> str:
    api_key = _get_api_key()
    url = args["url"]
    platform = args["platform"]
    public_key = args.get("public_key")

    endpoint = f"{APPETIZE_API}/apps"
    if public_key:
        endpoint = f"{APPETIZE_API}/apps/{public_key}"

    resp = httpx.post(
        endpoint,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"url": url, "platform": platform},
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Appetize API error {resp.status_code}: {resp.text}")

    data = resp.json()
    pk = data.get("publicKey", "")
    embed = f"https://appetize.io/embed/{pk}?device=pixel7&osVersion=14.0&scale=auto&autoplay=true&grantPermissions=true"
    direct = f"https://appetize.io/app/{pk}"

    return (
        f"publicKey: {pk}\n"
        f"embed_url: {embed}\n"
        f"direct_url: {direct}\n"
        f"platform: {data.get('platform', platform)}"
    )


def _appetize_delete(args: dict) -> str:
    api_key = _get_api_key()
    public_key = args["public_key"]

    resp = httpx.delete(
        f"{APPETIZE_API}/apps/{public_key}",
        headers={"X-API-KEY": api_key},
        timeout=30,
    )

    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Appetize API error {resp.status_code}: {resp.text}")

    return f"Deleted app {public_key}"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8091)
