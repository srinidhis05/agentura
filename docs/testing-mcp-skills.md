# Testing MCP-Enabled Skills

This guide shows how to test skills that use MCP (Model Context Protocol) servers.

## Quick Start

```bash
# Run all MCP tests
pytest sdk/tests/test_mcp_*.py -v

# Run integration tests (requires real Obot)
OBOT_URL=http://localhost:8080 \
OBOT_API_KEY=your-key \
pytest sdk/tests/ -m integration

# Run example tests to see patterns
pytest sdk/tests/test_mcp_skill_example.py -v
```

## Testing Patterns

### 1. Mock MCP Server (Unit Tests)

Use `pytest-httpserver` to mock MCP tool servers:

```python
def test_skill_with_mocked_notion(httpserver):
    """Test a skill by mocking the Notion MCP server."""

    # Mock tool discovery (/tools endpoint)
    httpserver.expect_request("/tools").respond_with_json([
        {
            "name": "search_pages",
            "description": "Search Notion pages",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    ])

    # Mock tool execution (/tools/call endpoint)
    httpserver.expect_request(
        "/tools/call",
        json={"name": "search_pages", "arguments": {"query": "test"}}
    ).respond_with_json({
        "is_error": False,
        "content": "Found 3 pages: [Page 1, Page 2, Page 3]"
    })

    # Use the mock server URL in your skill test
    mcp_url = httpserver.url_for("")

    # Test your skill with mocked MCP bindings
    # result = run_skill(
    #     skill_name="notion-searcher",
    #     mcp_bindings=[{
    #         "server": "notion",
    #         "url": mcp_url,
    #         "tools": ["search_pages"]
    #     }]
    # )
```

### 2. Test MCP Server Discovery

Verify your skill's `agentura.config.yaml` correctly declares MCP dependencies:

```python
def test_skill_declares_mcp_dependencies(tmp_path):
    """Verify skill config lists required MCP tools."""
    from agentura_sdk.mcp.registry import MCPRegistry

    # Create test skill config
    skill_dir = tmp_path / "pm" / "daily-briefing"
    skill_dir.mkdir(parents=True)
    (skill_dir / "agentura.config.yaml").write_text("""
domain:
  name: pm

mcp_tools:
  - server: granola
    tools: ["*"]
  - server: clickup
    tools: ["get_tasks", "create_task"]
  - server: notion
    tools: ["search_pages"]
""")

    # Discover MCP servers from skills
    registry = MCPRegistry()
    registry.discover_from_skills(str(tmp_path))

    # Verify registration
    granola = registry.get("granola")
    assert granola is not None
    assert "pm" in granola.domains_using

    clickup = registry.get("clickup")
    assert "get_tasks" in clickup.tools
    assert "create_task" in clickup.tools
```

### 3. Test MCP Error Handling

Mock error responses to verify graceful failure:

```python
def test_skill_handles_mcp_auth_error(httpserver):
    """Verify skill handles MCP authentication errors."""

    httpserver.expect_request("/tools").respond_with_json([
        {"name": "send_email", "description": "Send email", "input_schema": {...}}
    ])

    # Mock an auth error
    httpserver.expect_request("/tools/call").respond_with_json({
        "is_error": True,
        "content": "Authentication failed: OAuth token expired"
    })

    # Test that skill handles the error gracefully
    # (returns helpful error message, doesn't crash, etc.)
```

### 4. Test Tools Requiring Approval

For tools marked with `approval_required`:

```python
def test_skill_with_approval_tools(httpserver):
    """Test skills using approval-required MCP tools."""

    httpserver.expect_request("/tools").respond_with_json([
        {"name": "kubectl_apply", "description": "Apply K8s manifest", ...}
    ])

    # In practice, executor prompts user before calling
    httpserver.expect_request("/tools/call").respond_with_json({
        "is_error": False,
        "content": "deployment.apps/myapp created"
    })

    mcp_url = httpserver.url_for("")

    # Skill config marks this tool for approval
    # mcp_bindings=[{
    #     "server": "k8s",
    #     "url": mcp_url,
    #     "tools": ["kubectl_apply"],
    #     "approval_required": ["kubectl_apply"]
    # }]
```

### 5. Integration Tests with Real Obot

Test against real MCP servers via Obot gateway:

```python
import pytest
import os

@pytest.mark.integration
def test_skill_with_real_obot():
    """Integration test with real Obot MCP gateway."""

    obot_url = os.getenv("OBOT_URL")
    obot_api_key = os.getenv("OBOT_API_KEY")

    if not obot_url or not obot_api_key:
        pytest.skip("Obot not configured")

    from agentura_sdk.mcp.registry import MCPRegistry

    # Discover real servers
    registry = MCPRegistry()
    registry.discover_from_obot(obot_url, api_key=obot_api_key)

    # Verify expected servers
    notion = registry.get("notion")
    assert notion is not None
    assert notion.url.startswith("http")

    # Run skill with real MCP binding
    # result = run_skill(
    #     skill_name="notion-searcher",
    #     mcp_bindings=[{
    #         "server": "notion",
    #         "url": notion.url,
    #         "headers": {"Authorization": f"Bearer {obot_api_key}"},
    #         "tools": notion.tools
    #     }]
    # )
```

## Test File Structure

Organize tests alongside skills:

```
skills/
  pm/
    daily-briefing/
      SKILL.md
      agentura.config.yaml
      tests/
        test_daily_briefing.py      # Unit tests (mocked MCPs)
        test_integration.py          # Integration tests (real Obot)
        generated/
          corrections.yaml           # Auto-generated from CLI
```

## Running Tests

### Unit Tests (Mocked MCP)

```bash
# All unit tests
pytest skills/pm/daily-briefing/tests/test_daily_briefing.py -v

# Specific test
pytest skills/pm/daily-briefing/tests/test_daily_briefing.py::test_skill_searches_notion -v
```

### Integration Tests (Real Obot)

```bash
# Set credentials
export OBOT_URL=http://localhost:8080
export OBOT_API_KEY=your-api-key-here

# Run integration tests
pytest skills/pm/daily-briefing/tests/ -m integration -v
```

### Using the CLI

```bash
# Run skill tests via CLI
agentura test pm/daily-briefing

# Generate regression tests from corrections
agentura correct pm/daily-briefing \
  --input '{"date": "2026-03-14"}' \
  --expected '{"briefing": "..."}' \
  --description "Briefing includes meetings"
```

## MCP Session Protocol (Obot)

When testing with Obot MCP servers:

1. **Initialize session**: `POST /mcp-connect/{server_id}/initialize`
2. **Get session ID**: Response header `Mcp-Session-Id: session-abc123`
3. **Use session**: Include `Mcp-Session-Id` header in all subsequent calls

**Note**: The executor handles session protocol automatically. In unit tests, you don't need to mock the session initialization - just mock `/tools` and `/tools/call`.

## Common Patterns

### Verify Tool Filtering (GR-021)

Test that `tools: ["*"]` means "allow all":

```python
def test_wildcard_tools_allows_all():
    """Verify tools: ['*'] means allow all, not literal '*' match."""
    config = {
        "mcp_tools": [
            {"server": "notion", "tools": ["*"]}
        ]
    }

    # Should allow any tool from the server
    # NOT look for a tool literally named "*"
```

### Verify Tool Sanitization (GR-020)

Test that MCP tool definitions are sanitized before sending to Anthropic:

```python
def test_mcp_tools_sanitized():
    """MCP tool defs must be sanitized to {name, description, input_schema} only."""

    # Mock MCP server returns extra fields
    mcp_response = {
        "name": "search",
        "description": "Search",
        "input_schema": {...},
        "internal_id": "abc123",  # Should be stripped
        "version": "1.0"          # Should be stripped
    }

    # Verify executor strips non-standard fields before passing to Anthropic
```

## Best Practices

1. **Mock by default** - Use `pytest-httpserver` for fast, reliable unit tests
2. **Mark integration tests** - Use `@pytest.mark.integration` for tests requiring real services
3. **Test config first** - Verify `mcp_tools` section before testing skill logic
4. **Test error paths** - Mock MCP errors (`is_error: true`) to verify handling
5. **Test tool approval** - If using `approval_required`, verify the approval flow
6. **Don't mock sessions** - For Obot, the executor handles `Mcp-Session-Id` automatically
7. **Use fixtures** - Create reusable pytest fixtures for common MCP mocks

## Debugging Tips

### MCP Server Not Found

```python
# Check if server is registered
from agentura_sdk.mcp.registry import get_registry

registry = get_registry()
server = registry.get("notion")
assert server is not None, "Notion MCP server not registered"
```

### Tool Not Available

```python
# Verify tool is in server's tool list
assert "search_pages" in server.tools
```

### Session Issues (Obot)

Check executor logs for `Mcp-Session-Id` header:

```bash
kubectl logs -n agentura-system executor-xxx | grep "Mcp-Session-Id"
```

## Example Test Files

- **`sdk/tests/test_mcp_registry.py`** - MCP registry tests
- **`sdk/tests/test_mcp_skill_example.py`** - Example skill test patterns
- **`skills/pm/daily-briefing/tests/`** - Real skill test suite (create this)

## Further Reading

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [pytest-httpserver docs](https://pytest-httpserver.readthedocs.io/)
- [Obot MCP Gateway](../MEMORY.md#obot-mcp-gateway-dec-080-dec-081)
- [Skill Testing Guide](../skills/README.md#testing)
