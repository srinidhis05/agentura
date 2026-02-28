"""Slack notification poster using chat.postMessage API."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from agentura_sdk.types import SkillResult

logger = logging.getLogger(__name__)

SLACK_API_BASE = "https://slack.com/api"


class SlackNotifier:
    """Posts execution results to Slack channels."""

    def __init__(self) -> None:
        self.token = os.environ.get("SLACK_BOT_TOKEN", "")

    @property
    def available(self) -> bool:
        return bool(self.token)

    def post_result(
        self,
        channel_id: str,
        domain: str,
        skill_name: str,
        result: SkillResult,
        thread_mode: bool = False,
    ) -> None:
        """Post skill result to Slack. Optionally thread replies."""
        status_emoji = ":white_check_mark:" if result.success else ":x:"
        title = f"{status_emoji} *{domain}/{skill_name}*"

        # Extract structured output if available
        output = result.output or {}
        summary = output.get("summary", str(output)[:500]) if isinstance(output, dict) else str(output)[:500]

        main_text = f"{title}\n{summary}"

        ts = self._post_message(channel_id, main_text)
        if not ts:
            return

        if not thread_mode or not isinstance(output, dict):
            return

        # Post thread replies for structured output
        thread_replies = output.get("thread_replies", [])
        for reply in thread_replies:
            if isinstance(reply, str):
                self._post_message(channel_id, reply, thread_ts=ts)
            elif isinstance(reply, dict):
                self._post_message(
                    channel_id,
                    reply.get("text", json.dumps(reply, indent=2)),
                    thread_ts=ts,
                )

    def _post_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
    ) -> str | None:
        """Post a message to Slack, return the message ts on success."""
        payload: dict[str, Any] = {
            "channel": channel,
            "text": text,
            "unfurl_links": False,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        try:
            resp = httpx.post(
                f"{SLACK_API_BASE}/chat.postMessage",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error("slack post failed: %s", data.get("error", "unknown"))
                return None
            return data.get("ts")
        except Exception as e:
            logger.error("slack post error: %s", e)
            return None
