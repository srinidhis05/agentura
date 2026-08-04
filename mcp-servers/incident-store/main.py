"""Incident Store MCP Server — knowledge store for Ops Genie.

Stores and queries production incidents: enrichment hypotheses, RCA,
resolutions, and thread context. Every alert becomes a queryable record.

Tools are called by:
- Gateway post-processing (validate_and_record, update, add_alert)
- Alert-enricher skill (search_past_incidents, find_active_incident) — READ ONLY
- Thread-harvester skill (update_incident)
- Shift-briefer / incident-query (get_incident_summary, search_past_incidents)
"""

import hmac
import json
import os
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import psycopg2.pool
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="incident-store-mcp", version="0.1.0")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
MCP_AUTH_SECRET = os.environ.get("MCP_AUTH_SECRET", "")

# Known services — validation rejects unknown service names
KNOWN_SERVICES = {
    "falcon-api-service", "falcon-worker-service",
    "goblin-service", "lulu-fulfillment-service", "settlements-service",
    "app-server-service", "app-server-internal-service",
    "beneficiary-service", "rewards-api-service", "notification-service",
    "user-vault-service", "goms-service",
    "fx-api-service", "fx-worker-service",
    "casa-service",
}

VALID_SEVERITIES = {"P1", "P2", "P3"}
VALID_STATUSES = {"active", "monitoring", "resolved", "noise"}

# --- Connection Pool ---

_pool = None


def _get_pool():
    global _pool
    if _pool is None and DATABASE_URL:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2, maxconn=10, dsn=DATABASE_URL,
        )
    return _pool


# --- Auth Middleware ---

@app.middleware("http")
async def verify_mcp_auth(request: Request, call_next):
    if request.url.path in ("/health", "/tools"):
        return await call_next(request)
    if MCP_AUTH_SECRET:
        provided = request.headers.get("X-MCP-Auth", "")
        if not hmac.compare_digest(provided, MCP_AUTH_SECRET):
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return await call_next(request)


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
        "name": "search_past_incidents",
        "description": "Search past incidents by service, time window, or root cause. Returns structured records for 'Similar past incident' enrichment and ad-hoc queries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Datadog APM service name"},
                "days": {"type": "integer", "description": "Look-back period (default 90)", "default": 90},
                "root_cause_category": {"type": "string", "description": "Filter: deploy/traffic/infra/external/config/noise"},
                "status": {"type": "string", "description": "Filter: active/monitoring/resolved/noise"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "find_active_incident",
        "description": "Check if there's an active incident for a service within a time window. Used for dedup and correlation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Datadog APM service name"},
                "window_minutes": {"type": "integer", "description": "Look-back window (default 30)", "default": 30},
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "record_incident",
        "description": "Create a new incident record. Called by gateway post-processing after enricher assessment is validated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"},
                "title": {"type": "string"},
                "severity": {"type": "string", "description": "P1/P2/P3"},
                "alert_channel": {"type": "string"},
                "alert_ts": {"type": "string"},
                "enrichment_hypothesis": {"type": "string"},
                "enrichment_correlation_rule": {"type": "string"},
                "enrichment_suggested_actions": {"type": "array", "items": {"type": "string"}},
                "enrichment_raw_context": {"type": "object"},
                "enrichment_execution_id": {"type": "string"},
                "parent_incident_id": {"type": "string"},
                "monitor_name": {"type": "string"},
            },
            "required": ["service_name", "title", "severity"],
        },
    },
    {
        "name": "update_incident",
        "description": "Update an existing incident. Used by thread-harvester (RCA), alert-resolver (resolved_at), and button callbacks (hypothesis_correct).",
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "status": {"type": "string"},
                "root_cause_category": {"type": "string"},
                "root_cause_detail": {"type": "string"},
                "resolution_action": {"type": "string"},
                "resolution_detail": {"type": "string"},
                "resolved_at": {"type": "string", "description": "ISO 8601 timestamp"},
                "duration_min": {"type": "number"},
                "acknowledged_at": {"type": "string"},
                "thread_summary": {"type": "string"},
                "thread_message_count": {"type": "integer"},
                "thread_participants": {"type": "array", "items": {"type": "string"}},
                "hypothesis_correct": {"type": "boolean"},
                "harvested_at": {"type": "string"},
            },
            "required": ["incident_id"],
        },
    },
    {
        "name": "get_incident_summary",
        "description": "Get aggregated incident stats for a time window. Used by shift-briefer and service-health.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Time window: 8h, 1d, 7d, 30d", "default": "1d"},
                "service_name": {"type": "string", "description": "Optional: filter by service"},
            },
        },
    },
    {
        "name": "add_incident_alert",
        "description": "Link an additional alert to an existing incident (correlation).",
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "monitor_name": {"type": "string"},
                "monitor_id": {"type": "string"},
                "alert_channel": {"type": "string"},
                "alert_ts": {"type": "string"},
                "severity": {"type": "string"},
            },
            "required": ["incident_id", "monitor_name"],
        },
    },
    {
        "name": "validate_and_record_incident",
        "description": "Validate enrichment assessment and create incident. Called by gateway post-processing, not by LLM. Validates service_name, severity, and strips credential patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessment": {"type": "object", "description": "JSON assessment from enricher task_complete"},
                "alert_channel": {"type": "string"},
                "alert_ts": {"type": "string"},
                "execution_id": {"type": "string"},
            },
            "required": ["assessment"],
        },
    },
]


# --- Endpoints ---

@app.get("/health")
def health():
    pool = _get_pool()
    return {"status": "ready" if pool else "no_database"}


@app.get("/tools")
def list_tools():
    return TOOLS


@app.post("/tools/call")
async def call_tool(req: ToolCallRequest):
    handlers = {
        "search_past_incidents": _search_past_incidents,
        "find_active_incident": _find_active_incident,
        "record_incident": _record_incident,
        "update_incident": _update_incident,
        "get_incident_summary": _get_incident_summary,
        "add_incident_alert": _add_incident_alert,
        "validate_and_record_incident": _validate_and_record_incident,
    }
    handler = handlers.get(req.name)
    if not handler:
        return ToolCallResponse(content=f"Unknown tool: {req.name}", is_error=True)
    try:
        output = handler(req.arguments)
        return ToolCallResponse(content=output)
    except Exception as e:
        return ToolCallResponse(content=f"Error in {req.name}: {e}", is_error=True)


# --- Tool Implementations ---

def _search_past_incidents(args: dict) -> str:
    service = args.get("service_name", "")
    days = args.get("days", 90)
    root_cause = args.get("root_cause_category")
    status = args.get("status")
    limit = args.get("limit", 5)

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = ["service_name = %s", "started_at > NOW() - interval '%s days'"]
            values = [service, days]

            if root_cause:
                conditions.append("root_cause_category = %s")
                values.append(root_cause)
            if status:
                conditions.append("status = %s")
                values.append(status)

            values.append(limit)
            where = " AND ".join(conditions)
            cur.execute(
                f"SELECT id, title, severity, service_name, status, "
                f"root_cause_category, root_cause_detail, resolution_action, "
                f"resolution_detail, duration_min, started_at, resolved_at, "
                f"enrichment_hypothesis, hypothesis_correct, "
                f"thread_message_count, correlated_alert_count "
                f"FROM incidents WHERE {where} "
                f"ORDER BY started_at DESC LIMIT %s",
                values,
            )
            rows = cur.fetchall()
    finally:
        pool.putconn(conn)

    results = []
    for row in rows:
        d = dict(row)
        for k in ("started_at", "resolved_at"):
            if d.get(k) and hasattr(d[k], "isoformat"):
                d[k] = d[k].isoformat()
        results.append(d)

    return json.dumps(results, indent=2, default=str)


def _find_active_incident(args: dict) -> str:
    service = args.get("service_name", "")
    window = args.get("window_minutes", 30)

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, title, severity, started_at FROM incidents "
                "WHERE service_name = %s AND status IN ('active', 'monitoring') "
                "AND started_at > NOW() - interval '%s minutes' "
                "ORDER BY started_at DESC LIMIT 1",
                (service, window),
            )
            row = cur.fetchone()
    finally:
        pool.putconn(conn)

    if not row:
        return json.dumps(None)

    d = dict(row)
    if d.get("started_at") and hasattr(d["started_at"], "isoformat"):
        d["started_at"] = d["started_at"].isoformat()
    return json.dumps(d)


def _record_incident(args: dict) -> str:
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    service = args.get("service_name", "")
    title = args.get("title", "")
    severity = args.get("severity", "P3")

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO incidents
                   (id, service_name, title, severity, status, started_at,
                    alert_channel, alert_ts,
                    enrichment_hypothesis, enrichment_correlation_rule,
                    enrichment_suggested_actions, enrichment_raw_context,
                    enrichment_execution_id, parent_incident_id)
                   VALUES (%s, %s, %s, %s, 'active', NOW(),
                           %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    incident_id, service, title, severity,
                    args.get("alert_channel", ""),
                    args.get("alert_ts", ""),
                    args.get("enrichment_hypothesis", ""),
                    args.get("enrichment_correlation_rule", ""),
                    json.dumps(args.get("enrichment_suggested_actions", [])),
                    json.dumps(args.get("enrichment_raw_context", {})),
                    args.get("enrichment_execution_id", ""),
                    args.get("parent_incident_id"),
                ),
            )

            # Also create incident_alerts row for the triggering alert
            monitor_name = args.get("monitor_name") or args.get("title", "")
            cur.execute(
                """INSERT INTO incident_alerts
                   (incident_id, monitor_name, alert_channel, alert_ts, severity)
                   VALUES (%s, %s, %s, %s, %s)""",
                (incident_id, monitor_name, args.get("alert_channel", ""),
                 args.get("alert_ts", ""), severity),
            )
        conn.commit()
    finally:
        pool.putconn(conn)

    return json.dumps({"id": incident_id, "status": "created"})


def _update_incident(args: dict) -> str:
    incident_id = args.get("incident_id", "")
    if not incident_id:
        return json.dumps({"error": "incident_id required"})

    allowed = {
        "status", "root_cause_category", "root_cause_detail",
        "resolution_action", "resolution_detail", "resolved_at",
        "duration_min", "acknowledged_at", "thread_summary",
        "thread_message_count", "thread_participants",
        "hypothesis_correct", "harvested_at",
    }

    parts = ["updated_at = NOW()"]
    values = []
    for key, val in args.items():
        if key == "incident_id" or key not in allowed:
            continue
        if key == "thread_participants" and isinstance(val, list):
            parts.append(f"{key} = %s")
            values.append(val)
        elif key == "hypothesis_correct" and isinstance(val, bool):
            parts.append(f"{key} = %s")
            values.append(val)
        else:
            parts.append(f"{key} = %s")
            values.append(val)

    if len(parts) == 1:
        return json.dumps({"error": "no valid fields to update"})

    # Auto-compute duration_min when resolved_at is set
    if "resolved_at" in args and "duration_min" not in args:
        parts.append("duration_min = EXTRACT(EPOCH FROM (%s::timestamptz - started_at)) / 60")
        values.append(args["resolved_at"])

    values.append(incident_id)

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE incidents SET {', '.join(parts)} WHERE id = %s",
                values,
            )
        conn.commit()
    finally:
        pool.putconn(conn)

    return json.dumps({"id": incident_id, "status": "updated"})


def _get_incident_summary(args: dict) -> str:
    period = args.get("period", "1d")
    service = args.get("service_name")

    period_map = {"8h": "8 hours", "1d": "1 day", "7d": "7 days", "30d": "30 days"}
    interval = period_map.get(period, "1 day")

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            where = f"started_at > NOW() - interval '{interval}'"
            values = []
            if service:
                where += " AND service_name = %s"
                values.append(service)

            # Main stats
            cur.execute(
                f"""SELECT
                    COUNT(*) as total_incidents,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'monitoring') as monitoring,
                    COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
                    COUNT(*) FILTER (WHERE status = 'noise') as noise,
                    AVG(duration_min) FILTER (WHERE duration_min IS NOT NULL) as avg_duration_min,
                    COUNT(*) FILTER (WHERE hypothesis_correct = true) as correct_hypotheses,
                    COUNT(*) FILTER (WHERE hypothesis_correct IS NOT NULL) as scored_hypotheses
                FROM incidents WHERE {where}""",
                values,
            )
            stats = dict(cur.fetchone())

            # By service
            cur.execute(
                f"SELECT service_name, COUNT(*) as count "
                f"FROM incidents WHERE {where} "
                f"GROUP BY service_name ORDER BY count DESC",
                values,
            )
            stats["by_service"] = {r["service_name"]: r["count"] for r in cur.fetchall()}

            # By root cause
            cur.execute(
                f"SELECT root_cause_category, COUNT(*) as count "
                f"FROM incidents WHERE {where} AND root_cause_category IS NOT NULL "
                f"GROUP BY root_cause_category ORDER BY count DESC",
                values,
            )
            stats["by_root_cause"] = {r["root_cause_category"]: r["count"] for r in cur.fetchall()}

            # By severity
            cur.execute(
                f"SELECT severity, COUNT(*) as count "
                f"FROM incidents WHERE {where} "
                f"GROUP BY severity ORDER BY severity",
                values,
            )
            stats["by_severity"] = {r["severity"]: r["count"] for r in cur.fetchall()}

            # Carry-forward: active + monitoring incidents
            cur.execute(
                "SELECT id, service_name, title, severity, status, started_at "
                "FROM incidents WHERE status IN ('active', 'monitoring') "
                "ORDER BY severity, started_at DESC LIMIT 10",
            )
            carry = []
            for r in cur.fetchall():
                d = dict(r)
                if d.get("started_at") and hasattr(d["started_at"], "isoformat"):
                    d["started_at"] = d["started_at"].isoformat()
                carry.append(d)
            stats["carry_forward"] = carry

            # Total alerts
            cur.execute(
                f"SELECT COUNT(*) as total_alerts FROM incident_alerts ia "
                f"JOIN incidents i ON ia.incident_id = i.id WHERE i.{where.replace('started_at', 'i.started_at')}",
                values,
            )
            alert_row = cur.fetchone()
            stats["total_alerts"] = alert_row["total_alerts"] if alert_row else 0

            # Accuracy
            scored = stats.get("scored_hypotheses", 0)
            correct = stats.get("correct_hypotheses", 0)
            stats["accuracy_pct"] = round(100 * correct / scored, 1) if scored > 0 else None

            # Clean up numeric types
            for k in ("avg_duration_min",):
                if stats.get(k) is not None:
                    stats[k] = round(float(stats[k]), 1)

    finally:
        pool.putconn(conn)

    return json.dumps(stats, indent=2, default=str)


def _add_incident_alert(args: dict) -> str:
    incident_id = args.get("incident_id", "")

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO incident_alerts
                   (incident_id, monitor_name, monitor_id, alert_channel, alert_ts, severity)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    incident_id,
                    args.get("monitor_name", ""),
                    args.get("monitor_id", ""),
                    args.get("alert_channel", ""),
                    args.get("alert_ts", ""),
                    args.get("severity", ""),
                ),
            )
            cur.execute(
                "UPDATE incidents SET correlated_alert_count = correlated_alert_count + 1, "
                "updated_at = NOW() WHERE id = %s",
                (incident_id,),
            )
        conn.commit()
    finally:
        pool.putconn(conn)

    return json.dumps({"incident_id": incident_id, "status": "alert_linked"})


import re

_CREDENTIAL_PATTERNS = [
    re.compile(r'xox[bpras]-[A-Za-z0-9\-]+'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'(?:token|key|secret|password|bearer)\s*[:=]\s*["\']?[A-Za-z0-9+/=\-_]{20,}["\']?', re.IGNORECASE),
    re.compile(r'(postgres|mysql|mongodb|redis)://[^\s]+'),
]


def _strip_credentials(text: str) -> str:
    if not isinstance(text, str):
        return text
    for pattern in _CREDENTIAL_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def _validate_and_record_incident(args: dict) -> str:
    assessment = args.get("assessment", {})
    if not assessment:
        return json.dumps({"error": "assessment required", "valid": False})

    service = assessment.get("service_name", "")
    severity = assessment.get("severity", "")

    # Validate service name
    if service not in KNOWN_SERVICES:
        return json.dumps({
            "error": f"Unknown service: {service}. Known: {sorted(KNOWN_SERVICES)}",
            "valid": False,
        })

    # Validate severity
    if severity not in VALID_SEVERITIES:
        return json.dumps({
            "error": f"Invalid severity: {severity}. Must be P1/P2/P3.",
            "valid": False,
        })

    # Strip credential patterns from all string fields
    for key in ("hypothesis", "enrichment_hypothesis", "summary", "suggested_actions"):
        if key in assessment and isinstance(assessment[key], str):
            assessment[key] = _strip_credentials(assessment[key])
    if "suggested_actions" in assessment and isinstance(assessment["suggested_actions"], list):
        assessment["suggested_actions"] = [
            _strip_credentials(a) if isinstance(a, str) else a
            for a in assessment["suggested_actions"]
        ]

    # Record the incident
    record_args = {
        "service_name": service,
        "title": assessment.get("title", assessment.get("summary", f"{service} alert")),
        "severity": severity,
        "alert_channel": args.get("alert_channel", ""),
        "alert_ts": args.get("alert_ts", ""),
        "enrichment_hypothesis": assessment.get("hypothesis", assessment.get("enrichment_hypothesis", "")),
        "enrichment_correlation_rule": assessment.get("correlation_rule", assessment.get("enrichment_correlation_rule", "")),
        "enrichment_suggested_actions": assessment.get("suggested_actions", assessment.get("enrichment_suggested_actions", [])),
        "enrichment_raw_context": assessment.get("raw_context", assessment.get("enrichment_raw_context", {})),
        "enrichment_execution_id": args.get("execution_id", ""),
        "parent_incident_id": assessment.get("parent_incident_id"),
        "monitor_name": assessment.get("monitor_name", ""),
    }

    result = json.loads(_record_incident(record_args))
    result["valid"] = True
    return json.dumps(result)
