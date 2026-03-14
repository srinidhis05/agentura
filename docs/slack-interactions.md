# Slack Interaction Primitives

## Overview

Agentura now supports the full spectrum of Slack interactive elements:

- **Modals** (`view_submission`, `view_closed`) - Complex forms and multi-step workflows
- **Select Menus** - Dropdowns, multi-select, user/channel pickers
- **Shortcuts** - Message actions and global shortcuts
- **Block Actions** - Buttons and interactive elements
- **Overflow Menus** - Dropdown action menus

## How It Works

### 1. Interaction Types

Each interaction type is handled differently:

| Type | Slack Event | Use Case |
|------|-------------|----------|
| `modal_submission` | User submits a modal form | Collect structured input (forms, wizards) |
| `modal_closed` | User closes modal without submitting | Track dismissals, cleanup |
| `message_action` | User selects action from message menu | Act on specific messages (forward, tag, etc.) |
| `global_shortcut` | User clicks shortcut in Slack UI | Start workflows from anywhere |
| `select_action` | User picks from dropdown | Dynamic selections (assignees, categories) |
| `block_action` | User clicks button/interactive element | Simple actions (approve, acknowledge) |
| `overflow_action` | User selects from overflow menu | Contextual actions on items |

### 2. Configuration

Add interaction handlers to your Slack app config in `config.yaml`:

```yaml
triggers:
  slack:
    enabled: true
    apps:
      - name: "MySlackBot"
        bot_token: "${SLACK_BOT_TOKEN}"
        mode: "socket"  # or "http"
        domain_scope: "platform"
        interaction_handlers:
          # Modal submission example
          - callback_id: "create_issue_modal"
            type: "modal_submission"
            skill: "issue-creator"
            description: "Handle issue creation form submission"

          # Message action example
          - callback_id: "forward_to_team"
            type: "message_action"
            skill: "message-forwarder"
            description: "Forward message to another team"

          # Global shortcut example
          - callback_id: "start_incident"
            type: "global_shortcut"
            pipeline: "incident-response"
            description: "Start incident response workflow"

          # Select menu example
          - callback_id: "assign_ticket"
            type: "select_action"
            skill: "ticket-assigner"
            description: "Assign ticket to user"

          # Button click example
          - callback_id: "approve_request"
            type: "block_action"
            skill: "approval-handler"
            description: "Approve or reject request"
```

### 3. Skill Input

When an interaction is triggered, the skill receives structured input:

```json
{
  "user_id": "U123ABC",
  "channel_id": "C456DEF",
  "type": "modal_submission",
  "callback_id": "create_issue_modal",
  "form_values": {
    "title_block.title_input": "Bug in login flow",
    "description_block.description_input": "Users can't log in with SSO"
  }
}
```

For message actions:
```json
{
  "user_id": "U123ABC",
  "channel_id": "C456DEF",
  "type": "message_action",
  "callback_id": "forward_to_team",
  "message_text": "Original message content",
  "message_ts": "1234567890.123456"
}
```

### 4. Skill Response

Skills can return different response types:

**Text output** (posted to channel):
```json
{
  "output": {
    "text": "Issue created: #1234"
  }
}
```

**Modal** (opened in response):
```json
{
  "modal_view": {
    "type": "modal",
    "title": {"type": "plain_text", "text": "Confirm Action"},
    "blocks": [...]
  }
}
```

**Validation errors** (for modals):
```json
{
  "errors": {
    "title_block": "Title is required",
    "assignee_block": "Please select a valid user"
  }
}
```

## Example: Multi-Step Modal Workflow

### Step 1: Slack Shortcut Config

```yaml
interaction_handlers:
  - callback_id: "deploy_app"
    type: "global_shortcut"
    skill: "deployment-wizard"
```

### Step 2: Skill Opens Modal

When user clicks the shortcut, the skill returns a modal:

```json
{
  "modal_view": {
    "type": "modal",
    "callback_id": "deploy_confirm",
    "title": {"type": "plain_text", "text": "Deploy Application"},
    "submit": {"type": "plain_text", "text": "Deploy"},
    "close": {"type": "plain_text", "text": "Cancel"},
    "blocks": [
      {
        "type": "input",
        "block_id": "env_block",
        "element": {
          "type": "static_select",
          "action_id": "environment",
          "placeholder": {"type": "plain_text", "text": "Select environment"},
          "options": [
            {"text": {"type": "plain_text", "text": "Staging"}, "value": "staging"},
            {"text": {"type": "plain_text", "text": "Production"}, "value": "production"}
          ]
        },
        "label": {"type": "plain_text", "text": "Environment"}
      }
    ]
  }
}
```

### Step 3: Handle Modal Submission

Add handler for submission:

```yaml
interaction_handlers:
  - callback_id: "deploy_confirm"
    type: "modal_submission"
    skill: "deployment-executor"
```

The skill receives form values and executes the deployment.

## Best Practices

1. **Use descriptive callback_ids** - Make them specific and namespaced (e.g., `team_settings_update` not just `update`)

2. **Validate early** - Return validation errors from modal submissions instead of posting error messages

3. **Provide feedback** - Always respond to interactions, even if just "Processing..."

4. **Handle errors gracefully** - If a skill fails, the user sees an error message

5. **Test both modes** - Ensure your handlers work in both HTTP webhook and Socket Mode

## Supported Slack Interaction Types

All Slack interaction types are supported in both HTTP webhook and Socket Mode:

- ✅ Block actions (buttons, checkboxes, radio buttons)
- ✅ Static select menus
- ✅ Multi-static select menus
- ✅ User select menus
- ✅ Channel select menus
- ✅ Conversation select menus
- ✅ External select menus (with data source endpoint)
- ✅ Overflow menus
- ✅ Modal submissions (view_submission)
- ✅ Modal dismissals (view_closed)
- ✅ Message shortcuts (message_action)
- ✅ Global shortcuts (shortcut)

## Troubleshooting

**Interaction not triggering:**
- Check that `callback_id` in config matches exactly
- Verify `interaction_handlers` is at the correct YAML level
- Check gateway logs for "no handler configured" messages

**Skill not receiving input:**
- Ensure `domain_scope` is set correctly in app config
- Check executor logs for skill execution errors
- Verify skill name matches exactly (case-sensitive)

**Modal validation not working:**
- Return errors in format: `{"errors": {"block_id": "error message"}}`
- Use block_ids from your modal view definition
- Response must be synchronous (not posted async)
