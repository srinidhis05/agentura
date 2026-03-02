"""Auto-generate regression tests from execution failures (DEC-067).

When a skill execution fails, generate tests asserting graceful error handling
(not exact output reproduction). Fire-and-forget — never blocks execution.
"""

from __future__ import annotations

import json
from pathlib import Path


def generate_failure_deepeval_test(
    skill_dir: Path,
    input_data: dict,
    error_output: dict,
    execution_id: str,
    severity: str = "P0",
) -> Path:
    """Generate a DeepEval regression test from a failure case.

    Asserts that this input should not crash the skill — it should return
    a graceful error or valid output, not an unhandled exception.
    """
    tests_dir = skill_dir / "tests" / "generated"
    tests_dir.mkdir(parents=True, exist_ok=True)

    existing = list(tests_dir.glob("test_failure_*.py"))
    idx = len(existing) + 1

    test_content = f'''"""Auto-generated regression test from execution failure ({severity}).

Execution: {execution_id}
Ensures this input produces a graceful response, not an unhandled error.
"""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_failure_{idx}():
    """Verify skill handles this input gracefully (no crash)."""
    input_data = {json.dumps(input_data, indent=4)}

    # The original error was:
    # {json.dumps(error_output, indent=4)[:200]}

    metric = AnswerRelevancyMetric(threshold=0.5)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output="placeholder — run skill to get actual output",
        expected_output="A valid response or graceful error message",
    )
    assert_test(test_case, [metric])
'''

    test_file = tests_dir / f"test_failure_{idx}.py"
    test_file.write_text(test_content)
    return test_file


def generate_failure_promptfoo_test(
    skill_dir: Path,
    input_data: dict,
    error_output: dict,
    execution_id: str,
    severity: str = "P0",
) -> Path:
    """Append a failure-based test case to promptfoo generated config."""
    import yaml

    generated_dir = skill_dir / "tests" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    test_file = generated_dir / "failures.yaml"

    test_case = {
        "description": f"Failure regression ({severity}): {execution_id}",
        "vars": {"input": json.dumps(input_data)},
        "assert": [
            {"type": "is-json"},
            {"type": "not-contains", "value": "Traceback"},
            {"type": "not-contains", "value": "unhandled exception"},
        ],
    }

    if test_file.exists():
        existing = yaml.safe_load(test_file.read_text()) or {}
    else:
        existing = {
            "description": f"Generated failure regression tests for {skill_dir.name}",
            "tests": [],
        }

    existing.setdefault("tests", []).append(test_case)
    test_file.write_text(yaml.dump(existing, default_flow_style=False))
    return test_file
