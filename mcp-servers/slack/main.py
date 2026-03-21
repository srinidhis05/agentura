"""Slack MCP Server — read + write operations for Slack.

Provides tools for: channel history, posting messages, thread replies,
canvas create/update, reactions, and channel listing.

Multi-token support: Set SLACK_BOT_TOKEN as default. Skills can override
via bot_token parameter on write operations for domain-scoped bots.
"""
import os
import json
import logging

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="slack-mcp")
logger = logging.getLogger("uvicorn")

DEFAULT_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")


def _client(bot_token: str | None = None):
    from slack_sdk import WebClient
    return WebClient(token=bot_token or DEFAULT_BOT_TOKEN)


# --- Models ---

class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class HealthResponse(BaseModel):
    status: str


# --- Tool definitions ---

TOOLS = [
    # Read operations
    {
        "name": "slack_conversations_history",
        "description": "Get message history from a Slack channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID (e.g. C0123456789)"},
                "limit": {"type": "integer", "description": "Number of messages (max 200)", "default": 50},
                "oldest": {"type": "string", "description": "Only messages after this Unix timestamp"},
            },
            "required": ["channel"],
        },
    },
    {
        "name": "slack_conversations_list",
        "description": "List Slack channels the bot has access to.",
        "input_schema": {
            "type": "object",
            "properties": {
                "types": {"type": "string", "description": "Channel types: public_channel, private_channel", "default": "public_channel"},
                "limit": {"type": "integer", "default": 100},
            },
        },
    },
    {
        "name": "slack_users_list",
        "description": "List Slack workspace users.",
        "input_schema": {"type": "object", "properties": {}},
    },
    # Write operations
    {
        "name": "slack_post_message",
        "description": "Post a message to a Slack channel. Use mrkdwn formatting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID (e.g. C0123456789)"},
                "text": {"type": "string", "description": "Message text in Slack mrkdwn format"},
                "blocks": {"type": "array", "description": "Optional Block Kit blocks (JSON array)", "items": {"type": "object"}},
                "bot_token": {"type": "string", "description": "Override bot token for domain-scoped posting"},
            },
            "required": ["channel", "text"],
        },
    },
    {
        "name": "slack_reply_thread",
        "description": "Reply to a message in a thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID"},
                "thread_ts": {"type": "string", "description": "Parent message timestamp"},
                "text": {"type": "string", "description": "Reply text in Slack mrkdwn format"},
                "blocks": {"type": "array", "description": "Optional Block Kit blocks", "items": {"type": "object"}},
                "bot_token": {"type": "string", "description": "Override bot token"},
            },
            "required": ["channel", "thread_ts", "text"],
        },
    },
    {
        "name": "slack_add_reaction",
        "description": "Add an emoji reaction to a message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID"},
                "timestamp": {"type": "string", "description": "Message timestamp"},
                "name": {"type": "string", "description": "Emoji name without colons (e.g. eyes, white_check_mark)"},
                "bot_token": {"type": "string", "description": "Override bot token"},
            },
            "required": ["channel", "timestamp", "name"],
        },
    },
    {
        "name": "slack_update_message",
        "description": "Update an existing Slack message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID"},
                "ts": {"type": "string", "description": "Timestamp of message to update"},
                "text": {"type": "string", "description": "New message text"},
                "blocks": {"type": "array", "description": "Optional new Block Kit blocks", "items": {"type": "object"}},
                "bot_token": {"type": "string", "description": "Override bot token"},
            },
            "required": ["channel", "ts", "text"],
        },
    },
    {
        "name": "slack_create_canvas",
        "description": "Create a new Slack Canvas. Returns canvas_id and canvas_url.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Canvas title"},
                "markdown": {"type": "string", "description": "Canvas content in markdown format. Slack converts to rich text."},
                "channel": {"type": "string", "description": "Channel ID to share the canvas in (optional)"},
                "bot_token": {"type": "string", "description": "Override bot token"},
            },
            "required": ["title", "markdown"],
        },
    },
    {
        "name": "slack_update_canvas",
        "description": "Update an existing Slack Canvas by replacing all content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "canvas_id": {"type": "string", "description": "Canvas ID (e.g. F0123456789)"},
                "markdown": {"type": "string", "description": "New canvas content in markdown format"},
                "bot_token": {"type": "string", "description": "Override bot token"},
            },
            "required": ["canvas_id", "markdown"],
        },
    },
    {
        "name": "slack_lookup_channel",
        "description": "Find a channel ID by name. Returns channel ID and info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Channel name without # (e.g. growth-pulse)"},
            },
            "required": ["name"],
        },
    },
]


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ready" if DEFAULT_BOT_TOKEN else "missing_token")


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    handlers = {
        "slack_conversations_history": _conversations_history,
        "slack_conversations_list": _conversations_list,
        "slack_users_list": _users_list,
        "slack_post_message": _post_message,
        "slack_reply_thread": _reply_thread,
        "slack_add_reaction": _add_reaction,
        "slack_update_message": _update_message,
        "slack_create_canvas": _create_canvas,
        "slack_update_canvas": _update_canvas,
        "slack_lookup_channel": _lookup_channel,
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


# --- Read handlers ---

def _conversations_history(args: dict) -> str:
    client = _client(args.get("bot_token"))
    resp = client.conversations_history(
        channel=args["channel"],
        limit=min(args.get("limit", 50), 200),
        oldest=args.get("oldest"),
    )
    messages = resp.data.get("messages", [])
    return json.dumps({"message_count": len(messages), "messages": messages[:50]}, indent=2)


def _conversations_list(args: dict) -> str:
    client = _client(args.get("bot_token"))
    resp = client.conversations_list(
        types=args.get("types", "public_channel"),
        limit=args.get("limit", 100),
    )
    channels = [{"id": c["id"], "name": c["name"], "topic": c.get("topic", {}).get("value", "")}
                for c in resp.data.get("channels", [])]
    return json.dumps(channels, indent=2)


def _users_list(args: dict) -> str:
    client = _client(args.get("bot_token"))
    resp = client.users_list()
    users = [{"id": m["id"], "name": m.get("real_name", m.get("name", "")), "is_bot": m.get("is_bot", False)}
             for m in resp.data.get("members", []) if not m.get("deleted")]
    return json.dumps(users, indent=2)


# --- Write handlers ---

def _post_message(args: dict) -> str:
    client = _client(args.get("bot_token"))
    kwargs = {"channel": args["channel"], "text": args["text"]}
    if args.get("blocks"):
        kwargs["blocks"] = args["blocks"]
    resp = client.chat_postMessage(**kwargs)
    return json.dumps({"ok": True, "ts": resp["ts"], "channel": resp["channel"]})


def _reply_thread(args: dict) -> str:
    client = _client(args.get("bot_token"))
    kwargs = {
        "channel": args["channel"],
        "thread_ts": args["thread_ts"],
        "text": args["text"],
    }
    if args.get("blocks"):
        kwargs["blocks"] = args["blocks"]
    resp = client.chat_postMessage(**kwargs)
    return json.dumps({"ok": True, "ts": resp["ts"], "thread_ts": args["thread_ts"]})


def _add_reaction(args: dict) -> str:
    client = _client(args.get("bot_token"))
    client.reactions_add(
        channel=args["channel"],
        timestamp=args["timestamp"],
        name=args["name"],
    )
    return json.dumps({"ok": True})


def _update_message(args: dict) -> str:
    client = _client(args.get("bot_token"))
    kwargs = {"channel": args["channel"], "ts": args["ts"], "text": args["text"]}
    if args.get("blocks"):
        kwargs["blocks"] = args["blocks"]
    resp = client.chat_update(**kwargs)
    return json.dumps({"ok": True, "ts": resp["ts"]})


def _create_canvas(args: dict) -> str:
    client = _client(args.get("bot_token"))
    # Slack Canvases API: canvases.create
    document = {"type": "markdown", "markdown": args["markdown"]}
    resp = client.api_call(
        "canvases.create",
        json={"title": args["title"], "document_content": document},
    )
    canvas_id = resp.data.get("canvas_id", "")

    # Share to channel if specified
    if args.get("channel") and canvas_id:
        try:
            client.api_call(
                "conversations.canvases.create",
                json={"channel_id": args["channel"], "canvas_id": canvas_id},
            )
        except Exception as e:
            logger.warning(f"Failed to share canvas to channel: {e}")

    # Construct canvas URL — Slack canvases are accessible at /docs/{canvas_id}
    canvas_url = ""
    if canvas_id:
        try:
            auth = client.auth_test()
            team_id = auth.data.get("team_id", "")
            if team_id:
                canvas_url = f"https://app.slack.com/docs/{team_id}/{canvas_id}"
        except Exception:
            pass

    result = {"ok": True, "canvas_id": canvas_id}
    if canvas_url:
        result["canvas_url"] = canvas_url
    return json.dumps(result)


def _update_canvas(args: dict) -> str:
    client = _client(args.get("bot_token"))
    document = {"type": "markdown", "markdown": args["markdown"]}
    resp = client.api_call(
        "canvases.edit",
        json={
            "canvas_id": args["canvas_id"],
            "changes": [{"operation": "replace", "document_content": document}],
        },
    )
    return json.dumps({"ok": resp.data.get("ok", False), "canvas_id": args["canvas_id"]})


def _lookup_channel(args: dict) -> str:
    client = _client(args.get("bot_token"))
    target = args["name"].lstrip("#").lower()
    cursor = None
    while True:
        kwargs = {"types": "public_channel,private_channel", "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        resp = client.conversations_list(**kwargs)
        for ch in resp.data.get("channels", []):
            if ch["name"].lower() == target:
                return json.dumps({"id": ch["id"], "name": ch["name"], "is_private": ch.get("is_private", False)})
        cursor = resp.data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break
    return json.dumps({"error": f"Channel #{target} not found"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8092)
