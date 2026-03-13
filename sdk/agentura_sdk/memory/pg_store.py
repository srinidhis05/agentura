"""PostgreSQL-backed memory store with domain + workspace isolation.

Replaces json_store.py for production use. Activated when DATABASE_URL is set.
All tables are scoped by (domain, workspace_id) for cross-domain isolation.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import psycopg2.pool

_SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
    id SERIAL PRIMARY KEY,
    execution_id TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL DEFAULT '',
    workspace_id TEXT NOT NULL DEFAULT 'default',
    skill TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    input_summary JSONB,
    output_summary JSONB,
    outcome TEXT DEFAULT 'pending_review',
    cost_usd REAL DEFAULT 0.0,
    latency_ms REAL DEFAULT 0.0,
    model_used TEXT DEFAULT '',
    user_feedback TEXT,
    correction_generated_test BOOLEAN DEFAULT FALSE,
    reflexion_applied TEXT,
    reviewer_notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS corrections (
    id SERIAL PRIMARY KEY,
    correction_id TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL DEFAULT '',
    workspace_id TEXT NOT NULL DEFAULT 'default',
    skill TEXT NOT NULL,
    execution_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    original_output JSONB,
    user_correction TEXT DEFAULT '',
    correction_type TEXT DEFAULT 'domain-specific',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reflexions (
    id SERIAL PRIMARY KEY,
    reflexion_id TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL DEFAULT '',
    workspace_id TEXT NOT NULL DEFAULT 'default',
    skill TEXT NOT NULL,
    correction_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rule TEXT DEFAULT '',
    applies_when TEXT DEFAULT '',
    confidence REAL DEFAULT 0.0,
    validated_by_test BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_executions_skill ON executions(skill);
CREATE INDEX IF NOT EXISTS idx_executions_domain ON executions(domain);
CREATE INDEX IF NOT EXISTS idx_executions_workspace ON executions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_executions_outcome ON executions(outcome);
CREATE INDEX IF NOT EXISTS idx_corrections_skill ON corrections(skill);
CREATE INDEX IF NOT EXISTS idx_corrections_domain ON corrections(domain);
CREATE INDEX IF NOT EXISTS idx_reflexions_skill ON reflexions(skill);
CREATE INDEX IF NOT EXISTS idx_reflexions_domain ON reflexions(domain);

CREATE TABLE IF NOT EXISTS fleet_sessions (
    id SERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    pipeline_name TEXT NOT NULL DEFAULT '',
    trigger_type TEXT NOT NULL DEFAULT 'manual',
    repo TEXT NOT NULL DEFAULT '',
    pr_number INTEGER DEFAULT 0,
    pr_url TEXT NOT NULL DEFAULT '',
    head_sha TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    total_agents INTEGER DEFAULT 0,
    completed_agents INTEGER DEFAULT 0,
    failed_agents INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    input_data JSONB,
    github_check_posted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fleet_agents (
    id SERIAL PRIMARY KEY,
    agent_id TEXT UNIQUE NOT NULL,
    session_id TEXT NOT NULL REFERENCES fleet_sessions(session_id),
    skill_path TEXT NOT NULL DEFAULT '',
    execution_id TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    pod_name TEXT DEFAULT '',
    success BOOLEAN DEFAULT FALSE,
    output JSONB,
    cost_usd REAL DEFAULT 0.0,
    latency_ms REAL DEFAULT 0.0,
    error_message TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fleet_sessions_status ON fleet_sessions(status);
CREATE INDEX IF NOT EXISTS idx_fleet_sessions_repo ON fleet_sessions(repo);
CREATE INDEX IF NOT EXISTS idx_fleet_agents_session ON fleet_agents(session_id);
CREATE INDEX IF NOT EXISTS idx_fleet_agents_status ON fleet_agents(status);

-- MemRL: utility-scored memory (DEC-066)
ALTER TABLE reflexions ADD COLUMN IF NOT EXISTS utility_score REAL DEFAULT 0.5;
ALTER TABLE reflexions ADD COLUMN IF NOT EXISTS times_injected INT DEFAULT 0;
ALTER TABLE reflexions ADD COLUMN IF NOT EXISTS times_helped INT DEFAULT 0;
ALTER TABLE reflexions ADD COLUMN IF NOT EXISTS last_scored_at TIMESTAMPTZ;
ALTER TABLE reflexions ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'correction';
ALTER TABLE executions ADD COLUMN IF NOT EXISTS reflexions_injected TEXT[] DEFAULT '{}';

-- Incident-to-eval synthesis (DEC-067)
CREATE TABLE IF NOT EXISTS failure_cases (
    id SERIAL PRIMARY KEY,
    failure_case_id TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL DEFAULT '',
    workspace_id TEXT NOT NULL DEFAULT 'default',
    skill TEXT NOT NULL,
    execution_id TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'P0',
    input_summary JSONB,
    error_output JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_failure_cases_skill ON failure_cases(skill);
CREATE INDEX IF NOT EXISTS idx_failure_cases_domain ON failure_cases(domain);

-- Approval engine: pending tool calls stored per execution
ALTER TABLE executions ADD COLUMN IF NOT EXISTS pending_approvals JSONB DEFAULT '[]'::jsonb;

-- RBAC: track who triggered each execution
ALTER TABLE executions ADD COLUMN IF NOT EXISTS triggered_by VARCHAR(200) DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_executions_triggered_by ON executions(triggered_by);
"""


class PgStore:
    """PostgreSQL memory store with domain + workspace isolation."""

    def __init__(self, dsn: str | None = None, workspace_id: str = "default"):
        self._dsn = dsn or os.environ.get("DATABASE_URL", "")
        self._workspace_id = workspace_id or os.environ.get(
            "AGENTURA_WORKSPACE_ID", "default"
        )
        self._pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=self._dsn,
        )
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def _domain_from_skill(self, skill_path: str) -> str:
        return skill_path.split("/")[0] if "/" in skill_path else ""

    def _serialize_json(self, value: object) -> str | None:
        if value is None:
            return None
        return json.dumps(value)

    def _deserialize_row(self, row: dict) -> dict:
        d = dict(row)
        for field in ("input_summary", "output_summary", "original_output", "pending_approvals"):
            val = d.get(field)
            if isinstance(val, str):
                try:
                    d[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        for field in ("timestamp", "created_at"):
            val = d.get(field)
            if hasattr(val, "isoformat"):
                d[field] = val.isoformat()
        # Drop internal serial id
        d.pop("id", None)
        return d

    def log_execution(self, skill_path: str, data: dict) -> str:
        from uuid import uuid4
        execution_id = data.get(
            "execution_id",
            f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}",
        )
        domain = self._domain_from_skill(skill_path)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO executions
                       (execution_id, domain, workspace_id, skill, timestamp,
                        input_summary, output_summary, outcome, cost_usd,
                        latency_ms, model_used, triggered_by)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (execution_id) DO NOTHING""",
                    (
                        execution_id,
                        domain,
                        self._workspace_id,
                        skill_path,
                        data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        self._serialize_json(data.get("input_summary")),
                        self._serialize_json(data.get("output_summary")),
                        data.get("outcome", "pending_review"),
                        data.get("cost_usd", 0.0),
                        data.get("latency_ms", 0.0),
                        data.get("model_used", ""),
                        data.get("triggered_by", ""),
                    ),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return execution_id

    def get_execution_by_id(self, execution_id: str) -> dict | None:
        """Single-row SELECT by execution_id. Returns deserialized row or None."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM executions WHERE execution_id = %s AND workspace_id = %s",
                    (execution_id, self._workspace_id),
                )
                row = cur.fetchone()
                return self._deserialize_row(row) if row else None
        finally:
            self._pool.putconn(conn)

    def approve_execution_atomic(
        self, execution_id: str, new_outcome: str, reviewer_notes: str = ""
    ) -> tuple[str, dict | None]:
        """Atomic compare-and-swap: only updates if current outcome is pending_approval.

        Returns:
            ("approved"|"rejected", row) — success
            ("already_processed", row) — idempotent: already in target state
            ("wrong_state", row) — execution exists but in unexpected state
            ("not_found", None) — no such execution
        """
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Atomic CAS: only update if currently pending_approval
                cur.execute(
                    """UPDATE executions
                       SET outcome = %s, reviewer_notes = %s
                       WHERE execution_id = %s AND workspace_id = %s AND outcome = 'pending_approval'
                       RETURNING *""",
                    (new_outcome, reviewer_notes, execution_id, self._workspace_id),
                )
                row = cur.fetchone()
                if row:
                    conn.commit()
                    return (new_outcome, self._deserialize_row(row))

                # CAS failed — check why
                conn.rollback()
                cur.execute(
                    "SELECT * FROM executions WHERE execution_id = %s AND workspace_id = %s",
                    (execution_id, self._workspace_id),
                )
                existing = cur.fetchone()
                if not existing:
                    return ("not_found", None)

                existing_row = self._deserialize_row(existing)
                if existing_row.get("outcome") == new_outcome:
                    return ("already_processed", existing_row)
                return ("wrong_state", existing_row)
        finally:
            self._pool.putconn(conn)

    def update_execution_output(self, execution_id: str, output_summary: object, outcome: str | None = None) -> bool:
        """Update output_summary (and optionally outcome) for an execution. Returns True if found."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                if outcome:
                    cur.execute(
                        "UPDATE executions SET output_summary = %s, outcome = %s WHERE execution_id = %s AND workspace_id = %s",
                        (self._serialize_json(output_summary), outcome, execution_id, self._workspace_id),
                    )
                else:
                    cur.execute(
                        "UPDATE executions SET output_summary = %s WHERE execution_id = %s AND workspace_id = %s",
                        (self._serialize_json(output_summary), execution_id, self._workspace_id),
                    )
            conn.commit()
            return cur.rowcount > 0
        finally:
            self._pool.putconn(conn)

    def update_execution_pending_approvals(self, execution_id: str, pending_approvals: list[dict]) -> bool:
        """Store pending_approvals JSON array for an execution."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE executions SET pending_approvals = %s WHERE execution_id = %s AND workspace_id = %s",
                    (self._serialize_json(pending_approvals), execution_id, self._workspace_id),
                )
            conn.commit()
            return cur.rowcount > 0
        finally:
            self._pool.putconn(conn)

    def add_correction(self, skill_path: str, data: dict) -> str:
        domain = self._domain_from_skill(skill_path)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM corrections WHERE skill = %s",
                    (skill_path,),
                )
                count = cur.fetchone()[0]
                correction_id = data.get("correction_id", f"CORR-{count + 1:03d}")
                cur.execute(
                    """INSERT INTO corrections
                       (correction_id, domain, workspace_id, skill, execution_id,
                        timestamp, original_output, user_correction)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (correction_id) DO NOTHING""",
                    (
                        correction_id,
                        domain,
                        self._workspace_id,
                        skill_path,
                        data.get("execution_id", ""),
                        data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        self._serialize_json(data.get("original_output")),
                        data.get("user_correction", ""),
                    ),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return correction_id

    def add_reflexion(self, skill_path: str, data: dict) -> str:
        domain = self._domain_from_skill(skill_path)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM reflexions WHERE skill = %s",
                    (skill_path,),
                )
                count = cur.fetchone()[0]
                reflexion_id = data.get("reflexion_id", f"REFL-{count + 1:03d}")
                cur.execute(
                    """INSERT INTO reflexions
                       (reflexion_id, domain, workspace_id, skill, correction_id,
                        created_at, rule, applies_when, confidence, validated_by_test)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (reflexion_id) DO NOTHING""",
                    (
                        reflexion_id,
                        domain,
                        self._workspace_id,
                        skill_path,
                        data.get("correction_id", ""),
                        data.get(
                            "created_at", datetime.now(timezone.utc).isoformat()
                        ),
                        data.get("rule", ""),
                        data.get("applies_when", ""),
                        data.get("confidence", 0.0),
                        data.get("validated_by_test", False),
                    ),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return reflexion_id

    def get_reflexions(self, skill_path: str) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                cur.execute(
                    "SELECT * FROM reflexions WHERE skill = %s AND workspace_id = %s ORDER BY created_at",
                    (skill_path, self._workspace_id),
                )
                return [self._deserialize_row(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def search_similar(
        self, skill_path: str, query: str, limit: int = 5
    ) -> list[dict]:
        """Text-based search on reflexion rules (no vector search in PG)."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                cur.execute(
                    """SELECT * FROM reflexions
                       WHERE skill = %s AND workspace_id = %s
                         AND (rule ILIKE %s OR applies_when ILIKE %s)
                       ORDER BY confidence DESC LIMIT %s""",
                    (
                        skill_path,
                        self._workspace_id,
                        f"%{query}%",
                        f"%{query}%",
                        limit,
                    ),
                )
                return [self._deserialize_row(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def get_executions(self, skill_path: str | None = None, triggered_by: str | None = None) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                conditions = ["workspace_id = %s"]
                params: list[object] = [self._workspace_id]
                if skill_path:
                    conditions.append("skill = %s")
                    params.append(skill_path)
                if triggered_by:
                    conditions.append("triggered_by = %s")
                    params.append(triggered_by)
                query = f"SELECT * FROM executions WHERE {' AND '.join(conditions)} ORDER BY timestamp DESC"
                cur.execute(query, params)
                return [self._deserialize_row(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def get_corrections(self, skill_path: str | None = None) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                if skill_path:
                    cur.execute(
                        "SELECT * FROM corrections WHERE skill = %s AND workspace_id = %s ORDER BY timestamp DESC",
                        (skill_path, self._workspace_id),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM corrections WHERE workspace_id = %s ORDER BY timestamp DESC",
                        (self._workspace_id,),
                    )
                return [self._deserialize_row(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def get_all_reflexions(self) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                cur.execute(
                    "SELECT * FROM reflexions WHERE workspace_id = %s ORDER BY created_at",
                    (self._workspace_id,),
                )
                return [self._deserialize_row(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def update_reflexion(self, reflexion_id: str, updates: dict) -> None:
        if not updates:
            return
        allowed = {"rule", "applies_when", "confidence", "validated_by_test",
                   "utility_score", "times_injected", "times_helped", "source"}
        set_parts = []
        values: list[object] = []
        for key, value in updates.items():
            if key in allowed:
                set_parts.append(f"{key} = %s")
                values.append(value)
        if not set_parts:
            return
        values.append(reflexion_id)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE reflexions SET {', '.join(set_parts)} WHERE reflexion_id = %s",
                    values,
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    # --- MemRL: utility-scored memory (DEC-066) ---

    def record_reflexion_injection(self, execution_id: str, reflexion_ids: list[str]) -> None:
        """Record which reflexions were injected into an execution and increment times_injected."""
        if not reflexion_ids:
            return
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE executions SET reflexions_injected = %s WHERE execution_id = %s",
                    (reflexion_ids, execution_id),
                )
                for rid in reflexion_ids:
                    cur.execute(
                        "UPDATE reflexions SET times_injected = times_injected + 1 WHERE reflexion_id = %s",
                        (rid,),
                    )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def record_execution_success(self, execution_id: str) -> None:
        """Increment times_helped for reflexions injected into a successful execution, recalc utility."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT reflexions_injected FROM executions WHERE execution_id = %s",
                    (execution_id,),
                )
                row = cur.fetchone()
                if not row:
                    return
                injected = row.get("reflexions_injected") or []
                if not injected:
                    return
                for rid in injected:
                    cur.execute(
                        """UPDATE reflexions
                           SET times_helped = times_helped + 1,
                               utility_score = (times_helped + 1 + 2)::REAL / (times_injected + 4)::REAL,
                               last_scored_at = NOW()
                           WHERE reflexion_id = %s""",
                        (rid,),
                    )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_top_reflexions(self, skill_path: str, limit: int = 5, min_score: float = 0.3) -> list[dict]:
        """Retrieve reflexions sorted by utility score (Bayesian: (h+2)/(n+4))."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT * FROM reflexions
                       WHERE skill = %s AND workspace_id = %s AND utility_score >= %s
                       ORDER BY utility_score DESC, confidence DESC
                       LIMIT %s""",
                    (skill_path, self._workspace_id, min_score, limit),
                )
                return [self._deserialize_row(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def decay_stale_reflexions(self, days: int = 30) -> int:
        """Multiply utility_score by 0.9 for reflexions not scored in `days` days. Returns count updated."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE reflexions
                       SET utility_score = utility_score * 0.9,
                           last_scored_at = NOW()
                       WHERE (last_scored_at IS NULL OR last_scored_at < NOW() - INTERVAL '%s days')
                         AND times_injected > 0""",
                    (days,),
                )
                count = cur.rowcount
            conn.commit()
            return count
        finally:
            self._pool.putconn(conn)

    # --- Incident-to-eval: failure case storage (DEC-067) ---

    def log_failure_case(self, skill_path: str, data: dict) -> str:
        """Store a failure case for automatic test generation."""
        domain = self._domain_from_skill(skill_path)
        failure_case_id = data.get(
            "failure_case_id",
            f"FAIL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        )
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO failure_cases
                       (failure_case_id, domain, workspace_id, skill, execution_id,
                        severity, input_summary, error_output)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (failure_case_id) DO NOTHING""",
                    (
                        failure_case_id,
                        domain,
                        self._workspace_id,
                        skill_path,
                        data.get("execution_id", ""),
                        data.get("severity", "P0"),
                        self._serialize_json(data.get("input_summary")),
                        self._serialize_json(data.get("error_output")),
                    ),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return failure_case_id
