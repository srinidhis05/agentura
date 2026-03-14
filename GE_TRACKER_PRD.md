# GE Tracker — Product Requirements Document

> **Version:** 1.6
> **Date:** March 13, 2026
> **Owner:** Ashutosh Rungta
> **Status:** Draft — reviewed, pending final approval before build

---

## 1. Vision

A Slack-native project management bot for the Global Equities team that maintains Notion as the single source of truth. The bot acts as a persistent, intelligent PM — ingesting updates from any source, keeping artifacts current, answering questions, and nudging the team on deadlines.

**Core promise:** No one on the team should ever need to manually update Notion or wonder "what's the latest on X?" The bot knows, because it's always watching.

---

## 2. Architecture

### Two-Tier System

```
┌─────────────────────────────────────────────────────┐
│                    NOTION (Source of Truth)          │
│  Action Tracker · PRD · Roadmap · Context Pages     │
│  Meeting Archive · Partner Notes · Q&A Trackers     │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
        ┌──────▼──────┐        ┌──────▼──────┐
        │  SLACK BOT  │        │ LOCAL INST. │
        │  (Agentura) │        │ (Claude Code)│
        │             │        │              │
        │ Notion token│        │ Gmail MCP    │
        │ Slack token │        │ Granola MCP  │
        │ No personal │        │ Notion MCP   │
        │ data access │        │ Slack MCP    │
        └──────┬──────┘        └──────┬───────┘
               │                      │
        ┌──────▼──────────────────────▼───────┐
        │        #global-equities-team         │
        │  Everyone interacts here             │
        └─────────────────────────────────────┘
```

### Slack Bot (Server — Agentura)

- **Runtime:** Agentura platform — deployed as `pm/` domain (agency/pm/). Agentura handles all Slack infrastructure: Socket Mode connection, message routing, threading, ack reactions, and Claude CLI execution.
- **AI backend:** Claude CLI invoked by Agentura executor per skill. Each inbound message is routed to the appropriate SKILL.md file.
- **Access:** Notion integration token (scoped to GE workspace pages), Slack bot token — both managed as Agentura env vars.
- **No access to:** Personal email, Granola, Google Sheets, or any personal account
- **Scheduled tasks:** Agentura Heartbeat files (cron triggers defined in `agentura.config.yaml`)
- **We do NOT build:** Slack bot infrastructure (Socket Mode, intent routing, message formatting, Dockerfile). Agentura provides all of this. We build skills only.

### Local Instances (Ashutosh + Senior PM)

- **Runtime:** Claude Code on personal machine
- **Access:** Full personal MCPs — Gmail, Granola, Notion, Slack
- **Purpose:** Scan personal sources (Gmail, Granola) for GE-relevant content → push to Notion → trigger bot context refresh
- **Permission setup:** A one-time setup skill configures `settings.json` so the local GE skills run without per-action permission prompts (approved tools pre-whitelisted)

### Everyone Else (Varun, Parth, Himanshu, etc.)

- **Interact via Slack only.** Paste links, transcripts, status updates, ask questions.
- **No setup required.** The bot processes whatever they post.

---

## 3. Bot Capabilities

### 3.1 Intake — Processing Inbound Content

When a message arrives in `#global-equities-team`, the bot classifies it:

| Content Type | Detection | Bot Action |
|---|---|---|
| **Question** | Ends with `?`, or starts with "what/when/who/where/how/status of" | Q&A flow: search Notion, compose answer, reply in thread |
| **Granola link** | URL contains `granola.ai` or `granola.so` | Attempt to fetch via link. If inaccessible, ask poster to paste transcript |
| **Google Sheets link** | URL contains `docs.google.com/spreadsheets` | Attempt to read. If inaccessible, ask poster to make it viewable or paste content |
| **Meeting notes / transcript** | Long-form text with meeting indicators (participants, agenda, action items, timestamps) | Parse → extract facts + action items → run update flow |
| **Status update** | Short message with task references (e.g., "E5 done", "R12 blocked on DFSA") | Parse → extract status changes → auto-commit factual changes to Notion |
| **Zoom summary** | Forwarded Zoom AI Companion email content | Parse → extract decisions + action items → run update flow |
| **File / document** | Attached file | Acknowledge. If processable (text, PDF), extract content. Otherwise ask for paste. |
| **Casual / off-topic** | Does not match above patterns | Ignore. Do not react to every message. |
| **Bot command** | Explicit commands (see 3.2) | Execute the command |

**Intake rules:**
- Always acknowledge with a reaction emoji (e.g., :eyes:) before processing (so the poster knows the bot saw it)
- All extracted facts go through the update flow (Section 3.4)
- Never auto-commit interpretive changes — only factual ones (see Section 5)

**UX behavior contract:**

| Scenario | Bot responds in... | Format |
|---|---|---|
| Command (`status`, `tracker`, etc.) | **Thread** under the command message | Formatted response |
| Question (Q&A) | **Thread** under the question | Answer with source links |
| Intake (meeting notes, status update) | **Thread** under the original message | Processing summary + approval prompt if needed |
| Morning briefing (scheduled) | **Channel** (new top-level message) | Briefing post |
| Error / can't parse | **Thread** under the message | Brief error + suggestion |
| Casual / off-topic | **No response at all** | — |
| Malformed command (e.g., `updat E5 doen`) | **Thread** | "I didn't understand that. Did you mean: `update E5 status done`?" with closest match suggestion |
| Unknown command | **Thread** | "Unknown command. Type `help` for available commands." |

**Principle:** Bot never pollutes the main channel feed. All responses go in threads, except scheduled briefings.

### 3.2 Commands — Explicit Bot Interactions

| Command | What it does |
|---|---|
| `help` | Lists available commands |
| `morning` / `briefing` | Generates and posts the daily briefing (same as scheduled cron, but on-demand) |
| `sync` | Triggers a context file refresh from Notion |
| `status` | Shows current GE state: next milestone, overdue items, blocked items |
| `context` | Returns the latest context file (downloadable for Claude Code use) |
| `tracker` | Shows action tracker summary with counts by status |
| `overdue` | Lists all overdue items with owners |
| `item <ID>` | Shows details for a specific tracker item (e.g., `item E5`) |
| `update <ID> <change>` | Updates a tracker item (e.g., `update E5 status done`) |
| `search <query>` | Searches Notion GE pages for the query |

Commands can be triggered by:
- Direct message in the channel
- @mentioning the bot
- Thread reply to the bot

### 3.3 Q&A — Answering Questions

When someone asks a question:

1. Search relevant Notion pages (action tracker, PRD, roadmap, partner pages, context pages)
2. Search Slack channel history for recent context
3. Compose a concise answer with source links
4. Reply in thread

**Rules:**
- Only use information from Notion and Slack channel history. Never speculate.
- If the answer isn't in any source, say so: *"I don't have information on this. Check with [likely owner based on domain]."*
- Always cite the Notion page or Slack message where the info came from
- Never surface information from outside the GE workspace

### 3.4 Update Flow — Processing Changes into Notion

This is the core flow. Triggered by: intake parsing, explicit commands, local instance push, or scheduled sync.

**Step 1: Extract changes**
- Parse the source content (meeting notes, status update, email, etc.)
- Identify: status changes, new action items, deadline changes, decisions, context updates
- Classify each change as FACTUAL or INTERPRETIVE

**Step 2: Present for approval (if needed)**
- **Factual changes** (status: "not started" → "in progress", verbatim action items, explicit deadline mentions): Auto-commit. No approval needed.
- **Interpretive changes** (strategic conclusions, inferred priorities, suggested new tasks, context file narrative updates): Present in Slack thread for approval before committing.
- The bot posts a summary: "I found X changes. Y auto-committed (factual). Z need your approval:" followed by the list.

**Step 3: Commit to Notion**
- Update action tracker items (status, dates, remarks)
- Create new action tracker items
- Update context pages (PRD, roadmap, partner notes)
- Append to meeting notes archive
- **Provenance:** Every write includes metadata in the Remarks field or a dedicated audit trail:
  - `source_type`: slack_message | granola_link | gmail | zoom_summary | manual_command | local_push
  - `source_ref`: Slack message permalink (ts + channel) or source URL
  - `actor`: Slack user ID of the person who posted the content
  - `committed_at`: ISO timestamp of the write
  - Example remark suffix: `[via @varun, slack msg 2026-03-09, factual]`

**Step 4: Dedupe check**
- Before writing, check if the same `source_ref` has already been processed (search Remarks for the Slack message permalink or source URL)
- If duplicate detected: skip the write, reply "Already processed from [source]"
- This prevents double-commits when the same meeting notes are posted in Slack AND pushed via local instance
- **Known limitation:** `source_ref` matching catches identical sources (same Slack permalink posted twice). It will NOT catch semantically identical updates from different sources (e.g., same meeting captured via Granola link AND manually pasted transcript). For a 7-person team, this is acceptable — rare edge case, easily caught in daily digest review. Semantic deduplication deferred.

**Step 5: Confirm**
- Reply in thread with what was committed
- Tag relevant owners if their items changed

### 3.5 Morning Briefing — Scheduled Daily Post

Runs automatically via cron. Format varies by day:

| Day | Format | Content |
|---|---|---|
| Monday | Weekly overview | All items due this week, grouped by owner. Overdue items. |
| Tue–Thu | Daily | Items due today. Overdue items. |
| Friday | Accountability review | Done this week. Still overdue. Next week preview. |

Posted to `#global-equities-team` with owner @mentions.

### 3.6 Outbound Communications

The bot can draft communications for:
- Meeting follow-ups with external parties
- Action item reminders to team members
- Partner status requests

**MVP behavior (no email integration):**
- Bot drafts the message and presents it in a Slack thread as copy-paste-ready text
- Includes suggested recipients, subject line (for emails), and body
- The human copies and sends from their own email/Slack
- Bot has NO email sending capability — it can only compose text

**Future (if dedicated email configured):**
- If/when `ge-tracker@aspora.com` is set up (see Section 10, Open Items), the bot could send directly
- This is NOT part of MVP. Defer until trust is established with draft-only mode.

**Rules:**
- NEVER auto-send. Always draft and present for approval in Slack thread.
- Draft in the user's voice — concise, professional, direct.
- Human always performs the actual send action.

### 3.7 Task Creation

The bot can create new tasks in the Notion Action Tracker when:
- Meeting notes contain explicit action items
- Someone requests it ("create a task for Varun to set up sandbox by March 21")
- The bot identifies a gap (e.g., a decision was made but no follow-up task exists)

**Rules:**
- Auto-create for explicit, unambiguous action items from meetings (factual)
- Suggest creation (approval required) for inferred tasks
- Always assign an owner and target date
- Use existing ID conventions (E-prefix for Engineering, P for Product, R for Regulatory)

---

## 4. Local Instance Skills

### 4.1 Setup Skill (`/ge-setup`)

Run once per user. Configures Claude Code for frictionless GE operation:

1. Verifies all required MCPs are connected (Gmail, Granola, Notion, Slack)
2. Reports which are missing, with setup instructions
3. Edits `~/.claude/settings.json` to pre-approve GE skill tools:
   - Notion read/write tools
   - Slack read/send tools
   - Gmail read/draft tools
   - Granola read tools
   - File read/edit tools
   - Bash (for timestamp operations only)
4. Confirms setup complete

### 4.2 Local Sync Skill (`/ge-push`)

The primary local skill. Run after meetings or periodically:

1. **Scan sources** (parallel):
   - Granola: meetings since last push timestamp
   - Gmail: GE-relevant emails since last push timestamp
   - (Slack and Notion are handled by the bot directly)

2. **Filter for GE relevance** using keyword matching:
   - Partners: Alpaca, WealthKernel, GTN, Atom Prive, Tradetron, Massive, Quodd, LSEG, IntelliInvest, TradingView, ChartIQ, DriveWealth
   - Topics: Global equities, brokerage, US stocks, DIY investing, DIFC, DFSA, SCA5, FCA, GIFT City, NRI investing
   - People: Team member names

3. **Present summary** — one compact list:
   ```
   Found 3 items since last push (Mar 8, 6:30 PM):

   1. [Granola] Alpaca sync call — Mar 9, 2:00 PM
      → 4 factual changes, 2 need approval
   2. [Gmail] RE: WealthKernel sandbox access — Mar 9, 10:15 AM
      → 1 factual change
   3. [Gmail] DFSA license update from legal — Mar 9, 11:30 AM
      → 1 interpretive change (needs approval)

   Auto-commit 5 factual changes? [Approve / Review each / Skip]
   ```

4. **On approval:** Commits all approved changes to Notion in one batch. Bumps the push timestamp. Posts a summary to `#global-equities-team` via the bot.

**Data governance rules:**
- Only sync content matching GE keyword filters (Section 4.2 keyword list). Everything else is ignored.
- Never sync full email threads — extract only GE-relevant facts (action items, decisions, dates, status changes).
- Skip emails with sensitive labels/subjects: anything containing "HR", "compensation", "personal", "confidential" (case-insensitive).
- Granola transcripts: extract decisions and action items only. Do not copy verbatim transcript to Notion.
- The push summary (Step 3) shows exactly what will be written. Nothing goes to Notion without the user seeing it first.

**Design principle:** One command → one summary → one approval → done. No intermediate permission prompts, no "reading file X..." chatter. The setup skill pre-approves all tools so this flow is silent and fast.

### 4.3 Context Load Skill (`/ge-ref`)

Loads the GE context into the current Claude Code session:

1. Reads the context file (local copy or fetched from Notion)
2. Presents: launch timeline, partnership statuses, open decisions, Notion page index
3. Ends with: "Reference loaded. What are we working on?"

No MCP calls. Static context load for cheap session bootstrapping.

---

## 5. Approval & Permission Rules

### 5.1 Write Permission Model

Not everyone in the channel can mutate Notion. The bot enforces a simple allowlist:

| Role | Who | Can trigger writes? | Can approve interpretive changes? |
|---|---|---|---|
| **Admin** | Ashutosh, Varun S | Yes — all mutations | Yes — any change, any source |
| **Contributor** | Varun Y, Parth, Himanshu, Anurag | Yes — status updates, remarks, new items from meetings | Yes — blanket self-approval for changes from their own posts |
| **Observer** | Roshini, anyone else in channel | No writes. Can ask questions, post content for processing. | No |

> **Note:** Chandrakanth Rukula will be added as a third Admin once onboarded (Slack ID TBD).

**Enforcement:** The bot checks `event.user` against the allowlist before any Notion write. Unknown Slack users are treated as Observers.

**New user detection:** When the bot sees a Slack user not in the allowlist for the first time, it DMs the Admin (Ashutosh) once: *"New user @someone posted in #global-equities-team. They're currently Observer (read-only). Reply `add contributor @someone` to upgrade their role."* The bot tracks which users have been flagged to avoid repeat notifications. This handles the growing team (expected 10–15 people) without manual roster maintenance.

**Contributor self-approval (blanket):** When a Contributor posts content that generates interpretive changes, *they* can approve those changes — including changes that affect shared pages (benchmarking, partner pages, context). No scoping by item ownership — impractical given cross-cutting pages. The poster has context; they approve.

**Admin oversight via daily digest:** Instead of real-time approval, both Admins receive an end-of-day summary of all changes (see Section 5.6). Either Admin can revert any change via Notion version history if needed.

### 5.2 Change Classification Contract

Every extracted change is classified before commit:

```
                    ┌─────────────────────┐
                    │ Extracted change     │
                    └──────┬──────────────┘
                           │
                    ┌──────▼──────────────┐
                    │ Explicit verb +      │
                    │ known entity?        │
                    │ (e.g., "E5 is done") │
                    └──┬───────────┬──────┘
                      YES         NO
                       │           │
                ┌──────▼──┐  ┌────▼─────────────┐
                │ FACTUAL  │  │ Contains judgment, │
                │ → auto   │  │ inference, or      │
                │   commit │  │ strategic language? │
                └──────────┘  └──┬──────────┬─────┘
                                YES         UNCLEAR
                                 │           │
                          ┌──────▼──┐  ┌────▼────────┐
                          │INTERPRET.│  │ UNCERTAIN    │
                          │→ approval│  │ → approval   │
                          │  required│  │   required   │
                          └─────────┘  │ (default-safe)│
                                       └──────────────┘
```

**Classification rules:**

| Signal | Classification | Example |
|---|---|---|
| Explicit status verb ("done", "blocked", "started") + item ID | FACTUAL | "E5 is done" |
| Verbatim quote with assignee + deadline | FACTUAL | "Varun to set up sandbox by March 21" |
| Direct date reference + item | FACTUAL | "R12 deadline moved to April 1" |
| "I think", "seems like", "probably", "should consider" | INTERPRETIVE | "I think we should deprioritize Tradetron" |
| Strategic/priority language ("critical path", "key blocker", "pivot") | INTERPRETIVE | "GTN is now the critical path" |
| Summarization or narrative synthesis | INTERPRETIVE | "Partnership strategy shifted toward..." |
| Ambiguous — could be read either way | UNCERTAIN → treat as INTERPRETIVE | "Alpaca integration is looking tight" |

**Default on ambiguity: always ask.** False positives (asking unnecessarily) are cheap. False negatives (auto-committing wrong changes) break trust.

**Edge case test suite** (must produce consistent classification before Phase 2 gate):

| Input | Correct Classification | Why |
|---|---|---|
| "Varun said E5 is done" | FACTUAL | Reported speech of explicit status — Varun is a Contributor, treat as his statement |
| "Looks blocked on DFSA" | UNCERTAIN → approval | Hedged language ("looks"), no explicit item ID |
| "Move deadline to next Friday" | FACTUAL (with normalization) | Explicit date change. Bot resolves "next Friday" to ISO date and confirms in thread: "Setting Target Date to 2026-03-13. Correct?" |
| "Close this item" | UNCERTAIN → approval | "Close" could mean Done or archived deletion. Bot asks: "Mark as Done or Close/archive?" |
| Meeting transcript: "we should probably..." | INTERPRETIVE | "Should probably" = suggestion, not commitment |
| Same meeting posted in Slack AND pushed via `/ge-push` from Granola | Dedupe if same `source_ref`; otherwise both commit | `source_ref` only catches identical sources (same Slack permalink posted twice). Different sources (Slack message vs Granola link) produce different `source_ref` values and are NOT deduped — see known limitation in Section 3.4 Step 4. Rare for a 7-person team; caught in daily digest review. |
| "Create a task for Varun to do X" (no date) | FACTUAL (partial) | Explicit action item but missing date. Bot creates with owner, flags missing date: "No deadline specified — leaving Target Date empty." |
| "Partnership strategy is shifting toward API-first" | INTERPRETIVE | Narrative synthesis, strategic language |
| "Alpaca confirmed sandbox access on March 8" | FACTUAL | Verbatim factual statement with date |

### 5.3 Approval UX Grammar

When the bot needs approval, it posts in a Slack thread with this format:

```
I found 7 changes from [source]:

✅ Auto-committed (factual):
1. E5 status → Done
2. R12 remarks → "DFSA response received March 8"
3. New task: E33 — Varun to set up sandbox by March 21

⏳ Need approval (interpretive):
4. Context page: "GTN partnership is now the primary integration path"
5. New task (inferred): P25 — Review GTN API docs before next sync

Reply with:
• `approve all` — commit all pending changes
• `approve 4` — commit only item 4
• `approve 4,5` — commit items 4 and 5
• `reject all` — discard all pending changes
• `reject 5` — discard only item 5
• `edit 4 [new text]` — modify item 4 before committing
```

**When a Contributor disagrees with interpretation:**

The bot includes this guidance after every interpretive change list:

```
These changes are based on the bot's interpretation of your input.
If the interpretation is wrong, you can:
• `reject <#>` to discard a specific change
• `edit <#> [corrected text]` to fix the wording (one-shot, not a conversation)
• Or: run this through your local Claude Code session, refine the
  changes there, and paste the exact commit text here as a status update.
  The bot will treat your pasted text as factual and auto-commit it.
```

**Rules:**
- Approval prompt expires after **48 hours**. If no response, bot replies: "Approval timed out (48h). Changes discarded. Re-post to try again." The 48-hour window covers weekends (Friday evening → Sunday evening) and timezone/sleep gaps.
- The person who posted the content can approve their own interpretive changes — they don't need to wait for Admin.
- Either Admin (Ashutosh or Varun S) can approve any change from any source.
- `approve all` is the fast path for trusted batches. Individual approve/reject for fine-grained control.
- Edit is **one-shot**: `edit 4 [new text]` replaces item 4's text and re-presents for approval. No multi-turn conversation.

### 5.4 Conflict Resolution

When the same tracker item is updated from multiple sources:

- **Last write wins** with provenance trail. Notion version history preserves the full audit log.
- If two conflicting updates arrive within 5 minutes of each other (e.g., Slack says "E5 done" and local push says "E5 in progress"), the bot flags the conflict in a thread: "Conflicting updates for E5: [source 1] says Done, [source 2] says In Progress. Which one?" and waits for resolution.
- **Who resolves:** The person who posted the *later* update is asked to resolve (they have the most recent context). Either Admin can also resolve.
- **Timeout:** If unresolved after 48 hours, default to **last-write-wins** (the later update is committed). The conflict is logged in the daily digest with a note: "Auto-resolved: E5 conflict, last-write-wins applied."
- Outside the 5-minute window: later write silently overwrites. Provenance in Remarks shows who changed what and when.

### 5.5 Change Type Matrix

| Change Type | Examples | Auto-commit? |
|---|---|---|
| **Status change (explicit)** | "E5 is done", "R12 blocked on DFSA" | Yes |
| **Date change (explicit)** | "Deadline moved to March 21" | Yes |
| **New task (verbatim from meeting)** | "Varun to set up sandbox by March 21" | Yes |
| **Remarks update (factual)** | "Sandbox access confirmed by Alpaca" | Yes |
| **Context narrative update** | "Partnership strategy shifted toward..." | No — approval required |
| **New task (inferred)** | Bot thinks a task is needed based on discussion | No — approval required |
| **Priority/strategic changes** | "This is now the critical path" | No — approval required |
| **Any outbound communication** | Emails, Slack messages to external parties | No — always draft + approve |
| **Deletion of any kind** | Removing tasks, archiving items | No — always approval required |

**Principle:** If a human said it explicitly, the bot can commit it. If the bot is drawing a conclusion, it asks first.

### 5.6 Daily Change Digest

The bot DMs both Admins (Ashutosh + Varun S) once per day (6:00 PM GST) with a summary of all changes committed that day:

```
📋 GE Tracker — Daily Digest (March 9, 2026)

Auto-committed (factual): 8 changes
  • Varun S: E5 → Done, E12 → In Progress, new task E33
  • Parth: R12 remarks updated, R15 deadline → March 21
  • Bot (cron): context file refreshed

Approved by Contributors (interpretive): 3 changes
  • Varun S approved: Context page update re: GTN partnership
  • Himanshu approved: New inferred task P25

Expired (unapproved): 1 change
  • Anurag's post: inferred task re: Tradetron review (timed out)

Provenance trail in Notion Remarks for all changes above.
To revert any change: open the Notion item → Page History → restore.
```

**Rules:**
- Only sent if there were changes that day. No empty digests.
- Sent to both Admins — either can act on it. Two-person coverage means at least one reviews daily.
- This is Admin's oversight layer — review at your pace, revert if needed.
- Revert is manual via Notion version history (not a bot command). Provenance fields identify exactly which write to look at.

---

## 6. Data Model

### 6.1 Source of Truth: Notion

All GE information lives in Notion under the main GE page (`3091ab62faf58058b94bcd2f0445fe81`).

**Key databases/pages:**

| Asset | Purpose | Data Source ID |
|---|---|---|
| Action Tracker | Task/milestone tracking | `e35529f9-f380-4d18-ba4a-3d08a0e85fb2` |
| PRD | Product requirements | (page in Notion index) |
| Master Launch Plan | Timeline + milestones | (page in Notion index) |
| Partner Pages | Per-partner status + notes | (pages in Notion index) |
| Meeting Notes Archive | Lean meeting summaries | (page in Notion index) |
| Context Page | High-level state summary | (page in Notion index) |

### 6.2 Action Tracker Schema

| Property | API Name | Type | Values |
|---|---|---|---|
| Milestone | `Milestone` | Title | Free text |
| ID | `userDefined:ID` | Text | E1, P12, R30, etc. |
| Category | `Category` | Select | Engineering, Product & Design, Regulatory & Partnerships |
| Sub-Category | `Sub-Category` | Select | Phase 1–4, Alpaca, WealthKernel, GTN, Data Providers, Tradetron, Atom Prive, Charting & MF, Regulatory & Licensing, Other |
| Function | `Function` | Text | Team/role assignment |
| Owner | `Owner` | People | Notion user ID |
| Target Date | `date:Target Date:start` | Date | ISO date |
| Status | `Status` | Select | Not Started, In Progress, Blocked, Done, Closed |
| Sprint | `Sprint` | Select | Pre-Sprint, Sprint 1–6, Testing, Ongoing |
| Remarks | `Remarks` | Text | Free text |

**ID conventions:**
- `E` = Engineering (E1–E32 exist, use E33+)
- `P` = Product & Design (P1–P24 exist, use P25+)
- `R` = Regulatory & Partnerships (R1–R30 exist, use R31+)

### 6.3 Context File (Distribution Artifact)

A markdown file that serves as a portable snapshot of the GE state. NOT the source of truth — derived from Notion.

**Contains:**
- Last updated timestamp
- Launch timeline summary
- Partnership statuses (one line per partner)
- Open decisions
- Notion page index with links
- Team roster with Notion/Slack IDs
- Connector setup instructions

**Updated by:** The bot (after any Notion changes) or the local sync skill.

**Distributed via:** Bot serves it on `context` command in Slack. Anyone can load it into their Claude Code session.

### 6.4 Owner Mappings

| Name | Notion User ID | Slack ID |
|---|---|---|
| Ashutosh | `2c5d872b-594c-815b-9e88-00025eb6e7bc` | U0A2TNJD0BW |
| Varun S | `2b8d872b-594c-81bd-bf18-0002d425d7e7` | U09TRNAHXGF |
| Varun Y | `2dfd872b-594c-81bb-b4c6-0002bb981870` | U0A6RJ3Q2JV |
| Parth | `22cd872b-594c-8100-898b-00020aec6857` | U0332GTH2JH |
| Himanshu | `11fd872b-594c-811b-b4f1-0002a406b559` | U07RPP8FDHQ |
| Anurag | `308d872b-594c-81bc-b38e-0002114a52d0` | U0AFKQ8D17B |
| Roshini | `253d872b-594c-81d6-87d8-0002835258ee` | — |

### 6.5 Notion Scoping Rules

The bot operates on a defined subset of Notion — not the entire workspace. These rules prevent the bot from reading, updating, or referencing pages outside scope.

**Rule 1 — Hard scope to GE parent page.** All bot operations are confined to the Global Equities parent page (`3091ab62faf58058b94bcd2f0445fe81`) and its children. The bot never reads or writes pages outside this tree, even if linked from within GE pages.

**Rule 2 — Archive exclusion.** Pages under the Archive section within the GE parent are excluded by default. The bot does not search, reference, or update archived pages. If a user asks about an archived topic, the bot replies: *"That page is in the Archive. I can look it up if you want — reply `yes` to confirm."* One-time access only; the page does not re-enter regular scope. The bot writes a row to the Pending Interactions database (type: `archive-confirm`, payload: archived page ID) so that the follow-up `yes` reply can be resolved across invocations (see Section 7.1, platform gap #1).

**Rule 3 — Disambiguation.** When a search or update targets a Notion page and multiple pages match (e.g., "Master Launch Plan" exists in both active and archived sections, or similar titles exist), the bot presents a numbered list in the Slack thread:
```
Multiple pages match "Launch Plan":
1. Global Equities — Master Launch Plan (July 1, 2026) [active]
2. Master Launch Plan (archived)
Reply with the number to select.
```
The bot never silently picks one when ambiguous. It writes a row to the Pending Interactions database (type: `disambiguate`, payload: JSON array of candidate page IDs/titles) so that the follow-up number reply can be resolved across invocations (see Section 7.1, platform gap #1).

**Rule 4 — External links.** If someone pastes a Notion link to a page outside the GE parent, the bot reads it for that one operation only (to extract relevant facts). It does NOT add the page to its regular scope, does not monitor it for changes, and does not write to it.

**Rule 5 — Active page registry.** The `notion-page-index.md` reference file maintains the list of in-scope Notion pages with their IDs and titles. The `context-refresh` skill actively rebuilds this registry by scanning the GE parent tree, excluding Archive pages. This prevents stale references to deleted or moved pages.

---

## 7. Slack Bot Technical Design

### 7.1 Agentura Platform Responsibilities

The following are handled entirely by Agentura. We do NOT build these:

- **Slack connection:** Socket Mode, message receiving, ack reactions
- **Message delivery:** Agentura receives inbound Slack messages and delivers them to the configured skill
- **Claude CLI execution:** Agentura executor invokes Claude CLI with the skill prompt + message context
- **Output delivery:** Agentura posts Claude's response back to Slack (threading, formatting)
- **Health checks:** Agentura monitors bot uptime and restarts on failure
- **MCP tool access:** Notion MCP server configured in Agentura's environment, available to all skills at runtime

**Routing model — intake is the single entrypoint:** All channel messages are routed to `intake.md` via one Agentura trigger (`message: true`). The intake skill classifies the message (command, question, status update, meeting notes, approval reply, etc.) and handles it in a single invocation — loading the relevant reference files and applying the appropriate skill logic. There is no per-skill trigger routing from Agentura. This eliminates routing ambiguity: Agentura delivers messages, intake decides what to do with them. Scheduled jobs (cron triggers) bypass intake and invoke their respective skills directly.

**Slack formatting note:** Each skill must output Slack mrkdwn (not markdown). Key rules: `*bold*` not `**bold**`, `<url|text>` not `[text](url)`, no `##` headers. These rules are codified in `references/slack-formatting.md` and referenced by every skill.

**Platform gaps we handle ourselves** (no Srinidhi dependency):

1. **Thread interaction state (thread context gap):** Agentura invokes each skill in isolation — thread replies arrive without the parent message context. Multiple bot flows require thread state: approval batches ("approve 4"), archive confirmation ("yes"), and page disambiguation ("Reply with number"). In all cases, the user's reply is meaningless without the original prompt context. **Our solution:** A dedicated Notion database ("GE Pending Interactions") keyed by channel + thread_ts stores the context for any bot-initiated thread that expects a reply. Schema: `Thread TS` (title, key), `Channel` (text), `Interaction Type` (select: approval / archive-confirm / disambiguate), `Payload` (rich text, JSON — contents vary by type: change list for approvals, page ID for archive, candidate list for disambiguation), `Poster` (text, Slack ID), `Created At` (date), `Status` (select: Pending / Resolved). When a thread reply triggers intake, it queries this database by thread_ts. If a matching pending row exists, intake reads `Interaction Type` to determine how to interpret the reply (e.g., "approve 4" → approval flow, "yes" → archive lookup, "2" → disambiguation selection). Interactions expire after 48h by checking `created_at`; expired rows are marked Resolved and ignored. **Why Notion over a local file:** Notion provides persistence, atomic writes, and query-by-key — no questions about Agentura's filesystem persistence or concurrent-access behavior. We already have Notion MCP access. The tradeoff is one extra API call per thread interaction, acceptable for a 7-person team with low daily volume. Can be removed later if Agentura adds native thread context passing.

2. **Passive channel reading (message filtering gap):** Agentura's socket handler drops channel messages when `app_mention` is enabled. **Our solution:** Configure `message: true, app_mention: false` in `agentura.config.yaml`. The `intake` skill checks if the message text contains a bot mention (`<@BOT_ID>`) and routes accordingly. All channel messages are processed for intake; @mentions are handled within the same message handler. ~2 lines of detection logic in the intake skill.

3. **Notion MCP server:** Confirmed available. Agentura's MCP Gateway provides Notion access via `MCP_NOTION_URL` env var and Obot registry. No action needed.

### 7.2 Failure & Observability

**Retry policy:**

| Failure | Retry? | Action on failure |
|---|---|---|
| Notion API timeout/5xx | Retry once after 10s | If still failing, DM Ashutosh: "Notion write failed for [source]. Will retry on next cycle." |
| `claude --print` timeout (>5 min) | No retry | Reply in thread: "Processing timed out. Try again or simplify the input." |
| `claude --print` error exit | No retry | Reply in thread: "Something went wrong processing this. @Ashutosh flagged." |
| Slack API failure | Retry once | Log to console. If persistent, the bot is effectively down — Agentura health check catches it. |
| Malformed input (can't parse) | No retry | Reply: "I couldn't parse this. Can you rephrase or paste the key points as bullet points?" |
| Cron job failure | No retry within the same run | Next *scheduled* run will re-process any missing data (e.g., if morning briefing fails at 8 AM, the next day's 8 AM run covers it). If 2 consecutive runs fail, DM Ashutosh. This is *run-level* retry (next cycle), NOT item-level retry. |

**Alerting:** All failures DM Ashutosh (Slack user `U0A2TNJD0BW`). No external alerting system needed for a 7-person team.

**Logging:** Console stdout/stderr. Agentura captures these. No separate logging service for MVP.

**Partial failures in batch updates:** If a batch of 5 Notion writes partially fails (e.g., 3 succeed, 2 fail), commit the 3 that succeeded, report the 2 that failed in the Slack thread, and do NOT retry the failed items within the same batch — let the human decide. (This is distinct from cron-level retries: a cron job that fails entirely will be picked up by the next scheduled run. But within a single batch, failed items are surfaced, not auto-retried.)

### 7.3 Scheduled Jobs

| Job | Schedule | What it does |
|---|---|---|
| Morning briefing | Weekdays 8:00 AM GST | Reads Notion tracker → generates day-appropriate briefing → posts to channel |
| Context refresh | Daily 7:00 AM GST (before briefing) | Reads all Notion GE pages → regenerates context file → stores on Notion |
| Overdue check | Daily 9:00 AM GST | Scans tracker for items past due date → DMs owners with reminders |
| Daily change digest | Daily 6:00 PM GST | DMs both Admins (Ashutosh + Varun S) with summary of all day's changes by actor + type (see Section 5.6) |

---

## 8. Agentura Skill Structure

### 8.1 Server Skills (Agentura Domain: `agency/pm/`)

Deployed on Agentura as the `pm` domain. Each skill is a SKILL.md file + config entry.

```
agency/pm/
├── agentura.config.yaml             # Skill triggers, MCP tools, cron schedules
├── DECISIONS.md                     # Architecture decisions log
├── GUARDRAILS.md                    # Hard constraints (from real failures)
│
├── skills/
│   ├── intake.md                    # SINGLE ENTRYPOINT — classifies all channel messages, handles inline
│   ├── update.md                    # Referenced by intake for content processing → approval flow → commit
│   ├── qa.md                        # Referenced by intake for question answering
│   ├── morning-briefing.md          # Cron-triggered (not via intake) — daily briefing
│   ├── tracker-summary.md           # Referenced by intake for `tracker` command
│   ├── item-detail.md               # Referenced by intake for `item <ID>` command
│   ├── item-update.md               # Referenced by intake for `update <ID>` command
│   ├── search.md                    # Referenced by intake for `search` command
│   └── context-refresh.md           # Cron-triggered — rebuild context file + page index from Notion
│
├── references/                      # Loaded by skills on demand (not upfront)
│   ├── owner-mappings.md            # Notion/Slack ID mappings + role (Admin/Contributor/Observer)
│   ├── db-schema.md                 # Action tracker schema + ID conventions (E/P/R prefixes)
│   ├── slack-formatting.md          # mrkdwn rules + emoji mapping
│   ├── notion-page-index.md         # In-scope Notion pages with IDs (rebuilt by context-refresh)
│   └── keyword-lists.md             # Partner names, topic keywords for GE relevance filtering
```

**Thread interaction state storage:** A dedicated Notion database ("GE Pending Interactions") stores context for all bot-initiated threads that expect a reply. Schema: `Thread TS` (title, key), `Channel` (text), `Interaction Type` (select: approval / archive-confirm / disambiguate), `Payload` (rich text, JSON — change list for approvals, page ID for archive confirms, candidate list for disambiguation), `Poster` (text, Slack ID), `Created At` (date), `Status` (select: Pending / Resolved). Intake queries this DB by thread_ts on every thread reply and uses `Interaction Type` to dispatch to the correct handler. See Section 7.1 platform gap #1 for full design rationale.

**`agentura.config.yaml` declares:**
- One Slack trigger: all channel messages → `intake.md` (the single entrypoint)
- Cron triggers: `morning-briefing.md` (weekdays 8 AM), `context-refresh.md` (daily 7 AM), overdue check (daily 9 AM), daily digest (daily 6 PM) — these invoke their skills directly, bypassing intake
- MCP tools: Notion read+write, Slack read (available to all skills via MCP Gateway)
- Environment variables (`MCP_NOTION_URL`, Slack bot token, etc.)

### 8.2 Local Skills (Claude Code — `~/.claude/commands/`)

Unchanged from prior design. These run on Ashutosh's (and future Senior PM's) personal machine.

```
~/.claude/commands/
├── ge-setup.md                      # One-time: verify MCPs, configure settings.json permissions
├── ge-push.md                       # Scan Gmail/Granola → filter → present → approve → commit to Notion
├── ge-ref.md                        # Load GE context into current Claude Code session
└── references/
    └── ge-settings-template.json    # Pre-approved tool permissions for frictionless operation
```

### 8.3 What We Do NOT Build

- No `app.js`, `prompts.js`, `formatter.js` — Agentura handles Slack connection, routing, and response delivery
- No `Dockerfile` — Agentura deploys skills as config, not containers
- No `plugin.yaml` — replaced by `agentura.config.yaml`
- No `CLAUDE.md` for bot persona — skill instructions live in each SKILL.md file

---

## 9. Notion Integration Token Setup

The bot uses a **Notion Internal Integration** (not tied to any person's account):

1. Create integration at https://www.notion.so/my-integrations
2. Name: "GE Tracker Bot"
3. Capabilities: Read content, Update content, Insert content
4. Share all GE workspace pages with the integration (specifically the GE parent page and all children — see Section 6.5 scoping rules)
5. Set the integration token as the `MCP_NOTION_URL` env var in Agentura (the MCP Gateway handles auth centrally)

This gives the bot scoped access to only the GE pages — nothing else in the workspace.

---

## 10. Open Items / Future Considerations

| Item | Priority | Notes |
|---|---|---|
| **Dedicated email (ge-tracker@aspora.com)** | Low | Nice-to-have for forwarding Zoom summaries. Not load-bearing. Create if easy. |
| **Zoom transcript capture (when Ashutosh not on call)** | Medium | Unresolved from Srinidhi call. Options: Zoom API integration, ask attendee to paste transcript, use Zoom email summary. |
| **Granola access from server** | Parked | Not needed. Local instances handle Granola push. |
| **Google Sheets service account** | Not needed | Rare occurrence. Bot asks for access or paste when a sheet link is shared. |
| **GE Inbox database (for queued items)** | Medium | Needed for the process-inbox flow. Bot queues complex messages it can't auto-handle; Ashutosh reviews via local instance or Slack. |
| **Chrome plugin for sheet access** | Low | Fallback for when someone shares an inaccessible sheet. Not MVP. |
| **Onboarding new team members** | Done (in PRD) | New user detection added to Section 5.1 — bot DMs Admin when unknown user posts. |
| **Agentura deployment specifics** | Unblocked | Srinidhi confirmed: skills deploy as `pm/` domain, env vars for MCP tokens, cron via Heartbeat files, Notion MCP available via gateway. Platform gaps (thread context, passive reading) handled in our skills — no platform changes needed. |

---

## 11. Success Criteria

1. **Adoption:** At least 3 team members use the bot weekly within 2 weeks of launch
2. **Notion freshness:** Action tracker is never more than 24 hours stale
3. **Meeting capture:** 90%+ of GE meetings have notes processed within same day
4. **Response quality:** Bot answers questions accurately from Notion (spot-check weekly)
5. **Time saved:** Ashutosh spends <15 min/day on GE admin (vs. current 45–60 min estimate)

---

## 12. Build Sequence

| Phase | What | Depends on | Gate (must pass before next phase) |
|---|---|---|---|
| **Phase 1: Foundation** | `agentura.config.yaml`, references (owner-mappings, db-schema, slack-formatting, notion-page-index, keyword-lists), DECISIONS.md, GUARDRAILS.md | Nothing | Srinidhi confirms structure matches Agentura skill spec. Config deploys without errors. |
| **Phase 2: Core skills** | intake.md, update.md, qa.md, context-refresh.md | Phase 1 | Each skill tested standalone with `claude --print` against 3 sample inputs. Classification contract produces correct factual/interpretive split. |
| **Phase 3: Remaining skills** | morning-briefing.md, tracker-summary.md, item-detail.md, item-update.md, search.md | Phase 2 | Each skill tested standalone. Commands produce correct output. |
| **Phase 4: Cron triggers** | Heartbeat files for: morning briefing, context refresh, overdue check, daily digest | Phase 2 | Each cron tested with manual trigger. Output correct. Failure DMs Ashutosh. |
| **Phase 5: Local skills** | ge-setup.md, ge-push.md, ge-ref.md | Phase 1 | `/ge-setup` configures settings.json. `/ge-push` scans and presents summary without writing. `/ge-ref` loads context. |
| **Phase 5.5: Agentura Integration Gate** | Deploy skills to Agentura staging. Test cross-invocation thread interaction flows end-to-end. | Phase 3 + Srinidhi deploys to staging | **Must pass all 6 tests:** (1) Approval flow: post meeting notes → bot creates approval row in Pending Interactions DB (type: approval) → reply `approve 4` from a second invocation → confirm state resolves correctly. (2) Archive confirmation: ask about an archived topic → bot creates row (type: archive-confirm) → reply `yes` from second invocation → confirm bot looks up the archived page. (3) Disambiguation: trigger ambiguous page match → bot creates row (type: disambiguate) → reply `2` from second invocation → confirm correct page selected. (4) Interaction expiry: create a pending row, wait/simulate 48h, confirm auto-expiry marks it Resolved and follow-up reply is ignored. (5) Concurrent replies: two users reply to the same thread simultaneously → confirm no data loss or corruption. (6) Passive channel reading: post a status update (no @mention) → confirm intake skill processes it. |
| **Phase 6: Deploy to production** | Agentura production deployment, Notion integration token, Slack app creation | Phase 5.5 | Bot live in `#global-equities-team`. Responds to `help`. Commands and intake work. Cron triggers (Phase 4) added post-deploy when ready. |
| **Phase 7: Polish** | Edge cases, error handling, GUARDRAILS from real usage, team onboarding | Phase 6 | 1 week of live usage. GUARDRAILS.md updated with real failure modes. |

**Key change from prior versions:** There is no "Slack bot build" phase. Agentura handles all Slack infrastructure. We build skills only.

**MVP = Phases 1–3 + 5.5 + 6.** Local skills (Phase 5) and cron triggers (Phase 4) are parallel workstreams that enhance but don't block go-live.

**Srinidhi's role:** Deploy our skills to Agentura (Phase 6). We handle all platform gaps ourselves (see Section 7.1) — no platform-level changes required from his team. If Agentura later adds native thread context or passive reading support, we simplify our skills to use the platform features.

### Migration from Existing Slash Commands

The 5 existing `/ge-*` slash commands (`ge-ref`, `ge-sync`, `ge-morning`, `ge-update`, `ge-process`) are personal Claude Code commands used only by Ashutosh. This is NOT a production migration — it's replacing personal tooling.

**Cutover plan:**
1. Build the new skills. Keep old commands untouched during development.
2. Once Phase 5 local skills pass their gate, Ashutosh tests `/ge-push` and `/ge-ref` side-by-side with the old equivalents for 2–3 days.
3. If the new skills produce equivalent or better results, delete the old `/ge-*` command files from `~/.claude/commands/`.
4. No rollback needed — the old `.md` files can be restored from git/backup if anything regresses.

**No shadow mode or feature parity matrix needed.** The old commands have no users besides Ashutosh and no downstream dependencies.
