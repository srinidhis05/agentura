"""JSON file-based memory store — fallback when mem0 is not available.

This preserves backward compatibility with the existing .agentura/ JSON files.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class JSONStore:
    """Knowledge layer backed by .agentura/*.json files."""

    def __init__(self, knowledge_dir: Path | None = None):
        self._dir = knowledge_dir or Path(
            os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str(Path.cwd() / ".agentura")
        )
        self._dir.mkdir(parents=True, exist_ok=True)

    def _load(self, name: str) -> dict:
        f = self._dir / name
        if f.exists():
            return json.loads(f.read_text())
        return {}

    def _save(self, name: str, data: dict) -> None:
        (self._dir / name).write_text(json.dumps(data, indent=2))

    def log_execution(self, skill_path: str, data: dict) -> str:
        execution_id = data.get(
            "execution_id",
            f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        )
        data["execution_id"] = execution_id
        data.setdefault("skill", skill_path)
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        mem = self._load("episodic_memory.json")
        mem.setdefault("entries", []).append(data)
        self._save("episodic_memory.json", mem)
        return execution_id

    def add_correction(self, skill_path: str, data: dict) -> str:
        corr = self._load("corrections.json")
        corr.setdefault("corrections", [])
        idx = len(corr["corrections"]) + 1
        correction_id = data.get("correction_id", f"CORR-{idx:03d}")
        data["correction_id"] = correction_id
        data.setdefault("skill", skill_path)
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        corr["corrections"].append(data)
        self._save("corrections.json", corr)
        return correction_id

    def add_reflexion(self, skill_path: str, data: dict) -> str:
        refl = self._load("reflexion_entries.json")
        refl.setdefault("entries", [])
        idx = len(refl["entries"]) + 1
        reflexion_id = data.get("reflexion_id", f"REFL-{idx:03d}")
        data["reflexion_id"] = reflexion_id
        data.setdefault("skill", skill_path)
        data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        refl["entries"].append(data)
        self._save("reflexion_entries.json", refl)
        return reflexion_id

    def get_reflexions(self, skill_path: str) -> list[dict]:
        refl = self._load("reflexion_entries.json")
        return [
            e for e in refl.get("entries", [])
            if e.get("skill") == skill_path
        ]

    def search_similar(self, skill_path: str, query: str, limit: int = 5) -> list[dict]:
        """JSON store has no semantic search — returns exact skill matches."""
        refl = self._load("reflexion_entries.json")
        matches = [
            e for e in refl.get("entries", [])
            if e.get("skill") == skill_path
        ]
        return matches[:limit]

    def get_executions(self, skill_path: str | None = None) -> list[dict]:
        mem = self._load("episodic_memory.json")
        entries = mem.get("entries", [])
        if skill_path:
            entries = [e for e in entries if e.get("skill") == skill_path]
        return entries

    def get_corrections(self, skill_path: str | None = None) -> list[dict]:
        corr = self._load("corrections.json")
        corrections = corr.get("corrections", [])
        if skill_path:
            corrections = [c for c in corrections if c.get("skill") == skill_path]
        return corrections

    def get_all_reflexions(self) -> list[dict]:
        refl = self._load("reflexion_entries.json")
        return refl.get("entries", [])

    def update_reflexion(self, reflexion_id: str, updates: dict) -> None:
        refl = self._load("reflexion_entries.json")
        for entry in refl.get("entries", []):
            if entry.get("reflexion_id") == reflexion_id:
                entry.update(updates)
                break
        self._save("reflexion_entries.json", refl)
