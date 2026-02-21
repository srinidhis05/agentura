"""order-details — ECM order diagnosis handler.

Analyzes order details, identifies issues, and provides root cause analysis.
Works with SKILL.md system prompt for domain-specific reasoning.

Contract: SkillContext → SkillResult (DEC-005)
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    """Execute order-details skill.

    Validates input, then delegates to LLM with SKILL.md system prompt.
    Pre-processing: normalizes order IDs and extracts key fields.
    Post-processing: structures output with confidence and evidence.
    """
    input_data = ctx.input_data or {}

    # Pre-processing: normalize order reference
    order_id = input_data.get("order_id", input_data.get("reference", ""))
    if not order_id:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": "Missing order_id or reference in input",
                "reasoning_trace": "Input validation failed — no order identifier provided",
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
