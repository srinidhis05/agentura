"""classifier — Platform routing classifier handler.

Routes incoming requests to the appropriate domain and skill based on intent.
This is the entry point for multi-domain orchestration (manager role).

Contract: SkillContext → SkillResult (DEC-005)
"""

from agentura_sdk.types import SkillContext, SkillResult


async def handle(ctx: SkillContext) -> SkillResult:
    """Execute classifier skill.

    Analyzes user intent and routes to the appropriate domain/skill.
    Pre-processing: extracts query and context signals.
    Post-processing: returns route_to with confidence.
    """
    input_data = ctx.input_data or {}

    query = input_data.get("query", input_data.get("message", ""))
    if not query:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": "Missing query or message in input",
                "reasoning_trace": "Input validation failed — no query to classify",
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
