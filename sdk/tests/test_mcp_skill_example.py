"""Example tests for MCP-enabled skills.

This file demonstrates how to test skills that use MCP tools.
Use these patterns when writing tests for your own MCP-enabled skills.
"""

import pytest


def test_skill_with_mocked_mcp_server(httpserver):
    """Example: Test a skill by mocking its MCP server dependencies."""

    # Mock the MCP server's /tools endpoint (tool discovery)
    httpserver.expect_request("/tools").respond_with_json([
        {
            "name": "notion_search",
            "description": "Search Notion pages",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "notion_fetch_page",
            "description": "Fetch a Notion page by ID",
            "input_schema": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"}
                },
                "required": ["page_id"]
            }
        }
    ])

    # Mock tool execution - search returns results
    httpserver.expect_request(
        "/tools/call",
        json={"name": "notion_search", "arguments": {"query": "quarterly goals"}}
    ).respond_with_json({
        "is_error": False,
        "content": "Found 3 pages: [Q1 2026 Goals, Q4 2025 Review, OKR Template]"
    })

    # Mock tool execution - fetch returns page content
    httpserver.expect_request(
        "/tools/call",
        json={"name": "notion_fetch_page", "arguments": {"page_id": "page-123"}}
    ).respond_with_json({
        "is_error": False,
        "content": "Page content: Q1 2026 Goals\n\n- Revenue: $10M\n- Users: 100k"
    })

    # Now you can test your skill with this mocked MCP server
    # Example assertion (actual implementation depends on your skill runner)
    mcp_server_url = httpserver.url_for("")

    # Verify the mock server URL is available
    assert mcp_server_url.startswith("http://localhost:")

    # In a real test, you would:
    # from agentura_sdk.runner.skill_runner import run_skill
    # result = run_skill(
    #     skill_name="notion-searcher",
    #     domain="productivity",
    #     input_data={"query": "quarterly goals"},
    #     mcp_bindings=[{
    #         "server": "notion",
    #         "url": mcp_server_url,
    #         "tools": ["notion_search", "notion_fetch_page"]
    #     }]
    # )
    # assert result.exit_code == 0


def test_skill_with_mcp_error_handling(httpserver):
    """Example: Test how a skill handles MCP tool errors."""

    httpserver.expect_request("/tools").respond_with_json([
        {
            "name": "gmail_send",
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

    # Mock an error response from the MCP server
    httpserver.expect_request("/tools/call").respond_with_json({
        "is_error": True,
        "content": "Authentication failed: Invalid OAuth token"
    })

    mcp_server_url = httpserver.url_for("")

    # In a real test, verify your skill handles the error gracefully:
    # result = run_skill(...)
    # assert "authentication" in result.output.lower()
    # assert result.exit_code != 0

    assert mcp_server_url is not None


def test_mcp_server_discovery_from_skill_config(tmp_path):
    """Example: Test that skill config correctly declares MCP dependencies."""
    from agentura_sdk.mcp.registry import MCPRegistry

    # Create a test skill config
    skill_dir = tmp_path / "productivity" / "notion-searcher"
    skill_dir.mkdir(parents=True)
    (skill_dir / "agentura.config.yaml").write_text("""
domain:
  name: productivity

skills:
  - name: notion-searcher
    role: agent

mcp_tools:
  - server: notion
    tools:
      - notion_search
      - notion_fetch_page
  - server: gmail
    tools:
      - gmail_send
""")

    # Discover MCP servers from skill configs
    registry = MCPRegistry()
    registry.discover_from_skills(str(tmp_path))

    # Verify servers were discovered
    notion = registry.get("notion")
    assert notion is not None
    assert "notion_search" in notion.tools
    assert "notion_fetch_page" in notion.tools
    assert "productivity" in notion.domains_using

    gmail = registry.get("gmail")
    assert gmail is not None
    assert "gmail_send" in gmail.tools
    assert "productivity" in gmail.domains_using


def test_mcp_tools_with_approval_required(httpserver):
    """Example: Test skills that require approval for certain MCP tools."""

    httpserver.expect_request("/tools").respond_with_json([
        {
            "name": "kubectl_apply",
            "description": "Apply Kubernetes manifest",
            "input_schema": {
                "type": "object",
                "properties": {
                    "manifest": {"type": "string"}
                },
                "required": ["manifest"]
            }
        }
    ])

    # Simulate approval-required tool execution
    # In practice, the executor would prompt for approval before calling this
    httpserver.expect_request("/tools/call").respond_with_json({
        "is_error": False,
        "content": "deployment.apps/myapp created"
    })

    mcp_server_url = httpserver.url_for("")

    # In a real test with approval_required tools:
    # result = run_skill(
    #     ...,
    #     mcp_bindings=[{
    #         "server": "k8s",
    #         "url": mcp_server_url,
    #         "tools": ["kubectl_apply"],
    #         "approval_required": ["kubectl_apply"]
    #     }]
    # )

    assert mcp_server_url is not None


@pytest.mark.integration
def test_skill_with_real_obot_mcp_gateway():
    """Example: Integration test using real Obot MCP gateway.

    This test is marked as 'integration' and will only run when:
    - pytest is invoked with `-m integration`
    - Environment variables are set: OBOT_URL, OBOT_API_KEY
    """
    import os

    obot_url = os.getenv("OBOT_URL")
    obot_api_key = os.getenv("OBOT_API_KEY")

    if not obot_url or not obot_api_key:
        pytest.skip("Obot credentials not configured (OBOT_URL, OBOT_API_KEY)")

    from agentura_sdk.mcp.registry import MCPRegistry

    # Discover real MCP servers from Obot
    registry = MCPRegistry()
    registry.discover_from_obot(obot_url, api_key=obot_api_key)

    # Verify expected servers are available
    # Adjust these assertions based on your Obot configuration
    servers = registry.list_servers()
    assert len(servers) > 0, "No MCP servers found in Obot"

    # Example: Check for a specific server
    # notion = registry.get("notion")
    # if notion:
    #     assert notion.url.startswith("http")
    #     assert len(notion.tools) > 0
