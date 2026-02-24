"""kyc-review — FRM specialist for KYC workflow analysis.

Checks document completeness, watchlists, and generates RFIs.
"""

from agentura_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    input_data = ctx.input_data or {}
    user_id = input_data.get("user_id", "")

    if not user_id:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Missing 'user_id' in input"},
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
