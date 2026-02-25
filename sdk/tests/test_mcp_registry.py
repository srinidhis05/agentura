"""Tests for MCP server registry."""

from agentura_sdk.mcp.registry import MCPRegistry, MCPServerConfig


def test_register_and_get():
    reg = MCPRegistry()
    reg.register("redshift", MCPServerConfig(name="redshift", tools=["query"], url="stdio://mcp-redshift"))
    server = reg.get("redshift")
    assert server is not None
    assert server.name == "redshift"
    assert server.tools == ["query"]
    assert server.url == "stdio://mcp-redshift"


def test_list_servers():
    reg = MCPRegistry()
    reg.register("a", MCPServerConfig(name="a"))
    reg.register("b", MCPServerConfig(name="b"))
    assert len(reg.list_servers()) == 2


def test_get_missing_returns_none():
    reg = MCPRegistry()
    assert reg.get("nope") is None


def test_to_dict():
    reg = MCPRegistry()
    reg.register("sheets", MCPServerConfig(name="sheets", tools=["read", "write"], description="Google Sheets"))
    result = reg.to_dict()
    assert len(result) == 1
    assert result[0]["name"] == "sheets"
    assert result[0]["tools"] == ["read", "write"]


def test_discover_from_skills(tmp_path):
    """Discover MCP servers from skill config files."""
    # Create a minimal skill config
    domain_dir = tmp_path / "hr" / "interview-questions"
    domain_dir.mkdir(parents=True)
    (domain_dir / "agentura.config.yaml").write_text("""
domain:
  name: hr
mcp_tools:
  - server: redshift
    tools: ["query"]
  - server: google-sheets
    tools: ["read"]
""")

    reg = MCPRegistry()
    reg.discover_from_skills(str(tmp_path))

    assert reg.get("redshift") is not None
    assert reg.get("google-sheets") is not None
    assert "hr" in reg.get("redshift").domains_using
    assert "query" in reg.get("redshift").tools


def test_discover_from_obot(httpserver):
    """Discover MCP servers from obot registry."""
    httpserver.expect_request("/api/mcp-servers").respond_with_json({
        "items": [
            {
                "manifest": {
                    "name": "Notion",
                    "shortDescription": "Manage Notion pages",
                    "runtime": "remote",
                    "remoteConfig": {"url": "https://mcp.notion.com/mcp"},
                    "toolPreview": [
                        {"name": "search", "description": "Search"},
                        {"name": "fetch", "description": "Fetch page"},
                    ],
                },
                "configured": True,
                "connectURL": "http://localhost:8080/mcp-connect/notion",
            },
            {
                "manifest": {
                    "name": "Google Drive",
                    "shortDescription": "Manage files",
                    "runtime": "remote",
                    "remoteConfig": {"url": "https://gdrive.example.com/mcp"},
                    "toolPreview": [
                        {"name": "list_files", "description": "List"},
                        {"name": "get_file", "description": "Get"},
                    ],
                },
                "configured": True,
                "connectURL": "http://localhost:8080/mcp-connect/gdrive",
            },
        ]
    })

    reg = MCPRegistry()
    reg.discover_from_obot(httpserver.url_for(""))

    assert reg.get("notion") is not None
    assert "search" in reg.get("notion").tools
    assert "fetch" in reg.get("notion").tools
    assert reg.get("notion").url == "http://localhost:8080/mcp-connect/notion"

    assert reg.get("google-drive") is not None
    assert "list_files" in reg.get("google-drive").tools
    assert reg.get("google-drive").url == "http://localhost:8080/mcp-connect/gdrive"


def test_discover_from_obot_unreachable():
    """Obot discovery should silently fail if unreachable."""
    reg = MCPRegistry()
    reg.discover_from_obot("http://localhost:99999")
    assert len(reg.list_servers()) == 0


def test_health_check_not_found():
    reg = MCPRegistry()
    assert reg.health_check("nope") == "not_found"


def test_health_check_configured():
    reg = MCPRegistry()
    reg.register("test", MCPServerConfig(name="test"))
    assert reg.health_check("test") == "configured"
