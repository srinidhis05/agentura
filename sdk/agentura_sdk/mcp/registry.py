"""MCP Server Registry — discovers, registers, and manages MCP tool servers.

Each MCP server provides tools that skills can call during execution.
The registry tracks available servers, their health, and which domains use them.

Usage:
    registry = get_registry()
    registry.register("redshift", MCPServerConfig(url="stdio://mcp-redshift", tools=["query"]))
    server = registry.get("redshift")
    tools = registry.tools_for_skill("hr/interview-questions")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    url: str = ""  # stdio://path or http://host:port
    transport: str = "stdio"  # stdio | sse | streamable-http
    tools: list[str] = field(default_factory=list)
    description: str = ""
    health: str = "unknown"  # healthy | degraded | down | unknown
    domains_using: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class MCPToolBinding:
    """A tool binding for a specific skill execution."""
    server: str
    tool: str
    config: MCPServerConfig


class MCPRegistry:
    """Registry of MCP servers and their tool capabilities."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConfig] = {}

    def register(self, name: str, config: MCPServerConfig) -> None:
        config.name = name
        self._servers[name] = config

    def get(self, name: str) -> MCPServerConfig | None:
        return self._servers.get(name)

    def list_servers(self) -> list[MCPServerConfig]:
        return list(self._servers.values())

    def tools_for_skill(self, skill_path: str) -> list[MCPToolBinding]:
        """Get all MCP tool bindings needed for a skill based on its config."""
        domain = skill_path.split("/")[0] if "/" in skill_path else ""
        skill_name = skill_path.split("/")[1] if "/" in skill_path else skill_path

        # Find config file
        skills_dir = Path(os.environ.get("SKILLS_DIR", "skills"))
        config_path = skills_dir / domain / skill_name / "agentura.config.yaml"
        if not config_path.exists():
            # Try parent domain config
            for child in (skills_dir / domain).iterdir() if (skills_dir / domain).exists() else []:
                candidate = child / "agentura.config.yaml"
                if candidate.exists():
                    config_path = candidate
                    break
            else:
                return []

        try:
            config = yaml.safe_load(config_path.read_text()) or {}
        except Exception:
            return []

        bindings: list[MCPToolBinding] = []
        for mcp_ref in config.get("mcp_tools", []):
            server_name = mcp_ref.get("server", "")
            tool_names = mcp_ref.get("tools", [])
            server_config = self._servers.get(server_name)
            if not server_config:
                server_config = MCPServerConfig(name=server_name, health="not_registered")
            for tool in tool_names:
                bindings.append(MCPToolBinding(server=server_name, tool=tool, config=server_config))

        return bindings

    def health_check(self, name: str) -> str:
        """Check health of an MCP server. Returns status string."""
        server = self._servers.get(name)
        if not server:
            return "not_found"
        if not server.url:
            return "configured"
        # For HTTP servers, do a quick health check
        if server.transport in ("sse", "streamable-http") and server.url.startswith("http"):
            try:
                import httpx
                resp = httpx.get(f"{server.url}/health", timeout=5)
                server.health = "healthy" if resp.status_code == 200 else "degraded"
            except Exception:
                server.health = "down"
        else:
            server.health = "configured"
        return server.health

    def discover_from_skills(self, skills_dir: str = "skills") -> None:
        """Scan all skill configs and auto-register referenced MCP servers."""
        root = Path(skills_dir)
        if not root.exists():
            return

        for config_path in root.rglob("agentura.config.yaml"):
            try:
                config = yaml.safe_load(config_path.read_text()) or {}
            except Exception:
                continue

            domain_name = ""
            domain_cfg = config.get("domain", {})
            if isinstance(domain_cfg, dict):
                domain_name = domain_cfg.get("name", "")
            if not domain_name:
                # Derive from path
                rel = config_path.relative_to(root)
                domain_name = rel.parts[0] if rel.parts else ""

            for mcp_ref in config.get("mcp_tools", []):
                server_name = mcp_ref.get("server", "")
                if not server_name:
                    continue
                if server_name not in self._servers:
                    self._servers[server_name] = MCPServerConfig(
                        name=server_name,
                        tools=mcp_ref.get("tools", []),
                        health="configured",
                    )
                server = self._servers[server_name]
                if domain_name and domain_name not in server.domains_using:
                    server.domains_using.append(domain_name)
                # Merge tools
                for tool in mcp_ref.get("tools", []):
                    if tool not in server.tools:
                        server.tools.append(tool)

    def discover_from_obot(self, obot_url: str) -> None:
        """Discover MCP servers from a running obot registry."""
        try:
            import httpx
            resp = httpx.get(f"{obot_url}/api/mcp-servers", timeout=5)
            if resp.status_code != 200:
                return
            data = resp.json()
        except Exception:
            return

        for item in data.get("items", []):
            manifest = item.get("manifest", {})
            name = manifest.get("name", "").lower().replace(" ", "-")
            if not name:
                continue

            remote_cfg = manifest.get("remoteConfig", {}) or {}
            url = remote_cfg.get("url", "")
            connect_url = item.get("connectURL", "")
            description = manifest.get("shortDescription", "") or manifest.get("description", "")[:120]
            tool_previews = manifest.get("toolPreview", []) or []
            tools = [t.get("name", "") for t in tool_previews if t.get("name")]

            if name not in self._servers:
                self._servers[name] = MCPServerConfig(
                    name=name,
                    url=connect_url or url,
                    transport="streamable-http" if url.startswith("http") else "stdio",
                    tools=tools,
                    description=description,
                    health="configured" if item.get("configured") else "unknown",
                )
            else:
                server = self._servers[name]
                if not server.url:
                    server.url = connect_url or url
                for tool in tools:
                    if tool not in server.tools:
                        server.tools.append(tool)
                if not server.description:
                    server.description = description

    def to_dict(self) -> list[dict[str, Any]]:
        """Serialize registry for API responses."""
        return [
            {
                "name": s.name,
                "url": s.url,
                "transport": s.transport,
                "tools": s.tools,
                "description": s.description,
                "health": s.health,
                "domains_using": s.domains_using,
            }
            for s in self._servers.values()
        ]


_registry: MCPRegistry | None = None


def get_registry() -> MCPRegistry:
    """Return the MCP registry singleton. Auto-discovers servers on first call."""
    global _registry
    if _registry is not None:
        return _registry

    _registry = MCPRegistry()

    # 1. Auto-discover from obot MCP registry (primary source)
    obot_url = os.environ.get("OBOT_URL", "http://localhost:8080")
    _registry.discover_from_obot(obot_url)

    # 2. Supplement with skill config references (adds domain_using bindings)
    skills_dir = os.environ.get("SKILLS_DIR", "skills")
    _registry.discover_from_skills(skills_dir)

    # 3. Override URLs from environment for well-known servers
    _well_known = {
        "k8s": os.environ.get("MCP_K8S_URL", ""),
        "redshift": os.environ.get("MCP_REDSHIFT_URL", ""),
        "google-sheets": os.environ.get("MCP_GOOGLE_SHEETS_URL", ""),
        "google-drive": os.environ.get("MCP_GOOGLE_DRIVE_URL", ""),
        "notion": os.environ.get("MCP_NOTION_URL", ""),
        "jira": os.environ.get("MCP_JIRA_URL", ""),
        "slack": os.environ.get("MCP_SLACK_URL", ""),
        "postgres": os.environ.get("MCP_POSTGRES_URL", ""),
    }
    for name, url in _well_known.items():
        if url:
            if name in _registry._servers:
                _registry._servers[name].url = url
            else:
                _registry.register(name, MCPServerConfig(name=name, url=url))

    return _registry
