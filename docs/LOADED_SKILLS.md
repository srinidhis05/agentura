# Loaded Skills Inventory

**Total**: 50 configured skills across 11 domains
**MCP-Enabled**: 17 skills (34%)

## PM Domain (12 skills) 🔴 Most MCP-heavy

| Skill | MCP Servers | Slack Trigger | Description |
|-------|-------------|---------------|-------------|
| **daily-briefing** ✅ | granola, clickup, notion, slack | `morning briefing`, `daily briefing` | Morning digest: meetings + tasks + updates |
| **action-tracker** ✅ | granola, clickup | - | Extract action items from meetings |
| **meeting-update** ✅ | granola, notion, slack, clickup | `update {project} meeting`, `{project} update` | Process meeting → multi-system updates |
| **notion-sync** ✅ | notion, slack | - | Sync Notion pages to Slack |
| **pm-heartbeat** ✅ | granola, clickup | `daily status`, `pm status`, `check {project}` | Project status overview |
| **daily-wrap** ✅ | granola, clickup, notion, slack | - | EOD summary: what got done |
| **meeting-batch** ✅ | granola, notion | - | Batch process multiple meetings |
| **channel-digest** ✅ | slack, notion | - | Summarize Slack channel activity |
| **pm-query** ✅ | granola, clickup, notion | - | Answer PM questions from data |
| **project-bootstrap** ✅ | notion, clickup, slack | - | Initialize new project |
| **project-setup** | - | `setup {project}` | Create project config |
| **triage** | - | `*` (catch-all) | Route PM requests to specialists |

## ECM Domain (4 skills)

| Skill | MCP Servers | Slack Trigger | Description |
|-------|-------------|---------------|-------------|
| **triage** ✅ | (database via Redshift MCP) | `triage`, `triage last {days} days` | Score and route stuck orders |
| **process-stuck-order** ✅ | (database) | `order {order_id}`, `stuck at {category}` | Diagnose stuck order with runbook |
| **pattern-intelligence** ✅ | (Redshift analytics) | `patterns` | Recurring failure pattern analysis |
| **ecm-daily-flow** ✅ | (Redshift, slack) | `dashboard` | Daily backlog dashboard |

## Dev Domain (3 skills)

| Skill | MCP Servers | Slack Trigger | Description |
|-------|-------------|---------------|-------------|
| **deployer** ✅ | k8s | - | Generate + apply K8s manifests |
| **triage** | - | `*` (catch-all) | Route dev requests |
| **app-builder** | - | - | Code generation |

## Examples Domain (2 skills)

| Skill | MCP Servers | Slack Trigger | Description |
|-------|-------------|---------------|-------------|
| **daily-digest** ✅ | slack, notion | - | Example digest workflow |
| **meeting-processor** ✅ | granola, notion | - | Example meeting workflow |

## Other Domains

### HR Domain (2 skills)
- **triage** - Route HR requests
- **interview-questions** - Generate interview questions

### GE Domain (3 skills)
- **triage** - Route growth eng requests
- **experiment-analyzer** - A/B test analysis
- **funnel-optimizer** - Conversion funnel optimization

### Productivity Domain (2 skills)
- **email-summarizer** - Summarize email threads
- **task-prioritizer** - Prioritize task lists

### Support Domain (2 skills)
- **triage** - Route support requests
- **ticket-classifier** - Classify support tickets

### QA Domain (2 skills)
- **triage** - Route QA requests
- **test-generator** - Generate test cases

### Product Domain (2 skills)
- **triage** - Route product requests
- **feature-analyzer** - Analyze feature requests

### Platform Domain (1 skill)
- **classifier** - Generic intent classifier

### Incubator Domain (1 skill)
- **orchestrate** - Experimental multi-agent orchestration

## MCP Server Usage Matrix

| MCP Server | # Skills | Domains | Example Tools |
|------------|----------|---------|---------------|
| **granola** | 7 | pm, examples | get_todays_meetings, get_meeting_transcript |
| **clickup** | 6 | pm | get_tasks, create_task, update_task |
| **notion** | 9 | pm, examples | search_pages, fetch_page, create_page |
| **slack** | 6 | pm, ecm, examples | post_message, search_messages |
| **k8s** | 1 | dev | kubectl_apply, kubectl_get |
| **redshift** | 3 | ecm | query (analytics) |

## Slack Bot Command Reference

### PM Bot (@pm-bot)

```
@pm-bot morning briefing          → daily-briefing (4 MCPs)
@pm-bot daily briefing            → daily-briefing
@pm-bot update agentura meeting   → meeting-update (4 MCPs)
@pm-bot agentura update           → meeting-update
@pm-bot setup project-name        → project-setup
@pm-bot daily status              → pm-heartbeat (2 MCPs)
@pm-bot pm status                 → pm-heartbeat
@pm-bot check agentura            → pm-heartbeat
<any unmatched message>           → triage (routes to specialist)
```

### ECM Bot (@ecm-bot)

```
@ecm-bot triage                   → triage (database MCP)
@ecm-bot triage last 7 days       → triage
@ecm-bot order ORD-12345          → process-stuck-order (database)
@ecm-bot stuck at kyc-verification → process-stuck-order
@ecm-bot list kyc-verification    → process-stuck-order
@ecm-bot dashboard                → ecm-daily-flow (Redshift + Slack)
@ecm-bot patterns                 → pattern-intelligence (Redshift)
<any unmatched message>           → triage (routes to specialist)
```

## Status

✅ **All 50 skills loaded** in `skills/` directory
✅ **17 MCP-enabled skills** ready to test
✅ **Slack bots configured** for pm, ecm, incubator, ge domains
✅ **New Slack interaction primitives** (modals, buttons, select menus) implemented
✅ **Test infrastructure** complete (unit tests, integration tests, examples)

## Testing Priority

**Recommended test order:**

1. **pm/daily-briefing** - Uses all 4 MCP servers (Granola, ClickUp, Notion, Slack)
   ```
   @pm-bot morning briefing
   ```

2. **pm/meeting-update** - Complex multi-system workflow
   ```
   @pm-bot update agentura meeting
   ```

3. **ecm/triage** - Database MCP via Redshift
   ```
   @ecm-bot triage
   ```

4. **pm/project-setup** - Modal interaction example
   ```
   @pm-bot setup new-project
   ```

## References

- **MCP Testing Guide**: `docs/testing-mcp-skills.md`
- **Testing with Slack**: `docs/testing-mcp-via-slack.md`
- **Slack Interactions**: `docs/slack-interactions.md`
- **MCP Modes (Vigil/Individual)**: `docs/testing-mcp-modes.md`
