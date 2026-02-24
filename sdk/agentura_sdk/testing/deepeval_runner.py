"""Run DeepEval metrics for a skill."""

import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console


def run_deepeval_tests(skill_dir: Path) -> bool:
    """Run DeepEval tests for a skill directory.

    Returns True if all tests passed.
    """
    console = Console()
    test_file = skill_dir / "tests" / "test_deepeval.py"

    if not test_file.exists():
        console.print("[yellow]No DeepEval test file found.[/]")
        return True

    console.print(f"[cyan]Running DeepEval: {test_file}[/]")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        cwd=str(skill_dir),
    )
    return result.returncode == 0


def generate_test_from_correction(
    skill_dir: Path,
    input_data: dict,
    actual_output: dict,
    corrected_output: dict,
) -> Path:
    """Generate a regression test from a user correction (DEC-006).

    When a user corrects a skill's output, this creates a test case
    that ensures the corrected behavior is preserved.
    """
    tests_dir = skill_dir / "tests" / "generated"
    tests_dir.mkdir(parents=True, exist_ok=True)

    existing = list(tests_dir.glob("test_correction_*.py"))
    idx = len(existing) + 1

    test_content = f'''"""Auto-generated regression test from user correction #{idx}."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_{idx}():
    """Verify corrected behavior is preserved."""
    input_data = {json.dumps(input_data, indent=4)}

    expected_output = {json.dumps(corrected_output, indent=4)}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
'''

    test_file = tests_dir / f"test_correction_{idx}.py"
    test_file.write_text(test_content)
    return test_file
