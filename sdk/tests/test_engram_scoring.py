"""Tests for Engram rubric-scored rule lifecycle.

Engram concept: rules are the adaptive memory layer. SKILL.md is stable
(human-owned). Rules are system-owned, individually scored, auto-retired
when evidence fades.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agentura_sdk.memory.json_store import JSONStore


@pytest.fixture
def store(tmp_path: Path) -> JSONStore:
    return JSONStore(knowledge_dir=tmp_path)


def _add_reflexion(store: JSONStore, skill: str, rid: str, **kwargs) -> str:
    data = {
        "reflexion_id": rid,
        "rule": f"Rule for {rid}",
        "applies_when": "always",
        "confidence": 0.8,
    }
    data.update(kwargs)
    return store.add_reflexion(skill, data)


class TestRubricScoring:
    def test_score_reflexion_with_rubric_computes_weighted_average(self, store: JSONStore):
        """Rubric scoring should compute weighted average normalized to 0-1."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        rubric = {"accuracy": 4.0, "relevance": 3.5, "actionability": 4.5}

        composite = store.score_reflexion_with_rubric("REFL-001", rubric)

        # All weights are 1.0, so average = (4.0 + 3.5 + 4.5) / 3 / 5.0 = 0.8
        assert abs(composite - 0.8) < 0.01

        # Verify stored on the reflexion
        entries = store.get_reflexions("dev/deployer")
        assert entries[0]["rubric_scores"] == rubric
        assert abs(entries[0]["utility_score"] - 0.8) < 0.01

    def test_score_reflexion_updates_last_fired_at(self, store: JSONStore):
        """Scoring a reflexion should update last_fired_at."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        store.score_reflexion_with_rubric("REFL-001", {"accuracy": 5.0})

        entries = store.get_reflexions("dev/deployer")
        assert entries[0].get("last_fired_at") is not None

    def test_score_with_custom_dimensions(self, store: JSONStore):
        """Custom rubric dimensions not in RUBRIC_WEIGHTS use weight 1.0."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        rubric = {"accuracy": 5.0, "custom_dim": 2.5}

        composite = store.score_reflexion_with_rubric("REFL-001", rubric)

        # accuracy weight=1.0, custom_dim weight=1.0
        # (5.0*1.0 + 2.5*1.0) / 2.0 / 5.0 = 0.75
        assert abs(composite - 0.75) < 0.01

    def test_score_perfect_rubric(self, store: JSONStore):
        """All 5.0 scores should yield composite of 1.0."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        rubric = {"accuracy": 5.0, "relevance": 5.0, "actionability": 5.0}

        composite = store.score_reflexion_with_rubric("REFL-001", rubric)
        assert abs(composite - 1.0) < 0.01


class TestTimeBasedDecay:
    def test_recent_rule_no_decay(self, store: JSONStore):
        """A rule created just now should have minimal decay."""
        _add_reflexion(store, "dev/deployer", "REFL-001", utility_score=0.8)

        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        assert len(top) == 1

    def test_old_rule_decays_score(self, store: JSONStore):
        """A rule not fired in 25 days should have significantly decayed score."""
        old_time = (datetime.now(timezone.utc) - timedelta(days=25)).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.5,
            last_fired_at=old_time,
            created_at=old_time,
        )

        # decay_factor = max(0.1, 1.0 - 25/30) ≈ 0.167
        # decayed_score = 0.5 * 0.167 ≈ 0.083
        # This should fall below default min_score of 0.3
        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        assert len(top) == 0

    def test_very_old_rule_floors_at_ten_percent(self, store: JSONStore):
        """A rule not fired in 60 days should decay to 10% floor, not zero."""
        old_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=1.0,
            last_fired_at=old_time,
            created_at=old_time,
        )

        # decay_factor = max(0.1, 1.0 - 60/30) = max(0.1, -1.0) = 0.1
        # decayed_score = 1.0 * 0.1 = 0.1
        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.05)
        assert len(top) == 1
        # But should be excluded at normal min_score
        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        assert len(top) == 0

    def test_recently_fired_rule_retains_score(self, store: JSONStore):
        """A rule fired today should retain nearly full score."""
        now = datetime.now(timezone.utc).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.8,
            last_fired_at=now,
        )

        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.7)
        assert len(top) == 1


class TestAutoRetirement:
    def test_retire_stale_reflexions_retires_low_score(self, store: JSONStore):
        """Reflexions with decayed score below threshold get retired."""
        old_time = (datetime.now(timezone.utc) - timedelta(days=25)).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.5,
            last_fired_at=old_time,
            created_at=old_time,
        )
        _add_reflexion(
            store, "dev/deployer", "REFL-002",
            utility_score=0.9,
            last_fired_at=datetime.now(timezone.utc).isoformat(),
        )

        retired = store.retire_stale_reflexions("dev/deployer", min_score=0.3, max_age_days=30)

        assert "REFL-001" in retired
        assert "REFL-002" not in retired

    def test_retired_rules_excluded_from_get_top_reflexions(self, store: JSONStore):
        """Retired reflexions should not appear in get_top_reflexions."""
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.9,
            status="retired",
        )
        _add_reflexion(
            store, "dev/deployer", "REFL-002",
            utility_score=0.7,
        )

        top = store.get_top_reflexions("dev/deployer", limit=5, min_score=0.3)
        ids = [e["reflexion_id"] for e in top]
        assert "REFL-001" not in ids
        assert "REFL-002" in ids

    def test_retire_returns_retired_ids(self, store: JSONStore):
        """retire_stale_reflexions should return the list of retired IDs."""
        old_time = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.4,
            last_fired_at=old_time,
            created_at=old_time,
        )
        _add_reflexion(
            store, "dev/deployer", "REFL-002",
            utility_score=0.4,
            last_fired_at=old_time,
            created_at=old_time,
        )

        retired = store.retire_stale_reflexions("dev/deployer", min_score=0.3, max_age_days=30)

        assert len(retired) == 2
        assert "REFL-001" in retired
        assert "REFL-002" in retired

    def test_retire_only_affects_target_skill(self, store: JSONStore):
        """Retirement should be scoped to the specified skill."""
        old_time = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.4,
            last_fired_at=old_time,
            created_at=old_time,
        )
        _add_reflexion(
            store, "dev/reviewer", "REFL-002",
            utility_score=0.4,
            last_fired_at=old_time,
            created_at=old_time,
        )

        retired = store.retire_stale_reflexions("dev/deployer", min_score=0.3, max_age_days=30)

        assert "REFL-001" in retired
        assert "REFL-002" not in retired

    def test_already_retired_not_re_retired(self, store: JSONStore):
        """Already retired reflexions should not be processed again."""
        old_time = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.4,
            status="retired",
            last_fired_at=old_time,
            created_at=old_time,
        )

        retired = store.retire_stale_reflexions("dev/deployer", min_score=0.3, max_age_days=30)
        assert len(retired) == 0


class TestPromotion:
    def test_promote_reflexion_to_domain(self, store: JSONStore):
        """Promotion should change scope to domain and status to promoted."""
        _add_reflexion(store, "dev/deployer", "REFL-001", scope="skill")

        store.promote_reflexion("REFL-001", "domain")

        entries = store.get_reflexions("dev/deployer")
        assert entries[0]["scope"] == "domain"
        assert entries[0]["status"] == "promoted"

    def test_promote_reflexion_to_org(self, store: JSONStore):
        """Promotion to org scope should work."""
        _add_reflexion(store, "dev/deployer", "REFL-001", scope="skill")

        store.promote_reflexion("REFL-001", "org")

        entries = store.get_reflexions("dev/deployer")
        assert entries[0]["scope"] == "org"

    def test_promote_invalid_scope_raises(self, store: JSONStore):
        """Promotion to invalid scope should raise ValueError."""
        _add_reflexion(store, "dev/deployer", "REFL-001")

        with pytest.raises(ValueError, match="Invalid promotion target scope"):
            store.promote_reflexion("REFL-001", "invalid")

    def test_promoted_rule_visible_across_skills_in_domain(self, store: JSONStore):
        """A domain-promoted rule should be visible to other skills in the same domain."""
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.8,
            scope="skill",
        )
        store.promote_reflexion("REFL-001", "domain")

        # Query from a different skill in the same domain
        top = store.get_top_reflexions_with_scope("dev/reviewer", limit=5, min_score=0.3)
        ids = [e["reflexion_id"] for e in top]
        assert "REFL-001" in ids


class TestJudgeVerdictReflexion:
    def test_judge_verdict_creates_reflexion_with_rubric(self, store: JSONStore):
        """Simulates a judge verdict creating a reflexion with rubric_scores."""
        rubric = {"accuracy": 4.0, "relevance": 3.5, "actionability": 4.5}
        rid = store.add_reflexion("dev/deployer", {
            "reflexion_id": "REFL-JUDGE-001",
            "rule": "Always validate input schema before processing",
            "applies_when": "receiving external API payloads",
            "confidence": 0.85,
            "source": "judge-verdict",
            "rubric_scores": rubric,
        })

        entries = store.get_reflexions("dev/deployer")
        judge_entry = next(e for e in entries if e["reflexion_id"] == rid)
        assert judge_entry["source"] == "judge-verdict"
        assert judge_entry["rubric_scores"] == rubric

    def test_low_score_judge_creates_low_confidence_reflexion(self, store: JSONStore):
        """A low judge score should create a reflexion with lower confidence."""
        rid = store.add_reflexion("dev/deployer", {
            "reflexion_id": "REFL-JUDGE-002",
            "rule": "Consider caching API responses",
            "applies_when": "making repeated API calls",
            "confidence": 0.3,
            "source": "judge-verdict",
            "rubric_scores": {"accuracy": 2.0, "relevance": 1.5, "actionability": 2.0},
        })

        entries = store.get_reflexions("dev/deployer")
        judge_entry = next(e for e in entries if e["reflexion_id"] == rid)
        assert judge_entry["confidence"] == 0.3
        assert judge_entry["source"] == "judge-verdict"

    def test_judge_score_updates_utility(self, store: JSONStore):
        """Scoring a judge-created reflexion with rubric should update utility_score."""
        _add_reflexion(
            store, "dev/deployer", "REFL-JUDGE-003",
            source="judge-verdict",
        )

        rubric = {"accuracy": 5.0, "relevance": 5.0, "actionability": 5.0}
        composite = store.score_reflexion_with_rubric("REFL-JUDGE-003", rubric)

        assert abs(composite - 1.0) < 0.01

        entries = store.get_reflexions("dev/deployer")
        entry = next(e for e in entries if e["reflexion_id"] == "REFL-JUDGE-003")
        assert abs(entry["utility_score"] - 1.0) < 0.01


class TestScopeWithDecay:
    def test_get_top_reflexions_with_scope_excludes_retired(self, store: JSONStore):
        """Retired rules should not appear in scoped queries."""
        _add_reflexion(
            store, "dev/deployer", "REFL-001",
            utility_score=0.9,
            status="retired",
        )
        _add_reflexion(
            store, "dev/deployer", "REFL-002",
            utility_score=0.7,
        )

        top = store.get_top_reflexions_with_scope("dev/deployer", limit=5, min_score=0.3)
        ids = [e["reflexion_id"] for e in top]
        assert "REFL-001" not in ids
        assert "REFL-002" in ids

    def test_org_scoped_rule_visible_everywhere(self, store: JSONStore):
        """An org-scoped rule should be visible to any skill."""
        _add_reflexion(
            store, "dev/deployer", "REFL-ORG",
            utility_score=0.8,
            scope="org",
        )

        top = store.get_top_reflexions_with_scope("finance/analyzer", limit=5, min_score=0.3)
        ids = [e["reflexion_id"] for e in top]
        assert "REFL-ORG" in ids


class TestDefaultFieldsOnAdd:
    def test_add_reflexion_sets_default_status(self, store: JSONStore):
        """New reflexions should default to status='active'."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        entries = store.get_reflexions("dev/deployer")
        assert entries[0]["status"] == "active"

    def test_add_reflexion_sets_default_scope(self, store: JSONStore):
        """New reflexions should default to scope='skill'."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        entries = store.get_reflexions("dev/deployer")
        assert entries[0]["scope"] == "skill"

    def test_add_reflexion_sets_default_source(self, store: JSONStore):
        """New reflexions should default to source='correction'."""
        _add_reflexion(store, "dev/deployer", "REFL-001")
        entries = store.get_reflexions("dev/deployer")
        assert entries[0]["source"] == "correction"
