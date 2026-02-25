"""Single-stage LLM routing: natural language → skill selection."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from agentura_sdk.runner.skill_registry import SkillRegistry
from agentura_sdk.types import SkillContext, SkillRole

_DEFAULT_ROUTER_MODEL = "anthropic/claude-haiku-4.5"

_SYSTEM_PROMPT_TEMPLATE = """\
You are a skill router. Given a user query, select the best matching skill from the registry below.

{registry_context}

Return ONLY a raw JSON object (no markdown, no code fences, no explanation):
{{
  "domain": "string",
  "skill": "string",
  "confidence": 0.0-1.0,
  "entities": {{}},
  "reasoning": "one sentence"
}}

Rules:
- Match based on trigger patterns, description, and domain relevance.
- Extract entities from the query using {{entity}} patterns in triggers (e.g. order_id, user_id, rule_name).
- If no skill matches well, return confidence < 0.5.
- Do NOT invent skills that aren't in the registry.
"""


@dataclass
class RoutingResult:
    """Result of LLM-based query routing."""
    domain: str
    skill_name: str
    confidence: float
    entities: dict = field(default_factory=dict)
    reasoning: str = ""


async def route_query(
    query: str,
    registry: SkillRegistry,
    model: str = _DEFAULT_ROUTER_MODEL,
) -> RoutingResult:
    """Route a natural language query to a skill using a single LLM call."""
    from agentura_sdk.runner.local_runner import execute_skill

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        registry_context=registry.to_routing_context(),
    )

    ctx = SkillContext(
        skill_name="router",
        domain="platform",
        role=SkillRole.MANAGER,
        model=model,
        system_prompt=system_prompt,
        input_data={"query": query},
    )

    result = await execute_skill(ctx)

    return _parse_routing_result(result.output)


def _parse_routing_result(output: dict) -> RoutingResult:
    """Parse LLM output into RoutingResult, handling raw_output wrapper."""
    # If execute_skill wrapped it as {"raw_output": "..."}, parse the inner JSON
    if "raw_output" in output and len(output) == 1:
        raw = output["raw_output"]
        try:
            output = json.loads(_strip_code_fences(raw))
        except (json.JSONDecodeError, TypeError):
            return RoutingResult(
                domain="", skill_name="", confidence=0.0,
                reasoning="Router returned unparseable response",
            )

    return RoutingResult(
        domain=output.get("domain", ""),
        skill_name=output.get("skill", ""),
        confidence=float(output.get("confidence", 0.0)),
        entities=output.get("entities", {}),
        reasoning=output.get("reasoning", ""),
    )


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from LLM output."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
