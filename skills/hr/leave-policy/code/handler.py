"""leave-policy — HR specialist for leave policy Q&A.

Answers employee questions about leave entitlements and procedures.
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    input_data = ctx.input_data or {}
    question = input_data.get("question", "")

    if not question:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Missing 'question' in input"},
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
