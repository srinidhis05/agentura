"""Integration test: prove the feedback loop works end-to-end.

This is the single most important test in the entire platform.
It proves: run → correct → reflexion created → next run sees learned rule.

No LLM calls needed — we test the pipeline, not the model.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def workspace(tmp_path):
    """Create a minimal skill workspace with knowledge layer."""
    # Create skill directory
    skill_dir = tmp_path / "skills" / "test-domain" / "test-skill"
    skill_dir.mkdir(parents=True)

    # Write a minimal SKILL.md
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: test-skill\n"
        "role: specialist\n"
        "domain: test-domain\n"
        "trigger: api\n"
        "model: anthropic/claude-haiku-4.5\n"
        "---\n"
        "\n"
        "You are a test skill. Return JSON.\n"
    )

    # Write DOMAIN.md
    domain_dir = tmp_path / "skills" / "test-domain"
    (domain_dir / "DOMAIN.md").write_text("# Test Domain\nThis is a test domain.\n")

    # Create knowledge layer
    knowledge_dir = tmp_path / ".agentura"
    knowledge_dir.mkdir()

    # Seed with one execution
    (knowledge_dir / "episodic_memory.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "execution_id": "EXEC-TEST-001",
                        "skill": "test-domain/test-skill",
                        "timestamp": "2026-02-20T10:00:00+00:00",
                        "input_summary": {"query": "test input", "order_id": "ORD-123"},
                        "output_summary": {"answer": "wrong answer"},
                        "outcome": "pending_review",
                        "cost_usd": 0.01,
                        "latency_ms": 500,
                        "model_used": "anthropic/claude-haiku-4.5",
                    }
                ]
            },
            indent=2,
        )
    )

    # Empty corrections and reflexions
    (knowledge_dir / "corrections.json").write_text(json.dumps({"corrections": []}))
    (knowledge_dir / "reflexion_entries.json").write_text(json.dumps({"entries": []}))

    # Set env var so SDK finds the knowledge layer
    old_env = os.environ.get("AGENTURA_KNOWLEDGE_DIR")
    os.environ["AGENTURA_KNOWLEDGE_DIR"] = str(knowledge_dir)

    yield {
        "root": tmp_path,
        "skill_dir": skill_dir,
        "skill_md": skill_dir / "SKILL.md",
        "knowledge_dir": knowledge_dir,
    }

    # Cleanup
    if old_env is not None:
        os.environ["AGENTURA_KNOWLEDGE_DIR"] = old_env
    else:
        os.environ.pop("AGENTURA_KNOWLEDGE_DIR", None)


class TestFeedbackLoopEndToEnd:
    """Prove: correct → reflexion → re-injection into system prompt."""

    def test_correction_creates_reflexion(self, workspace):
        """Step 1: Submitting a correction creates a reflexion entry."""
        from agentura_sdk.cli.correct import _store_correction, _generate_reflexion

        correction_id = _store_correction(
            skill_path="test-domain/test-skill",
            execution_id="EXEC-TEST-001",
            correction="The answer should be 42, not wrong answer",
            original_output={"answer": "wrong answer"},
        )

        assert correction_id == "CORR-001"

        reflexion_id = _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id=correction_id,
            original_output={"answer": "wrong answer"},
            correction="The answer should be 42, not wrong answer",
            input_data={"query": "test input", "order_id": "ORD-123"},
        )

        assert reflexion_id == "REFL-001"

        # Verify reflexion was persisted
        refl_data = json.loads(
            (workspace["knowledge_dir"] / "reflexion_entries.json").read_text()
        )
        assert len(refl_data["entries"]) == 1

        entry = refl_data["entries"][0]
        assert entry["reflexion_id"] == "REFL-001"
        assert entry["skill"] == "test-domain/test-skill"
        assert entry["rule"] == "The answer should be 42, not wrong answer"
        assert entry["validated_by_test"] is False
        assert 0.5 <= entry["confidence"] <= 1.0

    def test_reflexion_injected_into_system_prompt(self, workspace):
        """Step 2: Loading the skill after correction includes the reflexion."""
        from agentura_sdk.cli.correct import _store_correction, _generate_reflexion
        from agentura_sdk.runner.skill_loader import load_skill_md

        # First, create correction + reflexion
        correction_id = _store_correction(
            skill_path="test-domain/test-skill",
            execution_id="EXEC-TEST-001",
            correction="UAE orders need LULU escalation path",
            original_output={"answer": "use standard path"},
        )
        _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id=correction_id,
            original_output={"answer": "use standard path"},
            correction="UAE orders need LULU escalation path",
            input_data={"order_id": "AE789"},
        )

        # Now load the skill — reflexion should be in the context
        loaded = load_skill_md(workspace["skill_md"])

        assert loaded.reflexion_context != ""
        assert "Learned Rules" in loaded.reflexion_context
        assert "REFL-001" in loaded.reflexion_context
        assert "UAE orders need LULU escalation path" in loaded.reflexion_context

    def test_composed_prompt_contains_reflexion(self, workspace):
        """Step 3: The final composed prompt (domain + reflexion + skill) includes the rule."""
        from agentura_sdk.cli.correct import _store_correction, _generate_reflexion
        from agentura_sdk.runner.skill_loader import load_skill_md

        # Create correction + reflexion
        correction_id = _store_correction(
            skill_path="test-domain/test-skill",
            execution_id="EXEC-TEST-001",
            correction="Always check compliance flag before processing",
            original_output={"answer": "processed without check"},
        )
        _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id=correction_id,
            original_output={"answer": "processed without check"},
            correction="Always check compliance flag before processing",
        )

        # Load and compose prompt (same logic as cli/run.py and server/app.py)
        skill_md = load_skill_md(workspace["skill_md"])

        prompt_parts = []
        if skill_md.domain_context:
            prompt_parts.append(skill_md.domain_context)
        if skill_md.reflexion_context:
            prompt_parts.append(skill_md.reflexion_context)
        prompt_parts.append(skill_md.system_prompt)
        composed = "\n\n---\n\n".join(prompt_parts)

        # The composed prompt must contain all three layers
        assert "Test Domain" in composed  # DOMAIN.md
        assert "Always check compliance flag" in composed  # Reflexion
        assert "You are a test skill" in composed  # SKILL.md

    def test_multiple_corrections_accumulate(self, workspace):
        """Multiple corrections create multiple reflexion rules, all injected."""
        from agentura_sdk.cli.correct import _store_correction, _generate_reflexion
        from agentura_sdk.runner.skill_loader import load_skill_md

        corrections = [
            "Rule one: always validate input",
            "Rule two: check rate limits",
            "Rule three: log audit trail",
        ]

        for i, corr in enumerate(corrections):
            cid = _store_correction(
                skill_path="test-domain/test-skill",
                execution_id="EXEC-TEST-001",
                correction=corr,
                original_output={"answer": "wrong"},
            )
            _generate_reflexion(
                skill_path="test-domain/test-skill",
                correction_id=cid,
                original_output={"answer": "wrong"},
                correction=corr,
            )

        loaded = load_skill_md(workspace["skill_md"])

        # All three reflexions should be present
        assert "REFL-001" in loaded.reflexion_context
        assert "REFL-002" in loaded.reflexion_context
        assert "REFL-003" in loaded.reflexion_context
        assert "always validate input" in loaded.reflexion_context
        assert "check rate limits" in loaded.reflexion_context
        assert "log audit trail" in loaded.reflexion_context

    def test_correction_stored_correctly(self, workspace):
        """Correction metadata is complete and linked."""
        from agentura_sdk.cli.correct import _store_correction

        cid = _store_correction(
            skill_path="test-domain/test-skill",
            execution_id="EXEC-TEST-001",
            correction="Fix this output",
            original_output={"answer": "bad"},
        )

        data = json.loads(
            (workspace["knowledge_dir"] / "corrections.json").read_text()
        )
        assert len(data["corrections"]) == 1

        c = data["corrections"][0]
        assert c["correction_id"] == cid
        assert c["execution_id"] == "EXEC-TEST-001"
        assert c["skill"] == "test-domain/test-skill"
        assert c["user_correction"] == "Fix this output"
        assert c["original_output"] == {"answer": "bad"}
        assert c["timestamp"]  # Not empty


class TestReflexionQuality:
    """Test that reflexion entries have meaningful derived fields."""

    def test_confidence_high_for_major_correction(self, workspace):
        """Major correction (completely different) = high confidence."""
        from agentura_sdk.cli.correct import _generate_reflexion

        _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id="CORR-001",
            original_output={"answer": "apples oranges bananas"},
            correction="The system should return 404 not found error with retry-after header",
        )

        data = json.loads(
            (workspace["knowledge_dir"] / "reflexion_entries.json").read_text()
        )
        entry = data["entries"][0]
        # Very different content = high confidence
        assert entry["confidence"] >= 0.7

    def test_confidence_lower_for_minor_correction(self, workspace):
        """Minor correction (similar words) = lower confidence."""
        from agentura_sdk.cli.correct import _generate_reflexion

        _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id="CORR-001",
            original_output={"answer": "The order status is pending review"},
            correction="The order status is pending approval not review",
        )

        data = json.loads(
            (workspace["knowledge_dir"] / "reflexion_entries.json").read_text()
        )
        entry = data["entries"][0]
        # Similar content = lower confidence (but still >= 0.5)
        assert 0.5 <= entry["confidence"] <= 0.85

    def test_applies_when_includes_input_keys(self, workspace):
        """applies_when should reference input data keys."""
        from agentura_sdk.cli.correct import _generate_reflexion

        _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id="CORR-001",
            original_output={},
            correction="Fix it",
            input_data={"order_id": "ORD-123", "region": "UAE"},
        )

        data = json.loads(
            (workspace["knowledge_dir"] / "reflexion_entries.json").read_text()
        )
        entry = data["entries"][0]
        assert "order_id" in entry["applies_when"]
        assert "UAE" in entry["applies_when"]

    def test_root_cause_categorization(self, workspace):
        """Root cause should be derived from correction text patterns."""
        from agentura_sdk.cli.correct import _generate_reflexion

        # Test "missing" pattern
        _generate_reflexion(
            skill_path="test-domain/test-skill",
            correction_id="CORR-001",
            original_output={"answer": "incomplete"},
            correction="The response is missing the compliance section",
        )

        data = json.loads(
            (workspace["knowledge_dir"] / "reflexion_entries.json").read_text()
        )
        entry = data["entries"][0]
        assert "omitted" in entry["root_cause"].lower() or "missing" in entry["root_cause"].lower()


class TestSkillLoader:
    """Test skill loading with reflexion injection."""

    def test_load_skill_without_reflexions(self, workspace):
        """Skill loads cleanly with no reflexions."""
        from agentura_sdk.runner.skill_loader import load_skill_md

        loaded = load_skill_md(workspace["skill_md"])

        assert loaded.metadata.name == "test-skill"
        assert loaded.metadata.domain == "test-domain"
        assert loaded.system_prompt == "You are a test skill. Return JSON."
        assert loaded.reflexion_context == ""
        assert "Test Domain" in loaded.domain_context

    def test_load_skill_with_domain_context(self, workspace):
        """DOMAIN.md is loaded from parent directory."""
        from agentura_sdk.runner.skill_loader import load_skill_md

        loaded = load_skill_md(workspace["skill_md"])
        assert "Test Domain" in loaded.domain_context

    def test_skill_name_matching(self, workspace):
        """Reflexion matching works with domain/skill format."""
        from agentura_sdk.runner.skill_loader import load_reflexion_entries

        # Write a reflexion entry
        refl_data = {
            "entries": [
                {
                    "reflexion_id": "REFL-001",
                    "correction_id": "CORR-001",
                    "skill": "test-domain/test-skill",
                    "rule": "Test rule",
                    "applies_when": "Always",
                    "confidence": 0.9,
                    "validated_by_test": False,
                }
            ]
        }
        (workspace["knowledge_dir"] / "reflexion_entries.json").write_text(
            json.dumps(refl_data)
        )

        result = load_reflexion_entries(workspace["skill_md"])
        assert "REFL-001" in result
        assert "Test rule" in result

    def test_unrelated_skill_reflexions_excluded(self, workspace):
        """Reflexions for other skills are not injected."""
        from agentura_sdk.runner.skill_loader import load_reflexion_entries

        refl_data = {
            "entries": [
                {
                    "reflexion_id": "REFL-001",
                    "skill": "other-domain/other-skill",
                    "rule": "Should not appear",
                    "applies_when": "Never",
                    "confidence": 0.9,
                    "validated_by_test": False,
                }
            ]
        }
        (workspace["knowledge_dir"] / "reflexion_entries.json").write_text(
            json.dumps(refl_data)
        )

        result = load_reflexion_entries(workspace["skill_md"])
        assert result == ""


class TestTestGeneration:
    """Test that corrections generate regression tests."""

    def test_deepeval_test_generated(self, workspace):
        """DeepEval test file is created from correction."""
        from agentura_sdk.testing.deepeval_runner import generate_test_from_correction

        test_file = generate_test_from_correction(
            skill_dir=workspace["skill_dir"],
            input_data={"query": "test"},
            actual_output={"answer": "wrong"},
            corrected_output={"correction": "right"},
        )

        assert test_file.exists()
        assert "test_correction_1" in test_file.name
        content = test_file.read_text()
        assert "def test_correction_1" in content
        assert "deepeval" in content

    def test_promptfoo_test_generated(self, workspace):
        """Promptfoo YAML test is created from correction."""
        from agentura_sdk.testing.test_generator import generate_promptfoo_test

        test_file = generate_promptfoo_test(
            skill_dir=workspace["skill_dir"],
            input_data={"query": "test"},
            expected_output={"correction": "right"},
            description="Test correction",
        )

        assert test_file.exists()
        assert test_file.name == "corrections.yaml"

        import yaml

        data = yaml.safe_load(test_file.read_text())
        assert len(data["tests"]) == 1
        assert data["tests"][0]["description"] == "Test correction"
