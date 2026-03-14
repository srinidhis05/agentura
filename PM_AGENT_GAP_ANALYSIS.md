# PM Agent Gap Analysis — Building on PR #10

**Context:** Ashutosh's PR #10 delivered 15 consolidated PM skills. This analysis identifies what's missing for the complete vision (hybrid workflows + GE Tracker).

---

## What Already Exists (PR #10 - Merged)

### ✅ 15 Server Skills

| # | Skill | What It Does | GE Tracker Mapping |
|---|---|---|---|
| 1 | **triage** | Routes ambiguous input to appropriate skill | ✅ Router (partial) |
| 2 | **meeting-update** | Processes meeting notes → Notion/Slack/ClickUp/Email | ✅ Intake (partial) |
| 3 | **meeting-scan** | Scans for unprocessed meetings (Granola) | ✅ Local push (partial) |
| 4 | **meeting-prep** | Prepares briefing for upcoming meetings | ➕ Bonus |
| 5 | **pm-query** | Answers questions from Notion | ✅ Q&A flow |
| 6 | **daily-briefing** | Morning status post (cron 9am) | ✅ Morning briefing |
| 7 | **daily-wrap** | End of day summary (cron 6pm) | ✅ Daily wrap |
| 8 | **weekly-digest** | Weekly summary (cron Mon 9am) | ➕ Bonus |
| 9 | **action-tracker** | Overdue tracking (cron 10am) | ✅ Overdue check |
| 10 | **project-status** | Project status report | ✅ Status command |
| 11 | **pm-heartbeat** | Health check across systems | ✅ Heartbeat |
| 12 | **channel-digest** | Slack channel summary (cron 5pm) | ➕ Bonus |
| 13 | **notion-sync** | Syncs data to Notion | ✅ Update flow (partial) |
| 14 | **context-refresh** | Rebuilds context file from Notion | ✅ Context refresh |
| 15 | **project-setup** | Initializes new project | ✅ Setup command |

### ✅ Documentation
- PACK-README.md - Skill overview
- PLATFORM-CHANGES.md - 8 platform requests (1 blocker)
- MIGRATION.md - How to upgrade configs
- ONBOARDING.md - User guide
- CODEX_REVIEW.md - Design review

### ✅ Project Config Template
- _template.md - Generic config with all fields

---

## What's Missing (Gaps)

### Gap 1: Hybrid Workflows (Asana-Style Task Creation)

**Missing:**
- ❌ task-form-opener skill (opens modal)
- ❌ task-creator skill (creates from modal submission)
- ❌ Interaction handlers config (modal, shortcuts, message actions)

**Value:** Immediate ROI (task creation: 2 min → 30 sec)

**Complexity:** Low (2 skills, gateway config, Slack app config)

---

### Gap 2: Unified Intake with Approval Flows

**Partially exists:** `triage` routes, `notion-sync` writes to Notion

**Missing:**
- ❌ Single intake entrypoint (all messages → classify → route)
- ❌ Factual vs interpretive classification contract
- ❌ Approval flow with Pending Interactions DB
- ❌ Thread state persistence across invocations
- ❌ Provenance trail (source tracking in Notion)

**Value:** Safety (no wrong auto-commits) + Trust (user sees what's happening)

**Complexity:** Medium (need Pending Interactions DB, classification logic)

---

### Gap 3: Thread Context Handling

**Platform blocker:** PLATFORM-CHANGES.md #5 - Thread context passing

**Missing:**
- ❌ Parent message context when user replies in thread
- ❌ Approval reply parsing (approve 3, reject all)
- ❌ Archive confirmation flow
- ❌ Page disambiguation flow

**Workaround:** Pending Interactions DB stores context (our solution from GE Tracker PRD)

**Value:** Enables multi-turn interactions (approve/reject, archive confirm)

**Complexity:** Medium (DB schema + intake routing)

---

### Gap 4: Platform Capabilities

**From PLATFORM-CHANGES.md:**

| Request | Priority | Status | Impact if Missing |
|---------|----------|--------|-------------------|
| 1. AskUserQuestion (buttoned approval) | **BLOCKER** | ❓ Unknown | Write skills unsafe (auto-exec on "yes") |
| 2. Project config injection | HIGH | ❓ Unknown | Skills can't resolve project-specific refs |
| 3. Run history logging | HIGH | ❓ Unknown | meeting-scan re-surfaces processed meetings |
| 4. Gmail MCP via Vigil | HIGH | ❓ Unknown | Email workflows blocked |
| 5. Thread context passing | MEDIUM | ❓ Unknown | Thread replies misrouted |
| 6. Server-side state store | MEDIUM | ❓ Unknown | Fallback to Notion works, slower |
| 7. Local file generation | MEDIUM | ❓ Unknown | Copy-paste friction for setup |
| 8. Cron timezone | LOW | ❓ Unknown | Crons run in wrong timezone |

**Action needed:** Ask Srinidhi which of these are already implemented.

---

## Revised Implementation Plan

### Phase 0: Platform Verification (Week 0 - Day 1)

**Goal:** Confirm platform capabilities before building.

**Tasks:**
1. Check with Srinidhi: which of 8 platform requests are already done?
2. Specifically confirm:
   - ✅/❌ AskUserQuestion with buttons (blocker)
   - ✅/❌ Project config injection
   - ✅/❌ Thread context passing
3. If AskUserQuestion is NOT implemented → highest priority platform work

**Gate:** Can't proceed without buttoned approval (safety critical)

---

### Phase 1: Hybrid Pattern (Week 1 - 3 days)

**Goal:** Add Asana-style task creation on top of existing skills.

**Deliverables:**

**1.1 New Skills**
- `task-form-opener.md` - Opens task creation modal
- `task-creator.md` - Creates task from validated form data

**1.2 Gateway Config**
```yaml
commands:
  - pattern: "create task"
    skill: "pm/task-form-opener"

interaction_handlers:
  - callback_id: "task_creation_form"
    type: "view_submission"
    skill: "pm/task-creator"

  - callback_id: "quick_create_task"
    type: "shortcut"
    skill: "pm/task-form-opener"

  - callback_id: "message_to_task"
    type: "message_action"
    skill: "pm/task-form-opener"
```

**1.3 Slack App Config**
- Global shortcut: "Create Task"
- Message action: "Create task from this"

**Success Criteria:**
- ✅ All 3 entry points work (command, shortcut, message action)
- ✅ Modal validates input (no typos possible)
- ✅ Task created in ClickUp + Notion
- ✅ Time < 30 seconds

**Timeline:** 3 days

---

### Phase 2: Unified Intake + Approval (Week 2 - 5 days)

**Goal:** Add safety layer to existing write skills.

**Deliverables:**

**2.1 Pending Interactions Database (Notion)**

Create in Notion:
```
Database: PM Pending Interactions

Schema:
  Thread TS (title, key)
  Channel (text)
  Interaction Type (select: approval / archive / disambiguate)
  Payload (rich text, JSON)
  Poster (text, Slack ID)
  Created At (date)
  Status (select: Pending / Resolved / Expired)
```

**2.2 Enhanced Intake Skill**

Update `triage.md` → `intake.md`:
```markdown
# Skill: Intake

Unified entrypoint for all Slack messages.

## Classification Logic

1. **Check for pending interaction** (thread reply)
   - Query Pending Interactions DB by thread_ts
   - If found → route to approval/archive/disambiguate handler

2. **Route to existing skills:**
   - Command (create task, status, etc.) → route to skill
   - Question → pm-query
   - Meeting notes → meeting-update (with approval flow)
   - Status update → notion-sync (with factual/interpretive split)
   - Off-topic → ignore

## Approval Flow

Extract changes → classify factual/interpretive → auto-commit factual → prompt for interpretive

Factual:
  - Explicit status ("E5 done")
  - Verbatim action items with owner + date
  - Direct date changes

Interpretive:
  - Strategic language
  - Summarization
  - Inferred tasks
  - Default-safe: uncertain → ask

## Tools
- Notion (query/write Pending Interactions, read/write tracker)
- Slack (post approval prompts, read replies)
```

**2.3 Update Existing Skills**

Enhance `meeting-update`, `notion-sync` with:
- Factual/interpretive classification
- Provenance trail in Remarks field
- Create Pending Interactions row for approvals

**Success Criteria:**
- ✅ Post meeting notes → bot extracts changes
- ✅ Factual auto-commits with provenance
- ✅ Interpretive prompts for approval
- ✅ Reply `approve all` → changes commit
- ✅ Thread state persists across invocations

**Timeline:** 5 days

---

### Phase 3: Integration + Polish (Week 3 - 3 days)

**Goal:** Connect all pieces, test end-to-end.

**Tasks:**
1. Test full flows:
   - Hybrid task creation (all 3 entry points)
   - Meeting notes → approval → commit
   - Status update → factual auto-commit
   - Question → pm-query answer
2. Error handling (timeouts, malformed input)
3. Update ONBOARDING.md with new workflows
4. Test with GE team (Ashutosh + 2-3 others)

**Success Criteria:**
- ✅ All flows work end-to-end
- ✅ No errors in logs
- ✅ 3+ team members use successfully

**Timeline:** 3 days

---

### Phase 4: Rollout (Week 4)

**Goal:** Deploy to production, onboard team.

**Tasks:**
1. Deploy to EKS (restart executor to sync skills)
2. Announce in #global-equities-team
3. Demo in team meeting
4. Monitor for 1 week, gather feedback
5. Update GUARDRAILS.md with real failure modes

**Success Criteria:**
- ✅ 50% weekly active usage
- ✅ Notion <24h stale
- ✅ No safety issues (wrong auto-commits)

**Timeline:** 1 week

---

## What We're NOT Building

These are already in PR #10:

- ❌ meeting-scan (exists)
- ❌ meeting-prep (exists)
- ❌ daily-briefing (exists)
- ❌ weekly-digest (exists)
- ❌ context-refresh (exists)
- ❌ pm-query (exists)
- ❌ project-setup (exists)
- ❌ All cron jobs (exist)
- ❌ Project config template (exists)

**We're ADDING:**
- ✅ Hybrid workflows (task-form-opener, task-creator)
- ✅ Unified intake with approval flows
- ✅ Pending Interactions DB
- ✅ Factual/interpretive classification
- ✅ Thread state persistence

---

## Platform Dependency Resolution

**BLOCKER: AskUserQuestion with buttons**

**If NOT implemented:**
- Option 1: Srinidhi implements (blocks Phase 2)
- Option 2: We use Pending Interactions DB workaround (text parsing fragile)
- Option 3: Ship Phase 1 only (hybrid workflows), defer approval flows

**Recommendation:** Ask Srinidhi status of PLATFORM-CHANGES.md requests ASAP.

**If implemented:**
- Phase 2 becomes simpler (use platform primitive instead of DB workaround)

---

## Success Metrics (Incremental)

| Metric | After Phase 1 | After Phase 2 | After Phase 4 |
|--------|---------------|---------------|---------------|
| **Task creation time** | < 30 sec | < 30 sec | < 30 sec |
| **Notion freshness** | Manual | < 24h | < 24h |
| **Adoption** | 2-3 users | 5+ users | 50%+ team |
| **Safety** | N/A | 0 wrong auto-commits | 0 wrong auto-commits |

---

## Effort Estimate

| Phase | What | Time | Dependency |
|-------|------|------|------------|
| 0 | Platform verification | 0.5 day | Srinidhi call |
| 1 | Hybrid workflows | 3 days | Phase 0 |
| 2 | Intake + approval | 5 days | Phase 0 + Phase 1 |
| 3 | Integration | 3 days | Phase 2 |
| 4 | Rollout | 5 days | Phase 3 |

**Total:** 16.5 days (3.5 weeks)

**Critical path:** Phase 0 gates everything (need platform status)

---

## Immediate Next Steps

**For You:**
1. Read Ashutosh's PLATFORM-CHANGES.md
2. Check with Srinidhi: which of 8 requests are implemented?
3. Specifically confirm AskUserQuestion status (blocker)
4. Share platform status with me

**For Me:**
1. Wait for platform status
2. If AskUserQuestion exists → start Phase 1 immediately
3. If not → adjust plan (use workaround or defer Phase 2)

**Timeline:** Get platform status by EOD, start Phase 1 tomorrow.
