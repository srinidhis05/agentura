# Testing Slack Interactions - Quick Start

## What's Deployed

3 interaction handlers are now live on the PM Slack bot:

| Callback ID | Type | Trigger | Skill | Use Case |
|------------|------|---------|-------|----------|
| `triage_message` | message_action | Right-click message | pm/triage | Analyze and route any Slack message |
| `quick_status` | shortcut | ⚡ shortcuts menu | pm/project-status | Get project status from anywhere |
| `create_task_modal` | view_submission | Modal form | pm/triage | Create task from structured input |

## How to Test Each One

### 1. Message Action (Easiest to test)

**Setup in Slack App** (one-time):
1. Go to https://api.slack.com/apps
2. Select your PM bot app
3. Navigate to **Interactivity & Shortcuts**
4. Under **Shortcuts**, click "Create New Shortcut"
5. Select **"On messages"** (message shortcut)
6. Fill in:
   - Name: `Triage Message`
   - Short Description: `Analyze and route this message`
   - Callback ID: `triage_message`
7. Click **Create**

**Test it**:
1. Go to any Slack channel where the PM bot is installed
2. Find any message (or send a test message)
3. Hover over the message → click the **⋮** (three dots)
4. Select **More message shortcuts** → **Triage Message**
5. Watch the PM bot respond with triage results!

**Verify it worked**:
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system logs -f deployment/gateway | grep "triage_message"
```

You should see:
```json
{"level":"INFO","msg":"handling slack interaction","type":"message_action","callback_id":"triage_message"}
{"level":"INFO","msg":"dispatching to skill","skill":"pm/triage","domain":"pm"}
```

---

### 2. Global Shortcut

**Setup in Slack App** (one-time):
1. Go to https://api.slack.com/apps → your PM bot
2. Navigate to **Interactivity & Shortcuts**
3. Under **Shortcuts**, click "Create New Shortcut"
4. Select **"Global"** (works from anywhere in Slack)
5. Fill in:
   - Name: `Quick Status`
   - Short Description: `Get project status report`
   - Callback ID: `quick_status`
6. Click **Create**

**Test it**:
1. In Slack, click the **⚡ lightning bolt** icon in the bottom left (or press `Cmd+/` and type "shortcuts")
2. Select **Quick Status** from the shortcuts menu
3. The PM bot executes `pm/project-status` skill
4. You'll see a status report in the channel or DM

**Verify it worked**:
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system logs -f deployment/gateway | grep "quick_status"
```

---

### 3. Modal Submission (Advanced)

This requires creating a modal first. You can trigger modals via:
- A slash command
- A button click
- A shortcut

**Quick test with a button**:

1. Post this message in a Slack channel (use the Slack API or Block Kit Builder):
```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Click to create a task"
      },
      "accessory": {
        "type": "button",
        "text": {
          "type": "plain_text",
          "text": "Create Task"
        },
        "action_id": "open_task_modal"
      }
    }
  ]
}
```

2. Add a button handler that opens this modal:
```json
{
  "type": "modal",
  "callback_id": "create_task_modal",
  "title": {
    "type": "plain_text",
    "text": "Create Task"
  },
  "submit": {
    "type": "plain_text",
    "text": "Create"
  },
  "blocks": [
    {
      "type": "input",
      "block_id": "task_title",
      "element": {
        "type": "plain_text_input",
        "action_id": "title"
      },
      "label": {
        "type": "plain_text",
        "text": "Task Title"
      }
    },
    {
      "type": "input",
      "block_id": "task_description",
      "element": {
        "type": "plain_text_input",
        "multiline": true,
        "action_id": "description"
      },
      "label": {
        "type": "plain_text",
        "text": "Description"
      }
    }
  ]
}
```

3. Fill out the form and click **Create**
4. The `pm/triage` skill receives the form data

**Verify it worked**:
```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system logs -f deployment/gateway | grep "create_task_modal"
```

---

## Watch All Interactions Live

Monitor all Slack interactions in real-time:

```bash
assume infrastructure && kubectl --context infrastructure -n agentura-system logs -f deployment/gateway | grep -E "interaction|callback_id|dispatching"
```

## Troubleshooting

**"Shortcut not found" in Slack**:
- Make sure you configured the shortcut in your Slack app settings
- Reinstall the app to your workspace if needed

**"No response from bot"**:
- Check gateway logs: `kubectl logs -f deployment/gateway -n agentura-system`
- Verify the skill exists: `kubectl exec deployment/executor -n agentura-system -- ls /skills/pm/`

**"Interaction not handled"**:
- Verify callback_id matches exactly (case-sensitive)
- Check config is loaded: `kubectl exec deployment/gateway -n agentura-system -- cat /app/config/config.yaml | grep interaction_handlers`

---

## Next Steps

Once you verify these work:

1. **Add more handlers** for your use cases (modals, buttons, select menus)
2. **Read the full guide**: `cat docs/slack-interactions.md`
3. **See all 7 interaction types**: `cat examples/slack-interactions/config.yaml`
4. **Create custom workflows** with private_metadata and state

## Example: Real Production Handler

```yaml
interaction_handlers:
  - callback_id: "approve_deployment"
    type: "block_actions"
    skill: "devops/deploy-approval"
    description: "Approve production deployment"

  - callback_id: "assign_task"
    type: "select_action"
    skill: "pm/task-assignment"
    description: "Assign task to team member"

  - callback_id: "incident_report"
    type: "view_submission"
    pipeline: "incident-response"
    description: "Submit incident report form"
```

---

**Status**: ✅ All handlers deployed and ready to test!
