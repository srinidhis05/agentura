"""Mem0-backed semantic memory store.

Provides vector-based semantic search for corrections, reflexions,
and executions. Automatically extracts facts and consolidates memories.

Requires: pip install mem0ai
Requires: ANTHROPIC_API_KEY or OPENAI_API_KEY env var
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from mem0 import Memory


def _build_config() -> dict:
    """Build mem0 config using available API keys."""
    config: dict = {}

    # LLM: prefer Anthropic, fallback to OpenAI
    if os.environ.get("ANTHROPIC_API_KEY"):
        config["llm"] = {
            "provider": "anthropic",
            "config": {
                "model": "claude-haiku-4-5-20251001",
                "temperature": 0.1,
                "max_tokens": 1000,
            },
        }

    # Embedder: use HuggingFace (free, local) so we don't need OpenAI key
    if not os.environ.get("OPENAI_API_KEY"):
        config["embedder"] = {
            "provider": "huggingface",
            "config": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }

    # Vector store: Qdrant in-memory (no external service needed)
    config["version"] = "v1.1"

    return config


class Mem0Store:
    """Semantic memory store backed by mem0.

    Memory categories (stored as agent_id):
    - "execution" — episodic execution memory
    - "correction" — user corrections
    - "reflexion" — learned rules from corrections

    Skills are stored as user_id for scoping.
    """

    def __init__(self):
        config = _build_config()
        self._memory = Memory.from_config(config)

    def log_execution(self, skill_path: str, data: dict) -> str:
        execution_id = data.get(
            "execution_id",
            f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        )
        data["execution_id"] = execution_id
        data.setdefault("skill", skill_path)
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        # Store as a memory with execution context
        message = (
            f"Skill {skill_path} executed. "
            f"Input: {json.dumps(data.get('input_summary', {}))[:500]}. "
            f"Output: {json.dumps(data.get('output_summary', {}))[:500]}. "
            f"Outcome: {data.get('outcome', 'pending_review')}. "
            f"Cost: ${data.get('cost_usd', 0):.4f}. "
            f"Latency: {data.get('latency_ms', 0):.0f}ms."
        )

        self._memory.add(
            message,
            user_id=skill_path,
            agent_id="execution",
            metadata={
                "execution_id": execution_id,
                "type": "execution",
                **{k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))},
            },
        )
        return execution_id

    def add_correction(self, skill_path: str, data: dict) -> str:
        correction_id = data.get("correction_id", f"CORR-{uuid.uuid4().hex[:6]}")
        data["correction_id"] = correction_id
        data.setdefault("skill", skill_path)
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        message = (
            f"User correction for {skill_path}: "
            f"Original output was wrong. "
            f"Correction: {data.get('user_correction', data.get('correction', ''))}. "
            f"This should be applied in future executions."
        )

        self._memory.add(
            message,
            user_id=skill_path,
            agent_id="correction",
            metadata={
                "correction_id": correction_id,
                "type": "correction",
                "execution_id": data.get("execution_id", ""),
                **{k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))},
            },
        )
        return correction_id

    def add_reflexion(self, skill_path: str, data: dict) -> str:
        reflexion_id = data.get("reflexion_id", f"REFL-{uuid.uuid4().hex[:6]}")
        data["reflexion_id"] = reflexion_id
        data.setdefault("skill", skill_path)
        data.setdefault("created_at", datetime.now(timezone.utc).isoformat())

        rule = data.get("rule", "")
        applies_when = data.get("applies_when", "")

        message = (
            f"Learned rule for {skill_path}: {rule}. "
            f"Applies when: {applies_when}. "
            f"Root cause: {data.get('root_cause', 'unknown')}. "
            f"Confidence: {data.get('confidence', 0.8)}."
        )

        self._memory.add(
            message,
            user_id=skill_path,
            agent_id="reflexion",
            metadata={
                "reflexion_id": reflexion_id,
                "type": "reflexion",
                "correction_id": data.get("correction_id", ""),
                "rule": rule,
                "applies_when": applies_when,
                "confidence": data.get("confidence", 0.8),
                "validated_by_test": data.get("validated_by_test", False),
            },
        )
        return reflexion_id

    def get_reflexions(self, skill_path: str) -> list[dict]:
        """Get all reflexion memories for a skill."""
        results = self._memory.get_all(
            user_id=skill_path,
            agent_id="reflexion",
        )
        entries = results.get("results", results) if isinstance(results, dict) else results
        return [self._to_reflexion_dict(m) for m in entries]

    def search_similar(self, skill_path: str, query: str, limit: int = 5) -> list[dict]:
        """Semantic search across corrections and reflexions for a skill."""
        results = self._memory.search(
            query=query,
            user_id=skill_path,
            limit=limit,
        )
        entries = results.get("results", results) if isinstance(results, dict) else results
        return [self._to_dict(m) for m in entries]

    def get_executions(self, skill_path: str | None = None) -> list[dict]:
        """Get execution history."""
        kwargs: dict = {"agent_id": "execution"}
        if skill_path:
            kwargs["user_id"] = skill_path
        results = self._memory.get_all(**kwargs)
        entries = results.get("results", results) if isinstance(results, dict) else results
        return [self._to_dict(m) for m in entries]

    def get_corrections(self, skill_path: str | None = None) -> list[dict]:
        """Get all corrections."""
        kwargs: dict = {"agent_id": "correction"}
        if skill_path:
            kwargs["user_id"] = skill_path
        results = self._memory.get_all(**kwargs)
        entries = results.get("results", results) if isinstance(results, dict) else results
        return [self._to_dict(m) for m in entries]

    def get_all_reflexions(self) -> list[dict]:
        """Get all reflexions across all skills."""
        results = self._memory.get_all(agent_id="reflexion")
        entries = results.get("results", results) if isinstance(results, dict) else results
        return [self._to_reflexion_dict(m) for m in entries]

    def update_reflexion(self, reflexion_id: str, updates: dict) -> None:
        """Update a reflexion entry by ID.

        mem0 doesn't support update by custom ID directly,
        so we search for the memory and update it.
        """
        all_refl = self.get_all_reflexions()
        for r in all_refl:
            if r.get("reflexion_id") == reflexion_id:
                mem_id = r.get("_mem0_id")
                if mem_id:
                    # Build update message
                    update_msg = f"Updated reflexion {reflexion_id}: "
                    if "validated_by_test" in updates:
                        update_msg += f"validated_by_test={updates['validated_by_test']}. "
                    if "confidence" in updates:
                        update_msg += f"confidence={updates['confidence']}. "
                    self._memory.update(mem_id, update_msg)
                break

    @staticmethod
    def _to_dict(mem: dict) -> dict:
        """Convert mem0 memory entry to flat dict."""
        result = {
            "_mem0_id": mem.get("id", ""),
            "memory": mem.get("memory", ""),
            "score": mem.get("score"),
        }
        metadata = mem.get("metadata", {}) or {}
        result.update(metadata)
        return result

    @staticmethod
    def _to_reflexion_dict(mem: dict) -> dict:
        """Convert mem0 memory to reflexion-compatible dict."""
        metadata = mem.get("metadata", {}) or {}
        return {
            "_mem0_id": mem.get("id", ""),
            "reflexion_id": metadata.get("reflexion_id", ""),
            "correction_id": metadata.get("correction_id", ""),
            "skill": mem.get("user_id", ""),
            "rule": metadata.get("rule", mem.get("memory", "")),
            "applies_when": metadata.get("applies_when", ""),
            "confidence": metadata.get("confidence", 0.8),
            "validated_by_test": metadata.get("validated_by_test", False),
            "created_at": mem.get("created_at", ""),
        }
