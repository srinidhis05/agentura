"""Memory synthesis from execution logs (DEC-068).

Reads execution history, groups failures by skill, sends patterns to a cheap LLM,
and generates candidate reflexion rules automatically.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Maximum entries to summarize per skill
_MAX_ENTRIES_PER_SKILL = 20
# Maximum error text length
_MAX_ERROR_LEN = 200


@dataclass
class SynthesisCandidate:
    rule: str
    applies_when: str
    pattern_count: int
    skill: str


@dataclass
class SynthesisResult:
    executions_analyzed: int = 0
    skills_analyzed: int = 0
    candidates: list[SynthesisCandidate] = field(default_factory=list)
    duplicates_skipped: int = 0
    stored_count: int = 0


_SYNTHESIS_PROMPT = """You are analyzing execution logs to find recurring failure patterns.

For each skill below, I'll show you recent failures and corrections. Find patterns that repeat across multiple executions.

## Execution Logs

{logs_section}

## Instructions

Extract actionable rules that would prevent these failures from recurring. Only include rules where you see the pattern appear {min_count}+ times.

Return a JSON array of objects:
```json
[
  {{
    "rule": "Always do X when Y",
    "applies_when": "condition when this rule applies",
    "pattern_count": 3,
    "skill": "domain/skill-name"
  }}
]
```

Return ONLY the JSON array. No explanation. If no patterns found, return `[]`."""


def synthesize(
    skill_filter: str | None = None,
    since_hours: int = 168,
    dry_run: bool = False,
    min_pattern_count: int = 3,
) -> SynthesisResult:
    """Run memory synthesis across execution history.

    Args:
        skill_filter: Restrict to a specific skill path (domain/name).
        since_hours: Look back this many hours (default: 7 days).
        dry_run: If True, don't store reflexions.
        min_pattern_count: Minimum pattern occurrences to generate a rule.

    Returns:
        SynthesisResult with candidates and counts.
    """
    from agentura_sdk.memory import get_memory_store

    store = get_memory_store()
    result = SynthesisResult()

    # Load executions
    if skill_filter:
        executions = store.get_executions(skill_filter)
    else:
        executions = store.get_executions()

    # Filter by time window
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    cutoff_str = cutoff.isoformat()
    executions = [e for e in executions if str(e.get("timestamp", "")) >= cutoff_str]

    result.executions_analyzed = len(executions)
    if not executions:
        return result

    # Group by skill, keep only failures/corrections
    by_skill: dict[str, list[dict]] = {}
    for ex in executions:
        skill = ex.get("skill", "")
        outcome = ex.get("outcome", "")
        if outcome not in ("error", "corrected", "rejected"):
            continue
        by_skill.setdefault(skill, []).append(ex)

    result.skills_analyzed = len(by_skill)
    if not by_skill:
        return result

    # Also load corrections for richer context
    corrections_by_skill: dict[str, list[dict]] = {}
    try:
        all_corrections = store.get_corrections()
        for c in all_corrections:
            skill = c.get("skill", "")
            corrections_by_skill.setdefault(skill, []).append(c)
    except Exception:
        pass

    # Build compact summaries
    logs_section = _build_logs_section(by_skill, corrections_by_skill)

    # Call cheap LLM
    prompt = _SYNTHESIS_PROMPT.format(
        logs_section=logs_section,
        min_count=min_pattern_count,
    )
    try:
        raw_response = _call_cheap_llm(prompt)
        candidates = _parse_candidates(raw_response)
    except Exception as e:
        logger.warning("Synthesis LLM call failed: %s", e)
        return result

    # Deduplicate against existing reflexions
    existing_reflexions = store.get_all_reflexions()
    existing_rules = {r.get("rule", "").lower().strip() for r in existing_reflexions}

    for c in candidates:
        if c.rule.lower().strip() in existing_rules:
            result.duplicates_skipped += 1
            continue
        if c.pattern_count < min_pattern_count:
            continue
        result.candidates.append(c)

    # Store if not dry-run
    if not dry_run:
        for c in result.candidates:
            try:
                store.add_reflexion(c.skill, {
                    "rule": c.rule,
                    "applies_when": c.applies_when,
                    "confidence": 0.5,
                    "source": "synthesis",
                })
                result.stored_count += 1
            except Exception:
                logger.debug("Failed to store synthesis reflexion", exc_info=True)

    return result


def _build_logs_section(
    by_skill: dict[str, list[dict]],
    corrections_by_skill: dict[str, list[dict]],
) -> str:
    """Build compact text representation of failures for the LLM."""
    sections = []
    for skill, entries in by_skill.items():
        lines = [f"### {skill} ({len(entries)} failures)"]
        for entry in entries[:_MAX_ENTRIES_PER_SKILL]:
            error = str(entry.get("output_summary", {}).get("error", ""))[:_MAX_ERROR_LEN]
            ts = str(entry.get("timestamp", ""))[:19]
            lines.append(f"- [{ts}] {error}")

        # Include corrections if available
        corrections = corrections_by_skill.get(skill, [])
        if corrections:
            lines.append(f"\nCorrections ({len(corrections)}):")
            for c in corrections[:5]:
                corr_text = str(c.get("user_correction", ""))[:_MAX_ERROR_LEN]
                lines.append(f"- {corr_text}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def _call_cheap_llm(prompt: str) -> str:
    """Call a cheap LLM (haiku) for pattern extraction."""
    # Try OpenRouter first
    if os.environ.get("OPENROUTER_API_KEY"):
        from agentura_sdk.runner.openrouter import chat_completion_messages

        resp = chat_completion_messages(
            model="anthropic/claude-haiku-4.5",
            messages=[
                {"role": "system", "content": "You extract patterns from execution logs. Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        return resp.content

    # Fallback to Anthropic direct
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic

        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system="You extract patterns from execution logs. Return only JSON.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return resp.content[0].text

    raise RuntimeError("No API key available for synthesis (OPENROUTER_API_KEY or ANTHROPIC_API_KEY)")


def _parse_candidates(raw: str) -> list[SynthesisCandidate]:
    """Parse JSON array of candidates from LLM response."""
    # Extract JSON from possible markdown wrapping
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []

    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    candidates = []
    for item in items:
        if not isinstance(item, dict):
            continue
        candidates.append(SynthesisCandidate(
            rule=item.get("rule", ""),
            applies_when=item.get("applies_when", ""),
            pattern_count=item.get("pattern_count", 1),
            skill=item.get("skill", ""),
        ))
    return candidates
