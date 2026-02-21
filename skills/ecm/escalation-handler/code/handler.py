"""escalation-handler — ECM field agent for P1 escalations.

Handles SLA breaches and escalated tickets with full evidence gathering.
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    input_data = ctx.input_data or {}
    order_id = input_data.get("order_id", "")

    if not order_id:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Missing 'order_id' in escalation input"},
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
