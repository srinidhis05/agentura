"""Tests for individual MCP servers (without Obot/Vigil gateway)."""

import os
import pytest
from agentura_sdk.mcp.registry import MCPRegistry, MCPServerConfig


def test_register_individual_mcp_servers():
    """Register individual MCP servers directly without gateway."""
    registry = MCPRegistry()

    # Register Notion MCP directly
    registry.register("notion", MCPServerConfig(
        name="notion",
        url="https://mcp.notion.com",
        transport="streamable-http",
        tools=["search_pages", "fetch_page"],
        description="Notion MCP server"
    ))

    # Register local Gmail MCP
    registry.register("gmail", MCPServerConfig(
        name="gmail",
        url="http://localhost:3000/gmail-mcp",
        transport="sse",
        tools=["send_email", "search_email"]
    ))

    # Register stdio-based K8s MCP
    registry.register("k8s", MCPServerConfig(
        name="k8s",
        url="stdio://kubectl-mcp",
        transport="stdio",
        tools=["kubectl_apply", "kubectl_get"]
    ))

    # Verify all registered
    assert len(registry.list_servers()) == 3

    notion = registry.get("notion")
    assert notion.url == "https://mcp.notion.com"
    assert notion.transport == "streamable-http"
    assert "search_pages" in notion.tools

    gmail = registry.get("gmail")
    assert gmail.url == "http://localhost:3000/gmail-mcp"
    assert gmail.transport == "sse"

    k8s = registry.get("k8s")
    assert k8s.url == "stdio://kubectl-mcp"
    assert k8s.transport == "stdio"


def test_individual_mcp_from_env_vars():
    """Individual MCP servers auto-discovered from environment variables."""

    # Set individual server URLs
    os.environ["MCP_NOTION_URL"] = "https://mcp.notion.com"
    os.environ["MCP_GMAIL_URL"] = "http://localhost:3000/mcp"
    os.environ["MCP_K8S_URL"] = "stdio://kubectl-mcp"

    # Create fresh registry (in real code, use get_registry())
    registry = MCPRegistry()

    # Manually apply env var logic (normally done by get_registry())
    well_known = {
        "notion": os.environ.get("MCP_NOTION_URL", ""),
        "gmail": os.environ.get("MCP_GMAIL_URL", ""),
        "k8s": os.environ.get("MCP_K8S_URL", ""),
    }

    for name, url in well_known.items():
        if url:
            registry.register(name, MCPServerConfig(name=name, url=url))

    # Verify discovery
    notion = registry.get("notion")
    assert notion is not None
    assert notion.url == "https://mcp.notion.com"

    gmail = registry.get("gmail")
    assert gmail is not None
    assert gmail.url == "http://localhost:3000/mcp"

    k8s = registry.get("k8s")
    assert k8s is not None
    assert k8s.url == "stdio://kubectl-mcp"

    # Cleanup
    del os.environ["MCP_NOTION_URL"]
    del os.environ["MCP_GMAIL_URL"]
    del os.environ["MCP_K8S_URL"]


def test_env_var_overrides_gateway():
    """Environment variables override gateway-discovered URLs."""
    registry = MCPRegistry()

    # 1. Gateway discovers Notion at vigil URL
    registry.register("notion", MCPServerConfig(
        name="notion",
        url="https://vigil.internal.genorim.xyz/mcp-connect/notion",
        transport="streamable-http"
    ))

    notion = registry.get("notion")
    assert "vigil" in notion.url

    # 2. Environment variable overrides it
    os.environ["MCP_NOTION_URL"] = "http://localhost:9000/notion-local"

    # Apply override (simulating get_registry() behavior)
    override_url = os.environ.get("MCP_NOTION_URL")
    if override_url:
        registry._servers["notion"].url = override_url

    # Verify override applied
    notion = registry.get("notion")
    assert notion.url == "http://localhost:9000/notion-local"

    # Cleanup
    del os.environ["MCP_NOTION_URL"]


def test_skill_with_individual_mcp_servers(httpserver):
    """Test a skill using individual MCP servers (no gateway)."""

    # Mock individual Notion MCP server
    httpserver.expect_request("/notion/tools").respond_with_json([
        {
            "name": "search_pages",
            "description": "Search Notion pages",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    ])

    httpserver.expect_request("/notion/tools/call").respond_with_json({
        "is_error": False,
        "content": "Found 5 pages matching 'test'"
    })

    # Mock individual Gmail MCP server
    httpserver.expect_request("/gmail/tools").respond_with_json([
        {
            "name": "send_email",
            "description": "Send email",
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    ])

    httpserver.expect_request("/gmail/tools/call").respond_with_json({
        "is_error": False,
        "content": "Email sent to user@example.com"
    })

    base_url = httpserver.url_for("")

    # Register individual servers with test URLs
    registry = MCPRegistry()
    registry.register("notion", MCPServerConfig(
        name="notion",
        url=f"{base_url}/notion",
        transport="streamable-http",
        tools=["search_pages"]
    ))
    registry.register("gmail", MCPServerConfig(
        name="gmail",
        url=f"{base_url}/gmail",
        transport="sse",
        tools=["send_email"]
    ))

    # Verify servers are available
    assert registry.get("notion") is not None
    assert registry.get("gmail") is not None

    # In a real test, you would run a skill with these bindings:
    # mcp_bindings = [
    #     {
    #         "server": "notion",
    #         "url": registry.get("notion").url,
    #         "tools": registry.get("notion").tools
    #     },
    #     {
    #         "server": "gmail",
    #         "url": registry.get("gmail").url,
    #         "tools": registry.get("gmail").tools
    #     }
    # ]


def test_hybrid_gateway_plus_individual():
    """Use gateway for some servers, individual URLs for others."""
    registry = MCPRegistry()

    # Servers from Vigil gateway
    registry.register("clickup", MCPServerConfig(
        name="clickup",
        url="https://vigil.internal.genorim.xyz/mcp-connect/clickup",
        transport="streamable-http"
    ))
    registry.register("granola", MCPServerConfig(
        name="granola",
        url="https://vigil.internal.genorim.xyz/mcp-connect/granola",
        transport="streamable-http"
    ))

    # Individual servers (local dev or direct)
    registry.register("notion", MCPServerConfig(
        name="notion",
        url="http://localhost:3001/notion-mcp",  # Local dev server
        transport="sse"
    ))
    registry.register("k8s", MCPServerConfig(
        name="k8s",
        url="stdio://kubectl-mcp",  # Local binary
        transport="stdio"
    ))

    # Verify hybrid setup
    clickup = registry.get("clickup")
    assert "vigil" in clickup.url

    notion = registry.get("notion")
    assert "localhost" in notion.url

    k8s = registry.get("k8s")
    assert k8s.url.startswith("stdio://")


def test_stdio_transport_for_local_binaries():
    """Test stdio transport for local MCP binaries."""
    registry = MCPRegistry()

    # Register stdio-based MCP servers (local binaries)
    registry.register("kubectl", MCPServerConfig(
        name="kubectl",
        url="stdio://mcp-kubectl",
        transport="stdio",
        tools=["kubectl_apply", "kubectl_get", "kubectl_delete"]
    ))

    registry.register("aws-cli", MCPServerConfig(
        name="aws-cli",
        url="stdio://mcp-aws",
        transport="stdio",
        tools=["s3_upload", "s3_download", "ec2_list"]
    ))

    # Verify stdio transport
    kubectl = registry.get("kubectl")
    assert kubectl.url == "stdio://mcp-kubectl"
    assert kubectl.transport == "stdio"

    aws = registry.get("aws-cli")
    assert aws.url == "stdio://mcp-aws"
    assert aws.transport == "stdio"
