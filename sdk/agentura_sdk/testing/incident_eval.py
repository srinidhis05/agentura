"""Incident-to-eval synthesis hook (DEC-067).

Called after every execution. If the execution failed and the skill has
capture_failure_cases enabled, generates regression tests in a daemon thread.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import yaml

from agentura_sdk.types import SkillContext, SkillResult

logger = logging.getLogger(__name__)


def maybe_generate_failure_tests(
    ctx: SkillContext,
    result: SkillResult,
    skills_dir: Path,
) -> None:
    """Fire-and-forget failure test generation. Never blocks execution response."""
    if result.success:
        return

    skill_dir = skills_dir / ctx.domain / ctx.skill_name
    config_path = skill_dir / "agentura.config.yaml"
    if not config_path.exists():
        return

    try:
        cfg = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return

    feedback = cfg.get("feedback", {})
    if not feedback.get("capture_failure_cases", False):
        return

    # Fire in daemon thread — never blocks
    thread = threading.Thread(
        target=_generate_tests_sync,
        args=(ctx, result, skill_dir),
        daemon=True,
    )
    thread.start()


def _generate_tests_sync(ctx: SkillContext, result: SkillResult, skill_dir: Path) -> None:
    """Synchronous test generation + failure case storage."""
    from datetime import datetime, timezone

    execution_id = f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    skill_path = f"{ctx.domain}/{ctx.skill_name}"

    try:
        from agentura_sdk.testing.failure_case_generator import (
            generate_failure_deepeval_test,
            generate_failure_promptfoo_test,
        )

        generate_failure_deepeval_test(
            skill_dir=skill_dir,
            input_data=ctx.input_data,
            error_output=result.output,
            execution_id=execution_id,
            severity="P0",
        )
        generate_failure_promptfoo_test(
            skill_dir=skill_dir,
            input_data=ctx.input_data,
            error_output=result.output,
            execution_id=execution_id,
            severity="P0",
        )
        logger.info("Generated failure regression tests for %s", skill_path)
    except Exception:
        logger.debug("Failed to generate failure tests for %s", skill_path, exc_info=True)

    # Store failure case metadata
    try:
        from agentura_sdk.memory import get_memory_store

        store = get_memory_store()
        if hasattr(store, "log_failure_case"):
            store.log_failure_case(skill_path, {
                "execution_id": execution_id,
                "severity": "P0",
                "input_summary": ctx.input_data,
                "error_output": result.output,
            })
    except Exception:
        logger.debug("Failed to store failure case for %s", skill_path, exc_info=True)
