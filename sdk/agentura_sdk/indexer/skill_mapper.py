"""Skill mapper — maps SDLC stages to external SKILL.md files.

Reads sdlc.yaml from SKILL_LIBRARY_DIR for stage → skill mappings.
Truncates skills > 30K chars at the last complete ## section boundary.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

import yaml

from agentura_sdk.types import MappedSkill, TechStack

logger = logging.getLogger(__name__)

_MAX_SKILL_CHARS = 30_000


def _velocity_dir() -> Path | None:
    """Resolve AI_VELOCITY_DIR from env. Returns None if not set."""
    raw = os.environ.get("AI_VELOCITY_DIR")
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_dir() else None


@lru_cache(maxsize=1)
def _load_sdlc_config(velocity_dir: str) -> dict:
    """Read and cache sdlc.yaml from the skill library root."""
    path = Path(velocity_dir) / "sdlc.yaml"
    if not path.exists():
        logger.warning("sdlc.yaml not found at %s", path)
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("stages", {}) if data else {}


def _resolve_skill_path(velocity_dir: Path, name: str) -> Path | None:
    """Resolve a skill name to its SKILL.md path.

    Checks root level first, then organizational-skills/ subdirectory.
    """
    for candidate in [
        velocity_dir / name / "SKILL.md",
        velocity_dir / "organizational-skills" / name / "SKILL.md",
    ]:
        if candidate.exists():
            return candidate
    return None


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
    """Load a single SKILL.md from skill library directory."""
    skill_path = _resolve_skill_path(velocity_dir, skill_name)
    if not skill_path:
        logger.debug("skill not found: %s", skill_name)
        return None

    content = skill_path.read_text(errors="ignore")
    content, truncated = _truncate_at_section(content, _MAX_SKILL_CHARS)

    return MappedSkill(
        name=skill_name,
        path=str(skill_path),
        content=content,
        truncated=truncated,
    )


def map_skills_for_stage(stage: str, language: str) -> list[MappedSkill]:
    """Map an SDLC stage + language to relevant skill library skills.

    Reads sdlc.yaml to collect base skills + language-specific overlays.
    Returns empty list if AI_VELOCITY_DIR is not set or sdlc.yaml is missing.
    """
    velocity_dir = _velocity_dir()
    if not velocity_dir:
        return []

    stages = _load_sdlc_config(str(velocity_dir))
    stage_config = stages.get(stage, {})
    if not stage_config:
        return []

    # Collect skill names: base + language-specific
    skill_names: list[str] = list(stage_config.get("base", []))
    if language:
        lang_skills = stage_config.get("languages", {}).get(language, [])
        for name in lang_skills:
            if name not in skill_names:
                skill_names.append(name)

    # Load and return
    skills: list[MappedSkill] = []
    for name in skill_names:
        skill = _load_skill(velocity_dir, name)
        if skill:
            skills.append(skill)

    return skills


def map_skills(tech: TechStack, task_type: str) -> list[MappedSkill]:
    """Map a tech stack + task type to relevant skill library skills.

    Backward-compatible wrapper around map_skills_for_stage().
    """
    primary = tech.languages[0] if tech.languages else ""
    return map_skills_for_stage(task_type, primary)
