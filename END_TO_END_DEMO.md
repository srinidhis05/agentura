# PM Agent End-to-End Demo Script
**Based on:** GE Tracker PRD + Meeting Notes (Neha/Srinidhi/Ashutosh)

**Project:** Gold (Digital Gold)
**Channel:** #agentura-pm-demo
**Date:** March 14, 2026

---

## Demo Scenario: Typical Week in the Life of PM Bot

### Day 1 (Monday): Week Start

#### 9:00 AM - Morning Briefing (Auto-posted by cron)
```
☀️ Gold Daily Briefing (March 14, 2026)

📋 Due Today (2):
  • E-005: Login Bug Fix (Alice)
  • A-007: Partner Documentation Update (Bob)

🚧 Blockers (1):
  • E-010: WealthKernel API Integration - Waiting on partner credentials

📅 Meetings Today:
  • 2pm: Weekly Partner Sync with WealthKernel

⏰ Overdue (0):
  None - great job team!

🔗 Action Tracker: https://notion.so/104d569f356e4ce28b130da249a0c9cc
```

---

#### 10:00 AM - Action Tracker Alert (Auto-posted by cron)
```
⚠️ Action Tracker Alert - Gold Project

🚧 Blocked Items (1):
  • E-010: WealthKernel API Integration
    Status: Blocked
    Assignee: Bob
    Blocker: Waiting on partner sandbox credentials
    Duration: 2 days

📝 Orphaned Items (1):
  • R-012: Infrastructure Refactoring
    No assignee assigned
    Due: April 1, 2026

💡 Suggested Actions:
  • Follow up with WealthKernel on E-010
  • Assign R-012 to an owner
```

---

#### 11:00 AM - User Query
**User (Ashutosh) in #agentura-pm-demo:**
```
@pm-bot gold: what items are in progress?
```

**Bot Response:**
```
📋 Gold Project - Items In Progress (2)

1. E-005: Login Bug Fix
   • Assignee: Alice
   • Priority: 🔴 High
   • Due: March 15 (tomorrow)
   • Status: In Progress
   • Description: Users unable to login with Google OAuth

2. P-042: DFSA Compliance Review
   • Assignee: Alice
   • Priority: 🔴 High
   • Due: March 18 (4 days)
   • Status: In Progress
   • Description: Regulatory approval for digital gold offering

🔗 View in Notion: https://notion.so/104d569f356e4ce28b130da249a0c9cc
```

---

#### 1:00 PM - Pre-Meeting Briefing
**User:**
```
@pm-bot gold: prep for WealthKernel partner sync
```

**Bot Response:**
```
📝 Meeting Briefing: WealthKernel Partner Sync
📅 Today, 2:00 PM

## Context
Recent activity with WealthKernel:
• E-010 API Integration is blocked waiting on sandbox credentials
• Last discussion: March 10 (4 days ago)
• Key contact: Sarah from WealthKernel

## Action Items to Discuss
1. ✅ A-007: Partner docs updated (Bob completed March 14)
2. ⏳ E-010: Need sandbox credentials to proceed
3. 📅 Review integration timeline

## Questions to Ask
• When will sandbox credentials be available?
• Any changes to API endpoints since last version?
• Testing timeline expectations?

## Blockers to Raise
• E-010 blocked for 2 days - team waiting on credentials

## Previous Decisions
• Agreed to use WealthKernel's v2 API (from March 10 meeting)
• Target integration completion: March 25

📎 Related Items in Notion:
  • E-010: WealthKernel API Integration
  • A-007: Partner Documentation Update
```

---

#### 3:00 PM - Post-Meeting Update
**User posts meeting notes:**
```
@pm-bot gold update:

Meeting: WealthKernel Partner Sync (March 14, 2026)
Attendees: Ashutosh, Bob, Sarah (WealthKernel)

Updates:
- Sarah confirmed sandbox credentials will be sent by EOD today
- E-010 API integration can proceed once credentials received
- Bob completed the partner documentation - Sarah reviewed and approved
- New action: Alice to test sandbox environment by March 17
- Performance issues in staging environment seem critical
- Team discussed infrastructure refactoring - seems like high priority work
- Decided to move compliance review deadline to March 20
```

**Bot Response:**
```
✅ Auto-committed (factual):
  • E-010 status → In Progress (explicit: "can proceed")
  • A-007 status → Done (explicit: "completed")
  • P-042 due date → March 20, 2026 (explicit: "move deadline to March 20")
  • A-015 created: "Alice to test sandbox environment" (due: March 17, owner: Alice)

⚠️ Needs approval (interpretive):
  1. Performance issues → Priority: High
     Reasoning: Inferred from "seem critical" (strategic language)

  2. Infrastructure refactoring → Priority: High
     Reasoning: Inferred from "seems like high priority" (judgment call)

Which interpretive changes should be committed?

[Approve All] [Approve 1] [Approve 2] [Reject All]
```

**User clicks:** `[Approve All]`

**Bot confirms:**
```
✅ Changes committed to Notion:

Factual (4 items):
  • E-010 status → In Progress
    Provenance: [via @ashutosh, granola 2026-03-14, factual]
  • A-007 status → Done
    Provenance: [via @ashutosh, granola 2026-03-14, factual]
  • P-042 due date → 2026-03-20
    Provenance: [via @ashutosh, granola 2026-03-14, factual]
  • A-015 created: "Alice to test sandbox"
    Provenance: [via @ashutosh, granola 2026-03-14, factual]

Interpretive (2 items - approved):
  • Performance issues priority → High
    Provenance: [via @ashutosh, granola 2026-03-14, interpretive - approved by @ashutosh]
  • Infrastructure refactoring priority → High
    Provenance: [via @ashutosh, granola 2026-03-14, interpretive - approved by @ashutosh]

🔗 View updates: https://notion.so/104d569f356e4ce28b130da249a0c9cc
```

---

#### 5:00 PM - Channel Digest (Auto-posted by cron)
```
📊 #agentura-pm-demo Channel Digest (March 14, 2026)

Key Discussions Today:
• WealthKernel credentials expected EOD
• E-010 unblocked - can proceed with integration
• Performance issues flagged as critical

Decisions Made:
• P-042 deadline extended to March 20
• Alice to test sandbox by March 17

Action Items Created:
• A-015: Alice to test sandbox environment (due: March 17)

Team Activity:
• Most active: @ashutosh (3 messages)
• @bob completed A-007 documentation

🔗 Notion updates: 6 items modified today
```

---

#### 6:00 PM - End of Day Wrap (Auto-posted by cron)
```
🌙 Gold Daily Wrap (March 14, 2026)

✅ Completed Today (1):
  • A-007: Partner Documentation Update (Bob)

📈 Progress Made (2):
  • E-010: Unblocked - credentials incoming
  • P-042: Deadline adjusted to March 20

🚧 Still Blocked (0):
  None - E-010 was unblocked!

📅 Tomorrow's Focus (March 15):
  • E-005: Login Bug Fix (due tomorrow - Alice)
  • Test WealthKernel sandbox when credentials arrive

🎯 Team Velocity:
  • Completed this week: 1 item
  • In progress: 3 items
  • On track for weekly goal

💪 Great progress today - E-010 unblocked!
```

---

### Day 2 (Tuesday): Mid-Week Operations

#### 9:00 AM - Morning Briefing
```
☀️ Gold Daily Briefing (March 15, 2026)

📋 Due Today (1):
  • E-005: Login Bug Fix (Alice) ⚠️

🔥 High Priority (3):
  • E-005: Login Bug (due today)
  • E-010: WealthKernel Integration (in progress)
  • P-042: DFSA Compliance (due March 18)

📅 Meetings Today:
  None scheduled

💡 Reminder:
  • A-015 sandbox testing due in 2 days (Alice)
```

---

#### 10:30 AM - Quick Status Update
**User (Alice) in Slack:**
```
E-005 is done, pushed to production
```

**Bot detects (via triage → notion-sync):**
```
✅ Updated E-005: status → Done

Provenance: [via @alice, slack 2026-03-15, factual]

🎉 Great work Alice!
```

---

#### 2:00 PM - User Query About Blockers
**User:**
```
@pm-bot gold: what's blocking us?
```

**Bot Response:**
```
🚧 Gold Project - Current Blockers (0)

Good news! No items are currently blocked.

Recent resolution:
  • E-010: Was blocked, unblocked yesterday (March 14)
    Unblocked by: Sandbox credentials received

⚠️ Potential Risks:
  • A-015: Sandbox testing due in 2 days (Alice)
    Risk: Could become blocker if testing reveals issues

📊 Overall Health: 🟢 Green (no active blockers)
```

---

#### 4:00 PM - Multi-Source Sync
**User:**
```
@pm-bot gold: sync from slack and meetings (last 2 days)
```

**Bot Response:**
```
🔄 Syncing Gold project from multiple sources...

Sources scanned:
  ✅ Slack #agentura-pm-demo: 12 messages (March 14-15)
  ✅ Granola meetings: 1 meeting found (WealthKernel Partner Sync)
  ⏭️ Gmail: No partner emails found

Extracted 5 updates:
  ✅ Auto-committed (4 factual):
    • E-005 status → Done (Alice, Slack)
    • E-010 status → In Progress (meeting)
    • A-007 status → Done (meeting)
    • P-042 due date → March 20 (meeting)

  ⚠️ Needed approval (1 interpretive):
    • Infrastructure priority → High (already approved)

Deduplication:
  • Merged 2 duplicate mentions of E-010 across sources
  • Merged 1 duplicate mention of A-007

✅ Notion updated with 5 changes
📊 Provenance trails added to all items
🔗 View: https://notion.so/104d569f356e4ce28b130da249a0c9cc
```

---

### Day 3 (Wednesday): Health Checks

#### 11:00 AM - System Heartbeat
**User:**
```
@pm-bot gold: heartbeat
```

**Bot Response:**
```
💓 Gold Project Health Check

Overall Status: 🟡 Yellow (1 warning)

✅ Healthy Signals:
  • No blocked items
  • All meetings processed (last 7 days)
  • Slack activity: Normal
  • 80% of items have assignees

⚠️ Warnings:
  • 1 orphaned item: R-012 (no assignee)
  • 1 item overdue: E-015 (due March 10, still "Not Started")

📊 Data Quality:
  • Items with category: 100%
  • Items with priority: 100%
  • Items with provenance: 83%

🔍 Falling Through Cracks:
  • R-012: Created 5 days ago, no owner assigned
  • Consider: Assign R-012 before it becomes urgent

💡 Recommended Actions:
  1. Assign R-012 to a team member
  2. Update or close E-015 (stale item)
```

---

#### 2:00 PM - Project Status Dashboard
**User:**
```
@pm-bot gold: project status
```

**Bot Response:**
```
📊 Gold Project Status Dashboard

Overall Health: 🟢 Green

📈 Velocity (Last 7 Days):
  • Completed: 2 items (A-007, E-005)
  • Started: 1 item (E-010)
  • Velocity: 2 items/week

🎯 Current Sprint (6 items active):
  Status breakdown:
    • ✅ Done: 2 items (33%)
    • 🔄 In Progress: 3 items (50%)
    • 🚧 Blocked: 0 items (0%)
    • ⏸️ Not Started: 1 item (17%)

👥 Team Workload:
  • Alice: 2 items (1 in progress, 1 upcoming)
  • Bob: 1 item (completed)
  • Carol: 1 item (not started)
  • Unassigned: 1 item ⚠️

🔴 High Priority Items (3):
  • P-042: DFSA Compliance (Alice, due March 18)
  • E-010: WealthKernel Integration (Bob, due March 20)
  • Infrastructure: Performance fixes (Carol, due March 25)

🏆 Top Contributors This Week:
  1. Alice (2 items completed/in-progress)
  2. Bob (1 item completed)

⏰ Upcoming Deadlines:
  • March 17: A-015 (Sandbox testing)
  • March 18: P-042 (Compliance review)
  • March 20: E-010 (API integration)

📊 Burn-down Trend: ↗️ On track
```

---

### Day 5 (Friday): Week End

#### 9:00 AM - Morning Briefing
```
☀️ Gold Daily Briefing (March 18, 2026)

📋 Due Today (1):
  • P-042: DFSA Compliance Review (Alice)

🎉 Week Progress:
  • Completed: 3 items
  • On track: 4 items
  • At risk: 0 items

📅 No meetings today

🌟 Team is on track for weekly goals!
```

---

### Monday (Week 2): Weekly Digest

#### 9:00 AM - Weekly Digest (Auto-posted by cron)
```
📊 Gold Weekly Digest (March 14-18, 2026)

🎉 Completed This Week (3):
  • A-007: Partner Documentation (Bob)
  • E-005: Login Bug Fix (Alice)
  • P-042: DFSA Compliance Review (Alice)

📈 Key Accomplishments:
  • WealthKernel integration unblocked
  • Compliance review completed on time
  • Zero active blockers by week end

🚀 Started This Week (2):
  • E-010: WealthKernel API Integration
  • A-015: Sandbox testing

✨ Highlights:
  • Team velocity: 3 items/week (↑ 50% vs last week)
  • Alice: 2 completions (top contributor)
  • Zero items missed deadlines

📅 Next Week Priorities:
  • Complete E-010 (WealthKernel integration)
  • Test sandbox environment
  • Address infrastructure refactoring

🎯 Sprint Health: 🟢 Green
💪 Great week team! Keep it up!
```

---

## Feature Coverage Matrix

| Feature | Demonstrated | When |
|---------|--------------|------|
| **daily-briefing** | ✅ | Every 9am |
| **action-tracker** | ✅ | Every 10am |
| **channel-digest** | ✅ | Every 5pm |
| **daily-wrap** | ✅ | Every 6pm |
| **weekly-digest** | ✅ | Monday 9am |
| **pm-query** | ✅ | "what items are in progress?" |
| **meeting-prep** | ✅ | "prep for WealthKernel sync" |
| **meeting-update** | ✅ | Post-meeting notes processing |
| **notion-sync** | ✅ | Multi-source sync + auto-commit |
| **triage** | ✅ | Automatic routing (background) |
| **pm-heartbeat** | ✅ | "heartbeat" health check |
| **project-status** | ✅ | "project status" dashboard |
| **meeting-scan** | ✅ | Find unprocessed meetings |
| **context-refresh** | ⏭️ | Background maintenance |
| **project-setup** | ⏭️ | One-time initialization |
| **task-form-opener** | ⏭️ | Hybrid workflow (next phase) |
| **task-creator** | ⏭️ | Hybrid workflow (next phase) |
| **intake** | ✅ | Universal routing (background) |

---

## Classification Examples from Demo

### ✅ Factual (Auto-committed)
- "E-010 can proceed" → Status change (explicit)
- "Bob completed documentation" → Status done (explicit verb)
- "Move deadline to March 20" → Date change (explicit)
- "Alice to test by March 17" → Action item (verbatim)
- "E-005 is done" → Status done (explicit)

### ⚠️ Interpretive (Needed approval)
- "Performance issues seem critical" → Priority (strategic language)
- "Seems like high priority work" → Priority (judgment call)

---

## Provenance Trail Examples

### Factual Sources
```
[via @ashutosh, granola 2026-03-14, factual]
[via @alice, slack 2026-03-15, factual]
[via @bob, email 2026-03-12, factual]
```

### Interpretive (After Approval)
```
[via @ashutosh, granola 2026-03-14, interpretive - approved by @ashutosh]
```

---

## Key Workflows Demonstrated

1. ✅ **Morning Workflow**: Briefing → Action tracker → Team alignment
2. ✅ **Meeting Workflow**: Prep → Attend → Process notes → Approval flow → Commit
3. ✅ **Update Workflow**: Quick Slack update → Auto-detected → Auto-committed
4. ✅ **Query Workflow**: Natural language question → Semantic search → Answer
5. ✅ **Health Workflow**: Heartbeat → Status dashboard → Identify issues
6. ✅ **End of Day**: Channel digest → Daily wrap → Team summary
7. ✅ **Week Review**: Weekly digest → Velocity tracking → Next week planning

---

## Success Metrics Achieved

| Metric | Target | Actual |
|--------|--------|--------|
| **Factual auto-commit rate** | >80% | 80% (4/5 changes) |
| **Classification accuracy** | >90% | 100% (all correct) |
| **Notion freshness** | <24h | <1h (real-time updates) |
| **Provenance coverage** | 100% | 100% (all items tagged) |
| **Response time** | <30 sec | <5 sec (avg) |
| **Zero wrong auto-commits** | 0 | 0 ✅ |

---

**This demo covers the complete GE Tracker vision from the PRD!** 🚀
