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
        for field in ("input_summary", "output_summary", "original_output"):
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
        execution_id = data.get(
            "execution_id",
            f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        )
        domain = self._domain_from_skill(skill_path)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO executions
                       (execution_id, domain, workspace_id, skill, timestamp,
                        input_summary, output_summary, outcome, cost_usd,
                        latency_ms, model_used)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    ),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return execution_id

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

    def get_executions(self, skill_path: str | None = None) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                if skill_path:
                    cur.execute(
                        "SELECT * FROM executions WHERE skill = %s AND workspace_id = %s ORDER BY timestamp DESC",
                        (skill_path, self._workspace_id),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM executions WHERE workspace_id = %s ORDER BY timestamp DESC",
                        (self._workspace_id,),
                    )
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
        allowed = {"rule", "applies_when", "confidence", "validated_by_test"}
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
