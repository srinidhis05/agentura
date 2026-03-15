# Project Config: {PROJECT_NAME}

## ClickUp
- workspace_id: "{CLICKUP_WORKSPACE_ID}"
- space: "{SPACE_NAME}" (id: {SPACE_ID})
- folder: "{FOLDER_NAME}" (id: {FOLDER_ID})
- default_list: "{LIST_NAME}" (id: {LIST_ID})
# Add more lists as needed:
# - {list_name}: "{LIST_NAME}" (id: {LIST_ID})

## Assignee Mapping
# Format: Full Name: clickup_user_id
# - Jane Doe: 123456789
# - John Smith: 987654321

## Slack
- channel: #{SLACK_CHANNEL} (look up via slack search if needed)
# - workspace_domain: "{WORKSPACE}.slack.com"
# Team member Slack IDs (for @mentions and tagging):
# - slack_ids:
#   - Jane Doe: U0ABC12345
#   - John Smith: U0DEF67890

## Notion
# Option A: Direct database ID
# - database_id: "{32_CHAR_HEX_ID}"
# Option B: Search-based (if database ID unknown)
# - Use notion-search to find the relevant database by project name
#
# Parent page for scoped search and context indexing:
# - parent_page_id: "{32_CHAR_HEX_ID}"
# - workspace: "{WORKSPACE_NAME}"
#
# Categories and statuses used in the tracker:
# - categories: ["{CATEGORY_1}", "{CATEGORY_2}"]
# - statuses: ["{STATUS_1}", "{STATUS_2}", "{STATUS_3}"]

## Granola
- meeting_search_terms: ["{KEYWORD_1}", "{KEYWORD_2}", "{KEYWORD_3}"]
- min_attendees: 3

## Partners
# Define external partner groups for smart email routing.
# If no partners, delete this section — meeting-update will skip email drafting.
#
# ### {Partner Name} ({Region})
# - domains: ["{partner-domain.com}"]
# - to: ["{contact@partner-domain.com}"]
# - cc: ["{cc@partner-domain.com}"]

## Sender
# The "From" address for partner emails
# - from: "{sender@your-domain.com}"

## Timezone
# Used for cron scheduling and date resolution
# - timezone: "Asia/Kolkata"

## Privacy
# Override default privacy filters if needed
# - exclude_meeting_keywords: ["1:1", "1-1", "one on one", "review", "performance", "feedback", "compensation", "career", "salary"]
# - min_attendees: 3

## Run History
# Server-side run history is managed by the platform (see PLATFORM-CHANGES.md #3).
# Local run history file (for Claude Code users):
# - local_run_history: "~/.claude/commands/{slug}-run-history.md"
