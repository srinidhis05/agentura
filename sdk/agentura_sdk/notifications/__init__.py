"""Post-execution notification dispatch.

Reads notification config from agentura.config.yaml and dispatches
to the appropriate channel (Slack, etc.) after skill execution.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from agentura_sdk.types import SkillResult

logger = logging.getLogger(__name__)


def dispatch_notifications(
    skill_root: Path,
    domain: str,
    skill_name: str,
    result: SkillResult,
) -> None:
    """Read notification config and dispatch to all configured channels."""
    config_path = skill_root / "agentura.config.yaml"
    if not config_path.exists():
        return

    try:
        cfg = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return

    notifications = cfg.get("notifications", [])
    if not notifications:
        return

    outcome = "success" if result.success else "error"

    for notif in notifications:
        triggers = notif.get("on", ["success", "error"])
        if outcome not in triggers:
            continue

        channel = notif.get("channel", "")
        config = notif.get("config", {})

        if channel == "slack":
            _dispatch_slack(domain, skill_name, result, config)
        else:
            logger.warning("unknown notification channel: %s", channel)


def _dispatch_slack(
    domain: str,
    skill_name: str,
    result: SkillResult,
    config: dict[str, Any],
) -> None:
    """Dispatch to Slack notification channel."""
    from agentura_sdk.notifications.slack import SlackNotifier

    channel_id = config.get("channel_id", "")
    if not channel_id:
        logger.warning("slack notification missing channel_id for %s/%s", domain, skill_name)
        return

    thread_mode = config.get("thread_mode", False)

    notifier = SlackNotifier()
    if not notifier.available:
        logger.warning("SLACK_BOT_TOKEN not set, skipping notification for %s/%s", domain, skill_name)
        return

    notifier.post_result(
        channel_id=channel_id,
        domain=domain,
        skill_name=skill_name,
        result=result,
        thread_mode=thread_mode,
    )
