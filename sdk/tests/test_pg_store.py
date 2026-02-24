"""Tests for PgStore — runs against PostgreSQL if DATABASE_URL is set, skips otherwise."""

import os
import pytest

HAS_PG = bool(os.environ.get("DATABASE_URL"))


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
class TestPgStore:
    def setup_method(self):
        from agentura_sdk.memory.pg_store import PgStore
        self.store = PgStore(workspace_id="test-workspace")

    def test_log_execution(self):
        eid = self.store.log_execution("ecm/triage", {
            "execution_id": "EXEC-TEST-001",
            "input_summary": {"case_id": "123"},
            "output_summary": {"assigned_to": "ops-team"},
            "outcome": "accepted",
            "cost_usd": 0.05,
            "latency_ms": 1200.0,
            "model_used": "claude-sonnet-4.5",
        })
        assert eid == "EXEC-TEST-001"

        execs = self.store.get_executions("ecm/triage")
        assert any(e["execution_id"] == "EXEC-TEST-001" for e in execs)

    def test_add_correction(self):
        cid = self.store.add_correction("ecm/triage", {
            "execution_id": "EXEC-TEST-001",
            "original_output": {"assigned_to": "ops-team"},
            "user_correction": "Should be assigned to compliance",
        })
        assert cid.startswith("CORR-")

    def test_add_reflexion(self):
        rid = self.store.add_reflexion("ecm/triage", {
            "correction_id": "CORR-001",
            "rule": "Route compliance cases to compliance team",
            "applies_when": "case_type == compliance",
            "confidence": 0.85,
        })
        assert rid.startswith("REFL-")

    def test_domain_isolation(self):
        """ECM data shouldn't leak into FRM queries."""
        self.store.log_execution("frm/risk-check", {
            "execution_id": "EXEC-FRM-001",
            "outcome": "accepted",
        })
        ecm_execs = self.store.get_executions("ecm/triage")
        assert not any(e["execution_id"] == "EXEC-FRM-001" for e in ecm_execs)


class TestPgStoreImport:
    def test_import_succeeds(self):
        from agentura_sdk.memory.pg_store import PgStore
        assert PgStore is not None

    def test_schema_sql_defined(self):
        from agentura_sdk.memory.pg_store import _SCHEMA
        assert "CREATE TABLE IF NOT EXISTS executions" in _SCHEMA
        assert "workspace_id" in _SCHEMA
        assert "domain" in _SCHEMA
