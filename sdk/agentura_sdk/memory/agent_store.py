"""Agent registry store — tracks agent identities and org hierarchy in PostgreSQL."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import psycopg2.pool

AGENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    domain TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'specialist',
    executor TEXT DEFAULT '',
    model TEXT DEFAULT '',
    reports_to TEXT REFERENCES agents(id),
    status TEXT NOT NULL DEFAULT 'idle',
    soul TEXT DEFAULT '',
    heartbeat_schedule TEXT DEFAULT '',
    config JSONB DEFAULT '{}',
    skills JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agents_domain ON agents(domain);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_reports_to ON agents(reports_to);
"""


class AgentStore:
    """PostgreSQL store for agent registry."""

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
                cur.execute(AGENT_SCHEMA)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def _serialize(self, value: object) -> str | None:
        if value is None:
            return None
        return json.dumps(value)

    def _row_to_dict(self, row: dict) -> dict:
        d = dict(row)
        for field in ("config", "skills"):
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
        return d

    def create_agent(
        self,
        name: str,
        display_name: str = "",
        domain: str = "",
        role: str = "specialist",
        executor: str = "",
        model: str = "",
        reports_to: str | None = None,
        status: str = "idle",
        soul: str = "",
        heartbeat_schedule: str = "",
        config: dict | None = None,
        skills: list | None = None,
    ) -> str:
        agent_id = uuid.uuid4().hex[:12]
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO agents
                       (id, name, display_name, domain, role, executor, model,
                        reports_to, status, soul, heartbeat_schedule, config, skills)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        domain = EXCLUDED.domain,
                        role = EXCLUDED.role,
                        executor = EXCLUDED.executor,
                        model = EXCLUDED.model,
                        reports_to = EXCLUDED.reports_to,
                        soul = EXCLUDED.soul,
                        heartbeat_schedule = EXCLUDED.heartbeat_schedule,
                        config = EXCLUDED.config,
                        skills = EXCLUDED.skills,
                        updated_at = NOW()
                       RETURNING id""",
                    (agent_id, name, display_name, domain, role, executor, model,
                     reports_to, status, soul, heartbeat_schedule,
                     self._serialize(config or {}), self._serialize(skills or [])),
                )
                result = cur.fetchone()
                if result:
                    agent_id = result[0]
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return agent_id

    def get_agent(self, agent_id: str) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM agents WHERE id = %s", (agent_id,))
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def get_agent_by_name(self, name: str) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM agents WHERE name = %s", (name,))
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def list_agents(
        self,
        domain: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conditions = ["status != 'terminated'"]
                values: list[object] = []
                if domain:
                    conditions.append("domain = %s")
                    values.append(domain)
                if status:
                    conditions.append("status = %s")
                    values.append(status)
                where = " AND ".join(conditions)
                cur.execute(
                    f"SELECT * FROM agents WHERE {where} ORDER BY domain, name",
                    values,
                )
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def update_agent(self, agent_id: str, **fields: object) -> None:
        allowed = {
            "display_name", "domain", "role", "executor", "model",
            "reports_to", "status", "soul", "heartbeat_schedule",
            "config", "skills",
        }
        parts = ["updated_at = NOW()"]
        values: list[object] = []
        for key, val in fields.items():
            if key not in allowed:
                continue
            if key in ("config", "skills"):
                val = self._serialize(val)
            parts.append(f"{key} = %s")
            values.append(val)
        if len(parts) == 1:
            return
        values.append(agent_id)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE agents SET {', '.join(parts)} WHERE id = %s",
                    values,
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def delete_agent(self, agent_id: str) -> None:
        """Soft delete — sets status to terminated."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE agents SET status = 'terminated', updated_at = NOW() WHERE id = %s",
                    (agent_id,),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_org_tree(self) -> list[dict]:
        """Recursive CTE to build the full org chart."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    WITH RECURSIVE org_tree AS (
                        SELECT id, name, display_name, domain, role, reports_to,
                               status, executor, model, skills, config, 0 as depth
                        FROM agents
                        WHERE reports_to IS NULL AND status != 'terminated'
                        UNION ALL
                        SELECT a.id, a.name, a.display_name, a.domain, a.role,
                               a.reports_to, a.status, a.executor, a.model,
                               a.skills, a.config, t.depth + 1
                        FROM agents a JOIN org_tree t ON a.reports_to = t.id
                        WHERE a.status != 'terminated'
                    )
                    SELECT * FROM org_tree ORDER BY depth, domain, name
                """)
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)
