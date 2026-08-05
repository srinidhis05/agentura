"""Seat identity store — persistent agent identity + append-only event ledger (PostgreSQL)."""
from __future__ import annotations

import json
import os
import uuid

import psycopg2
import psycopg2.extras
import psycopg2.pool

SEAT_SCHEMA = """
CREATE TABLE IF NOT EXISTS seats (
    id            TEXT PRIMARY KEY,
    name          TEXT UNIQUE NOT NULL,
    role          TEXT NOT NULL DEFAULT '',
    domain        TEXT NOT NULL DEFAULT '',
    pronouns      TEXT NOT NULL DEFAULT 'they/them',
    current_model TEXT DEFAULT '',
    renamed_from  TEXT DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'active',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS seat_events (
    id         BIGSERIAL PRIMARY KEY,
    seat_id    TEXT NOT NULL REFERENCES seats(id),
    session_id TEXT,
    type       TEXT NOT NULL,
    model      TEXT DEFAULT '',
    payload    JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_seat_events_seat ON seat_events(seat_id, created_at);
"""


class SeatStore:
    """PostgreSQL store for seat identity + append-only event ledger."""

    def __init__(self, dsn: str | None = None):
        self._dsn = dsn or os.environ.get("DATABASE_URL", "")
        self._pool = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=10, dsn=self._dsn)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(SEAT_SCHEMA)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_or_create_seat(self, name, role="", domain="", pronouns="they/them", model="") -> str:
        seat_id = uuid.uuid4().hex[:12]
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO seats (id, name, role, domain, pronouns, current_model)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (name) DO UPDATE SET
                         role = EXCLUDED.role,
                         domain = EXCLUDED.domain,
                         current_model = COALESCE(NULLIF(EXCLUDED.current_model, ''), seats.current_model)
                       RETURNING id""",
                    (seat_id, name, role, domain, pronouns, model),
                )
                row = cur.fetchone()
                if row:
                    seat_id = row[0]
            conn.commit()
        finally:
            self._pool.putconn(conn)
        return seat_id

    def get_seat(self, seat_id) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM seats WHERE id = %s", (seat_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def get_seat_by_name(self, name) -> dict | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM seats WHERE name = %s", (name,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            self._pool.putconn(conn)

    def append_event(self, seat_id, event_type, session_id=None, model="", payload=None) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO seat_events (seat_id, session_id, type, model, payload)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (seat_id, session_id, event_type, model, json.dumps(payload or {})),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_track_record(self, seat_id) -> dict:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT
                         count(*) FILTER (WHERE type IN ('session_completed','session_failed')) AS runs,
                         count(*) FILTER (WHERE type = 'session_completed') AS successes,
                         count(*) FILTER (WHERE type = 'gate_passed') AS gate_pass,
                         count(*) FILTER (WHERE type IN ('gate_passed','gate_failed')) AS gate_total,
                         avg((payload->>'cost_usd')::float)
                           FILTER (WHERE type IN ('session_completed','session_failed')) AS avg_cost,
                         avg((payload->>'latency_ms')::float)
                           FILTER (WHERE type IN ('session_completed','session_failed')) AS avg_latency,
                         avg((payload->>'rating')::float) FILTER (WHERE type = 'rating') AS avg_rating
                       FROM seat_events WHERE seat_id = %s""",
                    (seat_id,),
                )
                agg = cur.fetchone() or {}
                cur.execute(
                    """SELECT payload, created_at FROM seat_events
                       WHERE seat_id = %s AND type = 'session_completed'
                       ORDER BY created_at DESC LIMIT 3""",
                    (seat_id,),
                )
                wins = [dict(r) for r in cur.fetchall()]
        finally:
            self._pool.putconn(conn)
        runs = agg.get("runs") or 0
        gate_total = agg.get("gate_total") or 0
        return {
            "runs": runs,
            "success_rate": (agg.get("successes") or 0) / runs if runs else 0.0,
            "avg_cost_usd": float(agg.get("avg_cost") or 0.0),
            "avg_latency_ms": float(agg.get("avg_latency") or 0.0),
            "gate_pass_rate": (agg.get("gate_pass") or 0) / gate_total if gate_total else 0.0,
            "avg_rating": float(agg.get("avg_rating") or 0.0),
            "recent_wins": wins,
        }

    def rename_seat(self, seat_id, new_name) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM seats WHERE id = %s", (seat_id,))
                row = cur.fetchone()
                old = row[0] if row else ""
                cur.execute(
                    "UPDATE seats SET renamed_from = %s, name = %s WHERE id = %s",
                    (old, new_name, seat_id),
                )
                cur.execute(
                    "INSERT INTO seat_events (seat_id, type, payload) VALUES (%s, 'renamed', %s)",
                    (seat_id, json.dumps({"from": old, "to": new_name})),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)


_SEAT_STORE = None


def get_seat_store():
    """Lazy module-level singleton reused across calls. Returns None if DB unavailable."""
    global _SEAT_STORE
    if _SEAT_STORE is None:
        try:
            _SEAT_STORE = SeatStore()
        except Exception:
            return None
    return _SEAT_STORE
