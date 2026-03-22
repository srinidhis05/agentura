"""Notion MCP Server — read + write operations for Notion.

Provides tools for: search, database queries, page CRUD, block content,
and child page listing. Auth via NOTION_API_KEY (internal integration token).
"""
import os
import json
import logging

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="notion-mcp")
logger = logging.getLogger("uvicorn")

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class HealthResponse(BaseModel):
    status: str


TOOLS = [
    {
        "name": "notion_search",
        "description": "Search Notion pages and databases by title or content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "filter": {
                    "type": "object",
                    "description": "Filter by object type: {\"value\": \"page\"} or {\"value\": \"database\"}",
                },
                "page_size": {"type": "integer", "description": "Results per page (max 100)", "default": 20},
                "start_cursor": {"type": "string", "description": "Pagination cursor"},
            },
        },
    },
    {
        "name": "notion_query_database",
        "description": "Query a Notion database with filters and sorts. Returns matching pages/rows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "string", "description": "Database ID (UUID, no dashes ok)"},
                "filter": {"type": "object", "description": "Notion filter object (see Notion API docs)"},
                "sorts": {
                    "type": "array",
                    "description": "Sort criteria array",
                    "items": {"type": "object"},
                },
                "page_size": {"type": "integer", "description": "Results per page (max 100)", "default": 50},
                "start_cursor": {"type": "string", "description": "Pagination cursor"},
            },
            "required": ["database_id"],
        },
    },
    {
        "name": "notion_get_page",
        "description": "Get a Notion page's properties by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Page ID (UUID)"},
            },
            "required": ["page_id"],
        },
    },
    {
        "name": "notion_get_page_content",
        "description": "Get the block content (body) of a Notion page. Returns child blocks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "block_id": {"type": "string", "description": "Page or block ID to get children of"},
                "page_size": {"type": "integer", "description": "Blocks per page (max 100)", "default": 100},
                "start_cursor": {"type": "string", "description": "Pagination cursor"},
            },
            "required": ["block_id"],
        },
    },
    {
        "name": "notion_create_page",
        "description": "Create a new page in a database (row) or under a parent page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent": {
                    "type": "object",
                    "description": "Parent: {\"database_id\": \"...\"} or {\"page_id\": \"...\"}",
                },
                "properties": {
                    "type": "object",
                    "description": "Page properties (Notion property value objects)",
                },
                "children": {
                    "type": "array",
                    "description": "Optional page content blocks",
                    "items": {"type": "object"},
                },
            },
            "required": ["parent", "properties"],
        },
    },
    {
        "name": "notion_update_page",
        "description": "Update a page's properties (e.g. status, assignee, dates).",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Page ID to update"},
                "properties": {
                    "type": "object",
                    "description": "Properties to update (Notion property value objects)",
                },
            },
            "required": ["page_id", "properties"],
        },
    },
    {
        "name": "notion_get_database",
        "description": "Get a database's schema (properties/columns definition).",
        "input_schema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "string", "description": "Database ID (UUID)"},
            },
            "required": ["database_id"],
        },
    },
    {
        "name": "notion_list_users",
        "description": "List all users in the Notion workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_size": {"type": "integer", "default": 100},
                "start_cursor": {"type": "string"},
            },
        },
    },
    {
        "name": "notion_append_children",
        "description": "Append child blocks to a page or block. Use this to add content to an existing page in batches (max 100 blocks per call).",
        "input_schema": {
            "type": "object",
            "properties": {
                "block_id": {"type": "string", "description": "Page or block ID to append children to"},
                "children": {
                    "type": "array",
                    "description": "Array of block objects to append",
                    "items": {"type": "object"},
                },
            },
            "required": ["block_id", "children"],
        },
    },
]


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ready" if NOTION_API_KEY else "missing_token")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    handlers = {
        "notion_search": _search,
        "notion_query_database": _query_database,
        "notion_get_page": _get_page,
        "notion_get_page_content": _get_page_content,
        "notion_create_page": _create_page,
        "notion_update_page": _update_page,
        "notion_get_database": _get_database,
        "notion_list_users": _list_users,
        "notion_append_children": _append_children,
    }
    handler = handlers.get(req.name)
    if not handler:
        return {"content": f"Unknown tool: {req.name}", "is_error": True}
    try:
        result = handler(req.arguments)
        return {"content": result}
    except Exception as e:
        logger.error(f"Tool {req.name} failed: {e}")
        return {"content": str(e), "is_error": True}


def _search(args: dict) -> str:
    body = {}
    if args.get("query"):
        body["query"] = args["query"]
    if args.get("filter"):
        body["filter"] = args["filter"]
    body["page_size"] = min(args.get("page_size", 20), 100)
    if args.get("start_cursor"):
        body["start_cursor"] = args["start_cursor"]
    resp = httpx.post(f"{BASE_URL}/search", headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return json.dumps({
        "results": _slim_pages(data.get("results", [])),
        "has_more": data.get("has_more", False),
        "next_cursor": data.get("next_cursor"),
    }, indent=2)


def _query_database(args: dict) -> str:
    db_id = args["database_id"]
    body = {"page_size": min(args.get("page_size", 50), 100)}
    if args.get("filter"):
        body["filter"] = args["filter"]
    if args.get("sorts"):
        body["sorts"] = args["sorts"]
    if args.get("start_cursor"):
        body["start_cursor"] = args["start_cursor"]
    resp = httpx.post(
        f"{BASE_URL}/databases/{db_id}/query",
        headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return json.dumps({
        "results": _slim_pages(data.get("results", [])),
        "has_more": data.get("has_more", False),
        "next_cursor": data.get("next_cursor"),
    }, indent=2)


def _get_page(args: dict) -> str:
    page_id = args["page_id"]
    resp = httpx.get(f"{BASE_URL}/pages/{page_id}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return json.dumps(_slim_page(resp.json()), indent=2)


def _get_page_content(args: dict) -> str:
    block_id = args["block_id"]
    params = {"page_size": min(args.get("page_size", 100), 100)}
    if args.get("start_cursor"):
        params["start_cursor"] = args["start_cursor"]
    resp = httpx.get(
        f"{BASE_URL}/blocks/{block_id}/children",
        headers=_headers(), params=params, timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return json.dumps({
        "results": data.get("results", []),
        "has_more": data.get("has_more", False),
        "next_cursor": data.get("next_cursor"),
    }, indent=2)


def _create_page(args: dict) -> str:
    body = {"parent": args["parent"], "properties": args["properties"]}
    if args.get("children"):
        body["children"] = args["children"]
    resp = httpx.post(f"{BASE_URL}/pages", headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()
    page = resp.json()
    return json.dumps({"id": page["id"], "url": page.get("url", ""), "created": True}, indent=2)


def _update_page(args: dict) -> str:
    page_id = args["page_id"]
    body = {"properties": args["properties"]}
    resp = httpx.patch(
        f"{BASE_URL}/pages/{page_id}",
        headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()
    page = resp.json()
    return json.dumps({"id": page["id"], "url": page.get("url", ""), "updated": True}, indent=2)


def _get_database(args: dict) -> str:
    db_id = args["database_id"]
    resp = httpx.get(f"{BASE_URL}/databases/{db_id}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    props = {}
    for name, prop in data.get("properties", {}).items():
        props[name] = {"type": prop["type"], "id": prop.get("id", "")}
        if prop["type"] == "select":
            props[name]["options"] = [o["name"] for o in prop.get("select", {}).get("options", [])]
        elif prop["type"] == "multi_select":
            props[name]["options"] = [o["name"] for o in prop.get("multi_select", {}).get("options", [])]
        elif prop["type"] == "status":
            props[name]["options"] = [o["name"] for o in prop.get("status", {}).get("options", [])]
    return json.dumps({
        "id": data["id"],
        "title": _extract_title(data.get("title", [])),
        "properties": props,
    }, indent=2)


def _append_children(args: dict) -> str:
    block_id = args["block_id"]
    body = {"children": args["children"]}
    resp = httpx.patch(
        f"{BASE_URL}/blocks/{block_id}/children",
        headers=_headers(), json=body, timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return json.dumps({
        "block_id": block_id,
        "appended": len(args["children"]),
        "has_more": data.get("has_more", False),
    }, indent=2)


def _list_users(args: dict) -> str:
    params = {"page_size": min(args.get("page_size", 100), 100)}
    if args.get("start_cursor"):
        params["start_cursor"] = args["start_cursor"]
    resp = httpx.get(f"{BASE_URL}/users", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    users = [
        {"id": u["id"], "name": u.get("name", ""), "type": u.get("type", ""), "email": u.get("person", {}).get("email", "")}
        for u in data.get("results", [])
    ]
    return json.dumps({"users": users, "has_more": data.get("has_more", False)}, indent=2)


def _slim_pages(pages: list) -> list:
    return [_slim_page(p) for p in pages]


def _slim_page(page: dict) -> dict:
    """Extract key fields from a Notion page, keeping it readable for the LLM."""
    props = {}
    for name, prop in page.get("properties", {}).items():
        props[name] = _extract_property_value(prop)
    return {
        "id": page.get("id", ""),
        "url": page.get("url", ""),
        "created_time": page.get("created_time", ""),
        "last_edited_time": page.get("last_edited_time", ""),
        "properties": props,
    }


def _extract_property_value(prop: dict):
    """Flatten a Notion property to its plain value."""
    t = prop.get("type", "")
    if t == "title":
        return _extract_rich_text(prop.get("title", []))
    if t == "rich_text":
        return _extract_rich_text(prop.get("rich_text", []))
    if t == "number":
        return prop.get("number")
    if t == "select":
        sel = prop.get("select")
        return sel["name"] if sel else None
    if t == "multi_select":
        return [s["name"] for s in prop.get("multi_select", [])]
    if t == "status":
        st = prop.get("status")
        return st["name"] if st else None
    if t == "date":
        d = prop.get("date")
        if d:
            return {"start": d.get("start"), "end": d.get("end")}
        return None
    if t == "people":
        return [{"id": p["id"], "name": p.get("name", "")} for p in prop.get("people", [])]
    if t == "checkbox":
        return prop.get("checkbox")
    if t == "url":
        return prop.get("url")
    if t == "email":
        return prop.get("email")
    if t == "relation":
        return [r["id"] for r in prop.get("relation", [])]
    if t == "formula":
        f = prop.get("formula", {})
        return f.get(f.get("type", ""), None)
    if t == "rollup":
        r = prop.get("rollup", {})
        return r.get(r.get("type", ""), None)
    if t == "created_time":
        return prop.get("created_time")
    if t == "last_edited_time":
        return prop.get("last_edited_time")
    if t == "created_by":
        cb = prop.get("created_by", {})
        return {"id": cb.get("id", ""), "name": cb.get("name", "")}
    if t == "last_edited_by":
        eb = prop.get("last_edited_by", {})
        return {"id": eb.get("id", ""), "name": eb.get("name", "")}
    if t == "unique_id":
        uid = prop.get("unique_id", {})
        prefix = uid.get("prefix", "")
        number = uid.get("number", "")
        return f"{prefix}-{number}" if prefix else str(number)
    return prop.get(t)


def _extract_rich_text(rich_text: list) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text)


def _extract_title(title_array: list) -> str:
    return "".join(t.get("plain_text", "") for t in title_array)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)
