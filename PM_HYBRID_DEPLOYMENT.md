# PM Hybrid Workflows — Deployment Instructions

**Status:** ✅ Skills created and pushed to `feat/pm-hybrid-workflows` branch

**PR:** https://github.com/Vance-Club/agentura-skills/pull/new/feat/pm-hybrid-workflows

---

## What Was Built (Phase 1 - Hour 1-2)

### Skills Created

1. **task-form-opener** (Entry point)
   - Opens Slack modal with validated form
   - 3 entry points: command, global shortcut, message action
   - Smart pre-filling based on context
   - Model: Haiku (cheap, fast JSON generation)

2. **task-creator** (Executor)
   - Creates task from validated modal submission
   - 3-phase flow: ClickUp → Notion → Slack
   - Error handling with retry logic
   - Model: Sonnet (reasoning for MCP orchestration)

### Files

```
agentura-skills/
└── skills/pm/
    ├── task-form-opener/
    │   ├── SKILL.md
    │   └── agentura.config.yaml
    └── task-creator/
        ├── SKILL.md
        └── agentura.config.yaml
```

---

## Deployment Steps

### Step 1: Merge to Main (Required for EKS sync)

The skills need to be on `main` branch for the EKS executor to sync them.

**Option A: Quick merge** (if you trust the implementation)
```bash
cd /tmp/agentura-skills
git checkout main
git merge feat/pm-hybrid-workflows
git push origin main
```

**Option B: PR review** (if you want to review first)
1. Visit: https://github.com/Vance-Club/agentura-skills/pull/new/feat/pm-hybrid-workflows
2. Create PR
3. Review changes
4. Merge via GitHub UI

---

### Step 2: Restart EKS Executor (Sync Skills)

The executor has a `git-sync-skills` initContainer that clones from the repo on pod start.

**Auth first:**
```bash
granted sso login --sso-start-url https://d-9c6744377a.awsapps.com/start --sso-region eu-west-2
```

**Restart executor:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system rollout restart deployment/executor
```

**Verify skills loaded:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system exec deployment/executor -- ls /skills/pm/ | grep task
```

Expected output:
```
task-creator
task-form-opener
```

---

### Step 3: Configure Slack App (New Interactions)

The skills use interaction handlers that need to be configured in your Slack app.

#### 3a. Global Shortcut

1. Go to: https://api.slack.com/apps → Your app → **Interactivity & Shortcuts**
2. Under **Shortcuts**, click **Create New Shortcut**
3. Select **Global** shortcut type
4. Configure:
   - **Name:** Create Task
   - **Short Description:** Opens task creation form
   - **Callback ID:** `quick_create_task`
5. Save

#### 3b. Message Action

1. Same page (**Interactivity & Shortcuts**)
2. Under **Shortcuts**, click **Create New Shortcut**
3. Select **On messages** shortcut type
4. Configure:
   - **Name:** Create task from this
   - **Short Description:** Convert message to task
   - **Callback ID:** `message_to_task`
5. Save

#### 3c. Verify Request URL

Ensure the **Request URL** points to your gateway:
```
https://<your-gateway-url>/slack/interactions
```

---

### Step 4: Test All Entry Points

#### Test 1: Command (Existing trigger)

In any Slack channel:
```
@pm-bot create task
```

Expected: Modal opens with empty form

#### Test 2: Global Shortcut (New)

1. Click ⚡ (shortcuts icon) in Slack message box
2. Select "Create Task"

Expected: Modal opens with empty form

#### Test 3: Message Action (New)

1. Hover over any message
2. Click "..." (More actions)
3. Select "Create task from this"

Expected: Modal opens with pre-filled title/description from message

#### Test 4: Full Flow

1. Open modal via any entry point
2. Fill form:
   - **Title:** Test hybrid workflow
   - **Description:** Testing Phase 1 deployment
   - **Project:** Gold (or your test project)
   - **Assignee:** Select yourself
   - **Priority:** High
   - **Due Date:** Tomorrow
3. Click **Create**

Expected output in channel:
```
✅ Task created: Test hybrid workflow

📋 Details:
  • Project: Gold
  • Assignee: <@U123>
  • Priority: 🟠 High
  • Due: March 15, 2026

🔗 Links:
  • ClickUp: https://app.clickup.com/t/...
  • Notion: https://notion.so/...

Created by <@U123> via hybrid workflow
```

Expected in ClickUp:
- Task exists in Gold space
- Title, assignee, priority, due date match

Expected in Notion:
- Row in Action Tracker with ClickUp ID/URL
- Source = "Slack hybrid workflow"

---

## Verification Checklist

- [ ] Branch merged to main
- [ ] Executor restarted in EKS
- [ ] Skills visible in executor pod (`/skills/pm/task-*`)
- [ ] Slack global shortcut configured (callback_id: `quick_create_task`)
- [ ] Slack message action configured (callback_id: `message_to_task`)
- [ ] Command test works (`create task`)
- [ ] Shortcut test works (⚡ menu)
- [ ] Message action test works (right-click message)
- [ ] Task created in ClickUp
- [ ] Task recorded in Notion
- [ ] Confirmation posted to Slack

---

## Troubleshooting

### Modal doesn't open

**Check executor logs:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system logs deployment/executor --tail=50 | grep task-form-opener
```

**Verify skill loaded:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system exec deployment/executor -- cat /skills/pm/task-form-opener/SKILL.md | head -5
```

### Task creation fails

**Check Obot MCP connectivity:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system logs deployment/executor --tail=100 | grep -E "clickup|notion"
```

**Verify MCP session:**
- Obot API key has ClickUp and Notion server access enabled
- Session initialized correctly (check for `Mcp-Session-Id` in logs)

### Missing project config

**Error:** "Project 'gold' not configured"

**Fix:** Ensure project config exists in `/skills/pm/project-configs/gold.md`

**Check:**
```bash
assume infrastructure -- kubectl --context infrastructure -n agentura-system exec deployment/executor -- ls /skills/pm/project-configs/
```

---

## Next Steps (Day 2 - Approval Flows)

Once Phase 1 is verified working:

1. **Announce to team** (Hour 4 of fast-track plan):
   ```
   📣 Task creation is now live!

   3 ways to create tasks:
   • @pm-bot create task
   • ⚡ → "Create Task"
   • Right-click message → "Create task from this"

   Tasks go to ClickUp + Notion automatically. Try it out!
   ```

2. **Start Day 2 work** (Pending Interactions DB + intake skill)

---

## Success Metrics

- [ ] Task creation time < 30 seconds (all entry points)
- [ ] 0 validation errors (form handles typos)
- [ ] 100% sync rate (ClickUp + Notion)
- [ ] 3+ team members use successfully

---

## Time Spent

- Hour 1: Skill creation ✅ (45 min)
- Hour 2: Push to repo ✅ (15 min)
- **Hour 3:** Your work (deployment) — estimated 30 min
- **Hour 4:** Testing together — estimated 30 min

**Phase 1 ships in ~3 hours total** 🚀
