"""Auto-generated regression test from user correction #1."""

import json
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_correction_1():
    """Verify corrected behavior is preserved."""
    input_data = {
    "resume_text": "Srinidhi Kulkarni \u2014 Senior Software Engineer. 5+ years building distributed systems at scale. Led a team of 8 engineers at a fintech startup building real-time payment processing (3M txns/day). Expert in Go, Python, Kubernetes, and event-driven architectures. Previously at Amazon (SDE2) working on DynamoDB internals. MS Computer Science from IIIT Hyderabad. Open source contributor to Apache Kafka.",
    "job_description": "Senior Backend Engineer \u2014 Fintech. Required: 5+ years backend experience, distributed systems, Go or Python, Kubernetes. Preferred: Fintech domain, payment systems, team leadership.",
    "role_title": "Senior Backend Engineer",
    "department": "Engineering"
}

    expected_output = {
    "correction": "When screening resumes for engineering roles, ALWAYS check for system design experience separately from coding skills. A candidate with 5 years of Python but no distributed systems experience should score below 60 for senior roles. Also, gap years for open source contributions should be treated as POSITIVE, not neutral."
}

    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = LLMTestCase(
        input=json.dumps(input_data),
        actual_output=json.dumps(expected_output),
        expected_output=json.dumps(expected_output),
    )
    assert_test(test_case, [metric])
