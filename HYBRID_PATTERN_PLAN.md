# Hybrid Pattern Implementation Plan - Asana-Style Slack Workflows

## Vision

Transform Agentura's Slack interface from **chat-only** to **chat + structured workflows**, mimicking Asana's approach:

**Current (Chat-only):**
```
User: @pm-bot setup gold
Bot: ❌ Error: Missing required fields (team, start_date, description)
```

**Future (Hybrid):**
```
User: @pm-bot setup gold
      ↓
Bot: [Opens modal with form]
  - Project Name: gold (pre-filled)
  - Team: [Dropdown: Engineering, Product, Design]
  - Start Date: [Date picker]
  - Slack Channel: [Channel picker]
  - ClickUp Space: [Dropdown]
      ↓
User: Fills form, clicks "Create"
      ↓
Bot: ✅ Project "Gold" created
     - Notion page: [link]
     - ClickUp space: [link]
     - Slack channel: #gold
```

---

## Phase 1: Identify High-Value Workflows

### Workflows to Convert (Priority Order)

| Command | Current (Router) | Pain Point | Hybrid Benefit |
|---------|------------------|------------|----------------|
| 1. **setup {project}** | `@bot setup gold` | Needs 5+ params, error-prone | Form with validated inputs |
| 2. **Create task** (NEW) | Doesn't exist | Manual ClickUp entry | Quick capture from Slack |
| 3. **Add meeting notes** (NEW) | Upload file manually | Fragmented process | Structured template |
| 4. **update {project} meeting** | `@bot update gold meeting` | Ambiguous input | Form for action items |
| 5. **Weekly planning** (NEW) | N/A | No structure | Template for OKRs |

### Workflows to Keep Router-Only

| Command | Why Router is Better |
|---------|---------------------|
| `daily status` | Pure query, no input needed |
| `check {project}` | Quick lookup, no validation |
| `pm status` | Read-only dashboard |
| `what happened yesterday?` | Exploratory, needs AI triage |

---

## Phase 2: Implementation - Priority #1: "Create Task"

### Why This First?

✅ **Most requested workflow** (Asana does this best)
✅ **Clear value prop** (create tasks without leaving Slack)
✅ **Simple to implement** (single modal, single skill)
✅ **High usage** (daily action for PM teams)

---

### Before: Manual Process

```
User opens ClickUp → New Task → Fill fields → Save
(Context switch, loses Slack context)
```

### After: Hybrid Flow

```
Method 1 (Command):
  @pm-bot create task
      ↓
  Modal opens

Method 2 (Shortcut):
  ⚡ menu → "Create Task"
      ↓
  Modal opens

Method 3 (Contextual):
  Right-click message → "Create task from this"
      ↓
  Modal opens (pre-filled with message content)
```

---

### Implementation Steps

#### Step 1: Create Modal Opener Skill

**File:** `skills/pm/task-form-opener/SKILL.md`

```markdown
# Skill: Task Form Opener

Opens a modal for structured task creation.

## Role
Helper skill that displays a form. Does not create the task itself.

## Input
```json
{
  "pre_fill": {
    "title": "Optional: pre-filled title",
    "description": "Optional: pre-filled description",
    "project": "Optional: project slug"
  }
}
```

## Output
Opens a Slack modal (no text response).

## Tools
None (returns modal JSON).

## Instructions

1. Build a modal with these fields:
   - **Title** (required, plain_text_input)
   - **Description** (optional, multiline)
   - **Project** (required, static_select from project-configs)
   - **Assignee** (required, users_select)
   - **Priority** (optional, static_select: High/Medium/Low)
   - **Due Date** (optional, datepicker)

2. Pre-fill fields if provided in input

3. Set callback_id: "task_creation_form"

4. Return modal JSON
```

**File:** `skills/pm/task-form-opener/agentura.config.yaml`

```yaml
name: task-form-opener
domain: pm
description: Opens task creation modal
version: 1.0.0

executor: ptc

tools: []

input_schema:
  type: object
  properties:
    pre_fill:
      type: object
      properties:
        title:
          type: string
        description:
          type: string
        project:
          type: string
```

---

#### Step 2: Create Task Creator Skill

**File:** `skills/pm/task-creator/SKILL.md`

```markdown
# Skill: Task Creator

Creates a task in ClickUp from validated modal form data.

## Role
Receives form submission, creates task, posts confirmation.

## Input (from modal submission)
```json
{
  "form_data": {
    "title": {"value": "Fix login bug"},
    "description": {"value": "Users can't log in with Google"},
    "project": {"value": "gold"},
    "assignee": {"value": "U123ABC"},
    "priority": {"value": "high"},
    "due_date": {"value": "2026-03-20"}
  },
  "user": {
    "id": "U123",
    "name": "alice"
  },
  "channel": "C123"
}
```

## Output
```
✅ Task created: Fix login bug

📋 Details:
  • Project: Gold
  • Assignee: @alice
  • Priority: High
  • Due: March 20, 2026

🔗 View in ClickUp: https://app.clickup.com/t/abc123
```

## Tools
- clickup.create_task
- slack.post_message (confirmation to channel)
- notion.create_page (optional: task details page)

## Instructions

1. Extract form data from modal submission
2. Map project slug to ClickUp space ID (use project-configs)
3. Create task in ClickUp:
   ```python
   task = clickup.create_task(
       space_id=project_config.clickup_space_id,
       name=form_data["title"],
       description=form_data["description"],
       assignees=[form_data["assignee"]],
       priority=form_data["priority"],
       due_date=form_data["due_date"]
   )
   ```
4. Post confirmation to Slack channel (mention assignee)
5. Return formatted success message
```

**File:** `skills/pm/task-creator/agentura.config.yaml`

```yaml
name: task-creator
domain: pm
description: Creates task from modal form submission
version: 1.0.0

executor: ptc

mcp:
  clickup:
    tools: ["create_task", "get_space"]
  slack:
    tools: ["post_message"]
  notion:
    tools: ["create_page"]

input_schema:
  type: object
  required: ["form_data"]
  properties:
    form_data:
      type: object
      required: ["title", "project"]
```

---

#### Step 3: Update Gateway Config

**File:** `gateway/config/config.yaml`

Add to PM app section:

```yaml
- name: pm
  # ... existing config ...
  commands:
    # NEW: Hybrid command
    - pattern: "create task"
      skill: "pm/task-form-opener"
      description: "Open task creation form"

    # NEW: Also support contextual creation
    - pattern: "task"
      skill: "pm/task-form-opener"
      description: "Quick task creation"

    # ... existing commands ...

  interaction_handlers:
    # NEW: Handle modal submission
    - callback_id: "task_creation_form"
      type: "view_submission"
      skill: "pm/task-creator"
      description: "Create task from form data"

    # NEW: Shortcut for power users
    - callback_id: "quick_create_task"
      type: "shortcut"
      skill: "pm/task-form-opener"
      description: "Quick task creation"

    # NEW: Contextual - create from message
    - callback_id: "message_to_task"
      type: "message_action"
      skill: "pm/task-form-opener"
      description: "Create task from this message"
```

---

#### Step 4: Configure Slack App

**In Slack App Settings** (https://api.slack.com/apps):

1. **Enable Interactivity:**
   - Go to "Interactivity & Shortcuts"
   - Request URL: `https://your-gateway.com/slack/interactions`
   - Enable "Interactivity"

2. **Add Global Shortcut:**
   - Name: "Create Task"
   - Description: "Quickly create a task in ClickUp"
   - Callback ID: `quick_create_task`

3. **Add Message Shortcut:**
   - Name: "Create Task from Message"
   - Description: "Turn this message into a task"
   - Callback ID: `message_to_task`

4. **Reinstall App** to workspace (to pick up new scopes)

---

## Phase 3: Test & Iterate

### Test Cases

**Test 1: Command Entry**
```
Input: @pm-bot create task
Expected: Modal opens with empty form
Action: Fill "Fix bug", select "Gold", assign to self, click Create
Expected: Task created in ClickUp, confirmation posted to channel
```

**Test 2: Shortcut Entry**
```
Input: Click ⚡ → "Create Task"
Expected: Modal opens with empty form
Action: Same as Test 1
Expected: Same as Test 1
```

**Test 3: Contextual Entry**
```
Input: Right-click message "The login flow is broken"
Action: Select "Create Task from Message"
Expected: Modal opens with:
  - Title: pre-filled with "The login flow is broken"
  - Description: pre-filled with message content + link to message
Action: Select project, assignee, click Create
Expected: Task created with message context preserved
```

**Test 4: Validation**
```
Input: Open modal, leave Title empty, click Create
Expected: Error: "Title is required"
```

**Test 5: Project Configs**
```
Input: Create task for "Gold" project
Expected: Task created in Gold's ClickUp space (from project-configs)
Action: Verify ClickUp shows task in correct space
```

---

## Phase 4: Rollout

### Week 1: Create Task Only
- Ship `task-form-opener` + `task-creator` skills
- Update gateway config
- Configure Slack app
- Test with 2-3 power users
- Gather feedback

### Week 2: Iterate + Add Setup Project
- Fix bugs from Week 1
- Convert `setup {project}` to hybrid pattern
- Same process: opener skill → modal → creator skill

### Week 3: Add Meeting Notes
- New hybrid workflow: "Add meeting notes"
- Modal with structured fields (attendees, decisions, action items)
- Posts to Slack + Notion + creates ClickUp tasks for action items

### Week 4: Add Weekly Planning
- New hybrid workflow: "Weekly planning"
- Modal with OKR template
- Generates weekly plan doc in Notion

---

## Success Metrics

Track these to measure impact:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Task creation time** | < 30 seconds | Time from command to ClickUp task |
| **Error rate** | < 5% | Failed validations / total submissions |
| **Adoption** | 50% of team | Unique users per week |
| **Tasks created via Slack** | 20+ per week | Count from ClickUp API |
| **Feedback score** | 8/10 | User survey after 2 weeks |

---

## Future Enhancements

### Phase 5: Advanced Patterns

**1. Multi-step workflows:**
```
@pm-bot create project
  ↓
Modal 1: Basic info (name, team)
  ↓
Submit → Modal 2: Resources (channels, repos)
  ↓
Submit → Modal 3: Confirm
  ↓
Submit → Create all resources
```

**2. Approval flows:**
```
@pm-bot request budget $5000 for gold
  ↓
Posts to #approvals with [Approve] [Reject] buttons
  ↓
Manager clicks [Approve]
  ↓
Modal: "Add note" (optional)
  ↓
Updates Notion finance tracker
```

**3. Smart pre-filling:**
```
User: Types long message about a bug
User: Right-click → "Create task from this"
  ↓
AI extracts:
  - Title: "Fix authentication timeout"
  - Description: Full bug report
  - Project: "Gold" (detected from channel context)
  - Priority: "High" (detected from keywords)
  ↓
Modal opens with smart defaults
User: Just picks assignee, clicks Create
```

**4. Slack-native task management:**
```
Daily digest posts tasks with buttons:
  [✓ Complete] [Reassign] [Defer]
  ↓
Click button → Updates ClickUp
No need to open ClickUp for simple actions
```

---

## Implementation Checklist

### Code Changes
- [ ] Create `skills/pm/task-form-opener/` skill
- [ ] Create `skills/pm/task-creator/` skill
- [ ] Update `gateway/config/config.yaml` with hybrid config
- [ ] Add Slack app shortcuts in api.slack.com
- [ ] Test modal opening (opener skill)
- [ ] Test form submission (creator skill)
- [ ] Test all 3 entry points (command, shortcut, message action)

### Deployment
- [ ] Push skills to `Vance-Club/agentura-skills` repo
- [ ] Restart executor to sync skills
- [ ] Rebuild + push gateway (for config)
- [ ] Restart gateway
- [ ] Verify in logs

### Documentation
- [ ] Update `docs/slack-interactions.md` with examples
- [ ] Create `docs/TASK_CREATION_GUIDE.md` for users
- [ ] Add to `skills/pm/PACK-README.md`
- [ ] Write product note (see below)

### User Enablement
- [ ] Post announcement in #general
- [ ] Demo in team meeting
- [ ] Create video walkthrough (30 sec)
- [ ] Update onboarding docs

---

## Estimated Effort

| Phase | Tasks | Time |
|-------|-------|------|
| **Phase 1** | Planning + design | 2 hours |
| **Phase 2** | Implement create task | 4 hours |
| **Phase 3** | Test + iterate | 2 hours |
| **Phase 4** | Rollout + docs | 2 hours |
| **Total** | Full hybrid pattern for 1 workflow | **10 hours** |

**ROI:**
- Saves 2 min per task creation × 20 tasks/week = **40 min/week saved**
- Payback in ~15 weeks
- Ongoing value: better data quality, less context switching

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Users don't adopt | Add to daily workflow (e.g., daily standup reminder) |
| Modal UX is clunky | Start simple, iterate based on feedback |
| Skills fail silently | Add error handling + retry logic |
| ClickUp API rate limits | Add caching + batch operations |
| Slack app approval delays | Use existing app, just add scopes |

---

## Next Steps (Action Items)

**For Claude Code:**
1. ✅ Create this plan
2. Create `task-form-opener` skill
3. Create `task-creator` skill
4. Update gateway config
5. Push to repos + deploy

**For User:**
1. Review this plan
2. Approve approach
3. Configure Slack app shortcuts (api.slack.com)
4. Test workflows
5. Gather team feedback

**Timeline:** Ship Phase 1 (create task) by end of week.

---

## Appendix A: Modal JSON Examples

### Task Creation Modal (Full Spec)

```json
{
  "type": "modal",
  "callback_id": "task_creation_form",
  "title": {
    "type": "plain_text",
    "text": "Create Task"
  },
  "submit": {
    "type": "plain_text",
    "text": "Create"
  },
  "close": {
    "type": "plain_text",
    "text": "Cancel"
  },
  "blocks": [
    {
      "type": "input",
      "block_id": "title",
      "label": {
        "type": "plain_text",
        "text": "Title"
      },
      "element": {
        "type": "plain_text_input",
        "action_id": "value",
        "placeholder": {
          "type": "plain_text",
          "text": "e.g., Fix login bug"
        }
      }
    },
    {
      "type": "input",
      "block_id": "description",
      "optional": true,
      "label": {
        "type": "plain_text",
        "text": "Description"
      },
      "element": {
        "type": "plain_text_input",
        "action_id": "value",
        "multiline": true,
        "placeholder": {
          "type": "plain_text",
          "text": "Add details..."
        }
      }
    },
    {
      "type": "input",
      "block_id": "project",
      "label": {
        "type": "plain_text",
        "text": "Project"
      },
      "element": {
        "type": "static_select",
        "action_id": "value",
        "placeholder": {
          "type": "plain_text",
          "text": "Select a project"
        },
        "options": [
          {
            "text": {"type": "plain_text", "text": "Gold"},
            "value": "gold"
          },
          {
            "text": {"type": "plain_text", "text": "Remittance"},
            "value": "remittance"
          },
          {
            "text": {"type": "plain_text", "text": "Unify"},
            "value": "unify"
          }
        ]
      }
    },
    {
      "type": "input",
      "block_id": "assignee",
      "label": {
        "type": "plain_text",
        "text": "Assignee"
      },
      "element": {
        "type": "users_select",
        "action_id": "value",
        "placeholder": {
          "type": "plain_text",
          "text": "Assign to..."
        }
      }
    },
    {
      "type": "input",
      "block_id": "priority",
      "optional": true,
      "label": {
        "type": "plain_text",
        "text": "Priority"
      },
      "element": {
        "type": "static_select",
        "action_id": "value",
        "initial_option": {
          "text": {"type": "plain_text", "text": "Medium"},
          "value": "medium"
        },
        "options": [
          {
            "text": {"type": "plain_text", "text": "🔴 Urgent"},
            "value": "urgent"
          },
          {
            "text": {"type": "plain_text", "text": "🟠 High"},
            "value": "high"
          },
          {
            "text": {"type": "plain_text", "text": "🟡 Medium"},
            "value": "medium"
          },
          {
            "text": {"type": "plain_text", "text": "🟢 Low"},
            "value": "low"
          }
        ]
      }
    },
    {
      "type": "input",
      "block_id": "due_date",
      "optional": true,
      "label": {
        "type": "plain_text",
        "text": "Due Date"
      },
      "element": {
        "type": "datepicker",
        "action_id": "value",
        "placeholder": {
          "type": "plain_text",
          "text": "Select a date"
        }
      }
    }
  ]
}
```

---

## Appendix B: Skill Loading in PTC Worker

The `task-form-opener` skill returns modal JSON instead of text. Ensure PTC worker handles this:

**In `ptc_worker.py`:**
```python
# Check if response is a modal
if isinstance(result, dict) and result.get("response_type") == "modal":
    # Return modal to gateway
    return {
        "type": "modal",
        "trigger_id": context.trigger_id,
        "view": result["view"]
    }
else:
    # Normal text response
    return result
```

**Gateway handles modal response:**
```go
// In slack_webhook.go or slack_socket.go
if executionResult.Type == "modal" {
    // Open modal via Slack API
    _, err := client.OpenView(
        executionResult.TriggerID,
        executionResult.View,
    )
    // Return 200 (no message)
    return nil
}
```
