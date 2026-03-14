# MCP Connection Issue - FOUND & HOW TO FIX

## Status: ✅ DIAGNOSED

### What's Working
- ✅ MCP environment variables are set correctly
- ✅ Vigil URL: `https://vigil.internal.genorim.xyz`
- ✅ Network connectivity to Vigil works
- ✅ MCP server URLs configured (Granola, ClickUp, Notion, Slack, Gmail)
- ✅ ANTHROPIC_API_KEY is set

### The Problem
**Vigil API returns `403 Forbidden`**

When executor tries to call:
```
GET https://vigil.internal.genorim.xyz/api/mcp-servers
Authorization: Bearer ok1-4-11-CrQddk4CkVmaSKi1dwnqPFPoyfxJYEdxGIprthIBaGE
```

Response: `403 forbidden`

## Root Cause

The API key in `agentura-mcp-config` secret doesn't have permission to:
1. Access the `/api/mcp-servers` endpoint in Vigil
2. Or the key is invalid/expired

## Impact

Without successful `discover_from_obot()`:
- MCP registry only knows server NAMES from skill configs
- Doesn't load actual TOOL DEFINITIONS from Vigil
- Skills can't call MCP tools (no tool schemas)
- Falls back to returning cached/example data

## Fix Options

### Option 1: Update API Key Permissions in Vigil (Recommended)

1. **Log into Vigil**: https://vigil.internal.genorim.xyz
2. **Go to API Keys** (Settings → API Keys)
3. **Find key**: `ok1-4-11-CrQddk4CkVmaSKi1dwnqPFPoyfxJYEdxGIprthIBaGE`
4. **Update permissions**:
   - Enable: "MCP Server Discovery" or "Read MCP Servers"
   - Enable access to specific servers: Granola, ClickUp, Notion, Slack, Gmail
5. **Save changes**

6. **Restart executor** (to re-discover with new permissions):
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system rollout restart deployment/executor
```

### Option 2: Create New API Key with Correct Permissions

1. **In Vigil**: Create new API key with:
   - Name: "Agentura Executor MCP Access"
   - Permissions: "MCP Server Discovery" + access to all needed servers
   - Copy the new key

2. **Update Kubernetes secret**:
```bash
# Get the new key from Vigil first
NEW_API_KEY="your-new-key-here"

assume infrastructure && kubectl --context infrastructure -n agentura-system create secret generic agentura-mcp-config-new \
  --from-literal=OBOT_URL="https://vigil.internal.genorim.xyz" \
  --from-literal=MCP_GATEWAY_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_GRANOLA_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_GRANOLA_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms1grwzk" \
  --from-literal=MCP_CLICKUP_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_CLICKUP_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms1g9pdj" \
  --from-literal=MCP_NOTION_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_NOTION_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms175vh7" \
  --from-literal=MCP_SLACK_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_SLACK_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms18xbgr" \
  --from-literal=MCP_GMAIL_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_GMAIL_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms1vxw8d" \
  --dry-run=client -o yaml | assume infrastructure && kubectl --context infrastructure -n agentura-system apply -f -

# Delete old secret and rename new one
assume infrastructure && kubectl --context infrastructure -n agentura-system delete secret agentura-mcp-config
assume infrastructure && kubectl --context infrastructure -n agentura-system create secret generic agentura-mcp-config \
  --from-literal=OBOT_URL="https://vigil.internal.genorim.xyz" \
  --from-literal=MCP_GATEWAY_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_GRANOLA_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_GRANOLA_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms1grwzk" \
  --from-literal=MCP_CLICKUP_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_CLICKUP_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms1g9pdj" \
  --from-literal=MCP_NOTION_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_NOTION_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms175vh7" \
  --from-literal=MCP_SLACK_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_SLACK_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms18xbgr" \
  --from-literal=MCP_GMAIL_API_KEY="$NEW_API_KEY" \
  --from-literal=MCP_GMAIL_URL="https://vigil.internal.genorim.xyz/mcp-connect/ms1mvw8d"

# Restart executor
assume infrastructure && kubectl --context infrastructure -n agentura-system rollout restart deployment/executor
```

## Verification After Fix

**1. Test Vigil API access:**
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system exec deployment/executor -- python3 -c "
import os, httpx
url = os.getenv('OBOT_URL')
key = os.getenv('MCP_GATEWAY_API_KEY')
resp = httpx.get(f'{url}/api/mcp-servers', headers={'Authorization': f'Bearer {key}'}, timeout=10)
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    print(f'SUCCESS: {len(resp.json().get(\"items\", []))} servers found')
else:
    print(f'FAILED: {resp.text[:100]}')
"
```

**Expected**: `Status: 200`, `SUCCESS: 5+ servers found`

**2. Verify MCP registry discovery:**
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system exec deployment/executor -- python3 -c "
from agentura_sdk.mcp.registry import get_registry
reg = get_registry()
for s in reg.list_servers():
    print(f'{s.name}: {s.url} ({len(s.tools)} tools)')
"
```

**Expected**: Each server should show **multiple tools** (not just 1):
```
granola: https://vigil.../mcp-connect/ms1grwzk (5+ tools)
clickup: https://vigil.../mcp-connect/ms1g9pdj (12+ tools)
notion: https://vigil.../mcp-connect/ms175vh7 (8+ tools)
slack: https://vigil.../mcp-connect/ms18xbgr (6+ tools)
```

**3. Test daily-briefing skill:**
```
Send in Slack: @pm-bot morning briefing
```

**Expected output**:
- ✅ Date: **March 14, 2026** (today, not January 2025)
- ✅ Real meetings from Granola (if any scheduled)
- ✅ Real tasks from ClickUp
- ✅ `"systems_checked": ["granola", "clickup", "notion", "slack"]`
- ✅ `"posted_to_slack": true` (no permission errors)

## Current State (Before Fix)

```yaml
Status: READY TO FIX
Issue: Vigil API key lacks permissions
Impact: MCPs not loading tool definitions
Symptoms:
  - Old date in output (Jan 2025)
  - Generic/cached data
  - "Slack posting unavailable"

Configuration: ✅ CORRECT
  - Vigil URL: Set
  - MCP URLs: Set
  - API keys: Set (but 403)
  - Network: Working

Next Step: Update API key permissions in Vigil UI
```

## Who Can Fix This

**Permission needed**: Access to Vigil admin/settings to manage API keys

**Contact**: Ask your team who manages Vigil (likely infrastructure/platform team)

**Ask them to**:
1. Log into https://vigil.internal.genorim.xyz
2. Find API key ending in `...IBaGE`
3. Grant "MCP Server Discovery" permission
4. Grant access to: Granola, ClickUp, Notion, Slack, Gmail

**Then you run**:
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system rollout restart deployment/executor
```

---

**Summary**: The fix is simple - just need the Vigil API key to have the right permissions! Everything else is configured correctly.
