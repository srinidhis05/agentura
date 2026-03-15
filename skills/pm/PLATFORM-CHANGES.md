# Platform Change Requests

Changes needed in the Agentura platform to support the consolidated PM skill library. Ordered by priority.

---

## 1. AskUserQuestion — Buttoned Approval Pattern [BLOCKER]

**What:** AskUserQuestion must be a standard platform primitive that renders button options in Slack (not free-text parsing).

**Why:** Every write-path skill (meeting-update, notion-sync, meeting-scan, project-setup) depends on explicit buttoned approval as a hard safety boundary. Without this, write skills are either unsafe (auto-executing on text "yes") or require fragile ad-hoc text parsing. This is a safety-critical dependency, not a UX nicety.

**Spec:**
- Render as Slack interactive buttons (approve / reject / custom options)
- Support multi-select mode (for system selection in meeting-update)
- Return structured response (not raw text)
- Timeout: configurable per-skill (default 5 minutes)
- On timeout: treat as "rejected" (safe default)

---

## 2. Project Config Injection [HIGH]

**What:** Platform injects `project-configs/{slug}.md` into the skill's system prompt at runtime, based on the Slack channel or explicit `project_slug` parameter.

**Why:** Every skill reads system IDs, contacts, channels, and search terms from config. Without injection, skills can't resolve any project-specific references. This is an architectural dependency assumed by all 15 skills.

**Spec:**
- Match by Slack channel → project slug mapping (defined in config)
- Or match by explicit `project_slug` in the API call
- Inject as a `## Project Configuration` section in the system prompt
- Support multi-project: if no slug match, inject all configs (for cross-project skills like daily-briefing)

---

## 3. Run History Logging [HIGH]

**What:** Standard server-side pattern for skills to log execution results as operational state.

**Why:** meeting-scan and action-tracker depend on processed-vs-skipped state across executions. Run history is operational state (what was processed, what was skipped), not just audit reporting. Without this, meeting-scan re-surfaces already-processed meetings every run.

**Spec:**
- Per-project run log (append-only)
- Fields: timestamp, skill_name, meeting_title (if applicable), systems_updated, result (success/failed/skipped), skip_reason (if skipped)
- Queryable by skill: "has this meeting been processed?"
- Skip ledger: meetings explicitly marked as "skipped" don't re-surface

---

## 4. Gmail MCP via Vigil OAuth [HIGH]

**What:** Gmail MCP integration with per-user OAuth authentication through Vigil gateway.

**Why:** Partner email workflows (meeting-update, meeting-scan, weekly-digest) are blocked without Gmail access. Currently no way to send/read emails from the platform.

**Spec:**
- Per-user OAuth (not shared service account)
- Manual approval guardrails: every send must go through AskUserQuestion
- Read access for: searching project-related emails, checking pending partner threads
- Write access for: drafting and sending (with approval gate)

---

## 5. Thread Context Passing [MEDIUM]

**What:** When a user replies in a Slack thread, the platform passes the parent message context to the triage router.

**Why:** Triage needs the parent message to correctly route thread replies. Without this, thread replies are classified without context, leading to misroutes.

**Spec:**
- Include parent message text + metadata in the triage input
- Include thread_ts for skills that need to reply in-thread
- Don't include the full thread history (just parent + current message)

---

## 6. Server-Side Persistent State Store [MEDIUM]

**What:** A storage mechanism for skill-produced artifacts (page indexes, context files) that persists across executions and is queryable by other skills.

**Why:** `context-refresh` produces a page index and context file. Currently it stores these on Notion (as pages), which works but means every skill that needs the index must fetch from Notion. A dedicated server-side store would be faster and avoid Notion API overhead. Not blocking (Notion storage works as fallback), but improves reliability.

**Spec:**
- Key-value or document store, scoped per-project
- Skills can read/write arbitrary JSON or markdown artifacts
- Artifacts survive across skill executions
- Access pattern: `context-refresh` writes, `pm-query`/`meeting-prep`/`project-status` read

---

## 7. Local File Generation Story [MEDIUM]

**What:** A mechanism for server-side skills (like `project-setup`) to deliver files that end up on the user's local machine (`~/.claude/commands/`).

**Why:** `project-setup` generates local Claude Code skill templates. Currently it can only present them as text for the user to copy-paste. A first-class mechanism (e.g., download link, Slack file upload, or Claude Code plugin sync) would improve onboarding UX. Not blocking (copy-paste works), but creates friction.

**Spec:**
- project-setup produces 3 local skill files
- Platform delivers them to the user's machine or presents a one-click install
- Could be: Slack file attachment, downloadable archive, or sync via Claude Code plugin

---

## 8. Cron Timezone [LOW]

**What:** Confirm that cron expressions are evaluated in the project config's timezone, not UTC.

**Why:** A 9am briefing running at 9am UTC is useless for IST or GST users. The cron schedule assumes local time.

**Spec:**
- Each project config can specify `timezone: "Asia/Kolkata"` (or similar)
- Cron evaluator uses that timezone
- Default: workspace-level timezone setting
