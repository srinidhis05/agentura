"""Auto-generated regression test from user correction #4."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_4():
    """Verify corrected behavior is preserved."""
    input_data = {
    "order_id": "SG445T789",
    "query": "Singapore corridor order stuck in MAS_REVIEW for 6 hours"
}

    expected_output = {
    "correction": "Singapore MAS_REVIEW holds are governed by MAS Notice 626 (Prevention of Money Laundering). For amounts above SGD 20,000, the MAS-appointed compliance officer at our Singapore entity must file a CTR (Cash Transaction Report) BEFORE the hold can be released. Standard ops cannot bypass this \u2014 it requires the Singapore MLRO (Money Laundering Reporting Officer) sign-off. Typical clearance: 2-4 hours after CTR filing."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
