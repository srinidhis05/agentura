"""Fleet session store — tracks parallel pipeline executions in PostgreSQL."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

import psycopg2
import psycopg2.extras
import psycopg2.pool

FLEET_SCHEMA = """
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
"""


class FleetStore:
    """PostgreSQL store for fleet session tracking."""

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
                cur.execute(FLEET_SCHEMA)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def _serialize(self, value: object) -> str | None:
        if value is None:
            return None
        return json.dumps(value)

    def _row_to_dict(self, row: dict) -> dict:
        d = dict(row)
        for field in ("input_data", "output"):
            val = d.get(field)
            if isinstance(val, str):
                try:
                    d[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        for field in ("created_at", "updated_at"):
            val = d.get(field)
            if hasattr(val, "isoformat"):
                d[field] = val.isoformat()
        d.pop("id", None)
        return d

    def create_session(
        self,
        pipeline_name: str,
        trigger_type: str = "manual",
        repo: str = "",
        pr_number: int = 0,
        pr_url: str = "",
        head_sha: str = "",
        total_agents: int = 0,
        input_data: dict | None = None,
    ) -> str:
        session_id = f"fleet-{uuid.uuid4().hex[:12]}"
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO fleet_sessions
                       (session_id, pipeline_name, trigger_type, repo, pr_number,
                        pr_url, head_sha, status, total_agents, input_data)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)""",
                    (session_id, pipeline_name, trigger_type, repo, pr_number,
                     pr_url, head_sha, total_agents, self._serialize(input_data)),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return session_id

    def create_agent(
        self,
        session_id: str,
        agent_id: str,
        skill_path: str,
    ) -> str:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO fleet_agents
                       (agent_id, session_id, skill_path, status)
                       VALUES (%s, %s, %s, 'pending')""",
                    (agent_id, session_id, skill_path),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return agent_id

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        execution_id: str = "",
        pod_name: str = "",
        success: bool = False,
        output: dict | None = None,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        error_message: str = "",
    ) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE fleet_agents SET
                       status = %s, execution_id = %s, pod_name = %s,
                       success = %s, output = %s, cost_usd = %s,
                       latency_ms = %s, error_message = %s,
                       updated_at = NOW()
                       WHERE agent_id = %s""",
                    (status, execution_id, pod_name, success,
                     self._serialize(output), cost_usd, latency_ms,
                     error_message, agent_id),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def update_session_status(
        self,
        session_id: str,
        status: str,
        completed_agents: int | None = None,
        failed_agents: int | None = None,
        total_cost_usd: float | None = None,
        github_check_posted: bool | None = None,
    ) -> None:
        parts = ["status = %s", "updated_at = NOW()"]
        values: list[object] = [status]
        if completed_agents is not None:
            parts.append("completed_agents = %s")
            values.append(completed_agents)
        if failed_agents is not None:
            parts.append("failed_agents = %s")
            values.append(failed_agents)
        if total_cost_usd is not None:
            parts.append("total_cost_usd = %s")
            values.append(total_cost_usd)
        if github_check_posted is not None:
            parts.append("github_check_posted = %s")
            values.append(github_check_posted)
        values.append(session_id)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE fleet_sessions SET {', '.join(parts)} WHERE session_id = %s",
                    values,
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_session(self, session_id: str) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM fleet_sessions WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def get_session_agents(self, session_id: str) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM fleet_agents WHERE session_id = %s ORDER BY created_at",
                    (session_id,),
                )
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def list_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if status and status != "all":
                    cur.execute(
                        "SELECT * FROM fleet_sessions WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                        (status, limit),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM fleet_sessions ORDER BY created_at DESC LIMIT %s",
                        (limit,),
                    )
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def timeout_stale_sessions(self, timeout_minutes: int = 15) -> int:
        """Mark stale 'running' or 'pending' sessions as 'timed_out'.

        Sessions stuck in running/pending for longer than timeout_minutes
        are zombies from crashed/restarted executors. Mark them as timed_out
        and update their agents too.

        Returns the number of sessions timed out.
        """
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                # Timeout stale sessions
                cur.execute(
                    """UPDATE fleet_sessions
                       SET status = 'timed_out', updated_at = NOW()
                       WHERE status IN ('running', 'pending')
                         AND created_at < NOW() - INTERVAL '%s minutes'
                       RETURNING session_id""",
                    (timeout_minutes,),
                )
                timed_out = cur.fetchall()
                session_ids = [row[0] for row in timed_out]

                # Also timeout their agents
                if session_ids:
                    cur.execute(
                        """UPDATE fleet_agents
                           SET status = 'timed_out', updated_at = NOW()
                           WHERE session_id = ANY(%s)
                             AND status IN ('running', 'pending')""",
                        (session_ids,),
                    )

            conn.commit()

            if session_ids:
                logger.info("timed out %d stale fleet sessions: %s",
                            len(session_ids), session_ids[:5])
            return len(session_ids)
        finally:
            self._pool.putconn(conn)
