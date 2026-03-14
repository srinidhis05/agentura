# Slack Workflow Patterns - Best Practices

## Overview

Agentura supports two complementary primitives for Slack workflows:

| Primitive | Use Case | Entry Point | Output |
|-----------|----------|-------------|--------|
| **Router** | Quick queries, exploration | Message text | Skill execution |
| **Interactions** | Structured workflows, approvals | UI elements | Skill execution |

Both route to the same skills - the difference is how users trigger them.

---

## When to Use What

### Use Router (Message-based) for:

✅ **Quick status checks**
```
@bot daily status
@bot check gold project
@bot what happened yesterday?
```

✅ **Exploratory queries**
```
@bot show me all blocked tasks
@bot who's working on remittance?
@bot search "API integration"
```

✅ **AI-powered triage**
```
@bot help
@bot [ambiguous question that needs interpretation]
```

✅ **Notifications** (bot posting updates)
```
Daily digest at 9am
Weekly summary on Monday
Alert when task blocked
```

### Use Interactions (UI-based) for:

✅ **Structured data collection**
```
[Create Project] button → Modal with required fields
```

✅ **Multi-step workflows**
```
Submit expense → Review → Approve → Reimburse
```

✅ **Approval flows**
```
Deploy to prod? [Approve] [Reject]
```

✅ **Contextual actions**
```
Right-click message → "Create task from this"
```

✅ **Discoverability**
```
⚡ Shortcuts menu shows available actions
```

---

## Production Patterns

### Pattern 1: Pure Router (Simplest)

**Use when:** Workflows are simple queries with no required fields

**Config:**
```yaml
commands:
  - pattern: "daily status"
    skill: "pm-heartbeat"
  - pattern: "weekly digest"
    skill: "pm/weekly-digest"
  - pattern: "check {project}"
    skill: "pm/project-status"
    extract: {"project_slug": "{project}"}
```

**Pros:**
- Fastest to implement
- Lowest friction (just type)
- Natural for exploratory use

**Cons:**
- No input validation
- Ambiguous input (did user mean "gold" or "Gold Project"?)
- Hard to discover available commands

---

### Pattern 2: Pure Interactions (Most Structured)

**Use when:** Workflows require validated input, multi-step approval, or complex forms

**Config:**
```yaml
interaction_handlers:
  - callback_id: "create_project_modal"
    type: "view_submission"
    skill: "pm/project-setup"

  - callback_id: "approve_deployment"
    type: "block_actions"
    skill: "devops/deploy-approval"

  - callback_id: "assign_task"
    type: "select_action"
    skill: "pm/task-assignment"
```

**Pros:**
- Validated input (required fields, dropdowns)
- Discoverable (shortcuts menu)
- Visual (buttons, forms)
- Multi-step (modals → buttons → confirmation)

**Cons:**
- More clicks (open modal → fill form → submit)
- Requires Slack app configuration
- Less flexible than natural language

---

### Pattern 3: Hybrid (Recommended)

**Use when:** You want the best of both worlds

**How it works:**
1. User starts with **natural language** (Router)
2. Bot opens a **modal** if structured input needed (Interaction)
3. User submits form → Skill gets clean data

**Example: Task Creation**

**Step 1 - Router Config:**
```yaml
commands:
  - pattern: "create task"
    skill: "pm/task-initiator"
```

**Step 2 - Interaction Config:**
```yaml
interaction_handlers:
  - callback_id: "task_creation_form"
    type: "view_submission"
    skill: "pm/task-creator"
```

**Step 3 - Skill Logic** (`pm/task-initiator`):
```python
# User typed: "@bot create task"
# Open a modal instead of executing directly

def execute(context):
    # Return modal response
    return {
        "response_type": "modal",
        "trigger_id": context.trigger_id,
        "view": {
            "type": "modal",
            "callback_id": "task_creation_form",
            "title": {"type": "plain_text", "text": "Create Task"},
            "submit": {"type": "plain_text", "text": "Create"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title",
                    "label": {"type": "plain_text", "text": "Title"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_value"
                    }
                },
                {
                    "type": "input",
                    "block_id": "project",
                    "label": {"type": "plain_text", "text": "Project"},
                    "element": {
                        "type": "static_select",
                        "action_id": "project_value",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Gold"}, "value": "gold"},
                            {"text": {"type": "plain_text", "text": "Remittance"}, "value": "remittance"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "assignee",
                    "label": {"type": "plain_text", "text": "Assignee"},
                    "element": {
                        "type": "users_select",
                        "action_id": "assignee_value"
                    }
                }
            ]
        }
    }
```

**Step 4 - Actual Task Creator** (`pm/task-creator`):
```python
# Receives validated form data
def execute(context):
    title = context.form_data["title"]["title_value"]
    project = context.form_data["project"]["project_value"]
    assignee = context.form_data["assignee"]["assignee_value"]

    # Create task in ClickUp
    task = clickup.create_task(
        title=title,
        project=project,
        assignee=assignee
    )

    return f"✅ Task created: {task.url}"
```

**User Experience:**
```
User: @pm-bot create task
      ↓ (Router matches pattern)
      ↓
Bot: [Opens modal with form]
      ↓
User: Fills Title, Project (dropdown), Assignee (user picker)
      ↓
User: Clicks "Create"
      ↓ (Interaction handler receives form data)
      ↓
Bot: ✅ Task created: https://clickup.com/task/123
```

**Why this is best:**
- ✅ Low friction entry (just type "create task")
- ✅ Structured data collection (form validation)
- ✅ No ambiguity (dropdowns, user pickers)
- ✅ Discoverable (also add as shortcut for power users)

---

## Real-World Examples

### Example 1: PagerDuty Incident Response

**Router (Queries):**
```
@pagerduty who's on call?
@pagerduty show recent incidents
@pagerduty escalate incident #123
```

**Interactions (Actions):**
```
[Incident Alert Posted]
  [Acknowledge] [Escalate] [Resolve]
     ↓
  Click Acknowledge → Status updated
```

**Why both?**
- Quick queries don't need buttons
- Critical actions need one-click (no typing during incident)

---

### Example 2: Asana Task Management

**Router (Searches):**
```
@asana what's due today?
@asana tasks assigned to me
@asana search "API refactor"
```

**Interactions (Creation):**
```
Right-click Slack message → "Create Asana task"
    ↓
Modal opens with:
  - Task name (pre-filled from message)
  - Project (dropdown)
  - Assignee (user picker)
  - Due date (date picker)
    ↓
Submit → Task created with validated data
```

**Why both?**
- Queries need flexibility (natural language search)
- Task creation needs structure (required fields, no typos)

---

### Example 3: Agentura PM Workflows

**Router (Status & Queries):**
```yaml
commands:
  - pattern: "daily status"
    skill: "pm-heartbeat"
  - pattern: "check {project}"
    skill: "pm/project-status"
  - pattern: "what happened yesterday?"
    skill: "pm/triage"
```

**Interactions (Structured Actions):**
```yaml
interaction_handlers:
  # Contextual: Right-click message → Create task
  - callback_id: "message_to_task"
    type: "message_action"
    skill: "pm/task-from-message"

  # Global: ⚡ menu → Quick project status
  - callback_id: "quick_status"
    type: "shortcut"
    skill: "pm/project-status"

  # Form: Modal for new project setup
  - callback_id: "setup_project_form"
    type: "view_submission"
    skill: "pm/project-setup"
```

**Hybrid: Create Task Flow**
```yaml
# Step 1: User types command
commands:
  - pattern: "create task"
    skill: "pm/task-form-opener"  # Opens modal

# Step 2: User submits modal
interaction_handlers:
  - callback_id: "task_form"
    type: "view_submission"
    skill: "pm/task-creator"  # Creates task with validated data
```

---

## Migration Strategy

If you already have Router-based commands, here's how to add Interactions strategically:

### Step 1: Identify High-Value Workflows

Look for commands that:
- Require multiple parameters
- Have validation needs (dates, dropdowns)
- Are used frequently
- Cause errors due to ambiguous input

Example:
```
❌ @bot create task fix login bug for gold assign to alice due friday
   ↑ Error-prone: parsing "friday", who's "alice", is it "Gold" or "gold"?

✅ @bot create task
   → Modal with dropdowns, user picker, date picker
   → No parsing errors, no ambiguity
```

### Step 2: Add Hybrid Pattern

Don't remove Router commands - add Interactions alongside:

**Before:**
```yaml
commands:
  - pattern: "create task {title}"
    skill: "pm/task-creator"
```

**After (Hybrid):**
```yaml
commands:
  - pattern: "create task"
    skill: "pm/task-form-opener"  # Opens modal

interaction_handlers:
  - callback_id: "task_form"
    type: "view_submission"
    skill: "pm/task-creator"
```

### Step 3: Add Shortcuts for Discoverability

Power users don't want to type commands - add shortcuts:

```yaml
interaction_handlers:
  - callback_id: "quick_create_task"
    type: "shortcut"
    skill: "pm/task-form-opener"
```

Now users can:
- Type: `@bot create task` (Router)
- Click: ⚡ → "Create Task" (Shortcut)
- Right-click message: "Create task from this" (Message Action)

All three route to the same modal → same task creator skill.

---

## Decision Matrix

| Workflow | Router | Interactions | Hybrid |
|----------|--------|--------------|--------|
| **Quick status check** | ✅ Best | ❌ Overkill | ❌ Overkill |
| **Search/query** | ✅ Best | ❌ Wrong tool | ❌ Overkill |
| **Create with required fields** | ⚠️ Error-prone | ✅ Best | ✅ Best |
| **Multi-step approval** | ❌ Can't do | ✅ Best | ✅ Best |
| **Contextual action** | ❌ Can't do | ✅ Best | ❌ Overkill |
| **Exploratory triage** | ✅ Best | ❌ Wrong tool | ❌ Overkill |

---

## Recommendation for Agentura

**Keep both, use strategically:**

1. **Router (80% of interactions):**
   - All queries: status, search, "what happened?"
   - Quick commands: "daily digest", "check gold"
   - Triage: ambiguous questions

2. **Interactions (20% of interactions):**
   - Structured creation: New project, new task (with form)
   - Approvals: Deploy button, expense approval
   - Contextual: Right-click message → actions
   - Shortcuts: Power user quick actions

3. **Hybrid (for complex workflows):**
   - Start: `@bot create task` (Router)
   - Escalate: Modal with form (Interaction)
   - Execute: Task creator skill (validated data)

**Don't overthink it:**
- Start with Router (fastest to implement)
- Add Interactions when you notice:
  - Validation errors
  - Ambiguous inputs
  - Users asking "how do I...?" (discoverability problem)
  - Multi-step workflows

---

## Summary

**Router = Speed, Flexibility, Natural Language**
**Interactions = Structure, Validation, Discoverability**
**Hybrid = Best of Both**

Use Router for everything until you hit a pain point, then add Interactions strategically.

Most production Slack apps use 80% Router, 20% Interactions. The 20% handles the workflows that matter most (approvals, creation, critical actions).
