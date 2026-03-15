# Platform Pack Review — Pre-Push QA

## What You're Reviewing

A consolidated PM skill library for the Agentura bot platform. This pack replaces 4 overlapping skill sources (Srinidhi's platform, Srinidhi's templates, Neha's Gold skills, Ashutosh's GE skills) with ONE MECE library.

**15 server skills + 3 local skill templates + 3 docs + 2 domain files = 35 files total.**

This is going to Srinidhi's repo (`srinidhis05/agentura`) as a change request. Srinidhi will QA and deploy.

## What Changed from Srinidhi's Current Repo

| Action | Skill | Key Changes |
|--------|-------|-------------|
| MODIFY | `triage/` | 14-route table (was 11), content-type detection (Granola links, Sheets, Zoom, status updates) |
| MODIFY | `meeting-update/` | Change classification (factual/interpretive), provenance tagging, system pre-selection, smart partner routing |
| MODIFY | `pm-query/` | Exact-ID fast path before semantic search, scoped to project parent |
| MODIFY | `daily-briefing/` | Day-of-week variants (Mon=weekly overview, Fri=accountability) |
| MODIFY | `action-tracker/` | Orphan detection, no-assignee/no-date checks, incomplete metadata flagging |
| MODIFY | `pm-heartbeat/` | Preserved as automated cron (distinct from new project-status which is on-demand) |
| MODIFY | `notion-sync/` | Change classification, item-update mode, provenance, conflict detection. Context-refresh split out. |
| MODIFY | `project-setup/` | Merged template generation (outputs config + 3 local skills) |
| POLISH | `daily-wrap/` | Minor: privacy filter consistency, config-driven references |
| POLISH | `channel-digest/` | Minor: verify criteria added, feedback capture alignment |
| ADD | `meeting-scan/` | NEW: unprocessed meetings + pending partner emails + reply routing + skip-state ledger |
| ADD | `meeting-prep/` | NEW: pre-meeting briefing (from Neha's /gold-prep) |
| ADD | `weekly-digest/` | NEW: Monday rollup with partner email activity + agent execution stats |
| ADD | `project-status/` | NEW: on-demand dashboard (NOT cron — distinct from pm-heartbeat) |
| ADD | `context-refresh/` | RESTORED: separate from notion-sync — page tree scan, rebuild index, exclude bot-state DBs |
| REMOVE | `meeting-batch/` | Replaced by meeting-scan (superset) |
| REMOVE | `project-bootstrap/` | Deferred to v2 |

## Previous Codex Review Issues (v3 → v4)

These were identified in the first Codex review and should be resolved in this build:

| # | Issue | Expected Resolution |
|---|---|---|
| 1 | AskUserQuestion was medium priority | Should be BLOCKER in PLATFORM-CHANGES.md |
| 2 | pm-heartbeat merged into project-status = regression | pm-heartbeat should exist as separate cron skill; project-status should be on-demand only |
| 3 | meeting-scan didn't cover /gold-detect fully | meeting-scan should include: pending partner email scanning, reply routing, skip-state tracking |
| 4 | notion-sync over-merged (3 different jobs) | context-refresh should be separate skill; item-update should be explicit mode of notion-sync |
| 5 | action-tracker under-specified | Should have no-assignee/no-date task checks |
| 6 | weekly-digest missing features | Should have partner-email activity and agent stats |
| 7 | pm-query needs exact-ID path | Should have exact-ID fast path before semantic search |
| 8 | GE provenance/conflict detection not carried over | Should be in notion-sync and meeting-update |
| 9 | Config injection + run-history logging too low priority | Should be HIGH in PLATFORM-CHANGES.md |
| 10 | project-bootstrap framed as dead weight | Should be "deferred to v2" not "dropped" |

## Internal Verification Results (already passed)

| # | Check | Result |
|---|---|---|
| 1 | YAML frontmatter fields in all SKILL.md | PASS |
| 2 | agentura.config.yaml sections in all skills | PASS |
| 3 | DOMAIN.md index = 15 entries matching directories | PASS |
| 4 | Triage routes = 14 non-triage skills | PASS |
| 5 | No project-specific references in skills | PASS (fixed — was FAIL, genericized all examples) |
| 6 | AskUserQuestion in write skills | PASS (read-only skills correctly omit) |
| 7 | Cron schedules match between DOMAIN.md and configs | PASS |
| 8 | _template.md has all 9 config sections | PASS |
| 9 | MECE: unique non-overlapping purposes | PASS |
| 10 | Provenance in write skills | PASS (read-only skills correctly omit) |
| 11 | Privacy filtering in meeting-reading skills | PASS |
| 12 | pm-heartbeat=cron, project-status=on-demand | PASS |
| 13 | context-refresh separate from notion-sync | PASS |
| 14 | All 15 skill directories exist | PASS |

## Review Questions

### Architecture

1. **MECE completeness**: Are there any PM workflows missing that should be a skill? Are there any overlaps we missed?
2. **Skill boundaries**: Are meeting-update vs meeting-scan vs notion-sync clearly delineated? Is it obvious which one handles what?
3. **pm-heartbeat vs project-status**: Is the distinction clear enough (cron health alerts vs on-demand deep dashboard)?
4. **context-refresh separation**: Is the split from notion-sync clean? Any concerns about when context-refresh should run?

### Correctness

5. **Triage route table**: Does the 14-route table cover all realistic user inputs? Any routing gaps?
6. **Change classification**: Is the factual/interpretive split well-defined across meeting-update and notion-sync? Edge cases?
7. **Cron schedule**: Any timing conflicts or gaps? (Mon 9am weekly-digest, Tue-Fri 9am daily-briefing, 10am action-tracker, 5pm channel-digest, 6pm daily-wrap + pm-heartbeat)
8. **Approval gates**: Are AskUserQuestion gates in the right places? Any writes that should be gated but aren't?

### Platform Fit

9. **Config template**: Does `_template.md` cover all fields that skills need? Missing sections?
10. **PLATFORM-CHANGES.md**: Are the 6 change requests correctly prioritized? Is AskUserQuestion clearly framed as a blocker?
11. **Skill frontmatter format**: Does every SKILL.md match Srinidhi's expected format?
12. **agentura.config.yaml format**: Do all configs match the platform's expected structure?

### Risk

13. **Breaking changes**: Could any modification to existing skills break current users (Gold, Remittance)?
14. **Migration path**: Is it clear how existing project configs (gold.md, remittance.md) work with the new skills?
15. **Privacy**: Are privacy filters comprehensive enough across all meeting-reading skills?

## File Index (for reference)

```
build/platform/
├── README.md
├── PLATFORM-CHANGES.md
├── ONBOARDING.md
├── CODEX_REVIEW.md              ← this file
│
└── pm/
    ├── DOMAIN.md
    ├── project-configs/
    │   └── _template.md
    │
    ├── triage/                   SKILL.md + agentura.config.yaml
    ├── meeting-update/           SKILL.md + agentura.config.yaml
    ├── meeting-scan/             SKILL.md + agentura.config.yaml  [NEW]
    ├── meeting-prep/             SKILL.md + agentura.config.yaml  [NEW]
    ├── pm-query/                 SKILL.md + agentura.config.yaml
    ├── daily-briefing/           SKILL.md + agentura.config.yaml
    ├── daily-wrap/               SKILL.md + agentura.config.yaml
    ├── weekly-digest/            SKILL.md + agentura.config.yaml  [NEW]
    ├── action-tracker/           SKILL.md + agentura.config.yaml
    ├── project-status/           SKILL.md + agentura.config.yaml  [NEW]
    ├── pm-heartbeat/             SKILL.md + agentura.config.yaml
    ├── channel-digest/           SKILL.md + agentura.config.yaml
    ├── notion-sync/              SKILL.md + agentura.config.yaml
    ├── context-refresh/          SKILL.md + agentura.config.yaml  [RESTORED]
    └── project-setup/            SKILL.md + agentura.config.yaml
```
