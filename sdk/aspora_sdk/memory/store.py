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


def get_memory_store() -> MemoryStore:
    """Return the configured memory store (singleton — initialized once).

    Uses mem0 if ANTHROPIC_API_KEY or OPENAI_API_KEY is available.
    Falls back to JSON files otherwise.
    """
    global _store_instance
    if _store_instance is not None:
        return _store_instance

    # Check if mem0 can be initialized
    has_llm_key = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))

    if has_llm_key:
        try:
            from aspora_sdk.memory.mem0_store import Mem0Store
            _store_instance = Mem0Store()
            return _store_instance
        except Exception:
            pass

    from aspora_sdk.memory.json_store import JSONStore
    _store_instance = JSONStore()
    return _store_instance
