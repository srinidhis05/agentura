"""Build a skill registry from local skills for LLM-based routing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from agentura_sdk.runner.config_loader import load_config


@dataclass
class SkillEntry:
    """A single routable skill."""
    domain: str
    name: str
    role: str
    description: str
    triggers: list[str] = field(default_factory=list)


@dataclass
class SkillRegistry:
    """All routable skills in the workspace."""
    skills: list[SkillEntry] = field(default_factory=list)

    def to_routing_context(self) -> str:
        """Format as a markdown table for the LLM routing prompt."""
        lines = [
            "| Domain | Skill | Role | Description | Triggers |",
            "|--------|-------|------|-------------|----------|",
        ]
        for s in self.skills:
            triggers = "; ".join(s.triggers) if s.triggers else "manual"
            lines.append(
                f"| {s.domain} | {s.name} | {s.role} | {s.description} | {triggers} |"
            )
        return "\n".join(lines)


def build_registry(skills_dir: Path) -> SkillRegistry:
    """Scan all agentura.config.yaml files and SKILL.md to build the registry."""
    entries: list[SkillEntry] = []

    for config_path in sorted(skills_dir.rglob("agentura.config.yaml")):
        try:
            config = load_config(config_path)
        except Exception:
            continue

        # Skip platform domain — infrastructure, not user-facing
        if config.domain.name == "platform":
            continue

        skill_dir = config_path.parent
        for skill_ref in config.skills:
            triggers = _extract_config_triggers(skill_ref.triggers)
            description = ""

            # Try to load SKILL.md for extra context
            skill_md_path = skill_dir / "SKILL.md"
            if skill_md_path.exists():
                raw = skill_md_path.read_text()
                triggers.extend(_extract_skill_md_triggers(raw))
                description = _extract_task_description(raw)

            entries.append(SkillEntry(
                domain=config.domain.name,
                name=skill_ref.name,
                role=skill_ref.role,
                description=description,
                triggers=list(dict.fromkeys(triggers)),  # deduplicate, preserve order
            ))

    return SkillRegistry(skills=entries)


def _extract_config_triggers(triggers: list[dict]) -> list[str]:
    """Extract command patterns from config triggers."""
    patterns = []
    for t in triggers:
        if t.get("type") == "command" and t.get("pattern"):
            patterns.append(t["pattern"])
    return patterns


def _extract_skill_md_triggers(raw: str) -> list[str]:
    """Extract trigger bullet items from ## Trigger section in SKILL.md."""
    match = re.search(r"## Trigger\s*\n(.*?)(?:\n## |\Z)", raw, re.DOTALL)
    if not match:
        return []
    triggers = []
    for line in match.group(1).strip().splitlines():
        line = line.strip().lstrip("- ").strip('"').strip("'")
        if line:
            triggers.append(line)
    return triggers


def _extract_task_description(raw: str) -> str:
    """Extract first line of ## Task section as a one-line description."""
    match = re.search(r"## Task\s*\n+(.+)", raw)
    if match:
        return match.group(1).strip()
    # Fallback: use the first heading after frontmatter
    match = re.search(r"^# (.+)$", raw, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""
