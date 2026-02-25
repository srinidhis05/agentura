# Triggers & Channels

> **Purpose**: How skills are activated — cron schedules, Slack messages, webhooks, and the inbound channel architecture.

Agentura supports two ways to activate skills beyond the web UI and CLI:

1. **Cron triggers** — time-based scheduling (built into the gateway)
2. **Channel webhooks** — external services POST to a single endpoint

## Architecture

```
                 +--------------+
                 |  Slack Bot   |  (external, any language)
                 +--------------+
                        | POST /api/v1/channels/slack/inbound
   +----------+  +------v--------+  +----------+
   |   Cron   |->|   Gateway     |->| Executor |
   | Scheduler|  |   (Go:3001)   |  | (Py:8000)|
   +----------+  |               |  +----------+
                 | POST /api/v1/ |
   +----------+  | channels/*/   |
   | Telegram |->| inbound       |
   | (future) |  +---------------+
   +----------+
```

- **Built-in channels** (cron): run inside the gateway process
- **External channels** (Slack, Telegram, Discord): separate services that POST JSON to the gateway
- All requests flow through gateway middleware (auth, metrics, rate limiting, logging)

## Cron Triggers

### Declaring a cron trigger

Add a `cron` trigger to your skill's `agentura.config.yaml`:

```yaml
skills:
  - name: morning-briefing
    triggers:
      - type: cron
        schedule: "0 7 * * 1-5"          # standard 5-field cron
        description: "Daily briefing at 7 AM on weekdays"
```

The gateway discovers cron triggers by calling `GET /api/v1/triggers` on the executor at startup, then re-syncs every 5 minutes (configurable).

### Cron schedule format

Standard 5-field cron expressions:

```
┌───────── minute (0-59)
│ ┌─────── hour (0-23)
│ │ ┌───── day of month (1-31)
│ │ │ ┌─── month (1-12)
│ │ │ │ ┌─ day of week (0-6, Sun=0)
│ │ │ │ │
* * * * *
```

Examples:
- `0 7 * * 1-5` — weekdays at 7:00 AM
- `*/15 * * * *` — every 15 minutes
- `0 9 1 * *` — first of every month at 9:00 AM

### Monitoring cron jobs

```bash
# List registered jobs with next/prev run times
curl http://localhost:3001/api/v1/triggers

# Scheduler health
curl http://localhost:3001/api/v1/triggers/status
```

### Configuration

In `gateway/config/config.yaml`:

```yaml
triggers:
  enabled: true
  timezone: UTC
  cron:
    enabled: true
    poll_interval: 300    # re-sync triggers every N seconds
  webhook:
    enabled: true
    secret: "${WEBHOOK_SECRET}"   # optional HMAC signing key
```

### Prometheus metrics

- `agentura_cron_executions_total{domain, skill, status}` — counter of cron-triggered executions
- `agentura_cron_execution_duration_seconds{domain, skill}` — execution duration histogram

## Channel Webhooks

### The universal endpoint

```
POST /api/v1/channels/{channel}/inbound
```

Any external service (Slack bot, Telegram bot, email processor, custom integration) can POST a JSON message to this endpoint. The `{channel}` path parameter is a free-form label (e.g., `slack`, `telegram`, `email`, `custom`).

### Request body

```json
{
  "source": "slack",
  "user_id": "U123ABC",
  "text": "interview questions for senior PM",
  "domain": "hr",
  "skill": "interview-questions",
  "metadata": {
    "thread_ts": "1234567890.123456"
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `source` | no | Label identifying the origin (for logging) |
| `text` | yes | The user's message or command |
| `user_id` | no | Sender identifier |
| `domain` | no | Target domain (skip classifier if provided with `skill`) |
| `skill` | no | Target skill (skip classifier if provided with `domain`) |
| `metadata` | no | Arbitrary key-value pairs passed to the skill |

### Routing behavior

- **`domain` + `skill` provided**: executes the skill directly
- **Neither provided**: routes through `platform/classifier` for auto-routing based on the text

### HMAC signature verification (optional)

If `WEBHOOK_SECRET` is set, the gateway verifies inbound requests using HMAC-SHA256:

```bash
# Generate signature
SIGNATURE=$(echo -n '{"text":"hello"}' | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')

# Send signed request
curl -X POST http://localhost:3001/api/v1/channels/slack/inbound \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d '{"text":"hello"}'
```

If `WEBHOOK_SECRET` is not set, signature verification is skipped.

### Prometheus metrics

- `agentura_webhook_requests_total{channel, status}` — counter by channel and outcome

## Examples

### Direct skill execution via webhook

```bash
curl -X POST http://localhost:3001/api/v1/channels/test/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "domain": "hr",
    "skill": "interview-questions",
    "text": "for senior PM role",
    "user_id": "test-user"
  }'
```

### Auto-routed message (classifier decides the skill)

```bash
curl -X POST http://localhost:3001/api/v1/channels/slack/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "source": "slack",
    "text": "what is our leave policy?",
    "user_id": "U456DEF"
  }'
```

### Connecting an existing Slack bot

Change the Slack bot's target from the executor to the gateway:

```yaml
# docker-compose.yml
slack:
  environment:
    AGENTURA_EXECUTOR_URL: http://gateway:3001   # was: http://executor:8000
```

This gives the Slack bot all gateway middleware (auth, metrics, rate limiting) for free.

## Adding a New Channel

To add Telegram, Discord, email, or any other channel:

1. Build a service in any language that receives messages from the platform
2. POST JSON to `POST /api/v1/channels/{your-channel}/inbound`
3. That's it. No Go plugins, no gateway changes needed.

Example minimal Telegram bot (pseudocode):

```python
@bot.on_message
def handle(msg):
    resp = requests.post(
        "http://gateway:3001/api/v1/channels/telegram/inbound",
        json={
            "source": "telegram",
            "user_id": str(msg.from_user.id),
            "text": msg.text,
        },
    )
    bot.reply(msg, resp.json()["output"]["raw_output"])
```
