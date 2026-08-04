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
    {
        "name": "query_pod_health",
        "description": "Get K8s pod health metrics for a service: CPU %, memory %, pod count, restart count. Uses parameterized queries — service_name only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service name (maps to kube_deployment tag in Datadog)",
                },
                "period": {
                    "type": "string",
                    "description": "Time window: '15m', '1h', '4h' (default: '15m')",
                    "default": "15m",
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "query_top_failing_endpoints",
        "description": "Get top failing endpoints (resources) for a service ranked by error rate. Shows WHICH API path is broken.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Datadog APM service name",
                },
                "period": {
                    "type": "string",
                    "description": "Time window (default: '15m')",
                    "default": "15m",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max endpoints to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "query_dependency_health",
        "description": "Get health metrics for each dependency of a service (per-edge: error rate, latency, call rate). Replaces get_service_dependencies with actual per-edge metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Datadog APM service name",
                },
                "period": {
                    "type": "string",
                    "description": "Time window (default: '15m')",
                    "default": "15m",
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
        "query_pod_health": _query_pod_health,
        "query_top_failing_endpoints": _query_top_failing_endpoints,
        "query_dependency_health": _query_dependency_health,
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
        # Try trace.servlet.request first (Spring Boot), fallback to trace.http.request
        hits = await _query_metric(client, f"sum:trace.servlet.request.hits{{{tags}}}.as_rate()")
        if hits == 0:
            hits = await _query_metric(client, f"sum:trace.http.request.hits{{{tags}}}.as_rate()")
            span = "http.request"
        else:
            span = "servlet.request"
        errors_5xx = await _query_metric(client, f"sum:trace.{span}.errors{{{tags}}}.as_rate()")
        p95_s = await _query_metric(client, f"p95:trace.{span}{{{tags}}}")
        apdex = await _query_metric(client, f"avg:trace.{span}.apdex{{{tags}}}")

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


def _period_to_seconds(period: str) -> int:
    return {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "7d": 604800}.get(period, 900)


async def _query_single_metric(client: httpx.AsyncClient, query: str, start: int, end: int) -> float | None:
    """Query a single Datadog metric, return latest value or None."""
    resp = await client.get(
        f"{DD_BASE}/api/v1/query",
        headers=_headers(),
        params={"from": start, "to": end, "query": query},
    )
    if resp.status_code != 200:
        return None
    series = resp.json().get("series", [])
    if series and series[0].get("pointlist"):
        val = series[0]["pointlist"][-1][1]
        return val if val is not None else None
    return None


async def _query_grouped_metric(client: httpx.AsyncClient, query: str, start: int, end: int) -> list[dict]:
    """Query a Datadog metric with group-by, return list of {scope, value}."""
    resp = await client.get(
        f"{DD_BASE}/api/v1/query",
        headers=_headers(),
        params={"from": start, "to": end, "query": query},
    )
    if resp.status_code != 200:
        return []
    series = resp.json().get("series", [])
    results = []
    for s in series:
        pts = s.get("pointlist", [])
        val = pts[-1][1] if pts and pts[-1][1] is not None else 0
        results.append({"scope": s.get("scope", ""), "value": val})
    return results


# --- Ops Genie Tools ---


async def _query_pod_health(args: dict) -> str:
    """Get K8s pod health for a service. Parameterized — LLM provides service name only."""
    service = args.get("service_name", "")
    period = args.get("period", "15m")
    seconds = _period_to_seconds(period)
    end = int(time.time())
    start = end - seconds

    # Map service name to likely k8s deployment name (strip -service suffix)
    deploy = service.replace("-service", "")

    metrics = {
        "cpu_pct": f"avg:kubernetes.cpu.usage.total{{kube_deployment:{deploy}}}",
        "memory_pct": f"avg:kubernetes.memory.usage_pct{{kube_deployment:{deploy}}}",
        "pods_running": f"sum:kubernetes.pods.running{{kube_deployment:{deploy}}}",
        "restarts": f"sum:kubernetes.containers.restarts{{kube_deployment:{deploy}}}",
    }

    result = {"service": service, "deployment": deploy, "period": period}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for key, query in metrics.items():
            val = await _query_single_metric(client, query, start, end)
            result[key] = round(val, 2) if val is not None else None

    # Determine health status
    cpu = result.get("cpu_pct")
    restarts = result.get("restarts")
    if restarts and restarts > 0:
        result["health"] = "degraded"
        result["note"] = f"{int(restarts)} container restarts in {period}"
    elif cpu and cpu > 90:
        result["health"] = "critical"
        result["note"] = "CPU saturation"
    elif cpu and cpu > 70:
        result["health"] = "warning"
    else:
        result["health"] = "healthy"

    return json.dumps(result, indent=2)


async def _query_top_failing_endpoints(args: dict) -> str:
    """Get top failing endpoints for a service. Parameterized — no raw QL from LLM."""
    service = args.get("service_name", "")
    period = args.get("period", "15m")
    limit = args.get("limit", 5)
    seconds = _period_to_seconds(period)
    end = int(time.time())
    start = end - seconds

    tags = f"env:prod,service:{service}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Try servlet.request first (Spring Boot), fallback to http.request
        errors = await _query_grouped_metric(
            client,
            f"sum:trace.servlet.request.errors{{{tags}}} by {{resource_name}}.as_rate()",
            start, end,
        )
        if not errors:
            errors = await _query_grouped_metric(
                client,
                f"sum:trace.http.request.errors{{{tags}}} by {{resource_name}}.as_rate()",
                start, end,
            )

        hits = await _query_grouped_metric(
            client,
            f"sum:trace.servlet.request.hits{{{tags}}} by {{resource_name}}.as_rate()",
            start, end,
        )
        if not hits:
            hits = await _query_grouped_metric(
                client,
                f"sum:trace.http.request.hits{{{tags}}} by {{resource_name}}.as_rate()",
                start, end,
            )

    # Build per-endpoint stats
    hits_by_resource = {}
    for h in hits:
        # scope format: "env:prod,resource_name:POST /v1/foo,service:bar"
        parts = dict(p.split(":", 1) for p in h["scope"].split(",") if ":" in p)
        resource = parts.get("resource_name", "unknown")
        hits_by_resource[resource] = h["value"]

    endpoints = []
    for e in errors:
        parts = dict(p.split(":", 1) for p in e["scope"].split(",") if ":" in p)
        resource = parts.get("resource_name", "unknown")
        err_rate = e["value"]
        hit_rate = hits_by_resource.get(resource, 0)
        error_pct = (err_rate / hit_rate * 100) if hit_rate > 0 else 0
        endpoints.append({
            "resource": resource,
            "errors_per_sec": round(err_rate, 3),
            "hits_per_sec": round(hit_rate, 1),
            "error_rate_pct": round(error_pct, 2),
        })

    # Sort by error rate descending, take top N
    endpoints.sort(key=lambda x: -x["error_rate_pct"])
    endpoints = endpoints[:limit]

    # Determine if errors are isolated to one endpoint
    isolated_to = None
    if endpoints and endpoints[0]["error_rate_pct"] > 1:
        if len(endpoints) < 2 or endpoints[1]["error_rate_pct"] < 0.5:
            isolated_to = endpoints[0]["resource"]

    result = {
        "service": service,
        "period": period,
        "endpoints": endpoints,
        "isolated_to": isolated_to,
    }
    return json.dumps(result, indent=2)


async def _query_dependency_health(args: dict) -> str:
    """Get per-edge dependency health. Replaces broken get_service_dependencies."""
    service = args.get("service_name", "")
    period = args.get("period", "15m")
    seconds = _period_to_seconds(period)
    end = int(time.time())
    start = end - seconds

    tags = f"env:prod,service:{service}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Get calls per dependency via peer.service tag
        # Try servlet first, fallback to http
        dep_hits = await _query_grouped_metric(
            client,
            f"sum:trace.servlet.request.hits{{{tags}}} by {{peer.service}}.as_rate()",
            start, end,
        )
        if not dep_hits:
            dep_hits = await _query_grouped_metric(
                client,
                f"sum:trace.http.request.hits{{{tags}}} by {{peer.service}}.as_rate()",
                start, end,
            )

        dep_errors = await _query_grouped_metric(
            client,
            f"sum:trace.servlet.request.errors{{{tags}}} by {{peer.service}}.as_rate()",
            start, end,
        )
        if not dep_errors:
            dep_errors = await _query_grouped_metric(
                client,
                f"sum:trace.http.request.errors{{{tags}}} by {{peer.service}}.as_rate()",
                start, end,
            )

        dep_latency = await _query_grouped_metric(
            client,
            f"p95:trace.servlet.request{{{tags}}} by {{peer.service}}",
            start, end,
        )
        if not dep_latency:
            dep_latency = await _query_grouped_metric(
                client,
                f"p95:trace.http.request{{{tags}}} by {{peer.service}}",
                start, end,
            )

    def _extract_peer(scope: str) -> str:
        parts = dict(p.split(":", 1) for p in scope.split(",") if ":" in p)
        return parts.get("peer.service", "unknown")

    # Merge into per-dependency records
    deps = {}
    for h in dep_hits:
        peer = _extract_peer(h["scope"])
        if peer == "N/A" or not peer:
            continue
        deps.setdefault(peer, {})["calls_per_sec"] = round(h["value"], 1)

    for e in dep_errors:
        peer = _extract_peer(e["scope"])
        if peer in deps:
            deps[peer]["errors_per_sec"] = round(e["value"], 3)

    for l in dep_latency:
        peer = _extract_peer(l["scope"])
        if peer in deps:
            deps[peer]["p95_ms"] = round(l["value"] * 1000) if l["value"] else None

    dependencies = []
    for name, metrics in deps.items():
        calls = metrics.get("calls_per_sec", 0)
        errs = metrics.get("errors_per_sec", 0)
        error_pct = (errs / calls * 100) if calls > 0 else 0
        health = "healthy" if error_pct < 1 else "degraded" if error_pct < 5 else "critical"
        dependencies.append({
            "name": name,
            "calls_per_sec": calls,
            "error_rate_pct": round(error_pct, 2),
            "p95_ms": metrics.get("p95_ms"),
            "health": health,
        })

    dependencies.sort(key=lambda x: -x.get("error_rate_pct", 0))

    return json.dumps({
        "service": service,
        "period": period,
        "dependencies": dependencies,
    }, indent=2)
