"""Auto-generated regression test from user correction #3."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_3():
    """Verify corrected behavior is preserved."""
    input_data = {
    "order_id": "IN567R234",
    "query": "India inward remittance stuck in RBI_HOLD sub-state for 12 hours"
}

    expected_output = {
    "correction": "India inward remittances in RBI_HOLD MUST go through the Authorized Dealer (AD) bank route, not generic RBI Liaison. The AD bank is the only entity authorized to release RBI holds under FEMA Section 6. Always check FEMA purpose code (P0103 for family maintenance, P0107 for personal gifts) as wrong purpose code is the #1 reason for RBI holds on India corridors. Escalation goes to AD Bank compliance desk, not our internal team."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
