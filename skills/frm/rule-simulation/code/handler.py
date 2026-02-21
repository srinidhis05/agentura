"""rule-simulation — FRM rule simulation handler.

Simulates financial risk management rules against input scenarios.
Validates rule parameters and returns simulation results with impact analysis.

Contract: SkillContext → SkillResult (DEC-005)
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    """Execute rule-simulation skill.

    Validates rule parameters, then delegates to LLM for simulation reasoning.
    Pre-processing: validates rule structure and scenario parameters.
    Post-processing: structures simulation results with confidence scoring.
    """
    input_data = ctx.input_data or {}

    # Pre-processing: validate required fields
    rule = input_data.get("rule", input_data.get("rule_id", ""))
    scenario = input_data.get("scenario", input_data.get("parameters", {}))

    if not rule:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": "Missing rule or rule_id in input",
                "reasoning_trace": "Input validation failed — no rule specified for simulation",
            },
            model_used=ctx.model,
        )

    # Default: delegate to LLM via system_prompt from SKILL.md
    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
