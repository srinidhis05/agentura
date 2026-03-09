package handler

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"regexp"
	"io"
	"log/slog"
	"net/http"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
	"github.com/agentura-ai/agentura/gateway/internal/domain"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

var slackWebhookRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
	Name: "agentura_slack_webhook_requests_total",
	Help: "Total Slack webhook requests by app and status",
}, []string{"app", "status"})

const (
	slackTimestampMaxDrift = 5 * time.Minute
	slackAPIBaseURL        = "https://slack.com/api"
	slackMaxMessageLen     = 3900
)

// SlackWebhookHandler processes inbound Slack Events API webhooks.
type SlackWebhookHandler struct {
	executor *executor.Client
	apps     []config.SlackAppConfig
}

// NewSlackWebhookHandler creates a handler for Slack webhooks.
func NewSlackWebhookHandler(exec *executor.Client, cfg config.SlackConfig) *SlackWebhookHandler {
	// Apply event config defaults
	for i := range cfg.Apps {
		applyEventDefaults(&cfg.Apps[i])
	}
	return &SlackWebhookHandler{executor: exec, apps: cfg.Apps}
}

func applyEventDefaults(app *config.SlackAppConfig) {
	if app.Mode == "" {
		app.Mode = "http"
	}
	if app.DM.Policy == "" {
		app.DM.Policy = "open"
	}
	// Enable message and app_mention by default
	if !app.Events.Message && !app.Events.AppMention {
		app.Events.Message = true
		app.Events.AppMention = true
	}
}

// Handle processes POST /api/v1/webhooks/slack.
func (h *SlackWebhookHandler) Handle(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		slackWebhookRequestsTotal.WithLabelValues("unknown", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "failed to read body")
		return
	}

	// Find matching app by verifying signature against each app's signing secret
	timestamp := r.Header.Get("X-Slack-Request-Timestamp")
	signature := r.Header.Get("X-Slack-Signature")

	matchedApp := h.matchApp(body, timestamp, signature)
	if matchedApp == nil {
		slackWebhookRequestsTotal.WithLabelValues("unknown", "unauthorized").Inc()
		httputil.RespondError(w, http.StatusUnauthorized, "invalid slack signature")
		return
	}

	// Parse envelope
	var envelope domain.SlackEvent
	if err := json.Unmarshal(body, &envelope); err != nil {
		slackWebhookRequestsTotal.WithLabelValues(matchedApp.Name, "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "invalid slack event payload")
		return
	}

	switch envelope.Type {
	case "url_verification":
		slackWebhookRequestsTotal.WithLabelValues(matchedApp.Name, "challenge").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"challenge": envelope.Challenge})
		return

	case "event_callback":
		h.handleEventCallback(w, matchedApp, envelope)

	default:
		slackWebhookRequestsTotal.WithLabelValues(matchedApp.Name, "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored"})
	}
}

func (h *SlackWebhookHandler) matchApp(body []byte, timestamp, signature string) *config.SlackAppConfig {
	if timestamp == "" || signature == "" {
		return nil
	}

	// Reject stale timestamps
	ts, err := parseSlackTimestamp(timestamp)
	if err != nil || time.Since(ts) > slackTimestampMaxDrift {
		return nil
	}

	for i := range h.apps {
		if isSlackSecretPlaceholder(h.apps[i].SigningSecret) {
			continue
		}
		if verifySlackSignature(body, timestamp, signature, h.apps[i].SigningSecret) {
			return &h.apps[i]
		}
	}
	return nil
}

// handleEventCallback routes events based on type with DM/channel policy enforcement.
func (h *SlackWebhookHandler) handleEventCallback(w http.ResponseWriter, app *config.SlackAppConfig, envelope domain.SlackEvent) {
	event := envelope.Event

	// Ignore bot messages to prevent loops
	if event.BotID != "" {
		slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "reason": "bot_message"})
		return
	}

	// Route by event type
	switch event.Type {
	case "message", "app_mention":
		if !h.isEventEnabled(app, event.Type) {
			slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "reason": "event_disabled"})
			return
		}

		// Enforce DM policy
		if isDM(event.ChannelType) {
			if !h.isDMAllowed(app, event.User) {
				slackWebhookRequestsTotal.WithLabelValues(app.Name, "denied").Inc()
				httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "denied", "reason": "dm_policy"})
				return
			}
		} else {
			// Enforce channel policy
			if !h.isChannelAllowed(app, event.Channel, event.User, event.Type) {
				slackWebhookRequestsTotal.WithLabelValues(app.Name, "denied").Inc()
				httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "denied", "reason": "channel_policy"})
				return
			}
		}

		h.handleMessage(w, app, event)

	case "reaction_added", "reaction_removed":
		if !app.Events.Reaction {
			slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "reason": "reaction_disabled"})
			return
		}
		h.handleReaction(w, app, event)

	case "member_joined_channel":
		if !app.Events.MemberJoin {
			slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored"})
			return
		}
		h.handleMemberEvent(w, app, event)

	case "member_left_channel":
		if !app.Events.MemberLeave {
			slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored"})
			return
		}
		h.handleMemberEvent(w, app, event)

	case "channel_rename":
		if !app.Events.ChannelRename {
			slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored"})
			return
		}
		h.handleSystemEvent(w, app, event)

	case "pin_added", "pin_removed":
		if !app.Events.Pin {
			slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored"})
			return
		}
		h.handleSystemEvent(w, app, event)

	default:
		slackWebhookRequestsTotal.WithLabelValues(app.Name, "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "reason": event.Type})
	}
}

// ---------- DM & Channel Policy Enforcement ----------

func isDM(channelType string) bool {
	return channelType == "im" || channelType == "mpim"
}

func (h *SlackWebhookHandler) isDMAllowed(app *config.SlackAppConfig, userID string) bool {
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

func (h *SlackWebhookHandler) isChannelAllowed(app *config.SlackAppConfig, channelID, userID, eventType string) bool {
	// No channel ACLs configured = all channels allowed
	if len(app.Channels) == 0 {
		return true
	}

	for _, ch := range app.Channels {
		if ch.ID == channelID {
			switch ch.Policy {
			case "disabled":
				return false
			case "allowlist":
				for _, u := range ch.UserAllowlist {
					if u == userID {
						return !ch.MentionOnly || eventType == "app_mention"
					}
				}
				return false
			case "open", "":
				return !ch.MentionOnly || eventType == "app_mention"
			}
		}
	}

	// Channel not in ACL list — allow by default
	return true
}

func (h *SlackWebhookHandler) isEventEnabled(app *config.SlackAppConfig, eventType string) bool {
	switch eventType {
	case "message":
		return app.Events.Message
	case "app_mention":
		return app.Events.AppMention
	default:
		return true
	}
}

// ---------- Event Handlers ----------

func (h *SlackWebhookHandler) handleMessage(w http.ResponseWriter, app *config.SlackAppConfig, event domain.SlackMessageEvent) {
	text := strings.TrimSpace(event.Text)
	// Strip bot mention prefix (e.g. "<@U12345> run incubator/spec-analyzer")
	if idx := strings.Index(text, "> "); idx != -1 && strings.HasPrefix(text, "<@") {
		text = strings.TrimSpace(text[idx+2:])
	}

	cmd := parseSlackCommand(text)

	slog.Info("slack webhook received",
		"app", app.Name,
		"channel", event.Channel,
		"channel_type", event.ChannelType,
		"user", event.User,
		"command", cmd.Action,
		"thread_ts", event.ThreadTS,
		"is_dm", isDM(event.ChannelType),
	)

	// Respond 200 immediately (Slack requires < 3s)
	slackWebhookRequestsTotal.WithLabelValues(app.Name, "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "accepted"})

	// Ack reaction
	threadTS := event.ThreadTS
	if threadTS == "" {
		threadTS = event.TS
	}
	if app.AckReaction != "" {
		go addSlackReaction(app.BotToken, event.Channel, event.TS, app.AckReaction)
	}

	// Typing indicator
	typingReaction := app.TypingReaction
	if typingReaction != "" {
		go addSlackReaction(app.BotToken, event.Channel, event.TS, typingReaction)
	}

	go func() {
		result := h.dispatchAndFormat(app, event.Channel, event.User, cmd, threadTS)

		// Remove typing indicator
		if typingReaction != "" {
			removeSlackReaction(app.BotToken, event.Channel, event.TS, typingReaction)
		}

		// Post result as thread reply if in a thread, otherwise as a new message
		if threadTS != "" && threadTS != event.TS {
			postSlackThreadReply(app.BotToken, event.Channel, threadTS, result)
		} else {
			postSlackMessage(app.BotToken, event.Channel, result)
		}
	}()
}

func (h *SlackWebhookHandler) handleReaction(w http.ResponseWriter, app *config.SlackAppConfig, event domain.SlackMessageEvent) {
	slog.Info("slack reaction event",
		"app", app.Name,
		"type", event.Type,
		"reaction", event.Reaction,
		"user", event.User,
		"item_user", event.ItemUser,
	)

	slackWebhookRequestsTotal.WithLabelValues(app.Name, "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "accepted"})

	// Forward to executor as a system event
	go h.forwardSystemEvent(app, event)
}

func (h *SlackWebhookHandler) handleMemberEvent(w http.ResponseWriter, app *config.SlackAppConfig, event domain.SlackMessageEvent) {
	slog.Info("slack member event",
		"app", app.Name,
		"type", event.Type,
		"user", event.User,
		"channel", event.Channel,
	)

	slackWebhookRequestsTotal.WithLabelValues(app.Name, "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "accepted"})

	go h.forwardSystemEvent(app, event)
}

func (h *SlackWebhookHandler) handleSystemEvent(w http.ResponseWriter, app *config.SlackAppConfig, event domain.SlackMessageEvent) {
	slog.Info("slack system event",
		"app", app.Name,
		"type", event.Type,
		"channel", event.Channel,
	)

	slackWebhookRequestsTotal.WithLabelValues(app.Name, "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "accepted"})

	go h.forwardSystemEvent(app, event)
}

// forwardSystemEvent sends non-message events to the executor for processing.
func (h *SlackWebhookHandler) forwardSystemEvent(app *config.SlackAppConfig, event domain.SlackMessageEvent) {
	msg := domain.InboundMessage{
		Source:  "slack",
		Channel: app.Name,
		UserID:  event.User,
		Text:    fmt.Sprintf("[%s] %s", event.Type, event.Reaction),
		Domain:  app.DomainScope,
		Metadata: map[string]any{
			"event_type":   event.Type,
			"channel_id":   event.Channel,
			"reaction":     event.Reaction,
			"item_user":    event.ItemUser,
			"channel_name": event.Name,
		},
	}

	payload, err := json.Marshal(msg)
	if err != nil {
		slog.Error("failed to marshal system event", "error", err)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if _, err := h.executor.PostRaw(ctx, "/api/v1/channels/slack/inbound", payload); err != nil {
		slog.Error("failed to forward system event", "app", app.Name, "type", event.Type, "error", err)
	}
}

// ---------- Command Parsing & Dispatch ----------

type slackCommand struct {
	Action   string         // "run", "pipeline", "skills", "help", "auto"
	Target   string         // "domain/skill" or pipeline name
	InputRaw string         // raw JSON input string
	Input    map[string]any // parsed input
	Text     string         // original text (for auto-routing)
}

func parseSlackCommand(text string) slackCommand {
	parts := strings.SplitN(text, " ", 3)
	if len(parts) == 0 {
		return slackCommand{Action: "help", Text: text}
	}

	action := strings.ToLower(parts[0])

	switch action {
	case "run":
		cmd := slackCommand{Action: "run", Text: text}
		if len(parts) >= 2 {
			cmd.Target = parts[1]
		}
		if len(parts) >= 3 {
			cmd.InputRaw = parts[2]
			var parsed map[string]any
			if err := json.Unmarshal([]byte(parts[2]), &parsed); err == nil {
				cmd.Input = parsed
			}
		}
		return cmd

	case "pipeline":
		cmd := slackCommand{Action: "pipeline", Text: text}
		if len(parts) >= 2 {
			cmd.Target = parts[1]
		}
		if len(parts) >= 3 {
			cmd.InputRaw = parts[2]
			var parsed map[string]any
			if err := json.Unmarshal([]byte(parts[2]), &parsed); err == nil {
				cmd.Input = parsed
			}
		}
		return cmd

	case "skills":
		return slackCommand{Action: "skills", Text: text}

	case "help":
		return slackCommand{Action: "help", Text: text}

	default:
		return slackCommand{Action: "auto", Text: text}
	}
}

// matchCommandAlias checks if text matches any configured command alias for the app.
// Returns a "run" command if matched, nil if not.
// Uses two-pass matching: exact prefix match first, then fuzzy keyword match.
func matchCommandAlias(text string, app *config.SlackAppConfig) *slackCommand {
	if len(app.Commands) == 0 {
		return nil
	}

	lower := strings.ToLower(strings.TrimSpace(text))

	// Pass 1: Exact prefix match (current behavior)
	for _, alias := range app.Commands {
		input := matchPattern(lower, strings.ToLower(alias.Pattern))
		if input == nil {
			continue
		}

		return buildAliasCommand(text, lower, input, alias, app)
	}

	// Pass 2: Fuzzy keyword match — check if text contains a command keyword
	// e.g. "can you triage the orders" matches the "triage" command
	words := strings.Fields(lower)
	for _, alias := range app.Commands {
		patParts := strings.Fields(strings.ToLower(alias.Pattern))
		if len(patParts) == 0 {
			continue
		}
		keyword := patParts[0]
		if strings.HasPrefix(keyword, "{") {
			continue // Skip patterns that start with a placeholder
		}

		for wi, w := range words {
			if w != keyword {
				continue
			}
			// Keyword found — extract remaining text after keyword as input
			input := map[string]string{}
			remaining := strings.Join(words[wi+1:], " ")
			for _, pp := range patParts[1:] {
				if strings.HasPrefix(pp, "{") && strings.HasSuffix(pp, "}") {
					key := pp[1 : len(pp)-1]
					if remaining != "" {
						input[key] = remaining
					}
					break
				}
			}
			return buildAliasCommand(text, lower, input, alias, app)
		}
	}

	return nil
}

// buildAliasCommand constructs a slackCommand from a matched command alias.
func buildAliasCommand(text, lower string, input map[string]string, alias config.SlackCommandAlias, app *config.SlackAppConfig) *slackCommand {
	// Merge extracted params from pattern + any extract overrides
	for k, v := range alias.Extract {
		resolved := v
		for mk, mv := range input {
			resolved = strings.ReplaceAll(resolved, "{"+mk+"}", mv)
		}
		input[k] = resolved
	}

	// Also pass the original text for context
	inputAny := make(map[string]any, len(input)+1)
	for k, v := range input {
		inputAny[k] = v
	}
	inputAny["text"] = text

	target := alias.Skill
	if app.DomainScope != "" {
		target = app.DomainScope + "/" + alias.Skill
	}

	return &slackCommand{
		Action: "run",
		Target: target,
		Input:  inputAny,
		Text:   text,
	}
}

// matchPattern matches text against a pattern with {placeholders}.
// Returns extracted values if matched, nil if not.
// e.g. matchPattern("order abc123", "order {order_id}") => {"order_id": "abc123"}
func matchPattern(text, pattern string) map[string]string {
	patParts := strings.Fields(pattern)
	textParts := strings.Fields(text)

	if len(textParts) < len(patParts) {
		return nil
	}

	result := map[string]string{}
	ti := 0

	for _, pp := range patParts {
		if ti >= len(textParts) {
			return nil
		}

		if strings.HasPrefix(pp, "{") && strings.HasSuffix(pp, "}") {
			// Placeholder — capture value
			key := pp[1 : len(pp)-1]
			// If this is the last pattern part, capture all remaining text
			if pp == patParts[len(patParts)-1] {
				result[key] = strings.Join(textParts[ti:], " ")
				return result
			}
			result[key] = textParts[ti]
			ti++
		} else {
			// Literal match
			if textParts[ti] != pp {
				return nil
			}
			ti++
		}
	}

	return result
}

func (h *SlackWebhookHandler) dispatchAndFormat(app *config.SlackAppConfig, channel, user string, cmd slackCommand, threadTS string) string {
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
		result, err = h.dispatchSkill(ctx, app, cmd)
	case "pipeline":
		result, err = h.dispatchPipeline(ctx, app, cmd)
	case "skills":
		result, err = h.listSkills(ctx, app)
	case "help":
		result = h.helpText(app)
	default:
		// Auto-route: pass text to classifier scoped to domain
		result, err = h.dispatchAuto(ctx, app, cmd)
	}

	if err != nil {
		slog.Error("slack dispatch failed",
			"app", app.Name,
			"action", cmd.Action,
			"error", err,
		)
		result = fmt.Sprintf("Error: %s", err)
	}

	return result
}

func (h *SlackWebhookHandler) dispatchSkill(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, error) {
	if cmd.Target == "" {
		return "", fmt.Errorf("usage: `run <domain/skill> [json_input]`")
	}

	parts := strings.SplitN(cmd.Target, "/", 2)
	if len(parts) != 2 {
		return "", fmt.Errorf("skill must be in `domain/skill` format, got: %s", cmd.Target)
	}
	skillDomain, skillName := parts[0], parts[1]

	// Domain scope check
	if app.DomainScope != "" && skillDomain != app.DomainScope {
		return "", fmt.Errorf("app `%s` is scoped to domain `%s`, cannot run `%s`", app.Name, app.DomainScope, cmd.Target)
	}

	// Allowed skills check
	if !isAllowed(skillName, app.AllowedSkills) {
		return "", fmt.Errorf("skill `%s` is not in the allowed list for app `%s`", skillName, app.Name)
	}

	inputData := cmd.Input
	if inputData == nil {
		inputData = map[string]any{}
	}

	execReq := executor.ExecuteRequest{InputData: inputData}
	resp, err := h.executor.Execute(ctx, skillDomain, skillName, execReq)
	if err != nil {
		return "", fmt.Errorf("executing %s: %w", cmd.Target, err)
	}

	return formatSkillResult(resp), nil
}

func (h *SlackWebhookHandler) dispatchPipeline(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, error) {
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

	resp, err := h.executor.PostRaw(ctx, fmt.Sprintf("/api/v1/pipelines/%s/execute", cmd.Target), payload)
	if err != nil {
		return "", fmt.Errorf("executing pipeline %s: %w", cmd.Target, err)
	}

	return formatPipelineResult(resp), nil
}

func (h *SlackWebhookHandler) listSkills(ctx context.Context, app *config.SlackAppConfig) (string, error) {
	resp, err := h.executor.ListSkills(ctx)
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

func (h *SlackWebhookHandler) dispatchAuto(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, error) {
	// Domain-scoped bots: route unmatched messages to the domain's triage skill.
	// If triage fails (404), fall back to help text.
	if app.DomainScope != "" {
		target := app.DomainScope + "/triage"
		inputData := map[string]any{"text": cmd.Text}
		autoCmd := slackCommand{Action: "run", Target: target, Input: inputData, Text: cmd.Text}
		result, err := h.dispatchSkill(ctx, app, autoCmd)
		if err == nil {
			return result, nil
		}
		// Triage skill not found — fall through to help text
		slog.Debug("dispatchAuto: triage fallback failed", "domain", app.DomainScope, "error", err)
	}
	return h.helpText(app) + "\n\n_Type `help` to see available commands._", nil
}

func (h *SlackWebhookHandler) helpText(app *config.SlackAppConfig) string {
	var sb strings.Builder

	// If domain-specific commands are configured, show those prominently
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

// ---------- Slack API Helpers ----------

func postSlackMessage(botToken, channel, text string) error {
	if botToken == "" || isSlackSecretPlaceholder(botToken) {
		return fmt.Errorf("bot token not configured")
	}

	text = markdownToSlackMrkdwn(text)

	if len(text) > slackMaxMessageLen {
		text = text[:slackMaxMessageLen] + "\n... (truncated)"
	}

	payload, err := json.Marshal(map[string]string{
		"channel": channel,
		"text":    text,
	})
	if err != nil {
		return fmt.Errorf("marshaling slack message: %w", err)
	}

	return slackAPIPost(botToken, "/chat.postMessage", payload)
}

func postSlackThreadReply(botToken, channel, threadTS, text string) error {
	if botToken == "" || isSlackSecretPlaceholder(botToken) {
		return fmt.Errorf("bot token not configured")
	}

	text = markdownToSlackMrkdwn(text)

	if len(text) > slackMaxMessageLen {
		text = text[:slackMaxMessageLen] + "\n... (truncated)"
	}

	payload, err := json.Marshal(map[string]string{
		"channel":   channel,
		"text":      text,
		"thread_ts": threadTS,
	})
	if err != nil {
		return fmt.Errorf("marshaling slack thread reply: %w", err)
	}

	return slackAPIPost(botToken, "/chat.postMessage", payload)
}

func addSlackReaction(botToken, channel, timestamp, reaction string) {
	if botToken == "" || isSlackSecretPlaceholder(botToken) {
		return
	}

	payload, err := json.Marshal(map[string]string{
		"channel":   channel,
		"timestamp": timestamp,
		"name":      reaction,
	})
	if err != nil {
		return
	}

	if err := slackAPIPost(botToken, "/reactions.add", payload); err != nil {
		slog.Debug("failed to add slack reaction", "reaction", reaction, "error", err)
	}
}

func removeSlackReaction(botToken, channel, timestamp, reaction string) {
	if botToken == "" || isSlackSecretPlaceholder(botToken) {
		return
	}

	payload, err := json.Marshal(map[string]string{
		"channel":   channel,
		"timestamp": timestamp,
		"name":      reaction,
	})
	if err != nil {
		return
	}

	if err := slackAPIPost(botToken, "/reactions.remove", payload); err != nil {
		slog.Debug("failed to remove slack reaction", "reaction", reaction, "error", err)
	}
}

func slackAPIPost(botToken, endpoint string, payload []byte) error {
	req, err := http.NewRequest(http.MethodPost, slackAPIBaseURL+endpoint, bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("creating slack request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+botToken)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("posting to slack: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("slack API returned %d: %s", resp.StatusCode, respBody)
	}

	return nil
}

// ---------- Signature & Utilities ----------

func verifySlackSignature(body []byte, timestamp, signature, signingSecret string) bool {
	if !strings.HasPrefix(signature, "v0=") {
		return false
	}

	baseString := fmt.Sprintf("v0:%s:%s", timestamp, string(body))
	mac := hmac.New(sha256.New, []byte(signingSecret))
	mac.Write([]byte(baseString))
	expected := "v0=" + hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(expected), []byte(signature))
}

func parseSlackTimestamp(ts string) (time.Time, error) {
	var sec int64
	if _, err := fmt.Sscanf(ts, "%d", &sec); err != nil {
		return time.Time{}, err
	}
	return time.Unix(sec, 0), nil
}

func isSlackSecretPlaceholder(s string) bool {
	return strings.HasPrefix(s, "${") && strings.HasSuffix(s, "}")
}

func isAllowed(name string, allowList []string) bool {
	if len(allowList) == 0 {
		return true
	}
	for _, a := range allowList {
		if a == "*" || a == name {
			return true
		}
	}
	return false
}

func formatSkillResult(raw json.RawMessage) string {
	var result map[string]any
	if err := json.Unmarshal(raw, &result); err != nil {
		return string(raw)
	}

	// Try to extract output field and format for Slack
	if output, ok := result["output"]; ok {
		return formatOutputForSlack(output)
	}
	if response, ok := result["response"]; ok {
		return formatOutputForSlack(response)
	}

	// Fallback: pretty-print JSON
	pretty, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return string(raw)
	}
	return string(pretty)
}

func formatOutputForSlack(output any) string {
	m, ok := output.(map[string]any)
	if !ok {
		// Scalar or array — JSON-serialize
		b, err := json.MarshalIndent(output, "", "  ")
		if err != nil {
			return fmt.Sprintf("%v", output)
		}
		return string(b)
	}

	// Check for error
	if errMsg, ok := m["error"]; ok {
		return fmt.Sprintf(":warning: %v", errMsg)
	}

	// Check for summary (PTC worker output)
	if summary, ok := m["summary"]; ok {
		s := fmt.Sprintf("%v", summary)
		if s != "" {
			return s
		}
	}

	// Fallback: JSON-serialize the output map
	b, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return fmt.Sprintf("%v", output)
	}
	return string(b)
}

// markdownToSlackMrkdwn converts standard Markdown to Slack's mrkdwn format.
// Key differences: **bold** → *bold*, ## Headers → *Headers*, tables → code blocks.
var (
	mdBoldRe   = regexp.MustCompile(`\*\*(.+?)\*\*`)
	mdHeaderRe = regexp.MustCompile(`(?m)^#{1,4}\s+(.+)$`)
	mdHrRe     = regexp.MustCompile(`(?m)^---+\s*$`)
	mdTableRe  = regexp.MustCompile(`(?m)^\|.+\|$`)
	mdTableSep = regexp.MustCompile(`(?m)^\|[-| :]+\|$`)
)

func markdownToSlackMrkdwn(text string) string {
	// Headers: ## Title → *Title*
	text = mdHeaderRe.ReplaceAllString(text, "*$1*")
	// Bold: **text** → *text*
	text = mdBoldRe.ReplaceAllString(text, "*$1*")
	// Horizontal rules: --- → empty line
	text = mdHrRe.ReplaceAllString(text, "")
	// Table separator rows (|---|---|): remove entirely
	text = mdTableSep.ReplaceAllString(text, "")
	// Table data rows: keep as-is (Slack renders pipes fine in monospace)
	return text
}

func formatPipelineResult(raw json.RawMessage) string {
	var result map[string]any
	if err := json.Unmarshal(raw, &result); err != nil {
		return string(raw)
	}

	if status, ok := result["status"]; ok {
		return fmt.Sprintf("Pipeline completed with status: %v", status)
	}

	pretty, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return string(raw)
	}
	return string(pretty)
}
