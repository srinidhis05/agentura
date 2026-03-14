# End-to-End Demo Setup Guide

**Goal:** Complete demonstration of all PM Agent features from the GE Tracker PRD

**Time Required:** 30 minutes setup + 30 minutes demo

---

## Step 1: Add Test Data to Notion (5 min)

### Go to your Notion database:
https://www.notion.so/104d569f356e4ce28b130da249a0c9cc

### Add these 6 items:

**Click "+ New" and add each item:**

#### Item 1: E-005
- **Title:** E-005 Login Bug Fix
- **Status:** In Progress
- **Priority:** High
- **Category:** Technical
- **Assignee:** Alice (or your name)
- **Due Date:** 2026-03-15 (tomorrow)
- **Description:** Users unable to login with Google OAuth
- **Remarks:** `[via @ashutosh, meeting 2026-03-10, factual]`

#### Item 2: E-010
- **Title:** E-010 WealthKernel API Integration
- **Status:** Blocked
- **Priority:** High
- **Category:** Integration
- **Assignee:** Bob (or teammate)
- **Due Date:** 2026-03-20
- **Description:** Waiting on partner to provide sandbox credentials
- **Remarks:** `[via @alice, slack 2026-03-12, factual]`

#### Item 3: E-015
- **Title:** E-015 Database Performance Optimization
- **Status:** Not Started
- **Priority:** Medium
- **Category:** Technical
- **Assignee:** Carol
- **Due Date:** 2026-03-25
- **Description:** Query optimization for action items dashboard

#### Item 4: P-042
- **Title:** P-042 DFSA Compliance Review
- **Status:** In Progress
- **Priority:** High
- **Category:** Regulatory
- **Assignee:** Alice
- **Due Date:** 2026-03-18
- **Description:** Regulatory approval for digital gold offering
- **Remarks:** `[via @neha, email 2026-03-11, factual]`

#### Item 5: A-007
- **Title:** A-007 Partner Documentation Update
- **Status:** Done
- **Priority:** Medium
- **Category:** Documentation
- **Assignee:** Bob
- **Due Date:** 2026-03-14 (today)
- **Description:** Update API documentation for partners
- **Remarks:** `[via @bob, slack 2026-03-14, factual]`

#### Item 6: R-012
- **Title:** R-012 Infrastructure Refactoring
- **Status:** Not Started
- **Priority:** Low
- **Category:** Infrastructure
- **Assignee:** (Leave empty - orphaned item)
- **Due Date:** 2026-04-01
- **Description:** Refactor payment processing pipeline

---

## Step 2: Verify Notion Columns (2 min)

**Required columns in your database:**
- ✅ Title (title)
- ✅ Status (select: Not Started, In Progress, Blocked, Done)
- ✅ Priority (select: Low, Medium, High, Urgent)
- ✅ Category (select: Technical, Integration, Regulatory, Documentation, Infrastructure)
- ✅ Assignee (person)
- ✅ Due Date (date)
- ✅ Description (text)
- ✅ Remarks (text) - For provenance trails

**If missing, add them now in Notion!**

---

## Step 3: Test Basic Connectivity (3 min)

### Test 1: Query Items
**In #agentura-pm-demo:**
```
@pm-bot gold: what items are in progress?
```

**Expected:** Shows E-005 and P-042

---

### Test 2: Query Overdue
```
@pm-bot gold: what's overdue?
```

**Expected:** Shows A-007 (due today)

---

### Test 3: Query Blocked
```
@pm-bot gold: show me blocked items
```

**Expected:** Shows E-010

---

## Step 4: Run Demo Sequence (20 min)

Follow the script in **END_TO_END_DEMO.md**

### Quick Demo Sequence:

**1. Morning Briefing (2 min)**
```
@pm-bot gold: morning briefing
```

**2. Pre-Meeting Prep (2 min)**
```
@pm-bot gold: prep for partner sync
```

**3. Post-Meeting Update (5 min)**
```
@pm-bot gold update:

Meeting: Partner Sync (March 14, 2026)

Updates:
- E-010 can proceed, sandbox credentials received
- A-007 documentation is complete
- New action: Alice to test sandbox by March 17
- Performance issues seem critical
- Infrastructure work seems high priority
```

**Expected:** Factual auto-commits, interpretive prompts for approval

**4. Quick Status Update (1 min)**
```
@pm-bot gold: E-005 is done
```

**Expected:** Auto-commits (factual)

**5. Health Check (2 min)**
```
@pm-bot gold: heartbeat
```

**Expected:** Shows orphaned item (R-012), health status

**6. Project Dashboard (2 min)**
```
@pm-bot gold: project status
```

**Expected:** Velocity, team workload, burn-down

**7. Multi-Source Sync (3 min)**
```
@pm-bot gold: sync from slack (last 24h)
```

**Expected:** Scans channel, extracts updates

**8. Channel Digest (2 min)**
```
@pm-bot gold: digest this channel from today
```

**Expected:** Summary of discussions

---

## Step 5: Verify Provenance (5 min)

**Go back to Notion:** https://www.notion.so/104d569f356e4ce28b130da249a0c9cc

**Check Remarks field for:**
- ✅ `[via @you, slack 2026-03-14, factual]`
- ✅ `[via @you, granola 2026-03-14, interpretive - approved by @you]`

---

## Troubleshooting

### Issue: "Database is empty"
**Fix:** Add the 6 test items manually in Notion (Step 1)

### Issue: "No items found"
**Fix:** Check Notion DB ID in config matches: `104d569f356e4ce28b130da249a0c9cc`

### Issue: Approval buttons don't work (emoji only)
**Workaround:** Reply with text: `approve all`

### Issue: Bot doesn't respond
**Fix:**
1. Check bot is in channel: `/invite @pm-bot`
2. Check executor logs:
   ```bash
   kubectl logs deployment/executor -n agentura-system --tail=50
   ```

---

## Success Criteria

After completing demo, verify:

- [ ] 6 test items in Notion
- [ ] All queries return results
- [ ] Factual updates auto-commit
- [ ] Interpretive updates prompt for approval
- [ ] Provenance trails appear in Remarks
- [ ] Health check shows orphaned item
- [ ] Project status shows velocity
- [ ] Channel digest works

---

## Full Demo Script

See **END_TO_END_DEMO.md** for complete week-long scenario covering all 18 skills.

---

**Ready to run the demo!** 🚀

**Start with Step 1: Add test data to Notion, then try Test 1.**
