"""Self-critique evaluator loop — shared verify logic (DEC-069).

After an agent completes its task, run a verification pass against explicit criteria.
If issues are found, feed critique back for one retry.
"""

from __future__ import annotations

import re


def build_verify_prompt(criteria: list[str], output_text: str) -> str:
    """Construct the critique prompt for post-execution verification.

    The agent should respond with either:
    - VERIFIED: <confirmation>
    - ISSUES: <list of issues>
    """
    criteria_block = "\n".join(f"- {c}" for c in criteria)
    return f"""## Post-Execution Verification

Review the output below against these criteria:

{criteria_block}

### Output to Verify

{output_text[:4000]}

### Instructions

If ALL criteria are satisfied, respond with:
VERIFIED: <one-line confirmation>

If ANY criteria are NOT satisfied, respond with:
ISSUES: <numbered list of specific issues found>

Be strict. Only respond VERIFIED if you are confident all criteria pass."""


def parse_verify_response(text: str) -> tuple[bool, list[str]]:
    """Parse the verification response.

    Returns (passed, issues) where:
    - passed=True if VERIFIED, False if ISSUES
    - issues is a list of issue strings (empty if verified)
    """
    text = text.strip()

    # Check for VERIFIED first
    if re.match(r"^VERIFIED:", text, re.IGNORECASE):
        return True, []

    # Check for ISSUES
    issues_match = re.match(r"^ISSUES:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    if issues_match:
        issues_text = issues_match.group(1).strip()
        # Parse numbered or bulleted list
        issues = []
        for line in issues_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Strip numbering/bullets
            cleaned = re.sub(r"^[\d]+[.)\-]\s*", "", line).strip()
            cleaned = re.sub(r"^[-*]\s*", "", cleaned).strip()
            if cleaned:
                issues.append(cleaned)
        return False, issues if issues else [issues_text]

    # If no clear signal, assume issues
    return False, [text[:200]]
