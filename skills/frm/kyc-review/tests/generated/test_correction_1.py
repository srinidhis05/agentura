"""Auto-generated regression test from user correction #1."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_1():
    """Verify corrected behavior is preserved."""
    input_data = {
    "customer_id": "UAE-CUST-8812",
    "customer_type": "corporate",
    "jurisdiction": "UAE",
    "documents": [
        "trade_license",
        "passport",
        "bank_statement"
    ]
}

    expected_output = {
    "correction": "For UAE corporate KYC reviews, ALWAYS check DFSA (Dubai Financial Services Authority) sanctions list before proceeding. UAE corporates require mandatory DFSA screening plus UBO verification for any shareholder with >25% ownership. Missing DFSA check is a compliance violation."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
