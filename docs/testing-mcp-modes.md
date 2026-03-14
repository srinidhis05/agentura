# Testing with Different MCP Configurations

The testing infrastructure works with **Vigil, Obot, and individual MCP servers**. Here's how to use each mode.

## Mode 1: Vigil Gateway

Vigil is mentioned explicitly in the codebase as an alternative to Obot:

### Testing with Vigil

```python
@pytest.mark.integration
def test_skill_with_vigil():
    """Test using Vigil MCP gateway."""
    import os

    vigil_url = os.getenv("VIGIL_URL", "https://vigil.internal.genorim.xyz")
    vigil_api_key = os.getenv("MCP_GATEWAY_API_KEY")

    if not vigil_api_key:
        pytest.skip("MCP_GATEWAY_API_KEY not set")

    from agentura_sdk.mcp.registry import MCPRegistry

    # Same function works for both Obot and Vigil
    registry = MCPRegistry()
    registry.discover_from_obot(vigil_url, api_key=vigil_api_key)

    # Use discovered servers
    servers = registry.list_servers()
    assert len(servers) > 0
```

### Running with Vigil

```bash
# Production with Vigil
export OBOT_URL=https://vigil.internal.genorim.xyz
export MCP_GATEWAY_API_KEY=your-vigil-api-key

# Run tests
pytest -m integration
```

**Note**: The function name is `discover_from_obot` but works with **any** MCP gateway that implements the `/api/mcp-servers` endpoint. Vigil is explicitly supported.

## Mode 2: Individual MCP Servers (No Gateway)

You can connect to **individual MCP servers directly** without Obot/Vigil:

### Direct Server Registration

```python
def test_with_direct_mcp_servers():
    """Test using direct MCP server URLs (no gateway)."""
    from agentura_sdk.mcp.registry import MCPRegistry, MCPServerConfig

    registry = MCPRegistry()

    # Register individual servers directly
    registry.register("notion", MCPServerConfig(
        name="notion",
        url="https://mcp.notion.com",  # Direct URL
        transport="streamable-http",
        tools=["search_pages", "fetch_page"]
    ))

    registry.register("gmail", MCPServerConfig(
        name="gmail",
        url="http://localhost:3000/mcp",  # Local MCP server
        transport="sse",
        tools=["send_email", "search"]
    ))

    # Use the servers
    notion = registry.get("notion")
    assert notion.url == "https://mcp.notion.com"
```

### Using Environment Variables

The registry **automatically discovers** individual servers via env vars:

```bash
# Set individual MCP server URLs
export MCP_NOTION_URL=https://mcp.notion.com
export MCP_GMAIL_URL=http://localhost:3000/mcp
export MCP_K8S_URL=stdio://mcp-k8s  # stdio transport for local binary
export MCP_SLACK_URL=http://localhost:4000/slack-mcp

# These override any URLs discovered from Obot/Vigil
```

```python
def test_with_env_var_mcps():
    """Individual MCPs configured via environment variables."""
    import os

    # Set env vars (or use actual environment)
    os.environ["MCP_NOTION_URL"] = "https://mcp.notion.com"
    os.environ["MCP_GMAIL_URL"] = "http://localhost:3000/mcp"

    from agentura_sdk.mcp.registry import get_registry

    # Registry auto-discovers from env vars
    registry = get_registry()

    notion = registry.get("notion")
    assert notion is not None
    assert notion.url == "https://mcp.notion.com"

    gmail = registry.get("gmail")
    assert gmail is not None
    assert gmail.url == "http://localhost:3000/mcp"
```

### Mocking Individual MCP Servers

```python
def test_skill_with_multiple_individual_mcps(httpserver):
    """Mock multiple individual MCP servers separately."""

    # Mock Notion MCP server
    notion_server = httpserver
    notion_server.expect_request("/notion/tools").respond_with_json([
        {"name": "search_pages", "description": "Search", "input_schema": {}}
    ])
    notion_server.expect_request("/notion/tools/call").respond_with_json({
        "is_error": False,
        "content": "Found 3 pages"
    })

    # Mock Gmail MCP server (same httpserver, different paths)
    notion_server.expect_request("/gmail/tools").respond_with_json([
        {"name": "send_email", "description": "Send email", "input_schema": {}}
    ])
    notion_server.expect_request("/gmail/tools/call").respond_with_json({
        "is_error": False,
        "content": "Email sent"
    })

    base_url = httpserver.url_for("")

    # Test skill with individual MCP servers
    # mcp_bindings = [
    #     {"server": "notion", "url": f"{base_url}/notion", "tools": ["search_pages"]},
    #     {"server": "gmail", "url": f"{base_url}/gmail", "tools": ["send_email"]}
    # ]
```

## Mode 3: Hybrid (Gateway + Individual)

Combine gateway discovery with individual overrides:

```python
def test_hybrid_mcp_configuration():
    """Use Vigil for most servers, override specific ones."""
    import os

    # Use Vigil for general discovery
    os.environ["OBOT_URL"] = "https://vigil.internal.genorim.xyz"
    os.environ["MCP_GATEWAY_API_KEY"] = "vigil-key"

    # Override specific servers with direct URLs
    os.environ["MCP_NOTION_URL"] = "http://localhost:3001/notion"  # Local dev
    os.environ["MCP_K8S_URL"] = "stdio://kubectl-mcp"  # Local binary

    from agentura_sdk.mcp.registry import get_registry

    registry = get_registry()

    # Notion uses local override, not Vigil
    notion = registry.get("notion")
    assert notion.url == "http://localhost:3001/notion"

    # Other servers come from Vigil
    gmail = registry.get("gmail")
    assert gmail.url.startswith("https://vigil")
```

## Discovery Priority

The registry discovers servers in this order (later overrides earlier):

1. **Gateway discovery** (Obot/Vigil via `OBOT_URL`)
2. **Skill config discovery** (from `agentura.config.yaml` files)
3. **Environment variable overrides** (`MCP_{SERVER}_URL`)

```python
def test_discovery_priority():
    """Demonstrate discovery priority."""
    import os
    from agentura_sdk.mcp.registry import MCPRegistry

    # 1. Gateway says Notion is at vigil URL
    registry = MCPRegistry()
    registry.discover_from_obot("https://vigil.internal.genorim.xyz")

    notion = registry.get("notion")
    assert "vigil" in notion.url

    # 2. Skill config discovers it needs Notion
    # (doesn't change URL, just adds domain_using)

    # 3. Env var OVERRIDES the URL
    os.environ["MCP_NOTION_URL"] = "http://localhost:9000/notion"

    # Re-initialize to apply env vars
    from agentura_sdk.mcp.registry import get_registry
    registry = get_registry()

    notion = registry.get("notion")
    assert notion.url == "http://localhost:9000/notion"
```

## Testing Patterns for Each Mode

### Vigil

```bash
# Integration tests with Vigil
OBOT_URL=https://vigil.internal.genorim.xyz \
MCP_GATEWAY_API_KEY=your-key \
pytest -m integration
```

### Individual MCPs

```bash
# Test with direct server URLs
MCP_NOTION_URL=https://mcp.notion.com \
MCP_GMAIL_URL=http://localhost:3000/gmail \
pytest skills/pm/daily-briefing/tests/

# Test with local MCP servers
MCP_K8S_URL=http://localhost:8001/mcp \
MCP_SLACK_URL=http://localhost:8002/mcp \
pytest
```

### Mocked (Unit Tests)

```python
# No environment setup needed - all mocked
pytest skills/pm/daily-briefing/tests/test_daily_briefing.py
```

## Supported Transports

Individual MCP servers can use different transports:

```python
from agentura_sdk.mcp.registry import MCPServerConfig

# HTTP/HTTPS (most common)
MCPServerConfig(
    name="notion",
    url="https://mcp.notion.com",
    transport="streamable-http"
)

# SSE (Server-Sent Events)
MCPServerConfig(
    name="gmail",
    url="http://localhost:3000/mcp",
    transport="sse"
)

# stdio (local binary/process)
MCPServerConfig(
    name="k8s",
    url="stdio://kubectl-mcp",
    transport="stdio"
)
```

## Well-Known Individual Servers

The registry has built-in support for these individual servers via env vars:

- `MCP_K8S_URL` - Kubernetes MCP
- `MCP_REDSHIFT_URL` - AWS Redshift MCP
- `MCP_GOOGLE_SHEETS_URL` - Google Sheets MCP
- `MCP_GOOGLE_DRIVE_URL` - Google Drive MCP
- `MCP_NOTION_URL` - Notion MCP
- `MCP_JIRA_URL` - Jira MCP
- `MCP_SLACK_URL` - Slack MCP
- `MCP_POSTGRES_URL` - PostgreSQL MCP

Just set the env var and the registry auto-discovers it:

```bash
export MCP_NOTION_URL=https://my-notion-mcp.internal.com
export MCP_K8S_URL=stdio://mcp-kubectl
```

## Summary

✅ **Vigil**: Use `OBOT_URL=https://vigil.internal.genorim.xyz`
✅ **Individual MCPs**: Use `MCP_{SERVER}_URL` env vars
✅ **Hybrid**: Combine both (env vars override gateway)
✅ **Mocked**: Use `pytest-httpserver` (no setup needed)

All testing patterns work with **all three modes**!
