"""Heartbeat run store — tracks scheduled agent executions in PostgreSQL."""

from __future__ import annotations

import json
import os
import uuid

import psycopg2
import psycopg2.extras
import psycopg2.pool

HEARTBEAT_SCHEMA = """
CREATE TABLE IF NOT EXISTS heartbeat_runs (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    agent_name TEXT NOT NULL DEFAULT '',
    ticket_id TEXT REFERENCES tickets(id),
    status TEXT NOT NULL DEFAULT 'running',
    trigger TEXT NOT NULL DEFAULT 'schedule',
    cost_usd REAL DEFAULT 0.0,
    summary TEXT DEFAULT '',
    error_message TEXT DEFAULT '',
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cached_tokens INTEGER DEFAULT 0,
    model TEXT DEFAULT '',
    transcript JSONB DEFAULT '[]'::jsonb,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_heartbeat_agent ON heartbeat_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_heartbeat_status ON heartbeat_runs(status);
"""

HEARTBEAT_MIGRATION = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='heartbeat_runs' AND column_name='input_tokens') THEN
        ALTER TABLE heartbeat_runs ADD COLUMN input_tokens INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='heartbeat_runs' AND column_name='output_tokens') THEN
        ALTER TABLE heartbeat_runs ADD COLUMN output_tokens INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='heartbeat_runs' AND column_name='cached_tokens') THEN
        ALTER TABLE heartbeat_runs ADD COLUMN cached_tokens INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='heartbeat_runs' AND column_name='model') THEN
        ALTER TABLE heartbeat_runs ADD COLUMN model TEXT DEFAULT '';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='heartbeat_runs' AND column_name='transcript') THEN
        ALTER TABLE heartbeat_runs ADD COLUMN transcript JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;
"""


class HeartbeatStore:
    """PostgreSQL store for heartbeat run tracking."""

    def __init__(self, dsn: str | None = None):
        self._dsn = dsn or os.environ.get("DATABASE_URL", "")
        self._pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2, maxconn=10, dsn=self._dsn,
        )
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(HEARTBEAT_SCHEMA)
                cur.execute(HEARTBEAT_MIGRATION)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def _row_to_dict(self, row: dict) -> dict:
        d = dict(row)
        for field in ("started_at", "completed_at"):
            val = d.get(field)
            if hasattr(val, "isoformat"):
                d[field] = val.isoformat()
        # Ensure transcript is always a list (handle None from old rows)
        if "transcript" in d and d["transcript"] is None:
            d["transcript"] = []
        # Default new columns for old rows missing them
        d.setdefault("input_tokens", 0)
        d.setdefault("output_tokens", 0)
        d.setdefault("cached_tokens", 0)
        d.setdefault("model", "")
        d.setdefault("transcript", [])
        return d

    def create_run(
        self,
        agent_id: str,
        agent_name: str = "",
        ticket_id: str | None = None,
        trigger: str = "schedule",
    ) -> str:
        run_id = f"hb-{uuid.uuid4().hex[:12]}"
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO heartbeat_runs
                       (id, agent_id, agent_name, ticket_id, status, trigger)
                       VALUES (%s, %s, %s, %s, 'running', %s)""",
                    (run_id, agent_id, agent_name, ticket_id, trigger),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return run_id

    def complete_run(
        self,
        run_id: str,
        status: str = "completed",
        cost_usd: float = 0.0,
        summary: str = "",
        error_message: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        model: str = "",
    ) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE heartbeat_runs SET
                       status = %s, cost_usd = %s, summary = %s,
                       error_message = %s, input_tokens = %s,
                       output_tokens = %s, cached_tokens = %s,
                       model = %s, completed_at = NOW()
                       WHERE id = %s""",
                    (
                        status, cost_usd, summary, error_message,
                        input_tokens, output_tokens, cached_tokens,
                        model, run_id,
                    ),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def append_transcript(
        self,
        run_id: str,
        entry: dict,
    ) -> None:
        """Append a single transcript entry to a running heartbeat."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE heartbeat_runs
                       SET transcript = transcript || %s::jsonb
                       WHERE id = %s""",
                    (json.dumps([entry]), run_id),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def list_runs(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conditions: list[str] = []
                values: list[object] = []
                if agent_id:
                    conditions.append("agent_id = %s")
                    values.append(agent_id)
                if status:
                    conditions.append("status = %s")
                    values.append(status)
                where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                values.append(limit)
                cur.execute(
                    f"SELECT * FROM heartbeat_runs {where} ORDER BY started_at DESC LIMIT %s",
                    values,
                )
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def get_run(self, run_id: str) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM heartbeat_runs WHERE id = %s", (run_id,))
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def get_latest_run(self, agent_id: str) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT * FROM heartbeat_runs
                       WHERE agent_id = %s
                       ORDER BY started_at DESC LIMIT 1""",
                    (agent_id,),
                )
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def get_schedule(self) -> list[dict]:
        """Return all agents with heartbeat schedules and their latest run."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.id as agent_id, a.name as agent_name,
                           a.heartbeat_schedule, a.status as agent_status,
                           h.id as last_run_id, h.status as last_run_status,
                           h.started_at as last_run_at, h.cost_usd as last_cost_usd
                    FROM agents a
                    LEFT JOIN LATERAL (
                        SELECT * FROM heartbeat_runs hr
                        WHERE hr.agent_id = a.id
                        ORDER BY hr.started_at DESC LIMIT 1
                    ) h ON true
                    WHERE a.heartbeat_schedule != '' AND a.status != 'terminated'
                    ORDER BY a.domain, a.name
                """)
                rows = []
                for row in cur.fetchall():
                    d = dict(row)
                    for f in ("last_run_at",):
                        val = d.get(f)
                        if hasattr(val, "isoformat"):
                            d[f] = val.isoformat()
                    rows.append(d)
                return rows
        finally:
            self._pool.putconn(conn)
