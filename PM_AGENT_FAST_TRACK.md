# PM Agent Fast-Track Plan (5 Days Total)

**Context:** AskUserQuestion already exists (we built it). AI-accelerated development (Claude Code). Parallel execution.

---

## Aggressive Timeline

```
Day 1-2: Phase 1 (Hybrid) + Phase 3 (Docs) START IN PARALLEL
Day 2-5: Phase 2 (Approval flows) STARTS ON DAY 2
Day 4-5: Phase 4 (Testing) OVERLAPS WITH PHASE 2
Day 5: SHIP TO PRODUCTION
```

**Total:** 5 days (vs original 16.5)

---

## Day 1-2: Hybrid Workflows + Documentation (Parallel)

### Track A: Hybrid Pattern (Claude Code builds)

**Hour 1-2:**
- Create `task-form-opener.md`
- Create `task-creator.md`
- Test standalone with `claude --print`

**Hour 3:**
- Update `agentura.config.yaml` (commands + interaction_handlers)
- Push to agentura-skills repo

**Hour 4:**
- Deploy to EKS (restart executor)
- Configure Slack app shortcuts (you do this)

**Hour 5-6:**
- Test all 3 entry points:
  - Command: `@pm-bot create task`
  - Shortcut: ⚡ → "Create Task"
  - Message action: Right-click → "Create task from this"

**Deliverable:** Working task creation (< 30 sec) ✅

---

### Track B: Documentation Updates (Parallel with Track A)

**Hour 1-3:**
- Update ONBOARDING.md with hybrid workflows
- Update PACK-README.md (add task-form-opener, task-creator)
- Create quick-start guide

**Hour 4:**
- Record 30-sec video demo (task creation)
- Post announcement draft for #global-equities-team

**Deliverable:** User-ready docs ✅

---

## Day 2-5: Approval Flows (The Complex Part)

### Day 2: Pending Interactions DB + Intake

**Morning (3 hours):**
1. Create Pending Interactions DB in Notion:
   ```
   Thread TS (title)
   Channel (text)
   Interaction Type (select)
   Payload (rich text JSON)
   Poster (text)
   Created At (date)
   Status (select)
   ```

2. Build unified `intake.md`:
   - Wraps existing `triage.md`
   - Adds thread reply detection
   - Queries Pending Interactions DB
   - Routes to approval handler

**Afternoon (3 hours):**
3. Test intake routing:
   - Normal message → triage
   - Thread reply → check DB → route to approval
   - Command → route to skill

**Deliverable:** Intake skill working ✅

---

### Day 3: Classification Contract + Update Skills

**Morning (4 hours):**
1. Build classification logic:
   ```python
   def classify_change(change_text):
       # Factual signals
       if explicit_status(change_text):
           return FACTUAL
       if verbatim_action_item(change_text):
           return FACTUAL
       if direct_date_change(change_text):
           return FACTUAL

       # Interpretive signals
       if strategic_language(change_text):
           return INTERPRETIVE
       if summarization(change_text):
           return INTERPRETIVE

       # Default safe
       return INTERPRETIVE
   ```

2. Create test suite (10 edge cases)
3. Validate classification accuracy

**Afternoon (3 hours):**
4. Enhance `meeting-update.md`:
   - Add classification before writing
   - Create Pending Interactions row for interpretive
   - Add provenance trail

5. Enhance `notion-sync.md`:
   - Same classification logic
   - Same approval flow

**Deliverable:** Classification working ✅

---

### Day 4: Approval UX + Provenance

**Morning (3 hours):**
1. Build approval handler in `intake.md`:
   - Parse approve/reject commands
   - Query Pending Interactions DB
   - Commit approved changes
   - Update DB status

2. Add provenance trail template:
   ```
   Remarks: "DFSA response received [via @varun, slack msg 2026-03-14, factual]"
   ```

**Afternoon (3 hours):**
3. Test approval flow end-to-end:
   - Post meeting notes
   - Bot extracts 5 factual, 2 interpretive
   - Factual auto-commits
   - Reply `approve all`
   - Interpretive commits
   - Check Notion for provenance

**Deliverable:** Approval flow working ✅

---

### Day 5: Timeout + Error Handling

**Morning (2 hours):**
1. Add 48h timeout check:
   - Cron job checks Pending Interactions
   - Marks expired rows as Resolved
   - DMs poster: "Approval timed out"

2. Error handling:
   - Notion API timeout → retry once
   - Malformed input → helpful error
   - Partial batch failure → report

**Afternoon (2 hours):**
3. Test error scenarios:
   - Timeout after 48h
   - Notion API fails
   - User replies with invalid command

**Deliverable:** Robust error handling ✅

---

## Day 4-5: Testing + Rollout (Parallel with Day 4-5 of Phase 2)

### Day 4 Afternoon: Integration Testing

**Parallel while approval UX is being built:**

1. Test hybrid + approval together:
   - Create task via modal → works
   - Post meeting notes → approval flow → works
   - Both running simultaneously

2. Test existing skills still work:
   - daily-briefing
   - pm-query
   - meeting-scan

**Deliverable:** No regressions ✅

---

### Day 5 Afternoon: Production Deploy

**2 hours:**

1. Push all changes to agentura-skills repo
2. Restart executor in EKS
3. Verify skills loaded: `kubectl exec deployment/executor -- ls /skills/pm/`
4. Post announcement to #global-equities-team
5. Demo to Ashutosh + 2 team members

**Deliverable:** SHIPPED TO PRODUCTION ✅

---

## Parallel Execution Map

```
Day 1:
  ├─ Track A: task-form-opener (6h) ────┐
  └─ Track B: Documentation (4h) ────────┤
                                         └─> Test hybrid (end of Day 1)

Day 2:
  ├─ Pending Interactions DB (3h) ──────┐
  └─ Intake skill (3h) ──────────────────┤
                                         └─> Test intake (end of Day 2)

Day 3:
  ├─ Classification logic (4h) ─────────┐
  └─ Update skills (3h) ────────────────┤
                                        └─> Test classification (end of Day 3)

Day 4:
  ├─ Approval handler (3h) ─────────────┐
  ├─ Provenance trail (3h) ─────────────┤
  └─ Integration testing (parallel) ────┤
                                        └─> Test approval flow (end of Day 4)

Day 5:
  ├─ Timeout + errors (4h) ─────────────┐
  └─ Production deploy (2h) ────────────┤
                                        └─> SHIP (end of Day 5)
```

---

## Work Distribution (Claude Code vs You)

### Claude Code (Me) - 90% of work

- ✅ Write all skills
- ✅ Create DB schema
- ✅ Build classification logic
- ✅ Test standalone
- ✅ Update documentation
- ✅ Push to repos
- ✅ Restart deployments

### You - 10% of work

- ✅ Configure Slack app shortcuts (30 min, Day 1)
- ✅ Review and approve changes (30 min/day)
- ✅ Test in Slack with team (1 hour, Day 5)

**Your total time:** ~4 hours over 5 days

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **Classification errors** | Test suite with 10 edge cases + default-safe (uncertain → ask) |
| **Approval fatigue** | 80% of changes are factual (auto-commit) |
| **DB race conditions** | Single writer per thread (Slack user), atomic Notion writes |
| **Timeout edge cases** | 48h window covers weekends + timezones |
| **Integration breaks** | Test existing skills daily |

---

## Success Criteria (Day 5)

- ✅ Task creation < 30 sec (all 3 entry points)
- ✅ Approval flow: factual auto-commits, interpretive prompts
- ✅ 0 wrong auto-commits in testing
- ✅ Thread state persists across invocations
- ✅ Provenance trail in Notion
- ✅ 3+ team members test successfully

---

## Daily Checkpoints

**End of Day 1:**
- ✅ Can create tasks via modal? → Ship Phase 1

**End of Day 2:**
- ✅ Intake routes thread replies to approval handler? → Continue

**End of Day 3:**
- ✅ Classification test suite passes? → Continue

**End of Day 4:**
- ✅ Approval flow works end-to-end? → Final polish

**End of Day 5:**
- ✅ Production deploy successful? → DONE

---

## Immediate Next Steps (Today)

**Hour 1 (NOW):**
1. I create `task-form-opener.md`
2. I create `task-creator.md`
3. I test standalone

**Hour 2:**
1. I update `agentura.config.yaml`
2. I push to agentura-skills repo
3. I create deployment instructions for you

**Hour 3:**
1. You restart executor in EKS
2. You configure Slack app shortcuts
3. We test together in Slack

**Hour 4:**
1. We verify all 3 entry points work
2. I start Day 2 work (Pending Interactions DB)
3. You announce to team: "Task creation is live!"

**By EOD Today:**
- ✅ Phase 1 shipped (hybrid workflows)
- ✅ Day 2 started (approval flows)

---

## Key Acceleration Factors

1. **AI-powered development** (Claude Code writes skills in minutes, not hours)
2. **Existing foundation** (15 skills already built by Ashutosh)
3. **Platform ready** (AskUserQuestion exists, Slack interactions work)
4. **Parallel execution** (docs + code + testing simultaneously)
5. **Fast iteration** (test daily, ship incrementally)

**Traditional timeline:** 16.5 days
**AI-accelerated timeline:** 5 days
**Speedup:** 3.3x faster

---

## What Changes from Original Plan

| Original | Fast-Track | Why |
|----------|------------|-----|
| Phase 0: Platform check (0.5 days) | ❌ Skip | Already confirmed |
| Phase 1: Hybrid (3 days) | ✅ 1-2 days | AI writes code faster |
| Phase 2: Approval (5 days) | ✅ 3-4 days | Parallel docs + testing |
| Phase 3: Integration (3 days) | ✅ 1 day | Parallel with Phase 2 |
| Phase 4: Rollout (5 days) | ✅ Ongoing | Start Day 5, continue Week 2 |

**Total:** 16.5 days → 5 days (70% reduction)

---

## Ready to Start?

Say **"yes"** and I'll:
1. Create task-form-opener.md (15 min)
2. Create task-creator.md (15 min)
3. Update agentura.config.yaml (10 min)
4. Push to repo (5 min)
5. Give you deploy instructions

**Phase 1 ships in 1 hour.** 🚀
