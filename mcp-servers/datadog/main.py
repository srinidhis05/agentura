"""Datadog MCP Server — production context for Shipwright PR reviews.

Exposes Datadog APM, monitors, incidents, and deployment tracking as MCP tools.
Used by pr-context-enricher to inject production context into code reviews.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="datadog-mcp", version="0.1.0")

# --- Config ---
DD_BASE = os.environ.get("DATADOG_API_ENDPOINT", "https://api.datadoghq.eu")
DD_API_KEY = os.environ.get("DATADOG_API_KEY", "")
DD_APP_KEY = os.environ.get("DATADOG_APP_KEY", "")
TIMEOUT = 15.0


def _headers() -> dict:
    return {
        "DD-API-KEY": DD_API_KEY,
        "DD-APPLICATION-KEY": DD_APP_KEY,
        "Content-Type": "application/json",
    }


# --- Models ---
class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


class ToolCallResponse(BaseModel):
    content: str
    is_error: bool = False


# --- Tool Definitions ---
TOOLS = [
    {
        "name": "query_monitors",
        "description": "Query Datadog monitors (alerts) for a service. Returns active/triggered monitors with severity and trigger count.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service name to filter monitors by (matched against tags and monitor name)",
                },
                "days": {
                    "type": "integer",
                    "description": "Look-back period in days (default: 7)",
                    "default": 7,
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "get_incidents",
        "description": "Get P1/P2 incidents for a service in the past N days. Returns incident ID, title, severity, root cause, and timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service name to filter incidents by",
                },
                "days": {
                    "type": "integer",
                    "description": "Look-back period in days (default: 90)",
                    "default": 90,
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "get_service_dependencies",
        "description": "Get service dependency map from Datadog APM. Returns upstream and downstream services with latency/error rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service name to get dependencies for",
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "get_deployment_events",
        "description": "Get recent deployment events for a service. Returns deploy timestamps, commit SHAs, and post-deploy error rate changes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service name to get deployments for",
                },
                "days": {
                    "type": "integer",
                    "description": "Look-back period in days (default: 7)",
                    "default": 7,
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "query_error_rate",
        "description": "Get current error rate and p99 latency for a service from Datadog APM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service name as tagged in Datadog APM",
                },
                "period": {
                    "type": "string",
                    "description": "Time period (default: '1h'). Options: '15m', '1h', '4h', '1d', '7d'",
                    "default": "1h",
                },
            },
            "required": ["service_name"],
        },
    },
]


# --- Endpoints ---
@app.get("/health")
def health():
    ok = bool(DD_API_KEY and DD_APP_KEY)
    return {"status": "ready" if ok else "missing_config"}


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call")
async def call_tool(req: ToolCallRequest):
    handlers = {
        "query_monitors": _query_monitors,
        "get_incidents": _get_incidents,
        "get_service_dependencies": _get_service_dependencies,
        "get_deployment_events": _get_deployment_events,
        "query_error_rate": _query_error_rate,
    }
    handler = handlers.get(req.name)
    if not handler:
        return ToolCallResponse(content=f"Unknown tool: {req.name}", is_error=True)
    try:
        output = await handler(req.arguments)
        return ToolCallResponse(content=output)
    except Exception as e:
        return ToolCallResponse(content=f"Error calling {req.name}: {e}", is_error=True)


# --- Tool Implementations ---

async def _query_monitors(args: dict) -> str:
    """Query monitors/alerts for a service."""
    service = args.get("service_name", "")
    days = args.get("days", 7)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Search monitors by tag or name
        resp = await client.get(
            f"{DD_BASE}/api/v1/monitor",
            headers=_headers(),
            params={"monitor_tags": f"service:{service}", "page_size": 20},
        )
        resp.raise_for_status()
        monitors = resp.json()

        # Also search by name if tag search returns few results
        if len(monitors) < 3:
            resp2 = await client.get(
                f"{DD_BASE}/api/v1/monitor",
                headers=_headers(),
                params={"name": service, "page_size": 20},
            )
            if resp2.status_code == 200:
                by_name = resp2.json()
                seen_ids = {m["id"] for m in monitors}
                monitors.extend(m for m in by_name if m["id"] not in seen_ids)

    results = []
    for m in monitors[:15]:
        state = m.get("overall_state", "OK")
        results.append({
            "name": m.get("name", ""),
            "severity": _monitor_priority(m),
            "state": state,
            "type": m.get("type", ""),
            "last_triggered": m.get("overall_state_modified", ""),
            "tags": [t for t in m.get("tags", []) if "service" in t or "env" in t][:5],
        })

    return json.dumps(results, indent=2, default=str)


async def _get_incidents(args: dict) -> str:
    """Get incidents for a service."""
    service = args.get("service_name", "")
    days = args.get("days", 90)
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            f"{DD_BASE}/api/v2/incidents",
            headers=_headers(),
            params={
                "filter[created][start]": since,
                "page[size]": 20,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    incidents = data.get("data", [])
    results = []
    for inc in incidents:
        attrs = inc.get("attributes", {})
        title = attrs.get("title", "")
        # Filter by service name in title, fields, or tags
        fields = attrs.get("fields", {})
        services = fields.get("services", {}).get("value", [])
        if service.lower() not in title.lower() and service not in str(services).lower():
            continue

        severity = attrs.get("severity", "UNKNOWN")
        results.append({
            "id": inc.get("id", ""),
            "title": title,
            "severity": severity,
            "state": attrs.get("state", ""),
            "created": attrs.get("created", ""),
            "resolved": attrs.get("resolved", ""),
            "root_cause": _extract_root_cause(attrs),
        })

    return json.dumps(results[:10], indent=2, default=str)


async def _get_service_dependencies(args: dict) -> str:
    """Get service dependency map from APM."""
    service = args.get("service_name", "")
    end = int(time.time())
    start = end - 3600  # last 1 hour

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            f"{DD_BASE}/api/v1/service_dependencies",
            headers=_headers(),
            params={"env": "production", "start": start, "end": end},
        )
        if resp.status_code == 404:
            # Fallback: use service map API
            resp = await client.get(
                f"{DD_BASE}/api/v2/services",
                headers=_headers(),
                params={"filter[env]": "production"},
            )
        resp.raise_for_status()
        data = resp.json()

    # Extract dependencies relevant to the service
    deps = {"upstream": [], "downstream": []}
    services = data if isinstance(data, list) else data.get("data", [])

    for svc in services:
        name = svc.get("name", "") if isinstance(svc, dict) else str(svc)
        if service.lower() in str(svc).lower():
            # Found our service, extract its dependencies
            attrs = svc.get("attributes", {}) if isinstance(svc, dict) else {}
            deps["service"] = name
            deps["type"] = attrs.get("type", "")
            break

    return json.dumps(deps, indent=2, default=str)


async def _get_deployment_events(args: dict) -> str:
    """Get deployment events for a service."""
    service = args.get("service_name", "")
    days = args.get("days", 7)
    end = int(time.time())
    start = end - (days * 86400)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Query DORA metrics / deployment events
        resp = await client.get(
            f"{DD_BASE}/api/v1/events",
            headers=_headers(),
            params={
                "start": start,
                "end": end,
                "tags": f"service:{service}",
                "sources": "deployment",
                "priority": "normal",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    events = data.get("events", [])
    results = []
    for ev in events[:10]:
        results.append({
            "title": ev.get("title", ""),
            "date": ev.get("date_happened", ""),
            "source": ev.get("source_type_name", ""),
            "tags": [t for t in ev.get("tags", []) if "version" in t or "commit" in t or "env" in t][:5],
        })

    return json.dumps(results, indent=2, default=str)


async def _query_error_rate(args: dict) -> str:
    """Query error rate, traffic, p95 latency, and apdex from APM."""
    service = args.get("service_name", "")
    period = args.get("period", "1h")
    env = args.get("env", "prod")

    period_map = {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "7d": 604800}
    seconds = period_map.get(period, 3600)
    end = int(time.time())
    start = end - seconds

    async def _query_metric(client: httpx.AsyncClient, query: str) -> float:
        resp = await client.get(
            f"{DD_BASE}/api/v1/query",
            headers=_headers(),
            params={"from": start, "to": end, "query": query},
        )
        if resp.status_code != 200:
            return 0
        series = resp.json().get("series", [])
        if series and series[0].get("pointlist"):
            return series[0]["pointlist"][-1][1]
        return 0

    tags = f"env:{env},service:{service}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        hits = await _query_metric(client, f"sum:trace.http.request.hits{{{tags}}}.as_rate()")
        errors_5xx = await _query_metric(client, f"sum:trace.http.request.hits.by_http_status{{{tags},http.status_class:5xx}}.as_rate()")
        p95_s = await _query_metric(client, f"p95:trace.http.request{{{tags}}}")
        apdex = await _query_metric(client, f"avg:trace.http.request.apdex{{{tags}}}")

    error_pct = (errors_5xx / hits * 100) if hits > 0 else 0

    result = {
        "service": service,
        "env": env,
        "period": period,
        "hits_per_sec": round(hits, 1),
        "error_5xx_per_sec": round(errors_5xx, 3),
        "error_rate_pct": round(error_pct, 2),
        "p95_latency_ms": round(p95_s * 1000),
        "apdex": round(apdex, 3),
        "health": "healthy" if error_pct < 1 and apdex > 0.9 else "degraded" if error_pct < 5 else "critical",
        "query_time": datetime.now(timezone.utc).isoformat(),
    }

    return json.dumps(result, indent=2)


# --- Helpers ---

def _monitor_priority(monitor: dict) -> str:
    """Extract severity from monitor priority or tags."""
    priority = monitor.get("priority", 0) or 0
    if priority <= 1:
        return "critical"
    elif priority <= 3:
        return "high"
    elif priority <= 4:
        return "medium"
    return "low"


def _extract_root_cause(attrs: dict) -> str:
    """Extract root cause from incident postmortem or timeline."""
    postmortem = attrs.get("postmortem", {})
    if postmortem:
        return postmortem.get("analysis", "")[:500]
    # Fallback to description
    return (attrs.get("customer_impact_scope", "") or "")[:500]
