# Product Note: PM Agent — Hybrid Workflows + GE Tracker

**Ship Date:** March 2026
**Scope:** PM domain combining Asana-style workflows with intelligent automation
**Team:** Global Equities (pilot) → expand to Gold, Remittance, Unify

---

## What We're Building

A **Slack-native PM agent** that combines:
- ✅ **Asana-style task creation** (forms, not parsing)
- ✅ **Intelligent intake** (processes meeting notes, status updates)
- ✅ **Smart approval flows** (factual auto-commits, interpretive asks)
- ✅ **Notion as source of truth** (always current, never stale)
- ✅ **Works across projects** (one bot, multiple teams)

---

## The Problem Today

### Pain Point #1: Task Creation is Slow
```
Current: Open ClickUp → New Task → Fill fields → Save
Time: 2+ minutes
Errors: Typos, wrong project, missing fields
```

### Pain Point #2: Notion Gets Stale
```
Current: Manual updates after every meeting
Result: Notion 2-3 days behind
Impact: Team doesn't trust it as source of truth
```

### Pain Point #3: Context Switching
```
Current: Slack → ClickUp → Notion → Email → Slack
Time: 10+ switches per day
Cost: 45-60 min/day on PM admin
```

---

## The Solution

### 1. Hybrid Task Creation (Like Asana)

**Three ways to create a task:**

```
Method 1 (Natural Language):
  @pm-bot create task
      ↓
  Modal opens with form

Method 2 (Power User):
  Press ⚡ → "Create Task"
      ↓
  1-click → modal

Method 3 (Contextual):
  Right-click message → "Create task from this"
      ↓
  Pre-filled with message content
```

**Form validates everything:**
- Title (required)
- Project (dropdown - Gold, Remittance, Unify, GE)
- Assignee (user picker - no typos)
- Priority (dropdown - Urgent/High/Medium/Low)
- Due Date (date picker - no "next Friday" ambiguity)

**Result:**
```
✅ Task created: Fix login bug

📋 Details:
  • Project: Gold
  • Assignee: @alice
  • Priority: High
  • Due: March 20, 2026

🔗 ClickUp: https://app.clickup.com/t/abc123

Time: < 30 seconds (was 2+ minutes)
```

---

### 2. Intelligent Intake (Like GE Tracker)

The bot watches your channel and processes:

| You Post | Bot Does |
|----------|----------|
| **Meeting notes** | Extracts action items → creates tasks → updates Notion |
| **Status update** ("E5 done") | Updates tracker, notifies team |
| **Question** ("What's the status?") | Searches Notion, replies in thread |
| **Granola link** | Fetches transcript, processes decisions |
| **Random chat** | Ignores (doesn't pollute channel) |

**Smart classification:**

```
Input: "E5 is done. Varun to setup sandbox by March 21."

Bot analyzes:
  "E5 is done" → FACTUAL (explicit status)
  "Varun to setup sandbox by March 21" → FACTUAL (verbatim action item)

Auto-commits to Notion ✅
No approval needed
```

---

### 3. Approval Flows (Trust + Speed)

**Rule:** Factual changes auto-commit. Interpretive changes ask first.

```
Post meeting notes → Bot extracts 7 changes

✅ Auto-committed (factual):
1. E5 status → Done
2. R12 remarks → "DFSA response received"
3. New task: E33 — Varun, sandbox, March 21

⏳ Need approval (interpretive):
4. Context: "GTN is now primary integration path"
5. New task (inferred): P25 — Review GTN API docs

Reply: `approve all` or `approve 4,5` or `reject 5`
```

**Why this works:**
- 80% of changes are factual → auto-commit (no friction)
- 20% interpretive → quick approval (builds trust)
- Default-safe: when uncertain, bot asks

---

### 4. Daily Rhythms

**Morning Briefing (8 AM, weekdays):**
```
🌅 Morning Briefing — March 14, 2026 (Monday)

📅 This Week:
• @alice: E5, E12 (due Tue), P3 (due Thu)
• @bob: R7 (due Wed)

⚠️ Overdue (2):
• E9 — API integration (Mar 10, @alice)
• R4 — License filing (Mar 12, @varun)

🎯 Focus: Launch prep for Phase 1 (March 21)
```

**Daily Digest (6 PM, to Admins):**
```
📋 Daily Digest

Auto-committed: 8 changes
  • Varun: E5 → Done, E12 → In Progress
  • Parth: R12 updated

Approved by Contributors: 3 changes
  • Varun approved: Context update

Expired: 1 change (timed out)
```

---

## User Experience Highlights

### Before (Manual)

```
10:00 AM: Meeting with Alpaca
10:30 AM: Open Notion, write summary
10:45 AM: Open ClickUp, create 3 tasks
11:00 AM: Slack team with updates
11:15 AM: Update project tracker
11:20 AM: Finally done (80 min later)
```

### After (Automated)

```
10:00 AM: Meeting with Alpaca
10:30 AM: Paste Granola link to Slack

Bot:
  ✅ 3 tasks created in ClickUp
  ✅ Notion updated with summary
  ✅ Team notified in thread
  ⏳ 2 strategic changes need approval

You: `approve all`

Bot: ✅ All changes committed

10:32 AM: Done (2 min total)
```

**Time saved: 78 minutes → usable for actual work**

---

## Architecture (Non-Technical Version)

```
         NOTION
   (Source of Truth)
           ↓
    ┌──────┴──────┐
    ↓             ↓
SLACK BOT    LOCAL PUSH
    │             │
    ↓             ↓
  TEAM    PERSONAL DATA
         (Gmail, Granola)
```

**Slack Bot (team-facing):**
- Handles public data (meeting notes in channel, status updates)
- Creates tasks, answers questions
- Posts morning briefings

**Local Push (personal):**
- Ashutosh runs on his machine
- Scans his Gmail + Granola
- Filters for GE-relevant content
- Pushes to Notion with approval

**Everything flows to Notion → single source of truth**

---

## Permissions Model

| Role | Who | Can Do |
|------|-----|--------|
| **Admin** | Ashutosh, Varun S, Chandrakanth | All mutations, approve any change |
| **Contributor** | Varun Y, Parth, Himanshu, Anurag | Status updates, approve own changes |
| **Observer** | Others | Ask questions, post content |

**New user detection:** Bot DMs Admin when unknown user posts: "New user @someone. Add as Contributor?"

---

## Rollout Plan

### Week 1: Hybrid Pattern (Immediate Value)
- Ship "Create Task" workflow
- Test with 2-3 power users
- **Success metric:** 10+ tasks created via Slack

### Week 2: GE Tracker Core
- Add intake + approval flows
- Enable meeting notes processing
- **Success metric:** Notion <24h stale

### Week 3: Scheduled Jobs
- Morning briefing
- Context refresh
- Daily digest
- **Success metric:** Team uses briefing daily

### Week 4: Polish + Expand
- Edge cases, error handling
- Onboard full GE team (7 people)
- **Success metric:** 50% weekly active usage

### Month 2: Expand to Other Projects
- Gold, Remittance, Unify
- Same skills, different project configs
- **Success metric:** 80% of PM team uses daily

---

## Success Metrics

| Metric | Baseline | Target (Month 1) | ROI |
|--------|----------|------------------|-----|
| **Task creation** | 2 min | < 30 sec | 1.5 min saved × 20 tasks/week = **30 min/week** |
| **Notion freshness** | Manual | < 24h stale | Team trusts it |
| **Context switches** | 10/day | 2/day | **80% reduction** |
| **Admin time** | 60 min/day | < 15 min/day | **45 min/day saved** |
| **Adoption** | 0% | 50%+ active | Half the team uses it |

**Annual ROI (10-person PM team):**
- 45 min/day saved × 10 people × 250 days = **1,875 hours/year**
- = 47 weeks of productivity unlocked
- = **$150K+ value** (at $80/hr blended rate)

---

## Competitive Positioning

### vs. Asana Slack Bot

**What Asana does:**
- ✅ Task creation from Slack
- ✅ Search tasks

**What our bot does better:**
- ✅ **Meeting notes → tasks** (auto-extraction)
- ✅ **Project setup** (Notion + ClickUp + Slack in one flow)
- ✅ **AI-powered triage** (natural language routing)
- ✅ **Approval flows** (factual vs interpretive)
- ✅ **Custom domain skills** (PM, ECM, Infra)

### vs. Manual Process

| Task | Manual | PM Bot | Savings |
|------|--------|--------|---------|
| Create task | 2 min | 30 sec | 75% |
| Update Notion | 15 min | Auto | 100% |
| Morning status | 10 min | Auto | 100% |
| Answer "what's blocked?" | Search 5 min | Ask bot 10 sec | 98% |

---

## What's Next

### Immediate (Week 1)
- ✅ Ship "Create Task" workflow
- 🚧 Test with power users
- 📝 Gather feedback

### Near-term (Month 1)
- Meeting notes processing
- Morning briefing
- Daily digest

### Future (Month 2+)
- Weekly planning workflow
- Approval flows (deploy, expense)
- Multi-step wizards (project setup → onboarding → first sprint)
- AI pre-filling (analyze message → suggest task fields)

---

## FAQ

**Q: Do I have to use forms? Can I still type commands?**
A: Both work! Type `@pm-bot create task` if you prefer natural language. Form opens to prevent errors.

**Q: What if the bot makes a mistake?**
A: Interpretive changes always ask for approval. Factual changes auto-commit but you can revert via Notion history. Daily digest shows all changes.

**Q: Can I use this for my project (not GE)?**
A: Yes! Same bot, different project config. Gold, Remittance, Unify coming in Month 2.

**Q: What about personal data (my emails)?**
A: Server bot only sees public Slack data. Personal data (Gmail, Granola) stays on your machine, you control what gets pushed.

**Q: Will this slow me down?**
A: No. Forms take <30 sec. Manual ClickUp takes 2+ min. You save 1.5 min per task.

**Q: What if I'm offline / on vacation?**
A: Bot continues running. Morning briefings, auto-commits. When you're back, review daily digests (DM from bot).

---

## Key Principles (From Meeting)

**Neha:** "I want control. I don't want messages going without my approval till I feel confident."
- ✅ Factual auto-commits (builds trust with no-brainer changes)
- ⏳ Interpretive asks first (you approve strategic changes)

**Ashutosh:** "Some messages tactical, I'm fine auto. Any external or interpretive, I want approval."
- ✅ Classification contract (factual vs interpretive)
- ✅ Provenance trail (who changed what, when)

**Srinidhi:** "Notion as source of truth is good. Others can be triggers with approval."
- ✅ Notion is the authority
- ✅ Slack/Gmail/Granola are inputs with approval gates

---

## Vision

**Today:** PM work is manual, fragmented across tools, time-consuming.

**Future:** PM agent handles the busywork:
- ✅ Creates tasks from conversations
- ✅ Keeps Notion current
- ✅ Answers questions instantly
- ✅ Posts daily summaries
- ✅ Nudges on deadlines

**You focus on:** Strategy, unblocking team, stakeholder communication.

**Tagline:** "Your PM teammate that never sleeps."

---

## Team

- **Product:** Neha (requirements, UX feedback)
- **Engineering:** Srinidhi (Agentura platform)
- **Pilot User:** Ashutosh (GE project, daily feedback)
- **Implementation:** Claude Code (skill building)

**Timeline:** Ship Phase 1 by end of Week 1.

**Contact:** @srinidhi for technical questions, @ashutosh for pilot feedback.

---

**Status:** Ready to build. Awaiting approval to start Phase 1.
