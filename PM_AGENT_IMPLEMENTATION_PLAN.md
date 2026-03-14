# PM Agent Implementation Plan — Hybrid Pattern + GE Tracker

**Ship Date:** March 2026
**Scope:** PM domain (`agency/pm/`) combining:
- Asana-style hybrid workflows (task creation, project setup)
- GE Tracker bot (intake, approval flows, morning briefing)
- Meeting notes processing
- Daily/weekly digests

---

## Vision

Build a **Slack-native PM agent** that:
- ✅ **Understands natural language** (chat for queries)
- ✅ **Provides structure when needed** (forms for task creation)
- ✅ **Maintains Notion as source of truth** (auto-sync from all sources)
- ✅ **Requires approval for interpretive changes** (factual auto-commits)
- ✅ **Works across projects** (Gold, Remittance, Unify, GE)

**Key insight from meeting:** "Notion as source of truth is good. Others can be triggers with approval."

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              NOTION (Source of Truth)                    │
│  • Project Configs (Gold, Remittance, Unify, GE)        │
│  • Action Trackers (per project)                        │
│  • Meeting Notes Archive                                │
│  • Context Pages                                        │
│  • Pending Interactions DB (thread state)              │
└────────────┬──────────────────────┬────────────────────┘
             │                      │
      ┌──────▼──────┐        ┌─────▼──────┐
      │ SLACK BOT   │        │ LOCAL INST.│
      │ (Agentura)  │        │(Claude Code)│
      │             │        │             │
      │ • Intake    │        │ • Gmail MCP │
      │ • Approvals │        │ • Granola   │
      │ • Hybrid    │        │ • Push to   │
      │   workflows │        │   Notion    │
      └──────┬──────┘        └─────┬───────┘
             │                     │
      ┌──────▼─────────────────────▼──────┐
      │   #gold, #remittance, #ge, etc.   │
      │   Team interacts here             │
      └───────────────────────────────────┘
```

---

## Phase 1: Foundation (Week 1) — Hybrid Pattern Priority

### Goal
Ship "Create Task" hybrid workflow for immediate value.

### Deliverables

**1.1 Repository Structure**
```
agency/pm/
├── agentura.config.yaml
├── DECISIONS.md
├── GUARDRAILS.md
│
├── skills/
│   ├── intake.md                    # Single entrypoint (all messages)
│   ├── task-form-opener.md          # NEW: Opens task creation modal
│   ├── task-creator.md              # NEW: Creates task from modal submission
│   ├── update.md                    # Processes content → approval flow
│   ├── qa.md                        # Answers questions from Notion
│   └── context-refresh.md           # Rebuilds context file from Notion
│
└── references/
    ├── owner-mappings.md            # Notion/Slack ID mappings + roles
    ├── db-schema.md                 # Action tracker schema
    ├── slack-formatting.md          # mrkdwn rules
    ├── notion-page-index.md         # In-scope pages with IDs
    └── keyword-lists.md             # Project/partner keywords
```

**1.2 Core Skills (MVP)**

**`intake.md`** - Single entrypoint
```markdown
# Skill: Intake

Classifies all Slack messages and routes to appropriate handler.

## Classification Logic

1. **Command** (starts with known command word)
   - `create task` → task-form-opener
   - `help` → list commands
   - `status` → qa (project status query)

2. **Question** (ends with `?` or starts with what/when/who/where/how)
   - → qa skill

3. **Interaction reply** (thread reply to bot message)
   - Check Pending Interactions DB for thread_ts
   - If found → route based on interaction_type (approval/archive/disambiguate)

4. **Meeting notes** (long-form with meeting indicators)
   - → update skill (extract + approve flow)

5. **Status update** (short with task references like "E5 done")
   - → update skill (factual extraction)

6. **Off-topic** (doesn't match any pattern)
   - No response

## Tools
- Notion (query Pending Interactions DB)
- Slack (read message, post responses)

## Output
Routes to appropriate skill handler or responds inline.
```

**`task-form-opener.md`** - Hybrid pattern core
```markdown
# Skill: Task Form Opener

Opens a Slack modal for structured task creation.

## Input
```json
{
  "pre_fill": {
    "title": "Optional: from message content",
    "description": "Optional: from message body",
    "project": "Optional: detected from channel"
  }
}
```

## Modal Structure
- **Title** (required, plain_text_input)
- **Description** (optional, multiline)
- **Project** (required, static_select from project-configs)
- **Assignee** (required, users_select)
- **Priority** (optional: Urgent/High/Medium/Low)
- **Due Date** (optional, datepicker)

## Smart Pre-filling
- If triggered from channel (#gold) → pre-select Gold project
- If triggered from message action → pre-fill title/description from message
- If triggered from command → empty form

## Output
Returns modal JSON with callback_id: "task_creation_form"
```

**`task-creator.md`** - Executes task creation
```markdown
# Skill: Task Creator

Creates task in ClickUp from validated modal form data.

## Input (from modal submission)
```json
{
  "form_data": {
    "title": {"value": "Fix login bug"},
    "description": {"value": "Users can't log in"},
    "project": {"value": "gold"},
    "assignee": {"value": "U123ABC"},
    "priority": {"value": "high"},
    "due_date": {"value": "2026-03-20"}
  },
  "user": {"id": "U123", "name": "alice"},
  "channel": "C123"
}
```

## Process
1. Load project config from Notion project-configs/gold.md
2. Get ClickUp space ID from config
3. Create task via ClickUp MCP:
   ```
   clickup.create_task(
     space_id=config.clickup_space_id,
     name=form_data.title,
     description=form_data.description,
     assignees=[form_data.assignee],
     priority=form_data.priority,
     due_date=form_data.due_date
   )
   ```
4. Post confirmation to Slack channel
5. Write to Notion action tracker (for audit trail)

## Output
```
✅ Task created: Fix login bug

📋 Details:
  • Project: Gold
  • Assignee: @alice
  • Priority: High
  • Due: March 20, 2026

🔗 ClickUp: https://app.clickup.com/t/abc123
```

## Tools
- ClickUp (create_task)
- Notion (read project config, write to action tracker)
- Slack (post_message)
```

**1.3 Gateway Config**

Add to `agentura.config.yaml`:
```yaml
- name: pm
  domain_scope: "pm"

  commands:
    # Hybrid workflows
    - pattern: "create task"
      skill: "pm/task-form-opener"
      description: "Open task creation form"

    # Keep existing router commands
    - pattern: "daily status"
      skill: "pm/pm-heartbeat"

  interaction_handlers:
    # Modal submission
    - callback_id: "task_creation_form"
      type: "view_submission"
      skill: "pm/task-creator"
      description: "Create task from form"

    # Shortcuts
    - callback_id: "quick_create_task"
      type: "shortcut"
      skill: "pm/task-form-opener"
      description: "Quick task creation"

    # Message action
    - callback_id: "message_to_task"
      type: "message_action"
      skill: "pm/task-form-opener"
      description: "Create task from this message"

  events:
    message: true  # All messages → intake
```

**1.4 Slack App Configuration**

In https://api.slack.com/apps → PM bot:

1. **Interactivity & Shortcuts:**
   - Enable Interactivity
   - Request URL: `https://gateway.aspora.com/slack/interactions`

2. **Add Global Shortcut:**
   - Name: "Create Task"
   - Callback ID: `quick_create_task`

3. **Add Message Shortcut:**
   - Name: "Create Task from Message"
   - Callback ID: `message_to_task`

### Phase 1 Success Criteria

- ✅ User types `@pm-bot create task` → modal opens
- ✅ User fills form → task created in ClickUp + Notion
- ✅ User clicks ⚡ → "Create Task" → modal opens
- ✅ User right-clicks message → "Create task from this" → modal pre-filled
- ✅ No errors in logs

**Timeline:** 3-4 days
**ROI:** Immediate (task creation: 2 min → 30 sec)

---

## Phase 2: GE Tracker Core (Week 2)

### Goal
Implement intake + approval flows for GE project.

### Deliverables

**2.1 Update Skill with Approval Flow**

**`update.md`**
```markdown
# Skill: Update

Processes content (meeting notes, status updates) into Notion with approval flow.

## Classification Contract

Every change is classified as FACTUAL or INTERPRETIVE:

**FACTUAL (auto-commit):**
- Explicit status: "E5 is done"
- Verbatim action items: "Varun to set up sandbox by March 21"
- Direct dates: "R12 deadline moved to April 1"

**INTERPRETIVE (needs approval):**
- Strategic language: "GTN is now the critical path"
- Summarization: "Partnership strategy shifted..."
- Inferred tasks: "We should probably create a task for..."

**UNCERTAIN → treat as INTERPRETIVE (default-safe)**

## Approval Flow

1. Extract changes from input
2. Classify each change
3. Auto-commit factual changes
4. For interpretive changes:
   - Create row in Pending Interactions DB:
     ```
     Thread TS: <thread_ts>
     Channel: <channel_id>
     Interaction Type: approval
     Payload: JSON array of changes
     Poster: <user_id>
     Status: Pending
     ```
   - Present in Slack thread:
     ```
     I found 7 changes:

     ✅ Auto-committed (factual):
     1. E5 status → Done
     2. R12 remarks → "DFSA response received"

     ⏳ Need approval (interpretive):
     3. Context page: "GTN is primary integration path"

     Reply: `approve all`, `approve 3`, `reject 3`
     ```

4. When user replies in thread:
   - intake reads Pending Interactions DB by thread_ts
   - Parses reply (`approve 3` → commit item 3)
   - Updates DB row to Resolved
   - Commits approved changes to Notion

## Provenance Trail

Every write includes metadata:
```
Remarks: "DFSA response received [via @varun, slack msg 2026-03-09, factual]"
```

## Tools
- Notion (read tracker, write changes, read/write Pending Interactions)
- Slack (post approval prompt, read replies)
```

**2.2 Pending Interactions Database**

Create in Notion under GE workspace:

| Property | Type | Purpose |
|----------|------|---------|
| Thread TS | Title (key) | Slack thread timestamp |
| Channel | Text | Channel ID |
| Interaction Type | Select | approval / archive-confirm / disambiguate |
| Payload | Rich Text (JSON) | Context data for interaction |
| Poster | Text | Slack user ID |
| Created At | Date | Auto-timestamp |
| Status | Select | Pending / Resolved / Expired |

**2.3 Intake Enhancement**

Update `intake.md` to check Pending Interactions on every thread reply:

```markdown
## Thread Reply Handling

1. Check if message is a thread reply (thread_ts exists)
2. Query Pending Interactions DB: Thread TS = <thread_ts>
3. If found AND Status = Pending:
   - Read Interaction Type
   - Route based on type:
     - `approval` → parse approve/reject command → commit changes
     - `archive-confirm` → load archived page
     - `disambiguate` → select from candidate list
   - Update Status to Resolved
4. If not found OR Status != Pending:
   - Process as normal message classification
```

### Phase 2 Success Criteria

- ✅ Post meeting notes → bot extracts changes
- ✅ Factual changes auto-commit to Notion
- ✅ Interpretive changes prompt for approval
- ✅ Reply `approve all` → changes commit
- ✅ Pending Interactions DB updated correctly
- ✅ Provenance trail visible in Notion

**Timeline:** 4-5 days
**Dependency:** Phase 1 complete

---

## Phase 3: Scheduled Jobs (Week 3)

### Goal
Add cron-triggered workflows (morning briefing, context refresh, digests).

### Deliverables

**3.1 Morning Briefing**

**`morning-briefing.md`**
```markdown
# Skill: Morning Briefing

Generates daily project status post.

## Schedule
Weekdays 8:00 AM GST (via Heartbeat)

## Format Variations

**Monday:** Weekly overview
- All items due this week
- Grouped by owner
- Overdue items highlighted

**Tue-Thu:** Daily
- Items due today
- Overdue items

**Friday:** Accountability review
- Done this week
- Still overdue
- Next week preview

## Output
Posts to channel as top-level message (not thread):

```
🌅 Morning Briefing — March 14, 2026 (Monday)

📅 This Week (March 14-18):
• @alice: E5, E12 (due Tue), P3 (due Thu)
• @bob: R7 (due Wed)

⚠️ Overdue (2):
• E9 — API integration (due Mar 10, owner: @alice)
• R4 — License filing (due Mar 12, owner: @varun)

🎯 Focus: Launch prep for Phase 1 (target: March 21)
```

## Tools
- Notion (read action tracker, project configs)
- Slack (post_message to channel)
```

**3.2 Context Refresh**

**`context-refresh.md`**
```markdown
# Skill: Context Refresh

Rebuilds context file and page index from Notion.

## Schedule
Daily 7:00 AM GST (before morning briefing)

## Process
1. Scan GE parent page tree (excluding Archive)
2. Build notion-page-index.md with all in-scope pages
3. Generate context file:
   - Last updated timestamp
   - Launch timeline summary
   - Partnership statuses
   - Open decisions
   - Page index with links
4. Save context file to Notion
5. Update references/notion-page-index.md

## Tools
- Notion (read pages, write context)
```

**3.3 Daily Change Digest**

**`daily-digest.md`**
```markdown
# Skill: Daily Change Digest

DMs both Admins with summary of all day's changes.

## Schedule
Daily 6:00 PM GST

## Output
```
📋 PM Tracker — Daily Digest (March 14, 2026)

Auto-committed (factual): 8 changes
  • Varun S: E5 → Done, E12 → In Progress
  • Parth: R12 remarks updated

Approved by Contributors (interpretive): 3 changes
  • Varun S approved: Context page update

Expired (unapproved): 1 change
  • Anurag's post: inferred task (timed out)

Review in Notion for full details.
```

## Tools
- Notion (read changes from today, check Remarks provenance)
- Slack (DM to Admins)
```

**3.4 Heartbeat Configuration**

Add to `agentura.config.yaml`:
```yaml
heartbeats:
  - name: morning-briefing
    schedule: "0 8 * * 1-5"  # Weekdays 8 AM
    skill: "pm/morning-briefing"
    timezone: "Asia/Dubai"

  - name: context-refresh
    schedule: "0 7 * * *"  # Daily 7 AM
    skill: "pm/context-refresh"
    timezone: "Asia/Dubai"

  - name: daily-digest
    schedule: "0 18 * * *"  # Daily 6 PM
    skill: "pm/daily-digest"
    timezone: "Asia/Dubai"
```

### Phase 3 Success Criteria

- ✅ Morning briefing posts at 8 AM daily (Monday/Tue-Thu/Friday formats)
- ✅ Context refresh runs at 7 AM, updates page index
- ✅ Daily digest DMs Admins at 6 PM with change summary
- ✅ All crons log to console, DM Admin on failure

**Timeline:** 3 days
**Dependency:** Phase 2 complete

---

## Phase 4: Local Instance Skills (Parallel with Phase 2-3)

### Goal
Enable Ashutosh (and future PMs) to push from personal sources.

### Deliverables

**4.1 Setup Skill**

**`~/.claude/commands/ge-setup.md`**
```markdown
# Command: GE Setup

One-time setup for GE local skills.

## Process
1. Check for required MCPs:
   - Gmail
   - Granola
   - Notion
   - Slack
2. Report which are missing with setup instructions
3. Edit ~/.claude/settings.json to pre-approve GE tools:
   ```json
   {
     "allowedPrompts": [
       {
         "tool": "Bash",
         "prompt": "timestamp operations"
       },
       {
         "tool": "Read",
         "prompt": "read reference files"
       }
     ],
     "allowedTools": {
       "mcp__notion": ["*"],
       "mcp__gmail": ["search_messages", "read_message"],
       "mcp__granola": ["list_meetings", "get_meeting"],
       "mcp__slack": ["read_channel", "post_message"]
     }
   }
   ```
4. Confirm setup complete

## Tools
- Edit (for settings.json)
- Bash (to check MCP connections)
```

**4.2 Push Skill**

**`~/.claude/commands/ge-push.md`**
```markdown
# Command: GE Push

Scan Gmail + Granola for GE-relevant content, present for approval, push to Notion.

## Keyword Filters
(From references/keyword-lists.md)

**Partners:** Alpaca, WealthKernel, GTN, Atom Prive, etc.
**Topics:** Global equities, brokerage, US stocks, DIFC, DFSA, etc.
**People:** Team member names

## Process
1. Read last push timestamp from ~/.claude/ge-push-state.json
2. Scan sources (parallel):
   - Granola: meetings since last timestamp
   - Gmail: GE-relevant emails since last timestamp
3. Filter by keywords
4. Present compact summary:
   ```
   Found 3 items since Mar 8, 6:30 PM:

   1. [Granola] Alpaca sync — Mar 9, 2 PM
      → 4 factual, 2 need approval
   2. [Gmail] WealthKernel sandbox — Mar 9, 10 AM
      → 1 factual

   Auto-commit 5 factual? [Approve / Review / Skip]
   ```
5. On approval:
   - Commit to Notion (with provenance)
   - Update timestamp
   - Post summary to #global-equities-team via bot

## Tools
- Gmail MCP
- Granola MCP
- Notion MCP
- Slack MCP
- Write (for state file)
```

**4.3 Ref Load**

**`~/.claude/commands/ge-ref.md`**
```markdown
# Command: GE Ref

Load GE context into current session.

## Process
1. Read context file (from Notion or local cache)
2. Present:
   - Launch timeline
   - Partnership statuses
   - Open decisions
   - Page index
3. End with: "Reference loaded. What are we working on?"

## Tools
- Read (context file)
```

### Phase 4 Success Criteria

- ✅ `/ge-setup` configures settings.json correctly
- ✅ `/ge-push` scans, presents summary, commits on approval
- ✅ `/ge-ref` loads context into session
- ✅ No permission prompts during normal operation

**Timeline:** 2-3 days (parallel with Phase 2-3)

---

## Phase 5: Polish & Rollout (Week 4)

### Goal
Edge cases, error handling, team onboarding.

### Deliverables

**5.1 GUARDRAILS.md**

Document real failure modes:
```markdown
# Guardrails

## GR-030: Never auto-commit strategic language
**Mistake:** Bot auto-committed "GTN is critical path" as factual.
**Impact:** Team acted on unvalidated strategy change.
**Rule:** Any language with "critical", "priority", "pivot", "should" → INTERPRETIVE.
**Detection:** Classification contract test suite.

## GR-031: Always check Pending Interactions before responding to thread reply
**Mistake:** Bot treated approval reply as new question, missed context.
**Impact:** User had to re-post approval.
**Rule:** Every thread reply checks Pending Interactions DB first.
**Detection:** Thread reply without DB check in code.
```

**5.2 Error Handling**

Add to all skills:
- Notion API timeout → retry once, DM Admin on failure
- Claude timeout (>5 min) → reply in thread with error
- Malformed input → reply with suggestion
- Partial batch failure → commit successes, report failures

**5.3 Team Onboarding**

Create `docs/PM_BOT_ONBOARDING.md`:
```markdown
# PM Bot Onboarding

## Quick Start

**Create a task (3 ways):**
1. Type: `@pm-bot create task`
2. Click: ⚡ → "Create Task"
3. Right-click message → "Create task from this"

**Check status:**
- `@pm-bot daily status`
- `@pm-bot check gold`

**Ask questions:**
- `@pm-bot what's the status of E5?`
- `@pm-bot when is gold launching?`

## How It Works

The bot:
- ✅ Auto-commits factual changes (status updates, explicit action items)
- ⏳ Asks approval for interpretive changes (strategy, inferred tasks)
- 📝 Maintains Notion as source of truth
- 🔔 Posts morning briefing daily at 8 AM

## Permissions

| Role | Can Do |
|------|--------|
| **Admin** (Ashutosh, Varun S) | All mutations, approve any change |
| **Contributor** (Varun Y, Parth, etc.) | Status updates, approve own changes |
| **Observer** (others) | Ask questions, post for processing |

## Commands

- `help` — List commands
- `create task` — Open task form
- `status` — Project status
- `tracker` — Action tracker summary
- `item E5` — Details for item E5
- `search <query>` — Search Notion

## Approval Format

```
Reply with:
• `approve all` — commit all
• `approve 3` — commit only #3
• `reject all` — discard all
```

Approvals expire after 48 hours.
```

### Phase 5 Success Criteria

- ✅ GUARDRAILS.md has 5+ real failure modes
- ✅ Error handling tested (timeout, malformed input, partial failure)
- ✅ 3+ team members use bot weekly
- ✅ Notion tracker <24h stale

**Timeline:** 3-4 days
**Gate:** 1 week of live usage

---

## Implementation Phases Summary

| Phase | Focus | Timeline | Deliverables |
|-------|-------|----------|--------------|
| **1: Foundation** | Hybrid pattern (create task) | Week 1 (3-4 days) | task-form-opener, task-creator, intake, config |
| **2: GE Tracker Core** | Intake + approval flows | Week 2 (4-5 days) | update, Pending Interactions DB, classification |
| **3: Scheduled Jobs** | Cron workflows | Week 3 (3 days) | morning-briefing, context-refresh, daily-digest |
| **4: Local Skills** | Personal instance push | Parallel (2-3 days) | ge-setup, ge-push, ge-ref |
| **5: Polish** | Edge cases, onboarding | Week 4 (3-4 days) | GUARDRAILS, error handling, docs |

**Total:** 4 weeks (with phases 2-4 partially parallel)

---

## Testing Strategy

### Unit Tests (Per Skill)

Test each skill standalone with `claude --print`:

```bash
# Test task-form-opener
echo '{"pre_fill": {"title": "Test task", "project": "gold"}}' | \
  claude --print skills/pm/task-form-opener.md

# Test update classification
echo 'Meeting notes: E5 is done. Varun to setup sandbox by March 21.' | \
  claude --print skills/pm/update.md
```

**Success:** Correct modal JSON / correct factual/interpretive split

### Integration Tests (Cross-Skill)

Test flows that span multiple invocations:

**Test 1: Approval Flow**
1. Post meeting notes to Slack
2. Bot creates Pending Interactions row
3. Reply `approve all` in thread
4. Bot commits to Notion, marks row Resolved

**Test 2: Hybrid Task Creation**
1. Type `@pm-bot create task`
2. Modal opens
3. Fill form, submit
4. Task created in ClickUp + Notion

**Test 3: Thread State Persistence**
1. Trigger approval prompt (creates DB row)
2. Wait 5 minutes
3. Reply from different invocation
4. Confirm state resolves correctly

### Agentura Integration Gate (Phase 5.5)

**Must pass all 6 tests before production deploy:**

1. **Approval flow:** Post notes → bot creates DB row → reply `approve 4` → confirm commit
2. **Archive confirmation:** Ask archived topic → bot creates row → reply `yes` → confirm lookup
3. **Disambiguation:** Ambiguous page → bot creates row → reply `2` → confirm selection
4. **Expiry:** Create row, wait 48h (simulate), confirm auto-expire
5. **Concurrent replies:** Two users reply to same thread → confirm no corruption
6. **Passive reading:** Post status (no @mention) → confirm intake processes

**Who runs:** You + me together in staging environment
**Gate:** All 6 pass before production deploy

---

## Success Metrics

| Metric | Baseline | Target (Month 1) | How to Measure |
|--------|----------|------------------|----------------|
| **Task creation time** | 2 min (manual ClickUp) | < 30 sec | Time from command to task created |
| **Input error rate** | 15% (wrong project, typos) | < 5% | Failed validations / total |
| **Adoption** | 0% | 50% of PM team | Unique users per week |
| **Notion freshness** | Manual updates | < 24h stale | Last update timestamp |
| **Admin time saved** | 45-60 min/day | < 15 min/day | Ashutosh self-report |

---

## Migration from Existing

**Current state:**
- 5 existing `/ge-*` commands (personal, Ashutosh only)
- No production users

**Migration plan:**
1. Build new skills (keep old commands untouched)
2. Ashutosh tests new vs old side-by-side (2-3 days)
3. If equivalent → delete old `.md` files
4. No rollback needed (can restore from git)

**No shadow mode needed** (no other users, no dependencies)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **Users don't adopt** | Phase 1 immediate value (task creation ROI) + daily briefing visibility |
| **Classification errors** | Comprehensive test suite + default-safe (uncertain → approval) |
| **Approval fatigue** | Factual auto-commits cover 70-80% of changes |
| **Thread state failures** | Pending Interactions DB tested in Phase 5.5 gate |
| **Notion API limits** | Batch writes, retry logic, Admin alerts |

---

## Next Steps (Action Items)

**For You:**
1. Review this plan
2. Approve Phase 1 to start (or request changes)
3. Prepare Slack app for shortcuts configuration
4. Set up Notion integration token

**For Me:**
1. Create Phase 1 skills (task-form-opener, task-creator, intake)
2. Update agentura.config.yaml
3. Test standalone with `claude --print`
4. Deploy to Agentura staging for Phase 5.5 gate
5. Ship to production

**Timeline:** Start Phase 1 immediately, ship by end of week.

---

## Appendix: Key Design Decisions

**Why hybrid pattern first?**
- Immediate ROI (task creation time)
- Validates modal UX before investing in complex flows
- Proves infrastructure (thread context, modal handling)

**Why single intake entrypoint?**
- Eliminates routing ambiguity
- One skill sees full message context
- Easier to debug and test

**Why Pending Interactions DB in Notion?**
- Persistence across pod restarts
- Atomic writes, query-by-key
- Already have Notion MCP access
- Tradeoff: one extra API call (acceptable for 7-person team)

**Why factual vs interpretive classification?**
- Reduces approval fatigue (80% auto-commit)
- Builds trust (users see what's happening)
- Default-safe (uncertain → ask)

**Why 48h approval timeout?**
- Covers weekends + timezones
- Prevents stale state accumulation
- Logged in daily digest for oversight
