# Migration Guide: Existing Project Configs

This guide explains how to upgrade existing project configs (e.g., `gold.md`, `remittance.md`) to work with the consolidated skill library.

## What Changed

The new skills assume additional config fields that older configs may not have. Missing fields won't crash skills, but features that depend on them will be skipped or degraded.

## Required Additions

### 1. Notion Parent Page ID

**Used by:** `pm-query` (scoped search), `context-refresh` (page tree scanning)

Add to the `## Notion` section:

```
- parent_page_id: "{32_CHAR_HEX_ID}"
```

This is the top-level Notion page under which all project pages live. Find it from your Notion URL — it's the page ID in the URL when you open your project's root page.

### 2. Notion Workspace, Categories, Statuses

**Used by:** `notion-sync`, `project-status`

Add to the `## Notion` section:

```
- workspace: "{WORKSPACE_NAME}"
- categories: ["Technical", "Compliance", "Commercial"]
- statuses: ["Not Started", "In Progress", "Blocked", "Done"]
```

Adjust values to match your actual Notion database properties.

### 3. Slack User IDs

**Used by:** `daily-briefing` (mentions), `action-tracker` (mentions), `channel-digest` (attribution)

Add to the `## Slack` section:

```
- workspace_domain: "{WORKSPACE}.slack.com"
- slack_ids:
  - Jane Doe: U0ABC12345
  - John Smith: U0DEF67890
```

Find Slack user IDs by clicking a user's profile → "..." → "Copy member ID".

### 4. Partner Sections (if applicable)

**Used by:** `meeting-update` (email drafting), `meeting-scan` (pending email detection), `meeting-prep` (partner briefing), `weekly-digest` (partner email stats)

If your project has external partners, add a `## Partners` section:

```
## Partners

### Acme Corp (APAC)
- domains: ["acme.com"]
- to: ["contact@acme.com"]
- cc: ["pm@acme.com"]

### Global Partners (EMEA)
- domains: ["globalpartners.io"]
- to: ["ops@globalpartners.io"]
- cc: []
```

If no partners: delete or leave the section empty. Skills will skip email-related steps.

### 5. Sender Email

**Used by:** `meeting-update` (email drafting)

```
## Sender
- from: "yourname@your-domain.com"
```

### 6. Timezone and Privacy

**Used by:** All cron skills (timezone), all meeting-reading skills (privacy)

```
## Timezone
- timezone: "Asia/Kolkata"

## Privacy
- exclude_meeting_keywords: ["1:1", "1-1", "one on one", "review", "performance"]
- min_attendees: 3
```

These have sensible defaults, but adding them explicitly avoids surprises.

## Migration Steps

1. Open your existing config: `project-configs/{slug}.md`
2. Add the missing sections listed above (copy from `_template.md` as reference)
3. Fill in actual values for your project
4. Test with: `pm-query` (should scope search to your project), `meeting-scan` (should find unprocessed meetings)

## What Happens Without Migration

Skills degrade gracefully:

| Missing Field | Impact |
|---------------|--------|
| `parent_page_id` | `pm-query` searches globally instead of scoped; `context-refresh` can't scan page tree |
| `slack_ids` | No @mentions in briefings and reminders |
| `Partners` section | Email drafting and pending-email detection skipped entirely |
| `Sender` | Email drafting skipped |
| `Timezone` | Crons run in platform default timezone |
| `Privacy` | Uses built-in defaults (min 3 attendees, standard keyword list) |
