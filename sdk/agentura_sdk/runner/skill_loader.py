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
    project_configs: str
    reflexion_context: str
    raw_content: str
    injected_reflexion_ids: list[str] = field(default_factory=list)


def load_workspace_md(skill_path: Path) -> str:
    """Find WORKSPACE.md at the skills root directory.

    Walks up from skill dir (skills/hr/interview-questions/SKILL.md) to find
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

    Walks up from the skill directory (e.g., skills/hr/interview-questions/) to find
    DOMAIN.md at the domain level (skills/hr/DOMAIN.md). Stops when it reaches
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


def load_project_configs(skill_path: Path) -> str:
    """Load project configuration files from domain's project-configs directory.

    For PM domain skills, loads workspace config + all project-specific configs
    (gold.md, remittance.md, etc.) to provide ClickUp IDs, assignee mappings,
    Slack channels, and Granola search terms.

    Returns formatted markdown string with all project configurations.
    """
    # Find domain directory (parent of skill dir)
    domain_dir = skill_path.parent.parent  # skills/pm
    project_configs_dir = domain_dir / "project-configs"

    if not project_configs_dir.exists():
        return ""

    config_parts = []

    # Load workspace config first (if exists)
    workspace_file = project_configs_dir / "_workspace.md"
    if workspace_file.exists():
        config_parts.append(workspace_file.read_text().strip())

    # Load all project-specific config files
    project_files = sorted([
        f for f in project_configs_dir.glob("*.md")
        if not f.name.startswith("_")
    ])

    for project_file in project_files:
        config_parts.append(project_file.read_text().strip())

    if not config_parts:
        return ""

    return "\n\n---\n\n".join(config_parts)


def load_reflexion_entries(skill_path: Path) -> tuple[str, list[str]]:
    """Load reflexion entries relevant to this skill from the knowledge layer.

    Strategy:
    1. Try MemRL utility-scored retrieval (PgStore.get_top_reflexions) — best rules first
    2. Try mem0 semantic memory (if available) — returns semantically relevant rules
    3. Fall back to .agentura/reflexion_entries.json — exact skill-name matching

    Returns (formatted_markdown, list_of_reflexion_ids) for injection into system prompt.
    Empty string + empty list if no entries exist.
    """
    # skill_path is e.g. skills/hr/interview-questions/SKILL.md
    # We need domain/skill-name = hr/interview-questions
    skill_dir = skill_path.parent        # skills/hr/interview-questions
    domain_dir = skill_dir.parent        # skills/hr
    skill_name_full = f"{domain_dir.name}/{skill_dir.name}"
    # Also match just the skill directory name
    skill_dir_name = skill_dir.name

    # Try MemRL utility-scored retrieval first (DEC-066)
    relevant = _load_reflexions_from_store(skill_name_full)

    # Try mem0 next
    if not relevant:
        relevant = _load_reflexions_from_mem0(skill_name_full)

    # Fall back to JSON files
    if not relevant:
        relevant = _load_reflexions_from_json(skill_name_full, skill_dir_name, skill_path)

    if not relevant:
        return "", []

    reflexion_ids = [e.get("reflexion_id", "") for e in relevant if e.get("reflexion_id")]

    lines = ["## Learned Rules (from past corrections)", ""]
    for entry in relevant:
        rid = entry.get("reflexion_id", "REFL-?")
        rule = entry.get("rule", "")
        applies = entry.get("applies_when", "")
        confidence = entry.get("confidence", 0)
        validated = entry.get("validated_by_test", False)
        source = entry.get("source", "correction")

        badge = " [validated]" if validated else ""
        source_badge = f" [{source}]" if source and source != "correction" else ""
        lines.append(f"- **{rid}** (confidence: {confidence:.0%}{badge}{source_badge}): {rule}")
        if applies:
            lines.append(f"  _Applies when_: {applies}")
    return "\n".join(lines), reflexion_ids


def _load_reflexions_from_store(skill_name_full: str) -> list[dict]:
    """Try loading utility-scored reflexions from the memory store (PgStore/CompositeStore)."""
    try:
        from agentura_sdk.memory import get_memory_store

        store = get_memory_store()
        if hasattr(store, "get_top_reflexions"):
            return store.get_top_reflexions(skill_name_full, limit=5, min_score=0.3)
    except Exception:
        pass
    return []


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
        Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str("")) / "reflexion_entries.json",
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
    project_configs = load_project_configs(skill_path)
    if include_reflexions:
        reflexion_context, injected_ids = load_reflexion_entries(skill_path)
    else:
        reflexion_context, injected_ids = "", []

    # Try standard frontmatter first (--- delimiters)
    post = frontmatter.loads(raw)
    if post.metadata:
        metadata = _parse_metadata(post.metadata)
        return LoadedSkill(
            metadata=metadata,
            system_prompt=post.content.strip(),
            workspace_context=workspace_context,
            domain_context=domain_context,
            project_configs=project_configs,
            reflexion_context=reflexion_context,
            raw_content=raw,
            injected_reflexion_ids=injected_ids,
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
            project_configs=project_configs,
            reflexion_context=reflexion_context,
            raw_content=raw,
            injected_reflexion_ids=injected_ids,
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
        triggers=data.get("triggers", []),
        mcp_tools=data.get("mcp_tools", []),
        display=data.get("display", {}),
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
