"""Metabase MCP Server — query, chart, and dashboard operations for Metabase.

Provides tools for: listing databases/tables, running queries, creating
dashboards, adding chart cards, and generating public share links.

Auth: Set METABASE_API_KEY env var. Set METABASE_URL for instance URL.
"""
import os
import json
import logging

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="metabase-mcp")
logger = logging.getLogger("uvicorn")

METABASE_URL = os.environ.get("METABASE_URL", "").rstrip("/")
API_KEY = os.environ.get("METABASE_API_KEY", "")


def _headers() -> dict[str, str]:
    return {"x-api-key": API_KEY, "Content-Type": "application/json"}


def _get(path: str, params: dict | None = None) -> dict:
    resp = httpx.get(f"{METABASE_URL}/api{path}", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, body: dict | None = None) -> dict:
    resp = httpx.post(f"{METABASE_URL}/api{path}", headers=_headers(), json=body or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _put(path: str, body: dict | None = None) -> dict:
    resp = httpx.put(f"{METABASE_URL}/api{path}", headers=_headers(), json=body or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


# --- Models ---

class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class HealthResponse(BaseModel):
    status: str


# --- Tool definitions ---

TOOLS = [
    {
        "name": "metabase_list_databases",
        "description": "List all databases configured in Metabase.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "metabase_list_tables",
        "description": "List tables in a Metabase database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "integer", "description": "Metabase database ID"},
            },
            "required": ["database_id"],
        },
    },
    {
        "name": "metabase_execute_query",
        "description": "Execute a native SQL query against a Metabase database. Returns rows as JSON.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "integer", "description": "Metabase database ID"},
                "query": {"type": "string", "description": "Native SQL query"},
                "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
            },
            "required": ["database_id", "query"],
        },
    },
    {
        "name": "metabase_list_dashboards",
        "description": "List dashboards, optionally filtered by collection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "collection_id": {"type": "integer", "description": "Filter by collection ID (optional)"},
            },
        },
    },
    {
        "name": "metabase_get_dashboard",
        "description": "Get full details of a dashboard including its cards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
            },
            "required": ["dashboard_id"],
        },
    },
    {
        "name": "metabase_create_dashboard",
        "description": "Create a new empty dashboard.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Dashboard name"},
                "description": {"type": "string", "description": "Dashboard description"},
                "collection_id": {"type": "integer", "description": "Collection to place dashboard in (optional)"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "metabase_create_card",
        "description": "Create a saved question (card) with a native SQL query. Returns card_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Card/question name"},
                "database_id": {"type": "integer", "description": "Database to query"},
                "query": {"type": "string", "description": "Native SQL query"},
                "display": {"type": "string", "description": "Visualization type: table, bar, line, pie, area, scalar, row, funnel, map", "default": "table"},
                "collection_id": {"type": "integer", "description": "Collection to save card in (optional)"},
                "description": {"type": "string", "description": "Card description (optional)"},
            },
            "required": ["name", "database_id", "query"],
        },
    },
    {
        "name": "metabase_add_card_to_dashboard",
        "description": "Add an existing card to a dashboard at a given position.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
                "card_id": {"type": "integer", "description": "Card ID to add"},
                "row": {"type": "integer", "description": "Row position (0-based)", "default": 0},
                "col": {"type": "integer", "description": "Column position (0-based, max 17)", "default": 0},
                "size_x": {"type": "integer", "description": "Card width (1-18)", "default": 9},
                "size_y": {"type": "integer", "description": "Card height", "default": 6},
            },
            "required": ["dashboard_id", "card_id"],
        },
    },
    {
        "name": "metabase_create_collection",
        "description": "Create a collection to organize dashboards and cards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Collection name"},
                "parent_id": {"type": "integer", "description": "Parent collection ID (optional, root if omitted)"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "metabase_get_public_link",
        "description": "Get or create a public sharing link for a dashboard. Returns embeddable URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
            },
            "required": ["dashboard_id"],
        },
    },
]


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
def health():
    if not METABASE_URL or not API_KEY:
        return HealthResponse(status="missing_config")
    try:
        _get("/user/current")
        return HealthResponse(status="ready")
    except Exception:
        return HealthResponse(status="degraded")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    handlers = {
        "metabase_list_databases": _list_databases,
        "metabase_list_tables": _list_tables,
        "metabase_execute_query": _execute_query,
        "metabase_list_dashboards": _list_dashboards,
        "metabase_get_dashboard": _get_dashboard,
        "metabase_create_dashboard": _create_dashboard,
        "metabase_create_card": _create_card,
        "metabase_add_card_to_dashboard": _add_card_to_dashboard,
        "metabase_create_collection": _create_collection,
        "metabase_get_public_link": _get_public_link,
    }
    handler = handlers.get(req.name)
    if not handler:
        return {"content": f"Unknown tool: {req.name}", "is_error": True}
    try:
        result = handler(req.arguments)
        return {"content": result}
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500]
        logger.error("Metabase API %s %d: %s", req.name, e.response.status_code, body)
        return {"content": f"Metabase API error {e.response.status_code}: {body}", "is_error": True}
    except Exception as e:
        logger.error("Tool %s failed: %s", req.name, e)
        return {"content": str(e), "is_error": True}


# --- Handlers ---

def _list_databases(args: dict) -> str:
    data = _get("/database")
    dbs = [{"id": d["id"], "name": d["name"], "engine": d.get("engine", "")} for d in data.get("data", data) if isinstance(d, dict)]
    return json.dumps(dbs, indent=2)


def _list_tables(args: dict) -> str:
    db_id = args["database_id"]
    data = _get(f"/database/{db_id}/metadata", params={"include_hidden": "false"})
    tables = [{"id": t["id"], "name": t["name"], "schema": t.get("schema", "")} for t in data.get("tables", [])]
    return json.dumps(tables, indent=2)


def _execute_query(args: dict) -> str:
    limit = min(args.get("limit", 100), 2000)
    body = {
        "database": args["database_id"],
        "type": "native",
        "native": {"query": args["query"]},
    }
    data = _post("/dataset", body)
    cols = [c["name"] for c in data.get("data", {}).get("cols", [])]
    rows = data.get("data", {}).get("rows", [])[:limit]
    return json.dumps({"columns": cols, "rows": rows, "row_count": len(rows)}, indent=2)


def _list_dashboards(args: dict) -> str:
    collection_id = args.get("collection_id")
    if collection_id:
        items = _get(f"/collection/{collection_id}/items", params={"models": "dashboard"})
        dashes = [{"id": d["id"], "name": d["name"]} for d in items.get("data", items) if isinstance(d, dict)]
    else:
        all_dashes = _get("/dashboard")
        dashes = [{"id": d["id"], "name": d["name"], "collection_id": d.get("collection_id")} for d in all_dashes]
    return json.dumps(dashes, indent=2)


def _get_dashboard(args: dict) -> str:
    data = _get(f"/dashboard/{args['dashboard_id']}")
    cards = []
    for dc in data.get("dashcards", []):
        card = dc.get("card", {})
        cards.append({
            "dashcard_id": dc["id"],
            "card_id": card.get("id"),
            "card_name": card.get("name", ""),
            "display": card.get("display", ""),
            "row": dc.get("row", 0),
            "col": dc.get("col", 0),
            "size_x": dc.get("size_x"),
            "size_y": dc.get("size_y"),
        })
    result = {
        "id": data["id"],
        "name": data["name"],
        "description": data.get("description", ""),
        "public_uuid": data.get("public_uuid"),
        "cards": cards,
    }
    if data.get("public_uuid"):
        result["public_url"] = f"{METABASE_URL}/public/dashboard/{data['public_uuid']}"
    return json.dumps(result, indent=2)


def _create_dashboard(args: dict) -> str:
    body = {"name": args["name"]}
    if args.get("description"):
        body["description"] = args["description"]
    if args.get("collection_id"):
        body["collection_id"] = args["collection_id"]
    data = _post("/dashboard", body)
    return json.dumps({"id": data["id"], "name": data["name"]})


def _create_card(args: dict) -> str:
    body = {
        "name": args["name"],
        "dataset_query": {
            "database": args["database_id"],
            "type": "native",
            "native": {"query": args["query"]},
        },
        "display": args.get("display", "table"),
        "visualization_settings": {},
    }
    if args.get("collection_id"):
        body["collection_id"] = args["collection_id"]
    if args.get("description"):
        body["description"] = args["description"]
    data = _post("/card", body)
    return json.dumps({"id": data["id"], "name": data["name"], "display": data.get("display", "")})


def _add_card_to_dashboard(args: dict) -> str:
    dashboard_id = args["dashboard_id"]
    body = {
        "cardId": args["card_id"],
        "row": args.get("row", 0),
        "col": args.get("col", 0),
        "size_x": args.get("size_x", 9),
        "size_y": args.get("size_y", 6),
    }
    data = _post(f"/dashboard/{dashboard_id}/cards", body)
    return json.dumps({"ok": True, "dashcard_id": data.get("id"), "dashboard_id": dashboard_id})


def _create_collection(args: dict) -> str:
    body = {"name": args["name"]}
    if args.get("parent_id"):
        body["parent_id"] = args["parent_id"]
    data = _post("/collection", body)
    return json.dumps({"id": data["id"], "name": data["name"]})


def _get_public_link(args: dict) -> str:
    dashboard_id = args["dashboard_id"]
    # Check if already has public UUID
    dash = _get(f"/dashboard/{dashboard_id}")
    public_uuid = dash.get("public_uuid")
    if not public_uuid:
        # Enable public sharing
        result = _post(f"/dashboard/{dashboard_id}/public_link")
        public_uuid = result.get("uuid")
    url = f"{METABASE_URL}/public/dashboard/{public_uuid}" if public_uuid else ""
    return json.dumps({"dashboard_id": dashboard_id, "public_uuid": public_uuid, "public_url": url})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8097)
