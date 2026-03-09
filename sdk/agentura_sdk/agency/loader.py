"""Agent loader — reads agency/ directory and syncs agent definitions to PostgreSQL."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

AGENCY_DIR = Path(os.environ.get("AGENCY_DIR", "agency"))


def load_agents_from_directory(
    agency_dir: Path | None = None,
) -> list[dict]:
    """Walk agency/ directory and parse all agent.yaml files into dicts."""
    root = agency_dir or AGENCY_DIR
    if not root.exists():
        logger.warning("Agency directory not found: %s", root)
        return []

    agents: list[dict] = []
    for agent_yaml in sorted(root.rglob("agent.yaml")):
        try:
            agent = _parse_agent_dir(agent_yaml.parent)
            agents.append(agent)
        except Exception as e:
            logger.error("Failed to load agent from %s: %s", agent_yaml, e)
    logger.info("Loaded %d agent definitions from %s", len(agents), root)
    return agents


def _parse_agent_dir(agent_dir: Path) -> dict:
    """Parse a single agent directory (agent.yaml + SOUL.md + HEARTBEAT.md)."""
    with open(agent_dir / "agent.yaml") as f:
        config = yaml.safe_load(f) or {}

    # Load SOUL.md if present
    soul_path = agent_dir / "SOUL.md"
    if soul_path.exists():
        config["soul"] = soul_path.read_text().strip()

    # Load HEARTBEAT.md schedule info if present
    heartbeat_path = agent_dir / "HEARTBEAT.md"
    if heartbeat_path.exists():
        config["heartbeat_content"] = heartbeat_path.read_text().strip()
        # Extract schedule from heartbeat_schedule field in agent.yaml (cron or descriptive)
        if not config.get("heartbeat_schedule"):
            config["heartbeat_schedule"] = _extract_schedule(config["heartbeat_content"])

    return config


def _extract_schedule(heartbeat_md: str) -> str:
    """Extract first schedule line from HEARTBEAT.md as a simple string."""
    for line in heartbeat_md.split("\n"):
        stripped = line.strip().lstrip("- ")
        if any(t in stripped.lower() for t in ("daily", "hourly", "cron", ":")):
            return stripped
    return "daily"


def sync_agents_to_db(dsn: str, agency_dir: Path | None = None) -> int:
    """Load agent definitions and upsert them into PostgreSQL."""
    from agentura_sdk.memory.agent_store import AgentStore

    agents = load_agents_from_directory(agency_dir)
    if not agents:
        return 0

    store = AgentStore(dsn)

    # First pass: create all agents without reports_to (to avoid FK issues)
    name_to_id: dict[str, str] = {}
    for agent in agents:
        agent_id = store.create_agent(
            name=agent["name"],
            display_name=agent.get("display_name", agent["name"]),
            domain=agent.get("domain", ""),
            role=agent.get("role", "specialist"),
            executor=agent.get("executor", ""),
            model=agent.get("model", ""),
            reports_to=None,  # set in second pass
            status=agent.get("status", "idle"),
            soul=agent.get("soul", ""),
            heartbeat_schedule=json.dumps(agent["heartbeat_schedule"]) if isinstance(agent.get("heartbeat_schedule"), dict) else agent.get("heartbeat_schedule", ""),
            config={
                k: agent[k] for k in ("budget", "delegation", "mcp_tools")
                if k in agent
            },
            skills=agent.get("skills", []),
        )
        name_to_id[agent["name"]] = agent_id

    # Second pass: set reports_to references
    for agent in agents:
        reports_to_name = agent.get("reports_to")
        if reports_to_name and reports_to_name in name_to_id:
            agent_id = name_to_id[agent["name"]]
            parent_id = name_to_id[reports_to_name]
            store.update_agent(agent_id, reports_to=parent_id)

    logger.info("Synced %d agents to database", len(agents))
    return len(agents)
