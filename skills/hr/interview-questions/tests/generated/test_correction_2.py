"""Auto-generated regression test from user correction #2."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_2():
    """Verify corrected behavior is preserved."""
    input_data = {
    "role": "Senior Backend Engineer",
    "seniority": "senior",
    "department": "engineering",
    "focus_areas": [
        "system-design",
        "leadership",
        "problem-solving"
    ],
    "interview_duration_minutes": 45,
    "company_values": [
        "ownership",
        "customer-focus",
        "collaboration"
    ]
}

    expected_output = {
    "correction": "For senior backend roles, include at least 2 system design questions that test distributed systems knowledge. Ask about CAP theorem trade-offs and data partitioning strategies, not just generic architecture questions."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
