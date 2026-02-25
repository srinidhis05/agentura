"""Memory store abstraction — mem0 backend with JSON fallback.

Usage:
    store = get_memory_store()
    store.log_execution(skill_path, execution_data)
    store.add_correction(skill_path, correction_data)
    store.add_reflexion(skill_path, reflexion_data)
    results = store.search_similar(skill_path, query, limit=5)
    reflexions = store.get_reflexions(skill_path)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


class MemoryStore(Protocol):
    """Interface for the knowledge layer store."""

    def log_execution(self, skill_path: str, data: dict) -> str: ...
    def add_correction(self, skill_path: str, data: dict) -> str: ...
    def add_reflexion(self, skill_path: str, data: dict) -> str: ...
    def get_reflexions(self, skill_path: str) -> list[dict]: ...
    def search_similar(self, skill_path: str, query: str, limit: int = 5) -> list[dict]: ...
    def get_executions(self, skill_path: str | None = None) -> list[dict]: ...
    def get_corrections(self, skill_path: str | None = None) -> list[dict]: ...
    def get_all_reflexions(self) -> list[dict]: ...
    def update_reflexion(self, reflexion_id: str, updates: dict) -> None: ...


_store_instance: MemoryStore | None = None


def get_scoped_store(allowed_domains: set[str] | None = None) -> MemoryStore:
    """Return a domain-scoped memory store.

    Wraps the base store with domain isolation. Each domain agent only sees its own memories.
    Pass allowed_domains={"hr"} to restrict, or None / {"*"} for unrestricted.
    """
    from agentura_sdk.memory.scoped_store import DomainScopedStore

    base = get_memory_store()
    if allowed_domains is None or "*" in allowed_domains:
        return base
    return DomainScopedStore(base, allowed_domains)


class CompositeStore:
    """Postgres for durable storage + mem0 for semantic vector search."""

    def __init__(self, pg_store, mem0_store):
        self._pg = pg_store
        self._mem0 = mem0_store

    def log_execution(self, skill_path: str, data: dict) -> str:
        exec_id = self._pg.log_execution(skill_path, data)
        try:
            self._mem0.log_execution(skill_path, data)
        except Exception:
            pass
        return exec_id

    def add_correction(self, skill_path: str, data: dict) -> str:
        corr_id = self._pg.add_correction(skill_path, data)
        try:
            self._mem0.add_correction(skill_path, data)
        except Exception:
            pass
        return corr_id

    def add_reflexion(self, skill_path: str, data: dict) -> str:
        refl_id = self._pg.add_reflexion(skill_path, data)
        try:
            self._mem0.add_reflexion(skill_path, data)
        except Exception:
            pass
        return refl_id

    def get_reflexions(self, skill_path: str) -> list[dict]:
        return self._pg.get_reflexions(skill_path)

    def get_executions(self, skill_path: str | None = None) -> list[dict]:
        return self._pg.get_executions(skill_path)

    def get_corrections(self, skill_path: str | None = None) -> list[dict]:
        return self._pg.get_corrections(skill_path)

    def get_all_reflexions(self) -> list[dict]:
        return self._pg.get_all_reflexions()

    def update_reflexion(self, reflexion_id: str, updates: dict) -> None:
        self._pg.update_reflexion(reflexion_id, updates)
        try:
            self._mem0.update_reflexion(reflexion_id, updates)
        except Exception:
            pass

    def search_similar(self, skill_path: str, query: str, limit: int = 5) -> list[dict]:
        return self._mem0.search_similar(skill_path, query, limit)

    @property
    def pg(self):
        return self._pg

    @property
    def mem0(self):
        return self._mem0


def get_memory_store() -> MemoryStore:
    """Return the configured memory store (singleton — initialized once).

    Priority:
    1. PostgreSQL + mem0 composite (if both DATABASE_URL and LLM key available)
    2. PostgreSQL only (if DATABASE_URL set)
    3. mem0 only (if LLM key available)
    4. JSON files (local dev fallback)
    """
    global _store_instance
    if _store_instance is not None:
        return _store_instance

    database_url = os.environ.get("DATABASE_URL")
    has_llm_key = bool(os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))

    pg_store = None
    mem0_store = None

    if database_url:
        try:
            from agentura_sdk.memory.pg_store import PgStore
            pg_store = PgStore(dsn=database_url)
        except Exception:
            pass

    if has_llm_key:
        try:
            from agentura_sdk.memory.mem0_store import Mem0Store
            mem0_store = Mem0Store()
        except Exception:
            pass

    # Composite: Postgres persistence + mem0 semantic search
    if pg_store and mem0_store:
        _store_instance = CompositeStore(pg_store, mem0_store)
        return _store_instance

    if pg_store:
        _store_instance = pg_store
        return _store_instance

    if mem0_store:
        _store_instance = mem0_store
        return _store_instance

    # Fallback: JSON files
    from agentura_sdk.memory.json_store import JSONStore
    _store_instance = JSONStore()
    return _store_instance
