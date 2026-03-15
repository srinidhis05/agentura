# Onboarding a New Project

How to set up a new project on the Agentura PM bot.

---

## Prerequisites

- Agentura workspace with PM domain enabled
- Slack channel for the project
- Notion database (or willingness to create one)
- ClickUp workspace (optional — some projects use Notion-only)

## Steps

### 1. Run Project Setup

In your project's Slack channel, tell the bot:

> "Set up a new project called [Project Name]"

The bot routes to `project-setup`, which runs a 7-phase guided wizard:

1. **Project name & slug** — e.g., "Gold" → `gold`
2. **Granola search terms** — keywords to find your meetings
3. **Notion config** — database ID, workspace, categories, statuses
4. **Slack config** — channel name, workspace
5. **ClickUp config** — workspace/space/list IDs (skip if not using ClickUp)
6. **Team members** — names, ClickUp IDs, emails
7. **Partner groups** — external partners with email routing rules (0-4 groups)

### 2. Review Generated Files

The wizard generates:
- `project-configs/{slug}.md` — all system IDs, contacts, mappings
- Local skills: `{slug}.md` (context loader), `{slug}-config.md`, `{slug}-run-history.md`

### 3. Verify with a Test Run

Try these commands in your Slack channel:

| Command | What happens |
|---------|-------------|
| "What's the status of [project]?" | Routes to `pm-query` — tests Notion read access |
| "Process today's meeting" | Routes to `meeting-update` — tests full write pipeline |
| "What's overdue?" | Routes to `action-tracker` — tests ClickUp/Notion read |

### 4. Cron Skills Activate Automatically

Once the project config exists, cron skills pick it up:

| Time | Skill | What you'll see |
|------|-------|----------------|
| 9am weekdays | daily-briefing | Morning briefing in Slack |
| 10am weekdays | action-tracker | Overdue/deadline reminders |
| 5pm weekdays | channel-digest | Channel activity summary |
| 6pm weekdays | daily-wrap + pm-heartbeat | EOD recap + health alerts |
| Mon 9am | weekly-digest | Weekly rollup |

## Customization (Power Users)

- Edit `project-configs/{slug}.md` to change system IDs, contacts, search terms
- Add custom categories/statuses to match your Notion/ClickUp setup
- Configure partner email groups for smart routing
- Set `min_attendees` to control privacy filtering threshold

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot doesn't respond | Check Slack channel is mapped to a project config |
| Wrong project matched | Add more specific Granola search terms |
| Missing meetings | Check `min_attendees` setting (default: 3, filters 1-1s) |
| Partner emails not drafting | Add partner group to config with email domains |
| Cron not firing | Check project config exists and timezone is correct |
