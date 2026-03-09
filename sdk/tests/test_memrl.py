"""Tests for MemRL utility-scored memory (DEC-066)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agentura_sdk.memory.json_store import JSONStore


@pytest.fixture
def store(tmp_path: Path) -> JSONStore:
    return JSONStore(knowledge_dir=tmp_path)


def _add_reflexion(store: JSONStore, skill: str, rid: str, **kwargs) -> str:
    data = {"reflexion_id": rid, "rule": f"Rule for {rid}", "applies_when": "always", "confidence": 0.8}
    data.update(kwargs)
    return store.add_reflexion(skill, data)


class TestMemRLUtilityScoring:
    def test_default_utility_score(self, store: JSONStore):
        """New reflexions should have cold-start safe default score of 0.5."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        entries = store.get_reflexions("dev/deployer")
        assert len(entries) == 1
        # JSON store doesn't auto-set utility_score, but get_top_reflexions defaults to 0.5
        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        assert len(top) == 1

    def test_record_injection_increments_counter(self, store: JSONStore):
        _add_reflexion(store, "dev/deployer", "REFL-001")
        exec_id = store.log_execution("dev/deployer", {"execution_id": "EXEC-001"})
        store.record_reflexion_injection("EXEC-001", ["REFL-001"])
        entries = store.get_reflexions("dev/deployer")
        assert entries[0].get("times_injected") == 1

    def test_record_success_updates_utility(self, store: JSONStore):
        _add_reflexion(store, "dev/deployer", "REFL-001")
        store.log_execution("dev/deployer", {"execution_id": "EXEC-001"})
        store.record_reflexion_injection("EXEC-001", ["REFL-001"])
        store.record_execution_success("EXEC-001")
        entries = store.get_reflexions("dev/deployer")
        entry = entries[0]
        assert entry["times_helped"] == 1
        # Utility = (1 + 2) / (1 + 4) = 0.6
        assert abs(entry["utility_score"] - 0.6) < 0.01

    def test_bayesian_smoothing_formula(self, store: JSONStore):
        """After 5 injections and 3 successes: utility = (3+2)/(5+4) ≈ 0.56."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        for i in range(5):
            exec_id = f"EXEC-{i:03d}"
            store.log_execution("dev/deployer", {"execution_id": exec_id})
            store.record_reflexion_injection(exec_id, ["REFL-001"])
        # 3 of 5 succeed
        for i in range(3):
            store.record_execution_success(f"EXEC-{i:03d}")

        entries = store.get_reflexions("dev/deployer")
        entry = entries[0]
        assert entry["times_injected"] == 5
        assert entry["times_helped"] == 3
        expected = (3 + 2) / (5 + 4)  # ≈ 0.556
        assert abs(entry["utility_score"] - expected) < 0.01

    def test_low_utility_excluded_from_top(self, store: JSONStore):
        """Reflexions below min_score should not appear in get_top_reflexions."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        _add_reflexion(store, "dev/deployer", "REFL-002")

        # Manually set low utility on REFL-002
        refl = store._load("reflexion_entries.json")
        for e in refl["entries"]:
            if e["reflexion_id"] == "REFL-002":
                e["utility_score"] = 0.1
        store._save("reflexion_entries.json", refl)

        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        ids = [e["reflexion_id"] for e in top]
        assert "REFL-001" in ids
        assert "REFL-002" not in ids

    def test_top_reflexions_sorted_by_utility(self, store: JSONStore):
        _add_reflexion(store, "dev/deployer", "REFL-001")
        _add_reflexion(store, "dev/deployer", "REFL-002")

        refl = store._load("reflexion_entries.json")
        for e in refl["entries"]:
            if e["reflexion_id"] == "REFL-001":
                e["utility_score"] = 0.7
            elif e["reflexion_id"] == "REFL-002":
                e["utility_score"] = 0.9
        store._save("reflexion_entries.json", refl)

        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        assert top[0]["reflexion_id"] == "REFL-002"
        assert top[1]["reflexion_id"] == "REFL-001"


class TestFailureCaseStore:
    def test_log_failure_case(self, store: JSONStore):
        fid = store.log_failure_case("dev/deployer", {
            "execution_id": "EXEC-001",
            "severity": "P0",
            "input_summary": {"task": "deploy"},
            "error_output": {"error": "crashed"},
        })
        assert fid.startswith("FAIL-")
        cases = store._load("failure_cases.json")
        assert len(cases["cases"]) == 1
        assert cases["cases"][0]["skill"] == "dev/deployer"


class TestSkillLoaderReflexionIds:
    def test_load_reflexion_entries_returns_tuple(self, tmp_path: Path):
        """load_reflexion_entries should return (markdown, reflexion_ids) tuple."""
        from agentura_sdk.runner.skill_loader import load_reflexion_entries

        # Create skill directory structure
        skills_dir = tmp_path / "skills"
        skill_dir = skills_dir / "dev" / "deployer"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: deployer\nrole: agent\ndomain: dev\n---\nTest")

        # Create reflexion entries
        agentura_dir = tmp_path / ".agentura"
        agentura_dir.mkdir()
        refl_file = agentura_dir / "reflexion_entries.json"
        refl_file.write_text(json.dumps({
            "entries": [{
                "reflexion_id": "REFL-001",
                "skill": "dev/deployer",
                "rule": "Always use NodePort",
                "applies_when": "generating K8s service manifests",
                "confidence": 0.95,
                "validated_by_test": True,
            }]
        }))

        import os
        old_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = load_reflexion_entries(skill_md)
            assert isinstance(result, tuple)
            md, ids = result
            assert "REFL-001" in md
            assert "REFL-001" in ids
        finally:
            os.chdir(old_dir)
