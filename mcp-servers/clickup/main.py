"""ClickUp MCP Server — read + write operations for ClickUp.

Provides tools for: list/get/create/update tasks, spaces, and lists.
Auth via CLICKUP_API_KEY (personal or OAuth token).
"""
import os
import json
import logging

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="clickup-mcp")
logger = logging.getLogger("uvicorn")

CLICKUP_API_KEY = os.environ.get("CLICKUP_API_KEY", "")
BASE_URL = "https://api.clickup.com/api/v2"


def _headers():
    return {"Authorization": CLICKUP_API_KEY, "Content-Type": "application/json"}


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class HealthResponse(BaseModel):
    status: str


TOOLS = [
    {
        "name": "clickup_get_tasks",
        "description": "Get tasks from a ClickUp list with optional filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "ClickUp list ID"},
                "statuses": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Filter by status names (e.g. ['open', 'in progress'])",
                },
                "assignees": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Filter by assignee user IDs",
                },
                "due_date_gt": {"type": "integer", "description": "Tasks due after this Unix ms timestamp"},
                "due_date_lt": {"type": "integer", "description": "Tasks due before this Unix ms timestamp"},
                "include_closed": {"type": "boolean", "default": False},
                "page": {"type": "integer", "default": 0},
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "clickup_get_task",
        "description": "Get a single ClickUp task by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ClickUp task ID"},
                "include_subtasks": {"type": "boolean", "default": True},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "clickup_create_task",
        "description": "Create a new task in a ClickUp list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "ClickUp list ID"},
                "name": {"type": "string", "description": "Task name"},
                "description": {"type": "string", "description": "Task description (markdown)"},
                "status": {"type": "string", "description": "Status name"},
                "priority": {"type": "integer", "description": "1=Urgent, 2=High, 3=Normal, 4=Low"},
                "assignees": {"type": "array", "items": {"type": "integer"}, "description": "Assignee user IDs"},
                "due_date": {"type": "integer", "description": "Due date as Unix ms timestamp"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["list_id", "name"],
        },
    },
    {
        "name": "clickup_update_task",
        "description": "Update an existing ClickUp task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ClickUp task ID"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string"},
                "priority": {"type": "integer"},
                "assignees": {
                    "type": "object",
                    "description": "{\"add\": [user_ids], \"rem\": [user_ids]}",
                },
                "due_date": {"type": "integer"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "clickup_get_spaces",
        "description": "List spaces in a ClickUp workspace/team.",
        "input_schema": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "ClickUp team/workspace ID"},
            },
            "required": ["team_id"],
        },
    },
    {
        "name": "clickup_get_lists",
        "description": "Get lists in a ClickUp folder or space.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "ClickUp folder ID (use for folder lists)"},
                "space_id": {"type": "string", "description": "ClickUp space ID (use for folderless lists)"},
            },
        },
    },
    {
        "name": "clickup_get_members",
        "description": "List members of a ClickUp list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "ClickUp list ID"},
            },
            "required": ["list_id"],
        },
    },
]


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ready" if CLICKUP_API_KEY else "missing_token")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    handlers = {
        "clickup_get_tasks": _get_tasks,
        "clickup_get_task": _get_task,
        "clickup_create_task": _create_task,
        "clickup_update_task": _update_task,
        "clickup_get_spaces": _get_spaces,
        "clickup_get_lists": _get_lists,
        "clickup_get_members": _get_members,
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


def _get_tasks(args: dict) -> str:
    list_id = args["list_id"]
    params = {"page": args.get("page", 0)}
    if args.get("statuses"):
        for s in args["statuses"]:
            params.setdefault("statuses[]", [])
            params["statuses[]"].append(s)
    if args.get("assignees"):
        for a in args["assignees"]:
            params.setdefault("assignees[]", [])
            params["assignees[]"].append(a)
    if args.get("due_date_gt"):
        params["due_date_gt"] = args["due_date_gt"]
    if args.get("due_date_lt"):
        params["due_date_lt"] = args["due_date_lt"]
    if args.get("include_closed"):
        params["include_closed"] = "true"
    resp = httpx.get(f"{BASE_URL}/list/{list_id}/task", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    tasks = resp.json().get("tasks", [])
    return json.dumps({"tasks": [_slim_task(t) for t in tasks], "count": len(tasks)}, indent=2)


def _get_task(args: dict) -> str:
    task_id = args["task_id"]
    params = {"include_subtasks": "true"} if args.get("include_subtasks", True) else {}
    resp = httpx.get(f"{BASE_URL}/task/{task_id}", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return json.dumps(_slim_task(resp.json()), indent=2)


def _create_task(args: dict) -> str:
    list_id = args.pop("list_id")
    body = {k: v for k, v in args.items() if v is not None}
    resp = httpx.post(f"{BASE_URL}/list/{list_id}/task", headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()
    task = resp.json()
    return json.dumps({"id": task["id"], "name": task["name"], "url": task.get("url", ""), "created": True}, indent=2)


def _update_task(args: dict) -> str:
    task_id = args.pop("task_id")
    body = {k: v for k, v in args.items() if v is not None}
    resp = httpx.put(f"{BASE_URL}/task/{task_id}", headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()
    task = resp.json()
    return json.dumps({"id": task["id"], "name": task.get("name", ""), "updated": True}, indent=2)


def _get_spaces(args: dict) -> str:
    team_id = args["team_id"]
    resp = httpx.get(f"{BASE_URL}/team/{team_id}/space", headers=_headers(), timeout=30)
    resp.raise_for_status()
    spaces = resp.json().get("spaces", [])
    return json.dumps([{"id": s["id"], "name": s["name"]} for s in spaces], indent=2)


def _get_lists(args: dict) -> str:
    if args.get("folder_id"):
        url = f"{BASE_URL}/folder/{args['folder_id']}/list"
    elif args.get("space_id"):
        url = f"{BASE_URL}/space/{args['space_id']}/list"
    else:
        return json.dumps({"error": "Provide either folder_id or space_id"})
    resp = httpx.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    lists = resp.json().get("lists", [])
    return json.dumps([{"id": l["id"], "name": l["name"], "task_count": l.get("task_count", 0)} for l in lists], indent=2)


def _get_members(args: dict) -> str:
    list_id = args["list_id"]
    resp = httpx.get(f"{BASE_URL}/list/{list_id}/member", headers=_headers(), timeout=30)
    resp.raise_for_status()
    members = resp.json().get("members", [])
    return json.dumps([{"id": m["id"], "username": m.get("username", ""), "email": m.get("email", "")} for m in members], indent=2)


def _slim_task(task: dict) -> dict:
    """Extract key fields from a ClickUp task."""
    return {
        "id": task.get("id", ""),
        "name": task.get("name", ""),
        "description": (task.get("description", "") or "")[:500],
        "status": task.get("status", {}).get("status", ""),
        "priority": task.get("priority", {}).get("priority", "") if task.get("priority") else None,
        "assignees": [{"id": a["id"], "username": a.get("username", "")} for a in task.get("assignees", [])],
        "due_date": task.get("due_date"),
        "date_created": task.get("date_created"),
        "date_updated": task.get("date_updated"),
        "tags": [t["name"] for t in task.get("tags", [])],
        "url": task.get("url", ""),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8096)
