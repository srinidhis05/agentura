---
name: morning-briefing
role: field
domain: productivity
trigger: manual
model: anthropic/claude-haiku-4.5
cost_budget_per_execution: "$0.05"
timeout: "30s"
---

# Morning Briefing

## Trigger
- "morning briefing"
- "daily briefing"
- "what's happening today"
- "catch me up"
- "daily summary"

## Task

Generate a structured morning briefing that aggregates calendar events, pending tasks, key metrics, and relevant updates into a scannable daily report. Personalize based on the user's role and focus areas.

## Input Format

```json
{
  "date": "2026-02-24",
  "user_role": "string (e.g., engineering-manager, product-lead)",
  "focus_areas": ["team-updates", "metrics", "blockers"],
  "calendar_events": [
    {
      "time": "09:00",
      "title": "Sprint Planning",
      "attendees": 8
    }
  ],
  "pending_tasks": [
    {
      "title": "Review Q1 roadmap",
      "priority": "high",
      "due": "2026-02-25"
    }
  ],
  "metrics_snapshot": {
    "open_prs": 12,
    "failing_builds": 2,
    "sprint_velocity": "82%"
  }
}
```

## Output Format

```json
{
  "greeting": "Good morning! Here's your briefing for Monday, Feb 24.",
  "priority_actions": [
    "Review Q1 roadmap (due tomorrow)",
    "2 failing builds need attention"
  ],
  "calendar_summary": "3 meetings today. First: Sprint Planning at 9:00 AM (8 attendees).",
  "metrics_highlights": [
    {
      "metric": "Sprint Velocity",
      "value": "82%",
      "trend": "up",
      "note": "Improved from 76% last sprint"
    }
  ],
  "blockers": ["2 failing CI builds in payments-service"],
  "suggested_focus": "Clear the failing builds before Sprint Planning at 9 AM."
}
```

## Guardrails

1. Keep the briefing under 300 words — busy mornings need concise updates.
2. Priority actions always come first — surface what needs attention NOW.
3. If no calendar events are provided, skip that section (don't fabricate).
4. Metrics should show trend direction (up/down/stable) when historical data is available.
5. End with one concrete suggested focus for the day.
