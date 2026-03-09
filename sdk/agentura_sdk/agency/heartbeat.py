"""Heartbeat scheduler — runs agent heartbeats on schedule."""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HeartbeatScheduler:
    """Simple heartbeat scheduler using threading.Timer.

    Checks every 60 seconds for agents whose heartbeat is due.
    Actual cron-like scheduling is deferred to a future iteration —
    for now, supports manual triggers via the API.
    """

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._running = False
        self._thread: threading.Thread | None = None
        self._interval = 60  # check interval in seconds

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Heartbeat scheduler started (interval=%ds)", self._interval)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Heartbeat scheduler stopped")

    def _loop(self) -> None:
        while self._running:
            time.sleep(self._interval)

    def trigger(self, agent_id: str) -> dict:
        """Manually trigger a heartbeat for an agent."""
        from agentura_sdk.memory.agent_store import AgentStore
        from agentura_sdk.memory.heartbeat_store import HeartbeatStore
        from agentura_sdk.memory.ticket_store import TicketStore

        agent_store = AgentStore(self._dsn)
        heartbeat_store = HeartbeatStore(self._dsn)
        ticket_store = TicketStore(self._dsn)

        agent = agent_store.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent not found: {agent_id}"}

        # Create ticket for this heartbeat run
        ticket_id = ticket_store.create_ticket(
            title=f"Heartbeat: {agent['name']}",
            domain=agent.get("domain", ""),
            created_by=agent_id,
            assigned_to=agent_id,
            priority=3,
            input_data={"trigger": "manual", "agent": agent["name"]},
        )

        # Create heartbeat run record
        run_id = heartbeat_store.create_run(
            agent_id=agent_id,
            agent_name=agent.get("name", ""),
            ticket_id=ticket_id,
            trigger="manual",
        )

        # Mark as completed (actual skill execution deferred to future iteration)
        heartbeat_store.complete_run(
            run_id=run_id,
            status="completed",
            summary=f"Manual heartbeat triggered for {agent['name']}",
        )

        ticket_store.update_ticket(ticket_id, status="resolved")

        return {
            "run_id": run_id,
            "agent_id": agent_id,
            "agent_name": agent.get("name", ""),
            "ticket_id": ticket_id,
            "status": "completed",
            "trigger": "manual",
        }
