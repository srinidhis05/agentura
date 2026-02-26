"""Skill mapper — maps (tech_stack, task_type) → ai-velocity SKILL.md files.

Config-driven lookup, not if-else chains. Loads skills lazily from AI_VELOCITY_DIR.
Truncates skills > 30K chars at the last complete ## section boundary.
"""

from __future__ import annotations

import os
from pathlib import Path

from agentura_sdk.types import MappedSkill, TechStack

_MAX_SKILL_CHARS = 30_000

# (language_or_wildcard, task_type) → list of skill directory names
_SKILL_MAP: dict[tuple[str, str], list[str]] = {
    ("java", "code"): ["java-coding-standards", "java-application-development"],
    ("java", "test"): ["java-testing"],
    ("java", "instrument"): ["prometheus-instrumentation"],
    ("go", "code"): ["golang-coding-standards"],
    ("go", "test"): ["golang-unit-testing"],
    ("python", "code"): [],
    ("python", "test"): [],
    ("*", "instrument"): ["prometheus-instrumentation"],
    ("*", "dashboard"): ["datadog-dashboard-creation"],
    ("*", "alert"): ["alert-generation"],
}


def _velocity_dir() -> Path | None:
    """Resolve AI_VELOCITY_DIR from env. Returns None if not set."""
    raw = os.environ.get("AI_VELOCITY_DIR")
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_dir() else None


def _truncate_at_section(text: str, max_chars: int) -> tuple[str, bool]:
    """Truncate at the last complete ## section boundary within max_chars."""
    if len(text) <= max_chars:
        return text, False

    truncated = text[:max_chars]
    last_heading = truncated.rfind("\n## ")
    if last_heading > 0:
        return truncated[:last_heading].rstrip() + "\n", True
    return truncated.rstrip() + "\n", True


def _load_skill(velocity_dir: Path, skill_name: str) -> MappedSkill | None:
    """Load a single SKILL.md from ai-velocity directory."""
    skill_path = velocity_dir / skill_name / "SKILL.md"
    if not skill_path.exists():
        return None

    content = skill_path.read_text(errors="ignore")
    content, truncated = _truncate_at_section(content, _MAX_SKILL_CHARS)

    return MappedSkill(
        name=skill_name,
        path=str(skill_path),
        content=content,
        truncated=truncated,
    )


def map_skills(tech: TechStack, task_type: str) -> list[MappedSkill]:
    """Map a tech stack + task type to relevant ai-velocity skills."""
    velocity_dir = _velocity_dir()
    if not velocity_dir:
        return []

    primary = tech.languages[0] if tech.languages else ""

    # Collect skill names: specific language match + wildcard fallback
    skill_names: list[str] = []
    for key in [(primary, task_type), ("*", task_type)]:
        for name in _SKILL_MAP.get(key, []):
            if name not in skill_names:
                skill_names.append(name)

    # Load and return
    skills: list[MappedSkill] = []
    for name in skill_names:
        skill = _load_skill(velocity_dir, name)
        if skill:
            skills.append(skill)

    return skills
