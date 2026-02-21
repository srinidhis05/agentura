"""Auto-generated regression test from user correction #2."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_2():
    """Verify corrected behavior is preserved."""
    input_data = {
    "order_id": "AE789X123",
    "query": "UAE corridor order stuck in CNR_RESERVED"
}

    expected_output = {
    "correction": "UK corridor orders in COMPLIANCE_HOLD must be escalated to the FCA Regulatory Affairs team, not generic Compliance Operations. FCA holds require a specific SAR (Suspicious Activity Report) filing check within 4 hours. Standard compliance team cannot clear FCA holds \u2014 only the FCA liaison officer has authority."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
