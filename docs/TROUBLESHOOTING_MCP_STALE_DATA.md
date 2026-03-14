# Troubleshooting: MCP Skills Returning Stale Data

## Symptoms

- Skill output shows old dates (e.g., January 2025 instead of March 2026)
- Generic/random data instead of project-specific context
- "systems_unavailable" errors for MCP servers
- Skill says "Slack posting unavailable due to token permissions"

## Root Causes

### 1. MCP Servers Not Connected

**Check executor environment:**
```bash
kubectl exec -n agentura-system deployment/executor -- env | grep -E "OBOT_URL|MCP_"
```

**Expected:**
```
OBOT_URL=http://obot-service.obot-system.svc.cluster.local:8080
MCP_GATEWAY_API_KEY=your-key
```

Or for individual servers:
```
MCP_GRANOLA_URL=...
MCP_CLICKUP_URL=...
MCP_NOTION_URL=...
MCP_SLACK_URL=...
```

**Fix:** Set the env vars in the executor deployment and restart:
```bash
kubectl set env deployment/executor -n agentura-system \
  OBOT_URL=http://obot-service.obot-system.svc.cluster.local:8080 \
  MCP_GATEWAY_API_KEY=your-actual-key

kubectl rollout restart -n agentura-system deployment/executor
```

### 2. Obot/Vigil MCP Servers Not Configured

**Check Obot UI:**
1. Open Obot at http://localhost:8080 (or your Obot URL)
2. Go to MCP Servers section
3. Verify these servers are configured and CONNECTED:
   - Granola (meetings)
   - ClickUp (tasks)
   - Notion (notes)
   - Slack (messaging)

**Fix:** Configure each MCP server in Obot:
- Add OAuth tokens / API keys
- Test connection
- Enable for your API key

### 3. MCP Session Issues (Obot Only)

Obot requires session initialization. Check executor logs:

```bash
kubectl logs -n agentura-system deployment/executor --tail=100 | grep -i "mcp-session"
```

**Expected:**
```
INFO: MCP session initialized: Mcp-Session-Id=abc123
INFO: Calling MCP tool: granola.get_todays_meetings
```

**If missing:**
- Verify `hostNetwork: true` in PTC worker pods (DEC-082)
- Check DNS resolution: `kubectl exec -n agentura-system deployment/executor -- nslookup obot-service.obot-system.svc.cluster.local`

**Fix for VPN routing** (if Obot is behind VPN):
```yaml
# In executor deployment
spec:
  template:
    spec:
      hostNetwork: true
      dnsPolicy: Default
```

### 4. MCP Tools Returning Cached Data

Some MCP servers cache responses. Check if you're getting live data:

**Test Granola directly:**
```bash
curl -X POST http://localhost:8080/mcp-connect/ms1grwzk/tools/call \
  -H "Authorization: Bearer your-obot-key" \
  -H "Mcp-Session-Id: session-123" \
  -d '{"name": "get_todays_meetings", "arguments": {"date": "2026-03-14"}}'
```

**If returns old data:**
- Check if Granola account is connected
- Verify Granola has recent meeting data
- Check Granola MCP server logs (in Obot)

### 5. Wrong Date Being Passed

**Check skill input:**
The daily-briefing skill should receive today's date, not a hardcoded date.

**Verify in executor logs:**
```bash
kubectl logs -n agentura-system deployment/executor --tail=50 | grep "input_data"
```

**Should see:**
```json
{"date": "2026-03-14"}  # Today's date
```

**If seeing old date:**
- Check who's calling the skill (Slack bot, cron, API)
- Verify input_data is not hardcoded

### 6. Slack MCP Token Permissions

Error: `"Slack posting unavailable due to token permissions"`

**Check Slack bot token scopes:**
1. Go to api.slack.com → Your Apps → OAuth & Permissions
2. Verify these scopes are granted:
   - `chat:write` (required for posting)
   - `channels:read` (for channel lookup)
   - `users:read` (for user mentions)

**Fix:**
- Add missing scopes
- Reinstall app to workspace
- Update `SLACK_BOT_TOKEN` env var with new token
- Restart executor

### 7. Project Configs Not Being Used

**Verify project configs are loaded:**
```bash
kubectl logs -n agentura-system deployment/executor --tail=200 | grep "Project Configurations"
```

**Should see:**
```
System prompt includes: Project Configurations section
```

**If missing:**
- Check `skills/pm/project-configs/` exists
- Verify `_workspace.md`, `gold.md`, `remittance.md`, etc. exist
- Check executor has access to skills directory

## Debugging Workflow

### Step 1: Check MCP Registry

```bash
kubectl exec -n agentura-system deployment/executor -- python3 -c "
from agentura_sdk.mcp.registry import get_registry
reg = get_registry()
print('MCP Servers:')
for s in reg.list_servers():
    print(f'  {s.name}: {s.url} ({len(s.tools)} tools)')
"
```

**Expected output:**
```
MCP Servers:
  granola: http://obot-service.../mcp-connect/ms1grwzk (5 tools)
  clickup: http://obot-service.../mcp-connect/ms1nkz9j (12 tools)
  notion: http://obot-service.../mcp-connect/ms1mvw8d (8 tools)
  slack: http://obot-service.../mcp-connect/ms1g9pdj (6 tools)
```

**If empty or wrong URLs:**
- Fix `OBOT_URL` and `MCP_GATEWAY_API_KEY`
- Or set individual `MCP_{SERVER}_URL` env vars

### Step 2: Test MCP Call Directly

```bash
# Test Granola for today's meetings
kubectl exec -n agentura-system deployment/executor -- python3 -c "
from agentura_sdk.mcp.client import call_tool
result = call_tool(
    'http://obot-service.obot-system.svc.cluster.local:8080/mcp-connect/ms1grwzk',
    'get_todays_meetings',
    {'date': '2026-03-14'}
)
print(result)
"
```

**If fails:**
- Check network connectivity to Obot
- Verify Obot is running: `kubectl get pods -n obot-system`
- Check Obot logs for errors

### Step 3: Test Skill Execution with Logs

```bash
# Watch executor logs in real-time
kubectl logs -n agentura-system deployment/executor -f &

# Trigger skill from Slack
# Send: @pm-bot morning briefing

# Check logs for:
# - "Executing skill: pm/daily-briefing" ✓
# - "MCP bindings: granola, clickup, notion, slack" ✓
# - "Calling MCP tool: granola.get_todays_meetings" ✓
# - "MCP session initialized: Mcp-Session-Id=..." ✓
# - Any errors or "unavailable" messages ✗
```

### Step 4: Verify Skill Gets Correct Input

```bash
# Check what input the skill receives
kubectl logs -n agentura-system deployment/executor --tail=100 | grep -A 5 "pm/daily-briefing"
```

**Should see:**
```json
{
  "date": "2026-03-14",  ← TODAY, not old date
  "project_slug": null   ← or specific project
}
```

**If seeing wrong date:**
- Check Slack bot code (is it hardcoding old examples?)
- Check cron job configuration
- Check API caller

## Quick Fixes Summary

| Issue | Fix Command |
|-------|-------------|
| **MCP env vars missing** | `kubectl set env deployment/executor -n agentura-system OBOT_URL=... MCP_GATEWAY_API_KEY=...` |
| **Obot not reachable** | Check VPN, add `hostNetwork: true` to deployment |
| **Slack token** | Update scopes in Slack app, get new token, update env var |
| **Stale executor** | `kubectl rollout restart -n agentura-system deployment/executor` |
| **Gateway not restarted** | `kubectl rollout restart -n agentura-system deployment/gateway` |
| **Skills not synced** | Push to `agentura-skills` repo main, restart executor |

## After Fixes

1. **Restart executor**: `kubectl rollout restart -n agentura-system deployment/executor`
2. **Restart gateway**: `kubectl rollout restart -n agentura-system deployment/gateway`
3. **Wait for pods**: `kubectl wait --for=condition=ready pod -l app=executor -n agentura-system --timeout=2m`
4. **Test again**: `@pm-bot morning briefing` in Slack
5. **Check output**: Should show TODAY's date and real project data

## Still Not Working?

Check these files match between repos:
- Main repo: `skills/pm/project-configs/` (local dev only)
- Skills repo: `skills/pm/project-configs/` (deployed to EKS)

**Deployed skills come from**: `Vance-Club/agentura-skills` repo, NOT the main `agentura` repo!

To update deployed skills:
```bash
# Clone skills repo
git clone git@github.com:Vance-Club/agentura-skills.git
cd agentura-skills

# Update project configs
vim skills/pm/project-configs/gold.md
git add skills/pm/project-configs/
git commit -m "fix: update project configs with current data"
git push origin main

# Restart executor to sync
kubectl rollout restart -n agentura-system deployment/executor
```
