"""Degradable seat-ledger hooks for the pipeline engine. These never raise."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def record_outcome(store, seat_id, session_id, success, cost_usd=0.0, latency_ms=0.0, gate=None, model=""):
    """Append a session outcome (and optional gate) event. Never raises."""
    if not store or not seat_id:
        return
    try:
        store.append_event(
            seat_id,
            "session_completed" if success else "session_failed",
            session_id=session_id,
            model=model,
            payload={"success": bool(success), "cost_usd": cost_usd, "latency_ms": latency_ms},
        )
        if gate in ("pass", "fail"):
            store.append_event(
                seat_id,
                "gate_passed" if gate == "pass" else "gate_failed",
                session_id=session_id,
                payload={},
            )
    except Exception as e:
        logger.warning("record_outcome failed seat=%s: %s", seat_id, e)


def record_rating(store, skill_path, rating, task_id="", model=""):
    """Append a user rating (1-5) as a seat 'rating' event. Never raises."""
    if not store:
        return
    try:
        from agentura_sdk.runner.seat_resolver import resolve_seat
        seat_id = resolve_seat(store, skill_path, model=model)
        if not seat_id:
            return
        store.append_event(seat_id, "rating", session_id=task_id, model=model,
                           payload={"rating": int(rating), "task_id": task_id})
    except Exception as e:
        logger.warning("record_rating failed for %s: %s", skill_path, e)
