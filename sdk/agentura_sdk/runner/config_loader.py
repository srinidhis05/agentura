"""Parse agentura.config.yaml → SkillConfig."""

from pathlib import Path

import yaml

from agentura_sdk.types import SkillConfig


def load_config(config_path: Path) -> SkillConfig:
    """Load and validate an agentura.config.yaml file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text())
    if not raw:
        raise ValueError(f"Empty config: {config_path}")

    raw = _normalize_config(raw)
    return SkillConfig(**raw)


def _normalize_config(raw: dict) -> dict:
    """Normalize showcase-style config to SkillConfig shape.

    Handles two formats:
    1. Original: domain: {name: "x", description: "y"}
    2. Showcase: domain: "x" (string shorthand)
    """
    # domain: "hr" → domain: {name: "hr"}
    if isinstance(raw.get("domain"), str):
        raw["domain"] = {
            "name": raw["domain"],
            "description": raw.get("description", ""),
        }
        raw.pop("description", None)

    # skills: normalize field names
    for skill in raw.get("skills", []):
        if "cost_budget_per_execution" in skill and "cost_budget" not in skill:
            skill["cost_budget"] = skill.pop("cost_budget_per_execution")
        if "path" not in skill:
            skill["path"] = skill["name"]

    # routing: from/to shorthand → when/then
    normalized_routing = []
    for rule in raw.get("routing", []):
        if "from" in rule:
            normalized_routing.append({
                "when": {
                    "from_skill": rule["from"],
                    "condition": rule.get("condition", ""),
                },
                "then": {
                    "to_skill": rule["to"],
                    "context_pass": rule.get("context_pass", []),
                },
            })
        else:
            normalized_routing.append(rule)
    raw["routing"] = normalized_routing

    return raw


def find_config(skill_dir: Path) -> Path:
    """Find agentura.config.yaml walking up from skill_dir."""
    current = skill_dir.resolve()
    while current != current.parent:
        candidate = current / "agentura.config.yaml"
        if candidate.exists():
            return candidate
        current = current.parent
    raise FileNotFoundError(
        f"No agentura.config.yaml found in or above {skill_dir}"
    )
