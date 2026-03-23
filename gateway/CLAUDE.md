# Gateway — Architecture Notes for AI Agents

## Critical: Dual Slack Handlers (GR-031)

The gateway has TWO Slack message handlers that MUST stay in sync:

| File | Mode | Used by |
|------|------|---------|
| `slack_webhook.go` | HTTP Events API webhooks | Legacy/fallback |
| `slack_socket.go` | Socket Mode (WebSocket) | GE, PM, Growth, ECM bots |

Both files contain their own copies of `dispatchAndFormat`, `dispatchSkill`, `dispatchAuto`, and related functions. **Any change to dispatch logic in one file MUST be mirrored in the other.**

### Why this matters
Socket mode is the primary path for all Slack bots. If you fix a bug in the webhook handler but miss the socket handler (or vice versa), the fix won't apply to production Slack bots.

### Detection
```bash
# List dispatch functions in both files — any function in both is a sync risk
diff <(grep 'func.*dispatch\|func.*Format' internal/handler/slack_webhook.go) \
     <(grep 'func.*dispatch\|func.*Format' internal/handler/slack_socket.go)
```

### Common pitfalls
- `cmd = *aliasCmd` overwrites ALL fields including `UserID` — always save and restore `UserID`
- `cmd = slackCommand{...}` in thread continuity — must include `UserID: cmd.UserID`
- New fields added to `slackCommand` struct must be preserved in all `cmd =` assignments

## Request Flow

```
Slack Event → Socket Mode → handleSocketMessage → dispatchAndFormat → dispatchSkill
                                                                    → m.executor.Execute()
                                                                    → POST executor:8000/api/v1/skills/{d}/{s}/execute

API Request → HTTP Handler → ExecuteSkill → h.dispatcher.Dispatch() → ProxyDispatcher
                                          → d.client.Execute()
                                          → POST executor:8000/api/v1/skills/{d}/{s}/execute
```

Both paths end at the same executor endpoint. The `user_id` field in the JSON body controls OAuth token resolution. If `user_id` is empty, MCP bindings fall back to env-var URLs without authentication.

## Key Files

- `internal/handler/slack_socket.go` — Socket mode event handling (PRIMARY for Slack bots)
- `internal/handler/slack_webhook.go` — HTTP webhook event handling
- `internal/handler/skill.go` — REST API skill execution
- `internal/adapter/executor/dispatcher.go` — ExecutionDispatcher interface
- `internal/adapter/executor/proxy_dispatcher.go` — HTTP proxy to executor
- `internal/adapter/executor/http_client.go` — Executor HTTP client (`Client.Execute()`)
- `config/config.yaml` — Slack app configs, command aliases, cron jobs
