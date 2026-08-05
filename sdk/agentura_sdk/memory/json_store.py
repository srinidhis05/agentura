"""JSON file-based memory store — fallback when mem0 is not available.

This preserves backward compatibility with the existing .agentura/ JSON files.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


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
        data.setdefault("status", "active")
        data.setdefault("scope", "skill")
        data.setdefault("source", "correction")
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
                entry["last_fired_at"] = datetime.now(timezone.utc).isoformat()
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

    def _compute_decayed_score(self, entry: dict, max_age_days: int = 30) -> float:
        """Apply time-based decay to a reflexion's utility score.

        decay_factor = max(0.1, 1.0 - (days_since_last_fired / max_age_days))
        """
        base_score = entry.get("utility_score", 0.5)
        last_fired = entry.get("last_fired_at")
        if not last_fired:
            # Fall back to created_at
            last_fired = entry.get("created_at")
        if not last_fired:
            return base_score

        try:
            if isinstance(last_fired, str):
                # Handle ISO format with or without timezone
                last_fired_dt = datetime.fromisoformat(last_fired.replace("Z", "+00:00"))
            else:
                last_fired_dt = last_fired
            if last_fired_dt.tzinfo is None:
                last_fired_dt = last_fired_dt.replace(tzinfo=timezone.utc)
            days_since = (datetime.now(timezone.utc) - last_fired_dt).total_seconds() / 86400
            decay_factor = max(0.1, 1.0 - (days_since / max_age_days))
            return base_score * decay_factor
        except (ValueError, TypeError):
            return base_score

    def get_top_reflexions(self, skill_path: str, limit: int = 5, min_score: float = 0.3) -> list[dict]:
        refl = self._load("reflexion_entries.json")
        matches = []
        for e in refl.get("entries", []):
            if e.get("skill") != skill_path:
                continue
            if e.get("status", "active") == "retired":
                continue
            decayed = self._compute_decayed_score(e)
            if decayed >= min_score:
                e["_decayed_score"] = decayed
                matches.append(e)
        matches.sort(key=lambda e: e.get("_decayed_score", 0.5), reverse=True)
        # Strip internal sort key before returning
        for m in matches:
            m.pop("_decayed_score", None)
        return matches[:limit]

    def get_top_reflexions_with_scope(self, skill_path: str, limit: int = 5, min_score: float = 0.3) -> list[dict]:
        """Retrieve reflexions across skill/domain/org scopes with decay."""
        domain = skill_path.split("/")[0] if "/" in skill_path else ""
        refl = self._load("reflexion_entries.json")
        scope_priority = {"skill": 1, "domain": 2, "org": 3}
        matches = []
        for e in refl.get("entries", []):
            if e.get("status", "active") == "retired":
                continue
            scope = e.get("scope", "skill")
            include = False
            if scope == "skill" and e.get("skill") == skill_path:
                include = True
            elif scope == "domain":
                entry_domain = e.get("skill", "").split("/")[0] if "/" in e.get("skill", "") else ""
                if entry_domain == domain:
                    include = True
            elif scope == "org":
                include = True
            if not include:
                continue
            decayed = self._compute_decayed_score(e)
            if decayed >= min_score:
                e["_decayed_score"] = decayed
                e["_scope_priority"] = scope_priority.get(scope, 4)
                matches.append(e)
        matches.sort(key=lambda e: (e.get("_scope_priority", 4), -e.get("_decayed_score", 0)))
        for m in matches:
            m.pop("_decayed_score", None)
            m.pop("_scope_priority", None)
        return matches[:limit]

    # --- Engram: rubric-scored rule lifecycle ---

    def score_reflexion_with_rubric(self, reflexion_id: str, rubric_scores: dict[str, float]) -> float:
        """Score a reflexion using a multi-dimensional rubric.

        rubric_scores: {"accuracy": 4.0, "relevance": 3.5, "actionability": 4.5}
        Returns: composite score (weighted average normalized to 0-1).
        """
        from agentura_sdk.memory.store import RUBRIC_WEIGHTS

        refl = self._load("reflexion_entries.json")
        total_weight = 0.0
        weighted_sum = 0.0
        for dim, score in rubric_scores.items():
            weight = RUBRIC_WEIGHTS.get(dim, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        # Normalize to 0-1 range (rubric scores are 0-5)
        composite = (weighted_sum / total_weight / 5.0) if total_weight > 0 else 0.0

        for entry in refl.get("entries", []):
            if entry.get("reflexion_id") == reflexion_id:
                entry["rubric_scores"] = rubric_scores
                entry["utility_score"] = composite
                entry["last_fired_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save("reflexion_entries.json", refl)
        return composite

    def retire_stale_reflexions(self, skill_path: str, min_score: float = 0.3, max_age_days: int = 30) -> list[str]:
        """Retire reflexions that have decayed below threshold.

        Returns list of retired reflexion IDs.
        Rules are retired (status='retired'), not deleted.
        """
        refl = self._load("reflexion_entries.json")
        retired_ids: list[str] = []
        for entry in refl.get("entries", []):
            if entry.get("skill") != skill_path:
                continue
            if entry.get("status", "active") != "active":
                continue
            decayed = self._compute_decayed_score(entry, max_age_days)
            if decayed < min_score:
                entry["status"] = "retired"
                rid = entry.get("reflexion_id", "")
                retired_ids.append(rid)
                logger.info("retired reflexion %s (decayed_score=%.3f < min=%.3f)", rid, decayed, min_score)
        self._save("reflexion_entries.json", refl)
        return retired_ids

    def promote_reflexion(self, reflexion_id: str, target_scope: str) -> None:
        """Promote a reflexion from skill-scoped to domain-scoped or org-scoped."""
        if target_scope not in ("domain", "org"):
            raise ValueError(f"Invalid promotion target scope: {target_scope}")
        refl = self._load("reflexion_entries.json")
        for entry in refl.get("entries", []):
            if entry.get("reflexion_id") == reflexion_id:
                entry["scope"] = target_scope
                entry["status"] = "promoted"
                break
        self._save("reflexion_entries.json", refl)

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
