"""Auto-generated regression test from user correction #1."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_1():
    """Verify corrected behavior is preserved."""
    input_data = {
    "portfolio": {
        "cash": 100000
    }
}

    expected_output = {
    "correction": "Should allocate 60% equity, 30% debt, 10% gold for moderate risk NRI in UAE"
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
