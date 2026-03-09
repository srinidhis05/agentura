"""Ticket store — tracks work items and audit traces in PostgreSQL."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import psycopg2.pool

TICKET_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL DEFAULT '',
    assigned_to TEXT REFERENCES agents(id),
    created_by TEXT REFERENCES agents(id),
    status TEXT NOT NULL DEFAULT 'open',
    priority INTEGER DEFAULT 3,
    input_data JSONB DEFAULT '{}',
    result JSONB,
    parent_id TEXT REFERENCES tickets(id),
    execution_id TEXT DEFAULT '',
    trace_log JSONB DEFAULT '[]',
    cost_usd REAL DEFAULT 0.0,
    checked_out_by TEXT,
    checked_out_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_tickets_domain ON tickets(domain);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tickets_parent ON tickets(parent_id);
"""

TICKET_MIGRATION_V2 = """
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS checked_out_by TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS checked_out_at TIMESTAMPTZ;
"""


class TicketStore:
    """PostgreSQL store for ticket tracking."""

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
                cur.execute(TICKET_SCHEMA)
                cur.execute(TICKET_MIGRATION_V2)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def _serialize(self, value: object) -> str | None:
        if value is None:
            return None
        return json.dumps(value)

    def _row_to_dict(self, row: dict) -> dict:
        d = dict(row)
        for field in ("input_data", "result", "trace_log"):
            val = d.get(field)
            if isinstance(val, str):
                try:
                    d[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        for field in ("created_at", "updated_at", "resolved_at"):
            val = d.get(field)
            if hasattr(val, "isoformat"):
                d[field] = val.isoformat()
        return d

    def create_ticket(
        self,
        title: str,
        domain: str = "",
        assigned_to: str | None = None,
        created_by: str | None = None,
        priority: int = 3,
        input_data: dict | None = None,
        parent_id: str | None = None,
        execution_id: str = "",
    ) -> str:
        ticket_id = f"tkt-{uuid.uuid4().hex[:12]}"
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO tickets
                       (id, title, domain, assigned_to, created_by, status,
                        priority, input_data, parent_id, execution_id)
                       VALUES (%s, %s, %s, %s, %s, 'open', %s, %s, %s, %s)""",
                    (ticket_id, title, domain, assigned_to, created_by,
                     priority, self._serialize(input_data or {}),
                     parent_id, execution_id),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return ticket_id

    def get_ticket(self, ticket_id: str) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def list_tickets(
        self,
        domain: str | None = None,
        status: str | None = None,
        assigned_to: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                conditions: list[str] = []
                values: list[object] = []
                if domain:
                    conditions.append("domain = %s")
                    values.append(domain)
                if status:
                    conditions.append("status = %s")
                    values.append(status)
                if assigned_to:
                    conditions.append("assigned_to = %s")
                    values.append(assigned_to)
                where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                values.append(limit)
                cur.execute(
                    f"SELECT * FROM tickets {where} ORDER BY priority, created_at DESC LIMIT %s",
                    values,
                )
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def update_ticket(self, ticket_id: str, **fields: object) -> None:
        allowed = {
            "title", "assigned_to", "status", "priority",
            "result", "execution_id", "cost_usd",
        }
        parts = ["updated_at = NOW()"]
        values: list[object] = []
        for key, val in fields.items():
            if key not in allowed:
                continue
            if key == "result":
                val = self._serialize(val)
            parts.append(f"{key} = %s")
            values.append(val)
        # Auto-set resolved_at when status changes to resolved
        if fields.get("status") in ("resolved", "cancelled"):
            parts.append("resolved_at = NOW()")
        if len(parts) == 1:
            return
        values.append(ticket_id)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE tickets SET {', '.join(parts)} WHERE id = %s",
                    values,
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def add_trace_entry(self, ticket_id: str, entry: dict) -> None:
        """Append an immutable trace entry to the ticket's trace_log."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE tickets
                       SET trace_log = trace_log || %s::jsonb,
                           updated_at = NOW()
                       WHERE id = %s""",
                    (json.dumps([entry]), ticket_id),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_sub_tickets(self, parent_id: str) -> list[dict]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM tickets WHERE parent_id = %s ORDER BY created_at",
                    (parent_id,),
                )
                return [self._row_to_dict(row) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def checkout_ticket(
        self,
        agent_id: str,
        domain: str | None = None,
        ticket_id: str | None = None,
    ) -> dict | None:
        """Atomically claim the next available ticket using FOR UPDATE SKIP LOCKED.

        If ticket_id is provided, attempts to check out that specific ticket.
        Otherwise picks the highest-priority open ticket in the domain.
        Returns the checked-out ticket or None if nothing available.
        """
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if ticket_id:
                    # Attempt to lock a specific ticket
                    cur.execute(
                        """SELECT * FROM tickets
                           WHERE id = %s
                             AND status = 'open'
                             AND checked_out_by IS NULL
                           FOR UPDATE SKIP LOCKED""",
                        (ticket_id,),
                    )
                else:
                    # Pick next available by priority
                    conditions = ["status = 'open'", "checked_out_by IS NULL"]
                    values: list[object] = []
                    if domain:
                        conditions.append("domain = %s")
                        values.append(domain)
                    where = " AND ".join(conditions)
                    cur.execute(
                        f"""SELECT * FROM tickets
                            WHERE {where}
                            ORDER BY priority ASC, created_at ASC
                            LIMIT 1
                            FOR UPDATE SKIP LOCKED""",
                        values,
                    )

                row = cur.fetchone()
                if not row:
                    conn.commit()
                    return None

                # Claim it
                cur.execute(
                    """UPDATE tickets
                       SET checked_out_by = %s,
                           checked_out_at = NOW(),
                           status = 'in_progress',
                           updated_at = NOW()
                       WHERE id = %s""",
                    (agent_id, row["id"]),
                )
                conn.commit()

                ticket = self._row_to_dict(row)
                ticket["checked_out_by"] = agent_id
                ticket["status"] = "in_progress"
                return ticket
        finally:
            self._pool.putconn(conn)

    def release_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """Release a checked-out ticket back to the open pool.

        Only the agent who checked it out can release it.
        Returns True if released, False if not found or not owned.
        """
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE tickets
                       SET checked_out_by = NULL,
                           checked_out_at = NULL,
                           status = 'open',
                           updated_at = NOW()
                       WHERE id = %s AND checked_out_by = %s""",
                    (ticket_id, agent_id),
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            self._pool.putconn(conn)

    def get_ticket_stats(self, domain: str | None = None) -> dict:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                domain_filter = ""
                values: list[object] = []
                if domain:
                    domain_filter = "WHERE domain = %s"
                    values.append(domain)
                cur.execute(
                    f"""SELECT
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'open') as open,
                        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
                        COUNT(*) FILTER (WHERE status = 'escalated') as escalated,
                        COALESCE(SUM(cost_usd), 0) as total_cost_usd
                    FROM tickets {domain_filter}""",
                    values,
                )
                stats = dict(cur.fetchone())
                # By domain breakdown
                cur.execute(
                    """SELECT domain, COUNT(*) as count
                       FROM tickets GROUP BY domain ORDER BY domain""",
                )
                stats["by_domain"] = {
                    row["domain"]: row["count"] for row in cur.fetchall()
                }
                # By agent breakdown
                cur.execute(
                    """SELECT assigned_to, COUNT(*) as count
                       FROM tickets WHERE assigned_to IS NOT NULL
                       GROUP BY assigned_to""",
                )
                stats["by_agent"] = {
                    row["assigned_to"]: row["count"] for row in cur.fetchall()
                }
                return stats
        finally:
            self._pool.putconn(conn)
