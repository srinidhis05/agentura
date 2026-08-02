"""Independent model evaluation with rubrics (judge never produces — only evaluates).

The judge runs AFTER the agent completes, using a DIFFERENT model to evaluate
the agent's output against a rubric. This provides an independent quality gate
that cannot be gamed by the producing model.
"""

from __future__ import annotations

import re


def build_judge_prompt(rubric: str, output_text: str) -> str:
    """Construct the evaluation prompt for independent model judging.

    The judge should respond with EXACTLY:
    SCORE: <number 1-5>
    REASONING: <text>
    """
    return f"""## Independent Evaluation

You are an independent evaluator. Your job is to score the output below
against the provided rubric. You NEVER produce or modify content — you
only evaluate.

### Rubric

{rubric}

### Output to Evaluate

{output_text[:4000]}

### Scoring Scale

1 = Poor — fails most rubric dimensions
2 = Below acceptable — significant gaps
3 = Acceptable — meets minimum bar
4 = Good — solid quality, minor gaps
5 = Excellent — exceeds expectations on all dimensions

### Instructions

Respond in EXACTLY this format (nothing else):

SCORE: <number 1-5>
REASONING: <one paragraph explaining your score against each rubric dimension>

Be strict. A score of 3.0 means "acceptable", 4.0 means "good", 5.0 means "excellent".
Most outputs should score 2-4. Reserve 5 for genuinely excellent work."""


def parse_judge_response(text: str) -> tuple[float | None, str]:
    """Parse SCORE and REASONING from judge response.

    Returns (score, reasoning) where:
    - score is a float 1-5, or None if unparseable
    - reasoning is the extracted reasoning text, or the raw text if unparseable
    """
    text = text.strip()

    # Extract SCORE
    score_match = re.search(r"SCORE:\s*([\d.]+)", text, re.IGNORECASE)
    score: float | None = None
    if score_match:
        try:
            score = float(score_match.group(1))
        except ValueError:
            pass

    # Extract REASONING
    reasoning_match = re.search(
        r"REASONING:\s*(.*)", text, re.IGNORECASE | re.DOTALL
    )
    reasoning = reasoning_match.group(1).strip() if reasoning_match else text

    return score, reasoning
