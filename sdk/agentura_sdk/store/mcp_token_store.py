"""CRUD store for per-user OAuth tokens used by MCP server connections."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

_logger = logging.getLogger("agentura.mcp_token_store")

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS mcp_user_tokens (
    id SERIAL PRIMARY KEY,
    user_identifier VARCHAR(200) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    scope TEXT,
    client_id VARCHAR(200),
    client_secret VARCHAR(200),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_identifier, provider)
);
CREATE INDEX IF NOT EXISTS idx_mcp_user_tokens_user ON mcp_user_tokens(user_identifier);
CREATE INDEX IF NOT EXISTS idx_mcp_user_tokens_provider ON mcp_user_tokens(provider);
"""


class McpTokenStore:
    """Manages per-user OAuth tokens for MCP providers (Granola, Gmail, etc.)."""

    def __init__(self, dsn: str | None = None):
        self._dsn = dsn or os.environ.get("DATABASE_URL", "")
        if not self._dsn:
            raise ValueError("DATABASE_URL is required for McpTokenStore")
        self._ensure_schema()

    def _conn(self):
        return psycopg2.connect(self._dsn)

    def _ensure_schema(self) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def get_token(self, user_id: str, provider: str) -> dict | None:
        conn = self._conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM mcp_user_tokens WHERE user_identifier = %s AND provider = %s",
                    (user_id, provider),
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def save_token(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: str | None = None,
        token_type: str = "Bearer",
        expires_at: datetime | None = None,
        scope: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mcp_user_tokens
                        (user_identifier, provider, access_token, refresh_token,
                         token_type, expires_at, scope, client_id, client_secret, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_identifier, provider)
                    DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = COALESCE(EXCLUDED.refresh_token, mcp_user_tokens.refresh_token),
                        token_type = EXCLUDED.token_type,
                        expires_at = EXCLUDED.expires_at,
                        scope = EXCLUDED.scope,
                        client_id = COALESCE(EXCLUDED.client_id, mcp_user_tokens.client_id),
                        client_secret = COALESCE(EXCLUDED.client_secret, mcp_user_tokens.client_secret),
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        user_id, provider, access_token, refresh_token,
                        token_type, expires_at, scope, client_id, client_secret,
                        json.dumps(metadata or {}),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def list_connected(self, user_id: str) -> list[str]:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT provider FROM mcp_user_tokens WHERE user_identifier = %s ORDER BY provider",
                    (user_id,),
                )
                return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

    def delete_token(self, user_id: str, provider: str) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM mcp_user_tokens WHERE user_identifier = %s AND provider = %s",
                    (user_id, provider),
                )
            conn.commit()
        finally:
            conn.close()

    def refresh_if_expired(self, user_id: str, provider: str) -> str | None:
        """Return a valid access token, refreshing if expired. Returns None if no token stored."""
        token_row = self.get_token(user_id, provider)
        if not token_row:
            return None

        expires_at = token_row.get("expires_at")
        if expires_at and expires_at < datetime.now(timezone.utc):
            refresh_token = token_row.get("refresh_token")
            if not refresh_token:
                _logger.warning("Token expired for %s/%s but no refresh_token", user_id, provider)
                return None

            from agentura_sdk.oauth.providers import refresh_access_token
            new_tokens = refresh_access_token(
                provider,
                refresh_token,
                token_row.get("client_id"),
                token_row.get("client_secret"),
            )
            if not new_tokens:
                _logger.error("Token refresh failed for %s/%s", user_id, provider)
                return None

            self.save_token(
                user_id=user_id,
                provider=provider,
                access_token=new_tokens["access_token"],
                refresh_token=new_tokens.get("refresh_token", refresh_token),
                expires_at=new_tokens.get("expires_at"),
                client_id=token_row.get("client_id"),
                client_secret=token_row.get("client_secret"),
            )
            return new_tokens["access_token"]

        return token_row["access_token"]
