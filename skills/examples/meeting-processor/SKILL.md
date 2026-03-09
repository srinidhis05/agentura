---
name: meeting-processor
role: agent
domain: examples
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.50"
timeout: "120s"
---

# Meeting Processor

## Task

Process meeting notes into structured action items, then create tasks in your project management tool and post a summary to your team channel. This skill demonstrates the **MCP integration pattern** — orchestrating multiple external tools through a single agent.

## Input

You receive:
- `project_slug` — project identifier (e.g., "acme-redesign")
- `meeting_source` — where to find the notes: "latest" (most recent), or a specific meeting ID
- `output_channels` — where to post results: ["tasks", "messaging"] (default: both)

## MCP Tools Available

This skill uses external tools via MCP (Model Context Protocol):

| Server | Tools | Purpose |
|--------|-------|---------|
| `calendar` | `get_meetings`, `get_transcript` | Fetch meeting notes and transcripts |
| `tasks` | `create_task`, `list_tasks`, `update_task` | Create and manage action items |
| `messaging` | `post_message`, `post_thread` | Post summaries to team channels |

## Execution Protocol

### Phase 1: Fetch Meeting Notes

1. Call `calendar.get_meetings` filtered by `project_slug` and `meeting_source`
2. For the target meeting, call `calendar.get_transcript` to get full notes
3. If no meeting found, report error and stop

Context gate: "Found meeting '{title}' from {date} with {participant_count} participants."

### Phase 2: Extract Action Items

Parse the transcript to identify:
1. **Decisions made** — what was agreed upon
2. **Action items** — who does what by when
3. **Open questions** — unresolved topics needing follow-up
4. **Key updates** — status changes or announcements

For each action item, extract:
- `assignee` — who is responsible (from participant list)
- `title` — concise task title
- `description` — context from the discussion
- `due_date` — if mentioned, otherwise null
- `priority` — high/medium/low based on discussion urgency

### Phase 3: Create Tasks

For each action item:
1. Check if a similar task already exists via `tasks.list_tasks`
2. If not, create via `tasks.create_task`
3. Record the created task IDs

### Phase 4: Post Summary

Compose a summary and post via `messaging.post_message`:

```
Meeting: {title} ({date})
Participants: {list}

Decisions:
- {decision_1}
- {decision_2}

Action Items:
- [ ] {task_1} → @{assignee} (due: {date})
- [ ] {task_2} → @{assignee}

Open Questions:
- {question_1}

{task_count} tasks created in {task_tool_name}.
```

### Phase 5: Deliver

Write `TASK_RESULT.json`:

```json
{
  "summary": "Processed 'Sprint Planning' meeting. Created 4 tasks, posted summary to #acme-redesign.",
  "meeting_title": "Sprint Planning",
  "meeting_date": "2025-03-08",
  "decisions_count": 2,
  "action_items_created": 4,
  "open_questions": 1,
  "tasks_created": ["TASK-101", "TASK-102", "TASK-103", "TASK-104"],
  "summary_posted_to": "#acme-redesign"
}
```

## Graceful Degradation

If an MCP server is unavailable:
- **calendar down**: Cannot proceed — report error immediately
- **tasks down**: Extract action items but skip task creation. Note in summary: "Tasks not created — {tool} unavailable."
- **messaging down**: Complete processing but skip summary post. Write results to TASK_RESULT.json only.

## Guardrails

- NEVER fabricate meeting content — only extract from actual transcript.
- NEVER create duplicate tasks — always check existing tasks first.
- If the transcript is empty or too short (<50 words), report "insufficient content" rather than guessing.
- Respect participant names exactly as they appear — do not correct spellings.
- NEVER offer follow-up options — this is a single-shot execution.
