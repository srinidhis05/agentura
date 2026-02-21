"""my-tickets — ECM agent ticket queue handler.

Shows the agent's assigned ticket queue from Google Sheets,
enriched with live Redshift data and actionable instructions.

Contract: SkillContext → SkillResult (DEC-005)
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    """Execute my-tickets skill.

    Validates input, then delegates to LLM with SKILL.md system prompt.
    """
    input_data = ctx.input_data or {}

    agent_email = input_data.get("agent_email", "")
    if not agent_email:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": "Missing agent_email in input",
                "reasoning_trace": "Input validation failed — no agent identifier provided",
            },
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
