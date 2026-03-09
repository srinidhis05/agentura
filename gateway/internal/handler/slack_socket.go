package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"
	"time"

	"github.com/slack-go/slack"
	"github.com/slack-go/slack/slackevents"
	"github.com/slack-go/slack/socketmode"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
)

// SlackSocketManager manages Socket Mode connections for all configured apps.
type SlackSocketManager struct {
	executor *executor.Client
	apps     []config.SlackAppConfig
	clients  []*socketmode.Client
}

// NewSlackSocketManager creates the manager (does not connect yet).
func NewSlackSocketManager(exec *executor.Client, cfg config.SlackConfig) *SlackSocketManager {
	return &SlackSocketManager{executor: exec, apps: cfg.Apps}
}

// Start launches a goroutine for each app configured with mode: "socket".
func (m *SlackSocketManager) Start(ctx context.Context) {
	for i := range m.apps {
		app := &m.apps[i]
		if app.Mode != "socket" {
			continue
		}
		if app.AppToken == "" || isSlackSecretPlaceholder(app.AppToken) {
			slog.Warn("slack socket mode: skipping app — no app_token", "app", app.Name)
			continue
		}
		if app.BotToken == "" || isSlackSecretPlaceholder(app.BotToken) {
			slog.Warn("slack socket mode: skipping app — no bot_token", "app", app.Name)
			continue
		}

		applyEventDefaults(app)

		api := slack.New(app.BotToken,
			slack.OptionAppLevelToken(app.AppToken),
		)
		client := socketmode.New(api)
		m.clients = append(m.clients, client)

		go m.runSocket(ctx, client, app)
		slog.Info("slack socket mode: connected", "app", app.Name, "domain", app.DomainScope)
	}
}

func (m *SlackSocketManager) runSocket(ctx context.Context, client *socketmode.Client, app *config.SlackAppConfig) {
	go func() {
		for evt := range client.Events {
			switch evt.Type {
			case socketmode.EventTypeEventsAPI:
				evtAPI, ok := evt.Data.(slackevents.EventsAPIEvent)
				if !ok {
					continue
				}
				client.Ack(*evt.Request)
				m.handleEventsAPI(app, evtAPI)

			case socketmode.EventTypeSlashCommand:
				client.Ack(*evt.Request)
				// Not used — commands go through Events API

			case socketmode.EventTypeConnecting:
				slog.Info("slack socket: connecting", "app", app.Name)

			case socketmode.EventTypeConnected:
				slog.Info("slack socket: connected", "app", app.Name)

			case socketmode.EventTypeConnectionError:
				if connErr, ok := evt.Data.(*slack.ConnectionErrorEvent); ok {
					slog.Error("slack socket: connection error", "app", app.Name, "error", connErr.Error())
				} else {
					slog.Error("slack socket: connection error", "app", app.Name, "data", fmt.Sprintf("%v", evt.Data))
				}

			default:
				// ignore interactive_message, etc.
			}
		}
	}()

	if err := client.RunContext(ctx); err != nil {
		slog.Error("slack socket mode: run failed", "app", app.Name, "error", err)
	}
}

func (m *SlackSocketManager) handleEventsAPI(app *config.SlackAppConfig, evtAPI slackevents.EventsAPIEvent) {
	inner := evtAPI.InnerEvent
	switch ev := inner.Data.(type) {
	case *slackevents.MessageEvent:
		if ev.BotID != "" {
			return // ignore bot messages
		}
		if !m.isEventEnabled(app, "message") {
			return
		}
		// When app_mention is also enabled, skip channel messages to avoid
		// processing the same @mention twice (Slack fires both events).
		if app.Events.AppMention && !isDM(ev.ChannelType) {
			return
		}
		m.handleSocketMessage(app, ev.Channel, ev.ChannelType, ev.User, ev.Text, ev.TimeStamp, ev.ThreadTimeStamp)

	case *slackevents.AppMentionEvent:
		if !m.isEventEnabled(app, "app_mention") {
			return
		}
		m.handleSocketMessage(app, ev.Channel, "channel", ev.User, ev.Text, ev.TimeStamp, ev.ThreadTimeStamp)

	case *slackevents.ReactionAddedEvent:
		if !app.Events.Reaction {
			return
		}
		slog.Info("slack socket: reaction", "app", app.Name, "reaction", ev.Reaction, "user", ev.User)

	default:
		// member_joined, channel_rename, pin — handled if needed
	}
}

func (m *SlackSocketManager) handleSocketMessage(app *config.SlackAppConfig, channel, channelType, user, text, ts, threadTS string) {
	// DM policy check
	if isDM(channelType) {
		if !m.isDMAllowed(app, user) {
			slog.Debug("slack socket: DM denied", "app", app.Name, "user", user)
			return
		}
	}

	// Strip bot mention prefix
	cleanText := strings.TrimSpace(text)
	if idx := strings.Index(cleanText, "> "); idx != -1 && strings.HasPrefix(cleanText, "<@") {
		cleanText = strings.TrimSpace(cleanText[idx+2:])
	}

	cmd := parseSlackCommand(cleanText)

	slog.Info("slack socket: message",
		"app", app.Name,
		"channel", channel,
		"channel_type", channelType,
		"user", user,
		"command", cmd.Action,
		"is_dm", isDM(channelType),
	)

	slackWebhookRequestsTotal.WithLabelValues(app.Name, "accepted").Inc()

	// Ack reaction
	replyTS := threadTS
	if replyTS == "" {
		replyTS = ts
	}
	if app.AckReaction != "" {
		go addSlackReaction(app.BotToken, channel, ts, app.AckReaction)
	}
	typingReaction := app.TypingReaction
	if typingReaction != "" {
		go addSlackReaction(app.BotToken, channel, ts, typingReaction)
	}

	// Dispatch async
	go func() {
		result := m.dispatchAndFormat(app, channel, user, cmd, replyTS)

		if typingReaction != "" {
			removeSlackReaction(app.BotToken, channel, ts, typingReaction)
		}

		if replyTS != "" && replyTS != ts {
			postSlackThreadReply(app.BotToken, channel, replyTS, result)
		} else {
			postSlackMessage(app.BotToken, channel, result)
		}
	}()
}

// ---------- Dispatch (reuses same logic as HTTP handler) ----------

func (m *SlackSocketManager) dispatchAndFormat(app *config.SlackAppConfig, channel, user string, cmd slackCommand, threadTS string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	// For auto commands, try command aliases first
	if cmd.Action == "auto" {
		if aliasCmd := matchCommandAlias(cmd.Text, app); aliasCmd != nil {
			cmd = *aliasCmd
		}
	}

	var result string
	var err error

	switch cmd.Action {
	case "run":
		result, err = m.dispatchSkill(ctx, app, cmd)
	case "pipeline":
		result, err = m.dispatchPipeline(ctx, app, cmd)
	case "skills":
		result, err = m.listSkills(ctx, app)
	case "help":
		result = m.helpText(app)
	default:
		result, err = m.dispatchAuto(ctx, app, cmd)
	}

	if err != nil {
		slog.Error("slack socket dispatch failed", "app", app.Name, "action", cmd.Action, "error", err)
		result = fmt.Sprintf("Error: %s", err)
	}

	return result
}

func (m *SlackSocketManager) dispatchSkill(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, error) {
	if cmd.Target == "" {
		return "", fmt.Errorf("usage: `run <domain/skill> [json_input]`")
	}
	parts := strings.SplitN(cmd.Target, "/", 2)
	if len(parts) != 2 {
		return "", fmt.Errorf("skill must be in `domain/skill` format, got: %s", cmd.Target)
	}
	skillDomain, skillName := parts[0], parts[1]

	if app.DomainScope != "" && skillDomain != app.DomainScope {
		return "", fmt.Errorf("app `%s` is scoped to domain `%s`, cannot run `%s`", app.Name, app.DomainScope, cmd.Target)
	}
	if !isAllowed(skillName, app.AllowedSkills) {
		return "", fmt.Errorf("skill `%s` is not in the allowed list for app `%s`", skillName, app.Name)
	}

	inputData := cmd.Input
	if inputData == nil {
		inputData = map[string]any{}
	}

	resp, err := m.executor.Execute(ctx, skillDomain, skillName, executor.ExecuteRequest{InputData: inputData})
	if err != nil {
		return "", fmt.Errorf("executing %s: %w", cmd.Target, err)
	}
	return formatSkillResult(resp), nil
}

func (m *SlackSocketManager) dispatchPipeline(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, error) {
	if cmd.Target == "" {
		return "", fmt.Errorf("usage: `pipeline <name> [json_input]`")
	}
	if !isAllowed(cmd.Target, app.AllowedPipelines) {
		return "", fmt.Errorf("pipeline `%s` is not in the allowed list for app `%s`", cmd.Target, app.Name)
	}

	var payload []byte
	if cmd.InputRaw != "" {
		payload = []byte(cmd.InputRaw)
	} else {
		payload = []byte("{}")
	}

	resp, err := m.executor.PostRaw(ctx, fmt.Sprintf("/api/v1/pipelines/%s/execute", cmd.Target), payload)
	if err != nil {
		return "", fmt.Errorf("executing pipeline %s: %w", cmd.Target, err)
	}
	return formatPipelineResult(resp), nil
}

func (m *SlackSocketManager) listSkills(ctx context.Context, app *config.SlackAppConfig) (string, error) {
	resp, err := m.executor.ListSkills(ctx)
	if err != nil {
		return "", fmt.Errorf("listing skills: %w", err)
	}

	var skills []executor.SkillInfo
	if err := json.Unmarshal(resp, &skills); err != nil {
		return string(resp), nil
	}

	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("*Skills available for %s*", app.Name))
	if app.DomainScope != "" {
		sb.WriteString(fmt.Sprintf(" (domain: `%s`)", app.DomainScope))
	}
	sb.WriteString("\n")

	for _, s := range skills {
		if app.DomainScope != "" && s.Domain != app.DomainScope {
			continue
		}
		if !isAllowed(s.Name, app.AllowedSkills) {
			continue
		}
		sb.WriteString(fmt.Sprintf("- `%s/%s` (%s)\n", s.Domain, s.Name, s.Role))
	}

	return sb.String(), nil
}

func (m *SlackSocketManager) dispatchAuto(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, error) {
	// Domain-scoped bots: route unmatched messages to the domain's triage skill.
	// If triage fails (404), fall back to help text.
	if app.DomainScope != "" {
		target := app.DomainScope + "/triage"
		inputData := map[string]any{"text": cmd.Text}
		autoCmd := slackCommand{Action: "run", Target: target, Input: inputData, Text: cmd.Text}
		result, err := m.dispatchSkill(ctx, app, autoCmd)
		if err == nil {
			return result, nil
		}
		slog.Debug("dispatchAuto: triage fallback failed", "domain", app.DomainScope, "error", err)
	}
	return m.helpText(app) + "\n\n_Type `help` to see available commands._", nil
}

func (m *SlackSocketManager) helpText(app *config.SlackAppConfig) string {
	var sb strings.Builder

	if len(app.Commands) > 0 {
		if app.DomainScope != "" {
			sb.WriteString(fmt.Sprintf("*%s Commands*\n\n", strings.ToUpper(app.DomainScope)))
		}
		for _, cmd := range app.Commands {
			sb.WriteString(fmt.Sprintf("• `%s` — %s\n", cmd.Pattern, cmd.Description))
		}
		sb.WriteString("\n*System commands:*\n")
		sb.WriteString("• `skills` — List available skills\n")
		sb.WriteString("• `help` — This message\n")
	} else {
		sb.WriteString("*Available commands:*\n")
		sb.WriteString("• `run <domain/skill> [json_input]` — Execute a skill\n")
		sb.WriteString("• `pipeline <name> [json_input]` — Execute a pipeline\n")
		sb.WriteString("• `skills` — List available skills\n")
		sb.WriteString("• `help` — Show this message\n")
		if app.DomainScope != "" {
			sb.WriteString(fmt.Sprintf("\nThis bot is scoped to the `%s` domain.\n", app.DomainScope))
		}
		sb.WriteString("\nOr just type a message and it will be auto-routed.")
	}

	return sb.String()
}

// ---------- Policy helpers (reuse same logic) ----------

func (m *SlackSocketManager) isDMAllowed(app *config.SlackAppConfig, userID string) bool {
	switch app.DM.Policy {
	case "disabled":
		return false
	case "allowlist":
		for _, allowed := range app.DM.Allowlist {
			if allowed == userID {
				return true
			}
		}
		return false
	case "pairing", "open", "":
		return true
	default:
		return true
	}
}

func (m *SlackSocketManager) isEventEnabled(app *config.SlackAppConfig, eventType string) bool {
	switch eventType {
	case "message":
		return app.Events.Message
	case "app_mention":
		return app.Events.AppMention
	default:
		return true
	}
}
