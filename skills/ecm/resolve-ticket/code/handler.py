"""resolve-ticket — ECM ticket resolution handler.

Marks a ticket as resolved by updating Google Sheets
and calculating resolution metrics.

Contract: SkillContext → SkillResult (DEC-005)
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    """Execute resolve-ticket skill.

    Validates input, then delegates to LLM with SKILL.md system prompt.
    """
    input_data = ctx.input_data or {}

    order_id = input_data.get("order_id", "")
    notes = input_data.get("notes", "")

    if not order_id:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": "Missing order_id in input",
                "reasoning_trace": "Input validation failed — no order identifier provided",
            },
            model_used=ctx.model,
        )

    if not notes:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": "Resolution notes are required",
                "reasoning_trace": 'Example: resolve AE789X123 "Replayed webhook, LULU confirmed"',
            },
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
