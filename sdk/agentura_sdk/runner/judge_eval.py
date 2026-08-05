"""Measure judge quality: agreement between judge scores and human ratings. Pure, no I/O.

# NOTE: wiring to real (human_rating, judge_score) pairs from the DB + an endpoint is
# deferred until judge_score persistence is confirmed and labeled data exists (dev-serve).
"""
from __future__ import annotations


def score_agreement(pairs) -> dict:
    """pairs: iterable of (human_rating, judge_score). Returns agreement metrics.
    verdict: 'trustworthy' if >=75% within-1 (n>=20), else 'weak' (n>=20), else 'insufficient data'."""
    clean = [(float(h), float(j)) for h, j in pairs if h is not None and j is not None]
    n = len(clean)
    if n == 0:
        return {"n": 0, "exact_rate": 0.0, "within1_rate": 0.0, "mae": 0.0, "pearson": 0.0, "verdict": "insufficient data"}
    exact = sum(1 for h, j in clean if round(h) == round(j)) / n
    within1 = sum(1 for h, j in clean if abs(h - j) <= 1.0) / n
    mae = sum(abs(h - j) for h, j in clean) / n
    mh = sum(h for h, _ in clean) / n
    mj = sum(j for _, j in clean) / n
    cov = sum((h - mh) * (j - mj) for h, j in clean)
    vh = sum((h - mh) ** 2 for h, _ in clean)
    vj = sum((j - mj) ** 2 for _, j in clean)
    pearson = cov / ((vh * vj) ** 0.5) if vh > 0 and vj > 0 else 0.0
    if n >= 20:
        verdict = "trustworthy" if within1 >= 0.75 else "weak"
    else:
        verdict = "insufficient data"
    return {"n": n, "exact_rate": round(exact, 3), "within1_rate": round(within1, 3),
            "mae": round(mae, 3), "pearson": round(pearson, 3), "verdict": verdict}
