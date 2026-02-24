"""Parse SKILL.md frontmatter + body into SkillMetadata + prompt."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
import yaml

from agentura_sdk.types import SkillMetadata


@dataclass
class LoadedSkill:
    metadata: SkillMetadata
    system_prompt: str
    workspace_context: str
    domain_context: str
    reflexion_context: str
    raw_content: str


def load_workspace_md(skill_path: Path) -> str:
    """Find WORKSPACE.md at the skills root directory.

    Walks up from skill dir (skills/ecm/order-details/SKILL.md) to find
    WORKSPACE.md at skills root (skills/WORKSPACE.md).

    Returns empty string if no WORKSPACE.md exists (graceful degradation).
    """
    current = skill_path.parent  # skill dir
    levels_walked = 0
    while current != current.parent and levels_walked < 5:
        candidate = current / "WORKSPACE.md"
        if candidate.exists():
            return candidate.read_text().strip()
        current = current.parent
        levels_walked += 1
    return ""


def load_domain_md(skill_path: Path) -> str:
    """Find and load DOMAIN.md from the domain directory (parent of skill dir).

    Walks up from the skill directory (e.g., skills/ecm/order-details/) to find
    DOMAIN.md at the domain level (skills/ecm/DOMAIN.md). Stops when it reaches
    the skills root (parent of domain directories).

    Returns empty string if no DOMAIN.md exists (graceful degradation).
    """
    # Start from the skill directory and walk up to domain directory
    current = skill_path.parent
    levels_walked = 0
    while current != current.parent and levels_walked < 3:
        candidate = current / "DOMAIN.md"
        if candidate.exists():
            return candidate.read_text().strip()
        current = current.parent
        levels_walked += 1
    return ""


def load_reflexion_entries(skill_path: Path) -> str:
    """Load reflexion entries relevant to this skill from the knowledge layer.

    Strategy:
    1. Try mem0 semantic memory (if available) — returns semantically relevant rules
    2. Fall back to .agentura/reflexion_entries.json — exact skill-name matching

    Returns formatted Markdown section for injection into system prompt,
    or empty string if no entries exist.
    """
    # skill_path is e.g. skills/ecm/order-details/SKILL.md
    # We need domain/skill-name = ecm/order-details
    skill_dir = skill_path.parent        # skills/ecm/order-details
    domain_dir = skill_dir.parent        # skills/ecm
    skill_name_full = f"{domain_dir.name}/{skill_dir.name}"
    # Also match just the skill directory name
    skill_dir_name = skill_dir.name

    # Try mem0 first
    relevant = _load_reflexions_from_mem0(skill_name_full)

    # Fall back to JSON files
    if not relevant:
        relevant = _load_reflexions_from_json(skill_name_full, skill_dir_name, skill_path)

    if not relevant:
        return ""

    lines = ["## Learned Rules (from past corrections)", ""]
    for entry in relevant:
        rid = entry.get("reflexion_id", "REFL-?")
        rule = entry.get("rule", "")
        applies = entry.get("applies_when", "")
        confidence = entry.get("confidence", 0)
        validated = entry.get("validated_by_test", False)

        badge = " [validated]" if validated else ""
        lines.append(f"- **{rid}** (confidence: {confidence:.0%}{badge}): {rule}")
        if applies:
            lines.append(f"  _Applies when_: {applies}")
    return "\n".join(lines)


def _load_reflexions_from_mem0(skill_name_full: str) -> list[dict]:
    """Try loading reflexions from mem0 semantic memory."""
    try:
        from agentura_sdk.memory import get_memory_store
        from agentura_sdk.memory.mem0_store import Mem0Store

        store = get_memory_store()
        if isinstance(store, Mem0Store):
            return store.get_reflexions(skill_name_full)
    except Exception:
        pass
    return []


def _load_reflexions_from_json(
    skill_name_full: str, skill_dir_name: str, skill_path: Path
) -> list[dict]:
    """Fall back to loading reflexions from JSON files."""
    candidates = [
        Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or os.environ.get("ASPORA_KNOWLEDGE_DIR") or str("")) / "reflexion_entries.json",
        Path.cwd() / ".agentura" / "reflexion_entries.json",
        skill_path.parent.parent / "reflexion_entries.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text())
                entries = data.get("entries", [])
                relevant = [
                    e for e in entries
                    if e.get("skill", "") == skill_name_full
                    or e.get("skill", "").endswith(f"/{skill_dir_name}")
                    or e.get("skill", "") == skill_dir_name
                ]
                if relevant:
                    return relevant
            except (json.JSONDecodeError, KeyError):
                continue
    return []


def load_skill_md(skill_path: Path, include_reflexions: bool = True) -> LoadedSkill:
    """Load a SKILL.md file.

    Supports two frontmatter formats:
    1. Standard YAML frontmatter (--- delimiters) — used by packages/skills/
    2. YAML in code fence under ## Skill Metadata — used by examples/auto-rca/

    Set include_reflexions=False when only metadata is needed (e.g. listing skills)
    to avoid expensive mem0/reflexion store initialization.
    """
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    raw = skill_path.read_text()
    workspace_context = load_workspace_md(skill_path)
    domain_context = load_domain_md(skill_path)
    reflexion_context = load_reflexion_entries(skill_path) if include_reflexions else ""

    # Try standard frontmatter first (--- delimiters)
    post = frontmatter.loads(raw)
    if post.metadata:
        metadata = _parse_metadata(post.metadata)
        return LoadedSkill(
            metadata=metadata,
            system_prompt=post.content.strip(),
            workspace_context=workspace_context,
            domain_context=domain_context,
            reflexion_context=reflexion_context,
            raw_content=raw,
        )

    # Fallback: YAML in ```yaml code fence under ## Skill Metadata
    metadata_dict = _extract_code_fence_metadata(raw)
    if metadata_dict:
        # Metadata may be nested under 'skill' key
        skill_data = metadata_dict.get("skill", metadata_dict)
        metadata = _parse_metadata(skill_data)
        # Strip the metadata section, keep the rest as prompt
        prompt = _strip_metadata_section(raw)
        return LoadedSkill(
            metadata=metadata,
            system_prompt=prompt,
            workspace_context=workspace_context,
            domain_context=domain_context,
            reflexion_context=reflexion_context,
            raw_content=raw,
        )

    raise ValueError(
        f"No frontmatter found in {skill_path}. "
        "Use --- YAML --- or ## Skill Metadata with ```yaml code fence."
    )


def _parse_metadata(data: dict) -> SkillMetadata:
    """Parse metadata dict, tolerating missing optional fields."""
    return SkillMetadata(
        name=data.get("name", "unnamed-skill"),
        role=data.get("role", "specialist"),
        domain=data.get("domain", "default"),
        trigger=data.get("trigger", "manual"),
        model=data.get("model", "anthropic/claude-sonnet-4.5"),
        cost_budget_per_execution=str(
            data.get("cost_budget_per_execution", "$0.10")
        ),
        timeout=str(data.get("timeout", "60s")),
        routes_to=data.get("routes_to", []),
    )


def _extract_code_fence_metadata(content: str) -> dict | None:
    """Extract YAML from ```yaml code fence after ## Skill Metadata."""
    pattern = r"##\s*Skill Metadata\s*\n```ya?ml\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1))
    return None


def _strip_metadata_section(content: str) -> str:
    """Remove ## Skill Metadata + code fence, keep everything else."""
    pattern = r"##\s*Skill Metadata\s*\n```ya?ml\n.*?```\s*\n?"
    stripped = re.sub(pattern, "", content, flags=re.DOTALL)
    return stripped.strip()
