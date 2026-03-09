# MCP Gateway Architecture

## Overview

Agentura skills connect to external tools (Gmail, Notion, Slack, ClickUp, Granola) through a centralized MCP gateway. The gateway acts as the auth broker — it holds OAuth tokens and API keys so that individual users and agent workers never see credentials directly.

```
Slack / Web UI
     ↓
Agentura Gateway → Executor → PTC or CC Worker
     ↓
MCP tool calls (via MCP_GATEWAY_URL)
     ↓
MCP Gateway — holds stored OAuth tokens
     ↓
Granola / Gmail / Notion / Slack / ClickUp
```

## How Auth Works

1. **Authenticate once in the MCP gateway UI** — connect each tool (Gmail, Notion, etc.) using shared org credentials
2. **Agentura calls the gateway via MCP** — executor resolves `MCP_GATEWAY_URL` env var, passes `MCP_GATEWAY_API_KEY` as Bearer token
3. **Gateway calls the tool** — uses the stored OAuth token on behalf of the caller
4. **No per-user OAuth** — everyone goes through the gateway. Revoke access centrally, audit in one place.

```
Executor env vars:
  MCP_GATEWAY_URL=https://your-mcp-gateway.example.com/mcp
  MCP_GATEWAY_API_KEY=<stored in K8s secret>
```

## Tools to Configure in the MCP gateway

| Tool | Obot Reference | Auth Type | Account |
|------|----------------|-----------|---------|
| Gmail | `github.com/obot-platform/tools/google/gmail` | OAuth (Google) | ai-ops@your-domain.com or service account |
| Google Calendar | `github.com/obot-platform/tools/google/calendar` | OAuth (Google) | Same as Gmail |
| Notion | `github.com/obot-platform/tools/notion` | Integration token | Workspace-level Notion integration |
| Slack | `github.com/obot-platform/tools/slack` | Bot token | Workspace bot (already exists) |
| ClickUp | Custom or `github.com/gptscript-ai/tools/clickup` | API key | Workspace-level API key |
| Granola | Custom MCP (add via URL) | Org API key | Org-level Granola access |

## Meeting Synthesis — Individual User Meetings

Meetings are on individual users' Google Calendars. The pipeline does NOT need calendar access.

### Why Granola Solves This

| What you need | Source | Auth needed |
|---|---|---|
| Meeting notes/transcript | Granola (org API) | One org API key |
| Attendees | Granola metadata | Same key |
| Action items | Extracted by the skill | None |
| Calendar invite details | NOT needed | - |

Granola runs locally on each user's machine, captures notes regardless of whose calendar the meeting is on. One org API key gives access to all users' notes.

### Flow

```
User A has a meeting (their calendar, their machine)
     ↓
Granola captures notes (runs locally)
     ↓
Notes sync to Granola cloud (org account)
     ↓
User A in Slack: "update gold meeting"
     ↓
PM Bot → meeting-update skill → the MCP gateway MCP → Granola API
     ↓
Searches by meeting title/date → finds User A's notes
     ↓
Synthesizes → Notion + Slack + Email + ClickUp
```

### For Auto-Triggering (Without Slack Command)

If you want meetings processed automatically (no user typing a command):

1. **Google Workspace domain-wide delegation** — IT admin sets up once
2. Create a service account in Google Cloud Console
3. In Workspace Admin → Security → API Controls → Domain-wide delegation
4. Add scopes: `calendar.readonly`, `gmail.send`
5. Service account can impersonate any `@your-domain.com` user
6. Pipeline auto-detects "meeting ended" → triggers synthesis

This is the automation layer. Start with the Slack trigger + Granola API.

## Shared Access Pattern (No Personal Accounts)

### Gmail — Without Personal Mail Access

| Approach | How |
|----------|-----|
| Service Account / Shared Inbox | Connect ai-ops@your-domain.com to the MCP gateway once — everyone uses it via MCP |
| Scoped access | Restrict to read-only, specific labels only |

### Notion — Without Individual Access

| Approach | How |
|----------|-----|
| Notion Integration Token | Create one workspace-level integration → connect to the MCP gateway once |
| Page-level permissions | Scope which pages the integration can see |

### Benefits

- No individual OAuth per person
- All calls audited in one place (the MCP gateway logs)
- Credentials never leave the server
- Revoke access centrally — one change, everyone affected
- Scope what each tool can do (read-only, specific workspaces, etc.)

## Agentura Config

### Skill Config (agentura.config.yaml)

```yaml
mcp_tools:
  - server: mcp-gateway
    tools: ["*"]    # All tools from the MCP gateway, or list specific ones
```

### Executor Deployment (executor.yaml)

```yaml
env:
  # MCP gateway URLs loaded via K8s secretRef
  # See deploy/k8s/operator/executor.yaml
```

### Adding the API Key

```bash
kubectl create secret generic agentura-api-keys \
  --from-literal=MCP_GATEWAY_API_KEY=your-gateway-api-key \
  --from-literal=ANTHROPIC_API_KEY=your-anthropic-key \
  ... \
  -n agentura --dry-run=client -o yaml | kubectl apply -f -
```

---

# Bot Naming Convention

## Internal Name (`name` in config.yaml)

| Rule | Example | Anti-pattern |
|------|---------|-------------|
| Domain slug, lowercase | `ecm`, `pm`, `ge` | `ecm-bot`, `Agentura ECM` |
| Short, no prefix | `incubator` | `agentura-incubator-bot` |
| One bot per domain | `pm` handles all PM skills | Separate bot per skill |

## Slack Display Name (set in Slack API dashboard)

| Domain | Internal Name | Slack Display Name | Avatar |
|--------|--------------|-------------------|--------|
| ECM | `ecm` | ECM Ops | TA |
| PM | `pm` | PM Assistant | MU |
| Incubator | `incubator` | Incubator | IN |
| GE | `ge` | GE Partner | GE |

## Current Config

```yaml
slack:
  apps:
    - name: ecm           # internal slug
      domain_scope: "ecm"  # routes to ecm/* skills
      mode: "socket"
    - name: pm
      domain_scope: "pm"
      mode: "http"
    - name: incubator
      domain_scope: "incubator"
      mode: "http"
    - name: ge
      domain_scope: "ge"
      mode: "http"
```

## Rules

1. `name` field is internal — used in logs, metrics, command routing. Keep it as the domain slug.
2. `domain_scope` ties the bot to a skill domain. All skills in that domain are accessible.
3. Slack display name and avatar are set in the Slack API dashboard, not in config.yaml.
4. `commands[].description` is what shows in the `help` response — make these user-friendly.
5. Every domain-scoped bot auto-routes unmatched messages to `{domain}/triage` skill.
