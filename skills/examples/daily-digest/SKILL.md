---
name: daily-digest
role: agent
domain: examples
trigger: cron
cron: "0 9 * * 1-5"
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.30"
timeout: "60s"
---

# Daily Digest

## Task

Generate a daily status digest by aggregating data from multiple sources (tasks, calendar, messaging), then post a formatted summary to the team channel. This skill demonstrates the **cron trigger pattern** — scheduled automation with multi-source aggregation and graceful degradation.

## Input

You receive:
- `team_channel` — channel to post the digest (default: "#general")
- `lookback_hours` — how far back to check (default: 24)
- `project_filter` — (optional) limit to specific project slugs

## MCP Tools Available

| Server | Tools | Purpose |
|--------|-------|---------|
| `tasks` | `list_tasks`, `get_task_stats` | Fetch overdue/due-today tasks |
| `calendar` | `get_meetings` | Today's meetings with participants |
| `messaging` | `post_message` | Post the digest |

## Execution Protocol

### Phase 1: Gather Data

Query each source in sequence:

1. **Tasks**: Call `tasks.list_tasks` with filters:
   - `status: overdue` — tasks past their due date
   - `due_date: today` — tasks due today
   - `completed_since: {lookback_hours}h ago` — recently completed

2. **Calendar**: Call `calendar.get_meetings` for today:
   - Upcoming meetings with times and participants
   - Meetings from yesterday that may have generated action items

3. If `project_filter` is set, filter all results to matching projects.

Context gate: "Gathered {task_count} tasks, {meeting_count} meetings."

### Phase 2: Compile Digest

Organize data into sections:

```markdown
Good morning! Here's your daily digest for {date}.

**Overdue** ({count})
- [ ] {task_title} — @{assignee} (due {due_date})

**Due Today** ({count})
- [ ] {task_title} — @{assignee}

**Completed Yesterday** ({count})
- [x] {task_title} — @{assignee}

**Today's Meetings** ({count})
- {time} — {title} ({participants})

**Summary**
{overdue_count} overdue, {due_today_count} due today, {completed_count} completed yesterday.
```

### Phase 3: Post

Call `messaging.post_message` with the formatted digest to `team_channel`.

### Phase 4: Deliver

Write `TASK_RESULT.json`:

```json
{
  "summary": "Daily digest posted to #general. 2 overdue, 5 due today, 3 completed.",
  "overdue_count": 2,
  "due_today_count": 5,
  "completed_count": 3,
  "meetings_today": 4,
  "posted_to": "#general"
}
```

## Graceful Degradation

- **tasks down**: Skip task sections. Post digest with only calendar data and note: "Task data unavailable."
- **calendar down**: Skip meeting section. Post digest with only task data.
- **messaging down**: Write digest to TASK_RESULT.json only. Log warning.
- **All sources down**: Write error to TASK_RESULT.json. Do not post empty digest.

## Guardrails

- NEVER fabricate task or meeting data — only report what the APIs return.
- If all data sources return empty results, post a brief "all clear" message rather than skipping entirely.
- Keep the digest concise — max 20 items per section. Add "(and N more)" for overflow.
- NEVER offer follow-up options — this is a single-shot execution.
