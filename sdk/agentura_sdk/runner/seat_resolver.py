"""Resolve a skill to a persistent seat identity. v1 keys on skill_path."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def seat_key(skill_path: str) -> tuple[str, str, str]:
    """Pure: (name, role, domain) for a skill path. Keys on skill_path in v1."""
    skill_path = (skill_path or "").strip("/")
    parts = skill_path.split("/") if skill_path else []
    domain = parts[0] if len(parts) > 1 else ""
    role = parts[-1] if parts else ""
    return skill_path or "unknown", role, domain


def resolve_seat(store, skill_path: str, model: str = "") -> str | None:
    """Get-or-create the seat for a skill. Degradable: returns None on any failure."""
    try:
        name, role, domain = seat_key(skill_path)
        return store.get_or_create_seat(name=name, role=role, domain=domain, model=model)
    except Exception as e:
        logger.warning("seat resolve failed for %s: %s", skill_path, e)
        return None
