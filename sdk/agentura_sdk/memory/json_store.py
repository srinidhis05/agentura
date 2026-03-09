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

    # --- MemRL: utility-scored memory (DEC-066) ---

    def record_reflexion_injection(self, execution_id: str, reflexion_ids: list[str]) -> None:
        if not reflexion_ids:
            return
        mem = self._load("episodic_memory.json")
        for entry in mem.get("entries", []):
            if entry.get("execution_id") == execution_id:
                entry["reflexions_injected"] = reflexion_ids
                break
        self._save("episodic_memory.json", mem)
        refl = self._load("reflexion_entries.json")
        for entry in refl.get("entries", []):
            if entry.get("reflexion_id") in reflexion_ids:
                entry["times_injected"] = entry.get("times_injected", 0) + 1
        self._save("reflexion_entries.json", refl)

    def record_execution_success(self, execution_id: str) -> None:
        mem = self._load("episodic_memory.json")
        exec_entry = next(
            (e for e in mem.get("entries", []) if e.get("execution_id") == execution_id),
            None,
        )
        if not exec_entry:
            return
        injected = exec_entry.get("reflexions_injected", [])
        if not injected:
            return
        refl = self._load("reflexion_entries.json")
        for entry in refl.get("entries", []):
            if entry.get("reflexion_id") in injected:
                helped = entry.get("times_helped", 0) + 1
                total = entry.get("times_injected", 1)
                entry["times_helped"] = helped
                entry["utility_score"] = (helped + 2) / (total + 4)
        self._save("reflexion_entries.json", refl)

    def get_top_reflexions(self, skill_path: str, limit: int = 5, min_score: float = 0.3) -> list[dict]:
        refl = self._load("reflexion_entries.json")
        matches = [
            e for e in refl.get("entries", [])
            if e.get("skill") == skill_path and e.get("utility_score", 0.5) >= min_score
        ]
        matches.sort(key=lambda e: e.get("utility_score", 0.5), reverse=True)
        return matches[:limit]

    # --- Incident-to-eval (DEC-067) ---

    def log_failure_case(self, skill_path: str, data: dict) -> str:
        cases = self._load("failure_cases.json")
        cases.setdefault("cases", [])
        failure_case_id = data.get(
            "failure_case_id",
            f"FAIL-{len(cases['cases']) + 1:03d}",
        )
        data["failure_case_id"] = failure_case_id
        data.setdefault("skill", skill_path)
        cases["cases"].append(data)
        self._save("failure_cases.json", cases)
        return failure_case_id
