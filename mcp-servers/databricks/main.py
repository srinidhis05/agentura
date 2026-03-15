"""Databricks MCP Server — exposes Databricks SQL operations as MCP tools.

FastAPI server providing /health, /tools, /tools/call endpoints.
Proxies SQL queries to the Databricks SQL Statement API.
"""

from __future__ import annotations

import os
import time

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="databricks-mcp")

WORKSPACE_URL = os.environ.get("DATABRICKS_WORKSPACE_URL", "").rstrip("/")
DEFAULT_CATALOG = os.environ.get("DATABRICKS_CATALOG", "prod")
DEFAULT_SCHEMA = os.environ.get("DATABRICKS_SCHEMA", "silver_schema")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
STATEMENT_TIMEOUT = int(os.environ.get("DATABRICKS_STATEMENT_TIMEOUT", "120"))


def _headers() -> dict:
    token = os.environ.get("DATABRICKS_TOKEN", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --- Models ---

class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class ToolCallResponse(BaseModel):
    content: str
    is_error: bool = False


class HealthResponse(BaseModel):
    status: str


# --- Tool definitions ---

TOOLS = [
    {
        "name": "execute_sql_tool",
        "description": "Execute a SQL query against the Databricks SQL warehouse. Returns results as formatted text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to execute (SELECT only).",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "list_databases",
        "description": "List available catalogs (databases) in the Databricks workspace.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_schemas",
        "description": "List schemas in a given catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog": {
                    "type": "string",
                    "description": "Catalog name (default: prod).",
                },
            },
        },
    },
    {
        "name": "list_tables",
        "description": "List tables in a given catalog and schema.",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog": {
                    "type": "string",
                    "description": "Catalog name (default: prod).",
                },
                "schema_name": {
                    "type": "string",
                    "description": "Schema name (default: silver_schema).",
                },
            },
        },
    },
    {
        "name": "list_columns",
        "description": "List columns of a specific table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog": {
                    "type": "string",
                    "description": "Catalog name (default: prod).",
                },
                "schema_name": {
                    "type": "string",
                    "description": "Schema name (default: silver_schema).",
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name.",
                },
            },
            "required": ["table_name"],
        },
    },
]


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
def health():
    ok = bool(WORKSPACE_URL and os.environ.get("DATABRICKS_TOKEN") and WAREHOUSE_ID)
    return HealthResponse(status="ready" if ok else "missing_config")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call", response_model=ToolCallResponse)
def call_tool(req: ToolCallRequest):
    handlers = {
        "execute_sql_tool": _execute_sql,
        "list_databases": _list_databases,
        "list_schemas": _list_schemas,
        "list_tables": _list_tables,
        "list_columns": _list_columns,
    }
    handler = handlers.get(req.name)
    if not handler:
        return ToolCallResponse(content=f"Unknown tool: {req.name}", is_error=True)
    try:
        output = handler(req.arguments)
        return ToolCallResponse(content=output)
    except Exception as e:
        return ToolCallResponse(content=str(e), is_error=True)


# --- SQL Statement API ---

def _submit_statement(sql: str) -> dict:
    """Submit a SQL statement and poll until completion."""
    url = f"{WORKSPACE_URL}/api/2.0/sql/statements/"
    body = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": sql,
        "wait_timeout": "0s",
        "catalog": DEFAULT_CATALOG,
        "schema": DEFAULT_SCHEMA,
    }
    resp = httpx.post(url, headers=_headers(), json=body, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Databricks API error {resp.status_code}: {resp.text}")
    return resp.json()


def _poll_statement(statement_id: str) -> dict:
    """Poll a statement until it reaches a terminal state."""
    url = f"{WORKSPACE_URL}/api/2.0/sql/statements/{statement_id}"
    deadline = time.time() + STATEMENT_TIMEOUT
    while time.time() < deadline:
        resp = httpx.get(url, headers=_headers(), timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Poll error {resp.status_code}: {resp.text}")
        data = resp.json()
        state = data.get("status", {}).get("state", "")
        if state in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
            return data
        time.sleep(1)
    raise RuntimeError(f"Statement {statement_id} timed out after {STATEMENT_TIMEOUT}s")


def _format_results(data: dict) -> str:
    """Format statement results into a readable table."""
    status = data.get("status", {})
    state = status.get("state", "UNKNOWN")

    if state == "FAILED":
        error = status.get("error", {})
        return f"SQL Error: {error.get('message', 'Unknown error')}"

    if state != "SUCCEEDED":
        return f"Statement ended with state: {state}"

    manifest = data.get("manifest", {})
    columns = manifest.get("schema", {}).get("columns", [])
    result = data.get("result", {})
    rows = result.get("data_array", [])

    if not rows:
        return "Query returned no results."

    col_names = [c["name"] for c in columns]
    col_widths = [len(n) for n in col_names]
    for row in rows[:200]:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val or "")))

    header = " | ".join(n.ljust(w) for n, w in zip(col_names, col_widths))
    separator = "-+-".join("-" * w for w in col_widths)
    lines = [header, separator]
    for row in rows[:200]:
        line = " | ".join(str(v or "").ljust(w) for v, w in zip(row, col_widths))
        lines.append(line)

    total = result.get("row_count", len(rows))
    if total > 200:
        lines.append(f"\n... showing 200 of {total} rows")

    return "\n".join(lines)


# --- Tool implementations ---

def _execute_sql(args: dict) -> str:
    sql = args.get("sql", "").strip()
    if not sql:
        return "Error: No SQL provided."

    blocked = sql.strip().split()[0].upper()
    if blocked in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"):
        return f"Error: {blocked} statements are not allowed. Read-only access only."

    data = _submit_statement(sql)
    state = data.get("status", {}).get("state", "")
    if state in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
        return _format_results(data)

    statement_id = data.get("statement_id")
    if not statement_id:
        return f"Error: No statement_id returned. Response: {data}"

    data = _poll_statement(statement_id)
    return _format_results(data)


def _list_databases(args: dict) -> str:
    return _execute_sql({"sql": "SHOW CATALOGS"})


def _list_schemas(args: dict) -> str:
    catalog = args.get("catalog", DEFAULT_CATALOG)
    return _execute_sql({"sql": f"SHOW SCHEMAS IN {catalog}"})


def _list_tables(args: dict) -> str:
    catalog = args.get("catalog", DEFAULT_CATALOG)
    schema = args.get("schema_name", DEFAULT_SCHEMA)
    return _execute_sql({"sql": f"SHOW TABLES IN {catalog}.{schema}"})


def _list_columns(args: dict) -> str:
    catalog = args.get("catalog", DEFAULT_CATALOG)
    schema = args.get("schema_name", DEFAULT_SCHEMA)
    table = args["table_name"]
    return _execute_sql({"sql": f"DESCRIBE TABLE {catalog}.{schema}.{table}"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8092)
