"""Tests for the judge validation harness (score_agreement)."""

from __future__ import annotations


def test_score_agreement_empty():
    from agentura_sdk.runner.judge_eval import score_agreement
    r = score_agreement([])
    assert r["n"] == 0 and r["verdict"] == "insufficient data"


def test_score_agreement_perfect():
    from agentura_sdk.runner.judge_eval import score_agreement
    pairs = [(float(i % 5 + 1), float(i % 5 + 1)) for i in range(30)]
    r = score_agreement(pairs)
    assert r["exact_rate"] == 1.0 and r["within1_rate"] == 1.0 and r["verdict"] == "trustworthy"


def test_score_agreement_off_by_one():
    from agentura_sdk.runner.judge_eval import score_agreement
    pairs = [(3.0, 4.0)] * 30
    r = score_agreement(pairs)
    assert r["within1_rate"] == 1.0 and r["exact_rate"] == 0.0


def test_score_agreement_weak():
    from agentura_sdk.runner.judge_eval import score_agreement
    pairs = [(1.0, 5.0)] * 30
    r = score_agreement(pairs)
    assert r["within1_rate"] == 0.0 and r["verdict"] == "weak"
