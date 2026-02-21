"""Auto-generated regression test from user correction #2."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_2():
    """Verify corrected behavior is preserved."""
    input_data = {
    "risk_profile": "moderate",
    "investment_amount": 500000,
    "currency": "INR",
    "goals": [
        "retirement",
        "wealth_preservation"
    ],
    "horizon_years": 15
}

    expected_output = {
    "correction": "For Indian investors aged 55+, NEVER allocate more than 20% to equities. RBI guidelines recommend conservative allocation for pre-retirement. Also, always include gold (Sovereign Gold Bonds) as 10-15% allocation for Indian investors as inflation hedge \u2014 this is culturally important and financially sound."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
