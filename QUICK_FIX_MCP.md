# Quick Fix: MCP Stale Data Issue

## Problem
Your daily-briefing skill is returning:
- ❌ Old date (January 2025 instead of March 2026)
- ❌ "Slack posting unavailable due to token permissions"
- ❌ Generic/random project data

## Root Cause
MCP servers (Granola, ClickUp, Notion, Slack) are not connected or returning cached data.

## Fix (Run in Your Terminal)

### Option 1: Automated Script

```bash
cd /Users/apple/code/experimentation/agentura
./fix-mcp-connections.sh
```

This will:
1. Check current MCP configuration
2. Prompt you for Obot URL and API key
3. Set environment variables
4. Restart executor and gateway
5. Verify MCP servers are connected

### Option 2: Manual Commands

**1. Check current state:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system get pods
```

**2. Check if MCP env vars are set:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system get deployment executor -o yaml | grep -A 3 "OBOT_URL\|MCP_GATEWAY"
```

**3. Set MCP environment variables:**

You need these values:
- **OBOT_URL**: Your Obot service URL (e.g., `http://obot-service.obot-system.svc.cluster.local:8080` for in-cluster, or your external Obot URL)
- **MCP_GATEWAY_API_KEY**: Your Obot API key (get from Obot UI → Settings → API Keys)
- **ANTHROPIC_API_KEY**: Your Anthropic API key (for Claude)

```bash
# Replace with your actual values!
assume infrastructure -- kubectl --context infrastructure -n agentura-system set env deployment/executor \
  OBOT_URL="http://obot-service.obot-system.svc.cluster.local:8080" \
  MCP_GATEWAY_API_KEY="your-obot-api-key-here" \
  ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

**4. Restart services:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system rollout restart deployment/executor
assume infrastructure -- kubectl --context infrastructure -n agentura-system rollout restart deployment/gateway
```

**5. Wait for pods to be ready:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system wait --for=condition=ready pod -l app=executor --timeout=2m
assume infrastructure -- kubectl --context infrastructure -n agentura-system wait --for=condition=ready pod -l app=gateway --timeout=2m
```

**6. Verify MCP servers are loaded:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system exec deployment/executor -- python3 -c "
from agentura_sdk.mcp.registry import get_registry
reg = get_registry()
for s in reg.list_servers():
    print(f'{s.name}: {s.url} ({len(s.tools)} tools)')
"
```

Expected output:
```
granola: http://obot.../mcp-connect/ms1grwzk (5 tools)
clickup: http://obot.../mcp-connect/ms1nkz9j (12 tools)
notion: http://obot.../mcp-connect/ms1mvw8d (8 tools)
slack: http://obot.../mcp-connect/ms1g9pdj (6 tools)
```

## Test the Fix

**1. Send test message in Slack:**
```
@pm-bot morning briefing
```

**2. Expected output should have:**
- ✅ Current date: **March 14, 2026** (not January 2025)
- ✅ Real meetings from Granola (if any today)
- ✅ Real tasks from ClickUp
- ✅ `"systems_checked": ["granola", "clickup", "notion", "slack"]`
- ✅ `"posted_to_slack": true`

**3. If still showing old data, check executor logs:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system logs deployment/executor --tail=100 -f
```

Look for:
- `"Executing skill: pm/daily-briefing"` ✓
- `"MCP bindings: granola, clickup, notion, slack"` ✓
- `"Calling MCP tool: granola.get_todays_meetings"` ✓
- `"MCP session initialized: Mcp-Session-Id=..."` ✓ (for Obot)

## Additional Fixes

### If Slack MCP Still Failing

**Check Slack bot token scopes:**
1. Go to https://api.slack.com/apps
2. Select your Slack app
3. Go to "OAuth & Permissions"
4. Verify these scopes are granted:
   - `chat:write` ← Required!
   - `channels:read`
   - `users:read`
5. If missing, add them and reinstall app to workspace
6. Get the new Bot User OAuth Token
7. Update env var:
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system set env deployment/executor \
  SLACK_BOT_TOKEN="xoxb-your-new-token"
```

### If Using Vigil Instead of Obot

Set `OBOT_URL` to your Vigil instance:
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system set env deployment/executor \
  OBOT_URL="https://vigil.internal.genorim.xyz"
```

### If Using Individual MCP Servers (No Gateway)

Instead of `OBOT_URL`, set individual URLs:
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system set env deployment/executor \
  MCP_GRANOLA_URL="https://your-granola-mcp.com" \
  MCP_CLICKUP_URL="https://your-clickup-mcp.com" \
  MCP_NOTION_URL="https://your-notion-mcp.com" \
  MCP_SLACK_URL="https://your-slack-mcp.com"
```

## Where to Get the Values

### OBOT_URL
- **In-cluster Obot**: `http://obot-service.obot-system.svc.cluster.local:8080`
- **External Obot**: Ask your team for the URL
- **Check if Obot is running**: `assume infrastructure -- kubectl --context infrastructure -n obot-system get svc`

### MCP_GATEWAY_API_KEY
1. Open Obot UI (port-forward if needed)
2. Go to Settings → API Keys
3. Create new API key with MCP server access
4. Make sure the key has access to: Granola, ClickUp, Notion, Slack

### ANTHROPIC_API_KEY
- Get from https://console.anthropic.com/settings/keys
- Or check your `.env` file: `cat .env | grep ANTHROPIC_API_KEY`

## Troubleshooting

**Still getting old data?**
- The MCP servers themselves might be returning cached data
- Check Granola/ClickUp/Notion directly to verify they have current data
- Verify your accounts are connected in Obot

**"No MCP servers found"?**
- Check `OBOT_URL` is correct and Obot is reachable from executor pod
- Verify `MCP_GATEWAY_API_KEY` is valid
- Check Obot logs: `assume infrastructure -- kubectl --context infrastructure -n obot-system logs deployment/obot`

**Pod won't start after env var changes?**
- Check pod events: `assume infrastructure -- kubectl --context infrastructure -n agentura-system describe pod -l app=executor`
- Check logs: `assume infrastructure -- kubectl --context infrastructure -n agentura-system logs -l app=executor --tail=50`

## Success Criteria

After the fix, you should see:
- ✅ Executor pod has `OBOT_URL` and `MCP_GATEWAY_API_KEY` env vars
- ✅ MCP registry shows 4+ servers (granola, clickup, notion, slack)
- ✅ Slack bot responds with CURRENT date and REAL data
- ✅ No "systems_unavailable" or "token permissions" errors

---

**Need help?** Check full troubleshooting guide: `docs/TROUBLESHOOTING_MCP_STALE_DATA.md`
