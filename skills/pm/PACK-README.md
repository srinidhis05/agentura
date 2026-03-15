# Agentura PM Platform Pack — Proposal for Review

## What This Is

A consolidated, MECE skill library for the Agentura PM domain. Merges four overlapping sources (Srinidhi's platform, Srinidhi's templates, Neha's Gold skills, Ashutosh's GE skills) into one canonical library of **15 server skills + 3 local skill templates**.

**Status:** Proposal / QA pack for review. Some behaviors depend on platform capabilities that are requested in `PLATFORM-CHANGES.md` (AskUserQuestion as blocker, config injection, run-history logging). Skills are designed to degrade gracefully where those capabilities don't yet exist.

## For Srinidhi: How to Review

1. **Read `PLATFORM-CHANGES.md` first** — contains 8 platform change requests, 1 is a blocker
2. **Read `MIGRATION.md`** — explains how existing configs (gold.md, remittance.md) need to be updated
3. **Compare `pm/DOMAIN.md`** against your current deployed version — skill count goes from 12 → 15
4. **Review each skill directory** — every skill has `SKILL.md` (logic) + `agentura.config.yaml` (platform config)
5. **Check `pm/project-configs/_template.md`** — generic config template with all fields skills expect

## What Changed

| Type | Count | Details |
|------|-------|---------|
| Modified skills | 8 | triage, meeting-update, pm-query, daily-briefing, action-tracker, pm-heartbeat, notion-sync, project-setup |
| New skills | 5 | meeting-scan, meeting-prep, weekly-digest, project-status, context-refresh |
| Removed skills | 2 | meeting-batch (replaced by meeting-scan), project-bootstrap (deferred to v2) |
| New docs | 4 | README, PLATFORM-CHANGES, ONBOARDING, MIGRATION |

## Directory Structure

```
platform/
├── README.md                 ← you are here
├── PLATFORM-CHANGES.md       ← platform change requests for Srinidhi
├── MIGRATION.md              ← how to upgrade existing project configs
├── ONBOARDING.md             ← how users onboard a new project
│
└── pm/                       ← replaces /skills/pm/ in the Agentura repo
    ├── DOMAIN.md
    ├── project-configs/
    │   └── _template.md
    ├── triage/
    ├── meeting-update/
    ├── meeting-scan/         ← NEW
    ├── meeting-prep/         ← NEW
    ├── pm-query/
    ├── daily-briefing/
    ├── daily-wrap/
    ├── weekly-digest/        ← NEW
    ├── action-tracker/
    ├── project-status/       ← NEW
    ├── pm-heartbeat/
    ├── channel-digest/
    ├── notion-sync/
    ├── context-refresh/      ← NEW (was merged into notion-sync, now separate)
    └── project-setup/
```

## Skill Summary

| # | Skill | Trigger | Model | New/Modified |
|---|---|---|---|---|
| 1 | triage | Slack, API | Haiku | Modified |
| 2 | meeting-update | Slack, API, command | Sonnet | Modified |
| 3 | meeting-scan | Slack, API | Sonnet | **New** |
| 4 | meeting-prep | Slack, API | Sonnet | **New** |
| 5 | pm-query | Slack, API | Haiku | Modified |
| 6 | daily-briefing | Cron 9am, Slack | Sonnet | Modified |
| 7 | daily-wrap | Cron 6pm, Slack | Sonnet | Minor polish |
| 8 | weekly-digest | Cron Mon 9am, Slack | Sonnet | **New** |
| 9 | action-tracker | Cron 10am, Slack | Sonnet | Modified |
| 10 | project-status | Slack, API | Sonnet | **New** |
| 11 | pm-heartbeat | Cron 6pm, Slack | Sonnet | Modified |
| 12 | channel-digest | Cron 5pm, Slack | Haiku | Minor polish |
| 13 | notion-sync | Slack, API | Sonnet | Modified |
| 14 | context-refresh | Slack, API | Sonnet | **New** |
| 15 | project-setup | Slack, API, command | Sonnet | Modified |
