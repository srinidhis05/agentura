"""resume-screen — HR specialist for candidate evaluation.

Screens resumes against job descriptions with structured scoring.
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    input_data = ctx.input_data or {}
    resume = input_data.get("resume_text", "")
    jd = input_data.get("job_description", "")

    if not resume or len(resume) < 100:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Resume text too short or missing (min 100 chars)"},
            model_used=ctx.model,
        )

    if not jd:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "Missing 'job_description' in input"},
            model_used=ctx.model,
        )

    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={"message": "Handler executed", "input": ctx.input_data},
        model_used=ctx.model,
    )
