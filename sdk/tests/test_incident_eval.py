"""Tests for incident-to-eval synthesis (DEC-067)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from agentura_sdk.testing.failure_case_generator import (
    generate_failure_deepeval_test,
    generate_failure_promptfoo_test,
)
from agentura_sdk.testing.incident_eval import maybe_generate_failure_tests
from agentura_sdk.types import SkillContext, SkillResult, SkillRole


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    d = tmp_path / "skills" / "dev" / "deployer"
    d.mkdir(parents=True)
    return d


class TestFailureCaseGenerator:
    def test_generate_deepeval_test(self, skill_dir: Path):
        test_file = generate_failure_deepeval_test(
            skill_dir=skill_dir,
            input_data={"task": "deploy todo app"},
            error_output={"error": "pod crash loop"},
            execution_id="EXEC-001",
            severity="P0",
        )
        assert test_file.exists()
        assert "test_failure_1" in test_file.name
        content = test_file.read_text()
        assert "def test_failure_1" in content
        assert "EXEC-001" in content

    def test_generate_promptfoo_test(self, skill_dir: Path):
        test_file = generate_failure_promptfoo_test(
            skill_dir=skill_dir,
            input_data={"task": "deploy"},
            error_output={"error": "timeout"},
            execution_id="EXEC-002",
        )
        assert test_file.exists()
        data = yaml.safe_load(test_file.read_text())
        assert len(data["tests"]) == 1
        assert "EXEC-002" in data["tests"][0]["description"]

    def test_incrementing_test_indices(self, skill_dir: Path):
        for i in range(3):
            generate_failure_deepeval_test(
                skill_dir=skill_dir,
                input_data={"task": f"task-{i}"},
                error_output={"error": f"error-{i}"},
                execution_id=f"EXEC-{i:03d}",
            )
        gen_dir = skill_dir / "tests" / "generated"
        files = sorted(gen_dir.glob("test_failure_*.py"))
        assert len(files) == 3


class TestIncidentEvalHook:
    def test_skips_on_success(self, skill_dir: Path):
        """Hook should do nothing for successful executions."""
        ctx = SkillContext(
            skill_name="deployer",
            domain="dev",
            role=SkillRole.AGENT,
        )
        result = SkillResult(skill_name="deployer", success=True)
        # Should return immediately without error
        maybe_generate_failure_tests(ctx, result, skill_dir.parent.parent)

    def test_skips_without_config(self, skill_dir: Path):
        """Hook should skip if no config file exists."""
        ctx = SkillContext(
            skill_name="deployer",
            domain="dev",
            role=SkillRole.AGENT,
        )
        result = SkillResult(
            skill_name="deployer",
            success=False,
            output={"error": "crash"},
        )
        # No config file — should not raise
        maybe_generate_failure_tests(ctx, result, skill_dir.parent.parent)

    def test_skips_when_not_opted_in(self, skill_dir: Path):
        """Hook should skip when capture_failure_cases is False."""
        config_path = skill_dir / "agentura.config.yaml"
        config_path.write_text(yaml.dump({"feedback": {"capture_failure_cases": False}}))

        ctx = SkillContext(
            skill_name="deployer",
            domain="dev",
            role=SkillRole.AGENT,
        )
        result = SkillResult(
            skill_name="deployer",
            success=False,
            output={"error": "crash"},
        )
        # Should return without generating tests
        maybe_generate_failure_tests(ctx, result, skill_dir.parent.parent)
        gen_dir = skill_dir / "tests" / "generated"
        assert not gen_dir.exists()
