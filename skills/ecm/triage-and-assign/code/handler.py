"""triage-and-assign — ECM manager handler.

Classifies incoming ECM queries and routes to the correct specialist.
"""

from agentura_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    input_data = ctx.input_data or {}
    message = input_data.get("message", "")

    if not message:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Missing 'message' in input"},
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
