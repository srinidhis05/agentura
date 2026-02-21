"""Hello World — Minimal Python handler.

This handler is optional. The SKILL.md prompt is the primary skill definition.
Use a handler only when you need custom pre/post-processing logic.
"""

from aspora_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    query = ctx.input_data.get("query", "Hello!")
    return SkillResult(
        skill_name=ctx.skill_name,
        success=True,
        output={
            "response": f"Hello from {ctx.skill_name}! You said: {query}",
            "confidence": "high",
        },
        reasoning_trace=["Received input", "Generated greeting response"],
        model_used=ctx.model,
    )
