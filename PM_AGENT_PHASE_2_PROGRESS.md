# PM Agent Phase 2 Progress — Approval Flows

**Status:** Day 2-3 Core Work Complete ✅

**Branch:** `feat/pm-approval-flows` → merged to `main`

**Deployed to EKS:** ✅ (executor restarted, skills synced)

---

## What's Built (Day 2-3)

### 1. ✅ Pending Interactions Database Schema

**File:** `skills/pm/PENDING_INTERACTIONS_SCHEMA.md`

**What it does:**
- Defines Notion database schema for tracking thread state
- Enables multi-turn approval flows (user can reply hours later)
- Supports 4 interaction types: approval, archive_confirm, disambiguate, system_select

**Schema:**
- Thread TS (title, unique key)
- Channel, Interaction Type, Payload (JSON)
- Poster, Created At, Status, Expires At, Resolved At

**Access patterns:**
- Create when skill needs approval
- Query by thread_ts when user replies in thread
- Mark Resolved after approval
- Timeout check (cron finds expired > 48h)

**Status:** 📋 Schema spec ready — **USER NEEDS TO CREATE THIS DB IN NOTION**

---

### 2. ✅ Classification Contract

**File:** `skills/pm/CLASSIFICATION_CONTRACT.md`

**What it does:**
- Defines factual vs interpretive boundary
- Factual (auto-commit): explicit status, verbatim action items, direct dates
- Interpretive (approval needed): strategic language, inferred category, summarization
- Default-safe: uncertain → interpretive

**Key patterns:**
- "E-005 done" → Factual ✅
- "This seems urgent" → Interpretive ⚠️
- "Alice to review by Friday" → Factual ✅
- "Inferred category: Strategic" → Interpretive ⚠️

**Implementation:**
- Python classification function
- Provenance trail format
- Edge case handling
- Test suite (20 examples)

**Status:** ✅ Contract defined, ready for integration into skills

---

### 3. ✅ Unified Intake Skill

**File:** `skills/pm/intake/`

**What it does:**
- Universal entrypoint for all Slack messages
- Phase 0: Detect if thread reply or new message
- Phase 1: Query Pending Interactions DB if thread reply
- Phase 2: Route to triage if new message
- Phase 3: Handle approval flow if pending interaction found

**Approval command parsing:**
- `approve all` → commit all changes
- `approve 1,2` → commit specific changes
- `reject all` → discard all
- `cancel` → cancel operation

**Integration:**
- Replaces AskUserQuestion (synchronous) with thread-based approvals (async)
- Queries Pending Interactions DB by thread_ts
- Commits approved changes with provenance trail
- Marks interaction as Resolved

**Status:** ✅ Deployed to EKS (executor synced)

---

### 4. ✅ Approval Flow Migration Guide

**File:** `skills/pm/APPROVAL_FLOW_MIGRATION.md`

**What it does:**
- Documents migration from AskUserQuestion → Pending Interactions
- Shows code changes required for meeting-update
- Provides payload schemas for Notion/ClickUp approvals
- Testing checklist

**Skills to migrate:**
- meeting-update (Phases 1-4)
- notion-sync
- project-setup (optional)

**Status:** 📋 Migration guide ready — **ACTUAL SKILL UPDATES PENDING**

---

## What's Deployed to EKS

```bash
/skills/pm/
├── intake/               ✅ NEW (Phase 2)
│   ├── SKILL.md
│   └── agentura.config.yaml
├── task-creator/         ✅ (Phase 1)
├── task-form-opener/     ✅ (Phase 1)
├── triage/               ✅ (existing)
├── meeting-update/       ✅ (existing, needs migration)
├── notion-sync/          ✅ (existing, needs migration)
└── ... (12 other existing skills)
```

**Verified:**
```bash
$ kubectl exec deployment/executor -- ls /skills/pm/ | grep -E "intake|task"
intake
task-creator
task-form-opener
```

---

## What's Pending

### USER ACTION REQUIRED

**1. Create Pending Interactions Database in Notion**

Follow `/tmp/agentura-skills/skills/pm/PENDING_INTERACTIONS_SCHEMA.md`

Steps:
1. Open Notion workspace
2. Create database: **PM Pending Interactions**
3. Add properties (Thread TS, Channel, Interaction Type, Payload, Poster, Created At, Status, Expires At, Resolved At)
4. Copy database ID from URL
5. Add to project config:
   ```yaml
   pending_interactions_db: "abc123def456..."
   ```

**This is BLOCKING for Phase 2 to work.**

---

### SKILL MIGRATION (Day 3-4)

**2. Update meeting-update Skill**

**What needs to change:**
- Phase 1 (Notion updates): Replace AskUserQuestion with Pending Interaction creation
- Auto-commit factual changes immediately
- Create Pending Interaction for interpretive changes
- Post approval prompt to Slack thread
- Exit skill (don't block)

**Status:** 📋 Migration guide written, code changes not implemented yet

**File to edit:** `/tmp/agentura-skills/skills/pm/meeting-update/SKILL.md`

**See:** `/tmp/agentura-skills/skills/pm/APPROVAL_FLOW_MIGRATION.md` lines 94-153

---

**3. Update notion-sync Skill**

**What needs to change:**
- Classify item updates (factual vs interpretive)
- Auto-commit factual
- Create Pending Interaction for interpretive

**Status:** 📋 Not started

---

**4. Add Provenance Trail**

**What needs to change:**
- Every Notion write includes provenance in Remarks field
- Factual: `[via @alice, granola 2026-03-14, factual]`
- Interpretive: `[via @alice, granola 2026-03-14, interpretive - approved by @alice]`

**Status:** 📋 Format defined, not implemented in skills yet

---

### TIMEOUT HANDLING (Day 5)

**5. Cron Job for Expired Interactions**

**What it does:**
- Runs every 6 hours
- Queries Pending Interactions DB
- Finds interactions with Status=Pending AND Expires At < now()
- Marks as Expired
- DMs poster: "Approval request expired"

**Status:** 📋 Not started

---

## Phase 2 Timeline Update

**Original fast-track plan:**
- Day 2: Pending Interactions DB + Intake ✅ DONE
- Day 3: Classification + Update Skills ⏳ 50% DONE (classification done, skill updates pending)
- Day 4: Approval UX + Provenance 📋 BLOCKED (need Notion DB first)
- Day 5: Timeout + Error Handling 📋 NOT STARTED

**Current blocker:** User needs to create Pending Interactions DB in Notion

**Can't proceed with:**
- Skill migrations (meeting-update, notion-sync)
- End-to-end testing
- Provenance trail implementation

**Can proceed with (while waiting for DB):**
- Writing migration code for meeting-update (in parallel)
- Writing timeout cron job logic
- Creating test cases

---

## Testing Checklist (After DB Created)

- [ ] Pending Interactions DB exists in Notion
- [ ] DB ID added to project config
- [ ] intake skill can query DB successfully
- [ ] Test new message → routes to triage
- [ ] Test thread reply (no pending) → routes to triage
- [ ] Test thread reply (with pending) → routes to approval handler
- [ ] Test "approve all" → commits changes
- [ ] Test "approve 1,2" → partial approval
- [ ] Test "reject all" → discards changes
- [ ] Test invalid command → helpful error
- [ ] Provenance trail appears in Notion Remarks field
- [ ] Interaction marked as Resolved after approval

---

## Next Steps

**Immediate (Blocked on User):**
1. ⏳ User creates Pending Interactions DB in Notion
2. ⏳ User adds DB ID to project config

**Then (Day 3-4 - Can I do in parallel?):**
3. ✅ I can write meeting-update migration code (won't deploy until DB ready)
4. ✅ I can write notion-sync migration code
5. ✅ I can write timeout cron job
6. ✅ I can create test scenarios

**Once DB Ready:**
7. Deploy migrated skills
8. Test end-to-end approval flow
9. Test timeout handling
10. Ship Phase 2 to production

---

## Summary

**Phase 1 (Hybrid Workflows):**
- ✅ task-form-opener deployed
- ✅ task-creator deployed
- ⏳ User needs to configure Slack app (shortcuts)

**Phase 2 (Approval Flows):**
- ✅ Pending Interactions schema defined
- ✅ Classification contract defined
- ✅ intake skill deployed
- ✅ Migration guide written
- ⏳ User needs to create Notion DB (BLOCKER)
- 📋 Skill migrations pending (can write in parallel)
- 📋 Timeout cron pending

**Deployment status:**
- ✅ All code pushed to `agentura-skills` main branch
- ✅ EKS executor restarted and synced
- ✅ intake skill loaded and ready

**Blockers:**
1. User creates Pending Interactions DB in Notion
2. User configures Slack app shortcuts (Phase 1)

**Next work:**
- Should I continue with Day 3-4 work (skill migrations) in parallel?
- Or wait for Notion DB to be ready first?
