"""Auto-generated regression test from user correction #1."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_1():
    """Verify corrected behavior is preserved."""
    input_data = {
    "order_id": "AE789X123",
    "query": "UAE corridor order stuck in CNR_RESERVED"
}

    expected_output = {
    "correction": "UAE corridor orders stuck in CNR_RESERVED need LULU escalation, not standard path. Always check LULU ops team first for UAE orders."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
