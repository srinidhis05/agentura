# Testing MCP Skills via Slack

This guide shows how to test your MCP-enabled skills through the Slack bot interface.

## Prerequisites

### 1. Check Running Services

```bash
# EKS (production)
assume infrastructure -- kubectl --context infrastructure -n agentura-system get pods

# Expected pods:
# - gateway-xxx (Go gateway)
# - executor-xxx (Python executor with MCP support)
# - web-xxx (Next.js UI)
```

### 2. Verify Slack Bot Configuration

Your Slack bots are configured in `gateway/config/config.yaml`:

| Bot | Mode | Domain | Skills with MCP |
|-----|------|--------|-----------------|
| **pm** | Socket | pm | daily-briefing, action-tracker, meeting-update, notion-sync, pm-heartbeat (12 total) |
| **ecm** | Socket | ecm | triage, process-stuck-order, pattern-intelligence, ecm-daily-flow |
| **incubator** | HTTP | incubator | orchestrate |
| **ge** | HTTP | ge | (growth engineering) |

### 3. Required Environment Variables

Check these are set in the executor pod:

```bash
# For Obot MCP Gateway
OBOT_URL=http://obot-service.obot-system.svc.cluster.local:8080
MCP_GATEWAY_API_KEY=your-obot-api-key

# Or for Vigil
OBOT_URL=https://vigil.internal.genorim.xyz
MCP_GATEWAY_API_KEY=your-vigil-key

# Or for individual MCPs
MCP_GRANOLA_URL=...
MCP_CLICKUP_URL=...
MCP_NOTION_URL=...
MCP_SLACK_URL=...
```

## Testing Workflow

### Step 1: Test Basic Slack Connectivity

Send a message to your Slack bot in any channel where it's invited:

```
@pm-bot help
```

Expected response: Bot acknowledges with 👀 reaction, processes, responds.

### Step 2: Test MCP-Enabled Skill via Slack

**Example: Daily Briefing (uses 4 MCP servers)**

```
@pm-bot morning briefing
```

or (if using slash commands):

```
/pm morning briefing
```

**What happens:**
1. Slack → Gateway → Executor
2. Executor loads `pm/daily-briefing` skill
3. Skill config declares MCP tools:
   ```yaml
   mcp_tools:
     - server: granola
       tools: ["*"]
     - server: clickup
       tools: ["*"]
     - server: notion
       tools: ["*"]
     - server: slack
       tools: ["*"]
   ```
4. Executor discovers MCP servers (Obot/Vigil or individual URLs)
5. Skill agent calls MCP tools:
   - `granola.get_todays_meetings()`
   - `clickup.get_tasks(filter="due:today")`
   - `notion.search_pages(query="...")`
   - `slack.post_message(channel="...", text="...")`
6. Response posted back to Slack

### Step 3: Monitor Execution

**Gateway logs:**
```bash
kubectl logs -n agentura-system deployment/gateway --tail=50 -f
```

Look for:
- `Slack message received` - Incoming message
- `Executing skill: pm/daily-briefing` - Skill dispatched
- `MCP servers discovered: 4` - MCP registry working

**Executor logs:**
```bash
kubectl logs -n agentura-system deployment/executor --tail=50 -f
```

Look for:
- `Loading skill: pm/daily-briefing`
- `MCP bindings: granola, clickup, notion, slack`
- `Calling MCP tool: granola.get_todays_meetings`
- `MCP session initialized: Mcp-Session-Id=...` (for Obot)

### Step 4: Test Slack Interactions (NEW)

**Modal Interaction:**
```
@pm-bot setup new-project
```

Skill can return a modal:
```json
{
  "modal_view": {
    "type": "modal",
    "callback_id": "project_setup_modal",
    "title": {"type": "plain_text", "text": "Project Setup"},
    "blocks": [...]
  }
}
```

When user submits, it triggers another skill execution with form data.

**Button Interaction:**
Post a message with buttons, user clicks → skill receives callback.

**See**: `docs/slack-interactions.md` for full interaction guide.

## Testing Specific MCP Skills

### PM Domain (Socket Mode)

**Daily Briefing** (Granola + ClickUp + Notion + Slack):
```
@pm-bot morning briefing
@pm-bot daily briefing
```

**Meeting Update** (Granola + Notion + Slack + ClickUp):
```
@pm-bot update agentura meeting
@pm-bot agentura update
```

**Action Tracker** (Granola + ClickUp):
```
@pm-bot track actions
```

**Notion Sync** (Notion + Slack):
```
@pm-bot sync notion
```

**PM Heartbeat** (Granola + ClickUp):
```
@pm-bot daily status
@pm-bot pm status
@pm-bot check agentura
```

### ECM Domain (Socket Mode)

**Triage** (Database + Redshift MCP):
```
@ecm-bot triage
@ecm-bot triage last 7 days
```

**Process Stuck Order** (Database + Redshift + Internal APIs):
```
@ecm-bot order ORD-12345
@ecm-bot stuck at kyc-verification
@ecm-bot list kyc-verification
```

**Pattern Intelligence** (Redshift + Analytics):
```
@ecm-bot patterns
```

**Daily Flow** (Redshift + Slack):
```
@ecm-bot dashboard
```

## Debugging MCP Issues

### Issue: "MCP server not found"

**Check registry:**
```bash
# In executor pod
kubectl exec -n agentura-system deployment/executor -- python3 -c "
from agentura_sdk.mcp.registry import get_registry
reg = get_registry()
for s in reg.list_servers():
    print(f'{s.name}: {s.url} ({len(s.tools)} tools)')
"
```

**Fix:**
- Verify `OBOT_URL` and `MCP_GATEWAY_API_KEY` are set
- Or set individual `MCP_{SERVER}_URL` env vars
- Check Obot/Vigil has the server configured

### Issue: "Authentication failed"

**For Obot MCPs:**
- Check `MCP_GATEWAY_API_KEY` is valid
- Verify API key has access to the specific MCP server in Obot settings

**For individual MCPs:**
- Check if server requires auth headers
- Add to skill config:
  ```yaml
  mcp_tools:
    - server: notion
      tools: ["*"]
      headers:
        Authorization: "Bearer ${NOTION_API_KEY}"
  ```

### Issue: "Tool not allowed"

**Check skill config:**
```yaml
mcp_tools:
  - server: granola
    tools: ["*"]  # Allows all tools
  # vs
  - server: granola
    tools: ["get_todays_meetings"]  # Only this tool
```

**Fix:** Add the specific tool to the allowed list, or use `["*"]`.

### Issue: "Session expired" (Obot)

Obot uses session protocol:
1. POST `/mcp-connect/{server}/initialize` → get `Mcp-Session-Id`
2. Include header in all subsequent calls

**Fix:** Executor handles this automatically. If seeing this error:
- Check Obot is reachable from executor pods
- Verify `hostNetwork: true` in PTC worker pods (DEC-082)
- Check DNS resolution: `kubectl exec ... -- nslookup obot-service.obot-system.svc.cluster.local`

## Testing Patterns

### 1. Unit Test (Mocked MCPs)

```python
def test_daily_briefing_via_slack(httpserver):
    """Simulate Slack → Skill → MCP flow."""

    # Mock Slack webhook payload
    slack_payload = {
        "event": {
            "type": "app_mention",
            "text": "<@BOT> morning briefing",
            "user": "U123",
            "channel": "C456"
        }
    }

    # Mock MCP servers
    httpserver.expect_request("/granola/tools/call").respond_with_json({
        "is_error": False,
        "content": "Meetings: ..."
    })

    # Send to gateway
    # response = requests.post(f"{gateway_url}/api/slack/events", json=slack_payload)
```

### 2. Integration Test (Real Slack + Mocked MCPs)

```python
@pytest.mark.integration
def test_slack_bot_with_mocked_mcps(httpserver):
    """Send real Slack message, mock only the MCPs."""

    # Override MCP URLs to point to httpserver
    os.environ["MCP_GRANOLA_URL"] = httpserver.url_for("/granola")
    os.environ["MCP_CLICKUP_URL"] = httpserver.url_for("/clickup")

    # Mock MCP responses
    httpserver.expect_request("/granola/tools/call").respond_with_json(...)

    # Send REAL Slack message via Slack SDK
    from slack_sdk import WebClient
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.chat_postMessage(channel="#test", text="@pm-bot morning briefing")

    # Verify skill execution
    # Check httpserver received MCP calls
```

### 3. E2E Test (Real Slack + Real MCPs)

```bash
# Set real MCP gateway
export OBOT_URL=https://vigil.internal.genorim.xyz
export MCP_GATEWAY_API_KEY=real-key

# Restart executor to pick up env vars
kubectl rollout restart -n agentura-system deployment/executor

# Send message in Slack
# Manually verify response
```

## Verification Checklist

After sending a Slack message to test an MCP skill:

- [ ] Bot reacts with 👀 (acknowledgment)
- [ ] Bot shows ⏳ typing indicator
- [ ] Gateway logs show: `Executing skill: {domain}/{skill}`
- [ ] Executor logs show: `MCP bindings: {servers}`
- [ ] Executor logs show: `Calling MCP tool: {server}.{tool}`
- [ ] For Obot: logs show `Mcp-Session-Id` header
- [ ] Bot responds in Slack thread
- [ ] Response includes data from MCP calls

## Quick Reference

**Check if skill uses MCPs:**
```bash
grep -A 5 "mcp_tools:" skills/pm/daily-briefing/agentura.config.yaml
```

**List all MCP-enabled skills:**
```bash
find skills -name "agentura.config.yaml" -exec grep -l "mcp_tools:" {} \;
```

**Test in Slack:**
```
@pm-bot morning briefing       # PM domain, 4 MCPs
@ecm-bot triage                # ECM domain, database MCP
@pm-bot setup new-project      # Opens modal (interaction primitive)
```

**Monitor logs:**
```bash
# Both in parallel
kubectl logs -n agentura-system deployment/gateway -f &
kubectl logs -n agentura-system deployment/executor -f &
```

## Next Steps

1. **Send a test message** to @pm-bot in Slack
2. **Monitor logs** to see MCP calls
3. **Check Obot/Vigil** to verify servers are configured
4. **Try modal interactions** (setup commands that open forms)

For detailed Slack interaction primitives (modals, buttons, select menus), see:
- `docs/slack-interactions.md`
- `examples/slack-interactions/config.yaml`
