"""Build-deploy pipeline — thin wrapper over the generic pipeline engine.

Keeps backward compat for existing callers while delegating to engine.py.
"""

from collections.abc import AsyncGenerator
from typing import Any

from agentura_sdk.pipelines.engine import run_pipeline, run_pipeline_stream

PIPELINE_NAME = "build-deploy"


async def run_build_deploy(pipeline_input: dict[str, Any]) -> dict[str, Any]:
    """Run the build-deploy pipeline synchronously, return aggregated result."""
    return await run_pipeline(PIPELINE_NAME, pipeline_input)


async def run_build_deploy_stream(
    pipeline_input: dict[str, Any],
) -> AsyncGenerator[str, None]:
    """SSE streaming variant — yields newline-delimited JSON events."""
    async for event in run_pipeline_stream(PIPELINE_NAME, pipeline_input):
        yield event
