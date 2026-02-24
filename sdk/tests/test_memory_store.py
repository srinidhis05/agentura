"""Tests for the memory store abstraction (JSON backend).

mem0 backend requires API keys and is tested via integration tests.
These tests verify the JSONStore and the store interface work correctly.
"""

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def json_store(tmp_path):
    """Create a JSONStore pointing to a temp directory."""
    from agentura_sdk.memory.json_store import JSONStore

    store = JSONStore(knowledge_dir=tmp_path / ".agentura")
    return store


@pytest.fixture
def mem0_fallback(tmp_path, monkeypatch):
    """Ensure get_memory_store returns JSONStore when no API key."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ASPORA_KNOWLEDGE_DIR", str(tmp_path / ".agentura"))

    from agentura_sdk.memory.store import get_memory_store
    return get_memory_store()


class TestJSONStore:
    def test_log_execution(self, json_store):
        eid = json_store.log_execution("ecm/order-details", {
            "input_summary": {"query": "test"},
            "output_summary": {"answer": "ok"},
            "cost_usd": 0.01,
            "latency_ms": 500,
        })
        assert eid.startswith("EXEC-")

        executions = json_store.get_executions("ecm/order-details")
        assert len(executions) == 1
        assert executions[0]["skill"] == "ecm/order-details"

    def test_add_correction(self, json_store):
        cid = json_store.add_correction("ecm/order-details", {
            "execution_id": "EXEC-001",
            "user_correction": "Fix this",
            "original_output": {"answer": "wrong"},
        })
        assert cid.startswith("CORR-")

        corrections = json_store.get_corrections("ecm/order-details")
        assert len(corrections) == 1
        assert corrections[0]["user_correction"] == "Fix this"

    def test_add_and_get_reflexion(self, json_store):
        rid = json_store.add_reflexion("ecm/order-details", {
            "correction_id": "CORR-001",
            "rule": "Always check compliance",
            "applies_when": "When processing orders",
            "confidence": 0.9,
            "validated_by_test": False,
        })
        assert rid.startswith("REFL-")

        reflexions = json_store.get_reflexions("ecm/order-details")
        assert len(reflexions) == 1
        assert reflexions[0]["rule"] == "Always check compliance"

    def test_reflexions_scoped_by_skill(self, json_store):
        json_store.add_reflexion("ecm/order-details", {"rule": "ECM rule"})
        json_store.add_reflexion("wealth/suggest-allocation", {"rule": "Wealth rule"})

        ecm = json_store.get_reflexions("ecm/order-details")
        wealth = json_store.get_reflexions("wealth/suggest-allocation")

        assert len(ecm) == 1
        assert ecm[0]["rule"] == "ECM rule"
        assert len(wealth) == 1
        assert wealth[0]["rule"] == "Wealth rule"

    def test_get_all_reflexions(self, json_store):
        json_store.add_reflexion("ecm/order-details", {"rule": "Rule 1"})
        json_store.add_reflexion("wealth/suggest-allocation", {"rule": "Rule 2"})

        all_refl = json_store.get_all_reflexions()
        assert len(all_refl) == 2

    def test_update_reflexion(self, json_store):
        rid = json_store.add_reflexion("ecm/order-details", {
            "rule": "Test rule",
            "validated_by_test": False,
        })

        json_store.update_reflexion(rid, {"validated_by_test": True})

        reflexions = json_store.get_reflexions("ecm/order-details")
        assert reflexions[0]["validated_by_test"] is True

    def test_search_similar_returns_skill_matches(self, json_store):
        json_store.add_reflexion("ecm/order-details", {"rule": "Check compliance"})
        json_store.add_reflexion("ecm/order-details", {"rule": "Validate region"})
        json_store.add_reflexion("wealth/suggest-allocation", {"rule": "Other rule"})

        results = json_store.search_similar("ecm/order-details", "compliance check")
        assert len(results) == 2  # Only ecm skills, not wealth

    def test_executions_filtered_by_skill(self, json_store):
        json_store.log_execution("ecm/order-details", {"cost_usd": 0.01})
        json_store.log_execution("wealth/suggest-allocation", {"cost_usd": 0.02})

        ecm = json_store.get_executions("ecm/order-details")
        all_execs = json_store.get_executions()

        assert len(ecm) == 1
        assert len(all_execs) == 2


class TestMemoryStoreFallback:
    def test_returns_json_store_without_api_key(self, mem0_fallback):
        from agentura_sdk.memory.json_store import JSONStore
        assert isinstance(mem0_fallback, JSONStore)

    def test_fallback_store_works(self, mem0_fallback):
        rid = mem0_fallback.add_reflexion("test/skill", {
            "rule": "Test via fallback",
            "confidence": 0.7,
        })
        assert rid.startswith("REFL-")

        reflexions = mem0_fallback.get_reflexions("test/skill")
        assert len(reflexions) == 1
