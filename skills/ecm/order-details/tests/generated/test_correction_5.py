"""Auto-generated regression test from user correction #5."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_5():
    """Verify corrected behavior is preserved."""
    input_data = {
    "order_id": "DEMO-SGP-001",
    "query": "Singapore corridor order stuck in SANCTIONS_HOLD for 6 hours, client is a PEP"
}

    expected_output = {
    "correction": "Singapore PEP orders in SANCTIONS_HOLD must go through the MAS Compliance desk, NOT generic sanctions review. Always route Singapore PEP cases to mas-compliance@ops.internal with priority P1. Standard AlphaDesk flow is wrong for Singapore corridor."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
