---
name: onboarding-checklist
role: field
domain: hr
trigger: manual
model: anthropic/claude-haiku-4.5
cost_budget_per_execution: "$0.03"
timeout: "15s"
---

# Onboarding Checklist Generator

## Trigger
- "onboarding checklist for {role}"
- "new hire checklist"
- "onboard {employee_name}"
- "what does a new hire need"

## Task

Generate a role-specific onboarding checklist for a new hire. Cover IT setup, HR paperwork, team introductions, training milestones, and 30/60/90 day goals. Adapt based on role type (engineering, sales, ops) and employment type (full-time, contractor, intern).

## Input Format

```json
{
  "employee_name": "Alex Chen",
  "role": "Product Manager",
  "department": "product",
  "employment_type": "full_time",
  "start_date": "2026-03-01",
  "location": "remote",
  "manager": "Sarah Kim",
  "buddy": "James Park"
}
```

## Output Format

```json
{
  "employee": "Alex Chen",
  "role": "Product Manager",
  "start_date": "2026-03-01",
  "phases": [
    {
      "phase": "pre_start",
      "title": "Before Day 1",
      "owner": "HR + IT",
      "tasks": [
        {"task": "Ship laptop and equipment", "owner": "IT", "due": "2026-02-25"},
        {"task": "Send welcome email with first-day agenda", "owner": "HR", "due": "2026-02-27"},
        {"task": "Create accounts (email, Slack, GitHub, Jira)", "owner": "IT", "due": "2026-02-26"}
      ]
    },
    {
      "phase": "week_1",
      "title": "First Week",
      "owner": "Manager + Buddy",
      "tasks": []
    },
    {
      "phase": "day_30",
      "title": "30-Day Milestone",
      "goals": ["Complete all compliance training", "Ship first small contribution"]
    },
    {
      "phase": "day_60",
      "title": "60-Day Milestone",
      "goals": []
    },
    {
      "phase": "day_90",
      "title": "90-Day Milestone",
      "goals": ["Formal performance check-in with manager"]
    }
  ],
  "compliance_items": [
    {"item": "Sign NDA", "deadline": "Day 1", "required": true},
    {"item": "Complete security awareness training", "deadline": "Week 1", "required": true}
  ]
}
```

## Guardrails

1. Always include compliance items (NDA, security training) regardless of role.
2. Remote hires need equipment shipping tasks with lead time before start date.
3. Contractors skip benefits enrollment and stock option tasks.
4. Interns get a simplified checklist — no 90-day goals, focus on learning plan.
5. Every task must have a clear owner (HR, IT, Manager, Buddy) — no orphan tasks.
