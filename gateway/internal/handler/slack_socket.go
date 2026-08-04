package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"regexp"
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

			case socketmode.EventTypeInteractive:
				client.Ack(*evt.Request)
				m.handleSocketInteractive(app, evt)

			default:
				// ignore other event types
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
			if wb := matchWatchBot(app, ev.BotID, ev.Channel); wb != nil {
				if wb.PassRawText {
					// Ops-genie path: full-text pass-through (Datadog alerts)
					// Dedup handled in-skill via find_active_incident (not a blunt rate limit)
					go m.handleOpsGenieWatchBot(app, wb, ev)
				} else {
					// ECM path: existing behavior, untouched
					go m.handleWatchBotMessage(app, wb, ev)
				}
			}
			return
		}
		// Skip messages posted via API (e.g. our own bot replies) — they have
		// no User set.  Without this guard the bot's thread reply loops back
		// as a new event and gets re-dispatched as a standalone channel post.
		if ev.User == "" {
			return
		}
		if !m.isEventEnabled(app, "message") {
			return
		}
		// When app_mention is also enabled, skip channel messages that
		// contain a bot @mention to avoid processing the same mention
		// twice (Slack fires both message and app_mention events).
		// Non-mention channel messages (e.g. command aliases like
		// "funnel", "pulse") must pass through.
		if app.Events.AppMention && !isDM(ev.ChannelType) && strings.HasPrefix(ev.Text, "<@") {
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
		m.handleReactionFeedback(app, ev)

	default:
		// member_joined, channel_rename, pin — handled if needed
	}
}

// handleReactionFeedback processes emoji reactions on bot messages as feedback signals.
// Looks up the thread registry to find which skill produced the message,
// then logs the feedback with a Prometheus counter for accuracy tracking.
func (m *SlackSocketManager) handleReactionFeedback(app *config.SlackAppConfig, ev *slackevents.ReactionAddedEvent) {
	sentiment := classifyReaction(ev.Reaction)
	if sentiment == "" {
		return // not a feedback reaction
	}

	channel := ev.Item.Channel
	messageTS := ev.Item.Timestamp

	// Look up which skill produced this message via thread registry
	skill := "unknown"
	if entry := lookupThread(app.Name, channel, messageTS); entry != nil {
		skill = entry.skill
	}

	slog.Info("slack socket: reaction feedback",
		"app", app.Name,
		"reaction", ev.Reaction,
		"sentiment", sentiment,
		"skill", skill,
		"user", ev.User,
		"channel", channel,
		"message_ts", messageTS,
	)

	slackReactionFeedbackTotal.WithLabelValues(app.Name, skill, sentiment).Inc()
}

// classifyReaction maps emoji names to feedback sentiment.
func classifyReaction(reaction string) string {
	switch reaction {
	case "white_check_mark", "+1", "thumbsup", "heavy_check_mark", "check":
		return "positive"
	case "x", "-1", "thumbsdown", "no_entry", "no_entry_sign":
		return "negative"
	default:
		return ""
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
	cmd.UserID = user

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
		result, finalCmd := m.dispatchAndFormat(app, channel, user, cmd, threadTS, replyTS)

		if typingReaction != "" {
			removeSlackReaction(app.BotToken, channel, ts, typingReaction)
		}

		// Suppress response if result is empty (e.g. triage-router returned null route)
		if strings.TrimSpace(result) == "" {
			slog.Info("empty result — suppressing Slack response",
				"app", app.Name, "channel", channel)
			return
		}

		// Post result — use Block Kit if skill returned rich_output
		var postedTS string
		if blocks, fallback, ok := tryParseRichOutput(result); ok {
			slog.Info("rich_output detected, posting Block Kit",
				"app", app.Name,
				"channel", channel,
				"blocks_count", len(blocks),
			)
			// Always reply in a thread (like Pearl) — use original message as parent
			threadParent := replyTS
			if threadParent == "" || threadParent == ts {
				threadParent = ts
			}
			postedTS, _ = postSlackBlocksWithTS(app.BotToken, channel, threadParent, fallback, blocks)
		} else {
			// Always reply in a thread under the triggering message.
			// This keeps the channel clean — bot output is in threads, not flat messages.
			postedTS, _ = postSlackThreadReply(app.BotToken, channel, ts, result)
		}

		// Thread registration: remember skill for thread continuity
		if finalCmd.Action == "run" && finalCmd.Target != "" && !strings.HasPrefix(result, "Error:") {
			regKey := threadTS
			if regKey == "" {
				regKey = postedTS
			}
			if regKey != "" {
				turn := 1
				if entry := lookupThread(app.Name, channel, threadTS); entry != nil {
					turn = entry.turn + 1
				}
				registerThread(app.Name, channel, regKey, finalCmd.Target, result, extractEntities(finalCmd.Input), user, turn)
			}
		}
	}()
}

// ---------- Dispatch (reuses same logic as HTTP handler) ----------

func (m *SlackSocketManager) dispatchAndFormat(app *config.SlackAppConfig, channel, user string, cmd slackCommand, origThreadTS, replyTS string) (string, slackCommand) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	// Thread continuity: thread replies skip triage, reuse previous skill
	if origThreadTS != "" && cmd.Action == "auto" {
		if entry := lookupThread(app.Name, channel, origThreadTS); entry != nil {
			cmd = slackCommand{
				Action: "run",
				Target: entry.skill,
				Input: map[string]any{
					"text": cmd.Text,
					"thread_context": map[string]any{
						"previous_output": entry.lastOutput,
						"turn":            entry.turn + 1,
					},
				},
				Text:   cmd.Text,
				UserID: cmd.UserID,
			}
			for k, v := range entry.entities {
				cmd.Input[k] = v
			}
			slog.Info("thread continuity: reusing skill", "app", app.Name, "skill", entry.skill, "turn", entry.turn+1)
		}
	}

	// For auto commands: try command aliases first (highest priority),
	// then fall back to domain triage if no alias matches.
	if cmd.Action == "auto" {
		if aliasCmd := matchCommandAlias(cmd.Text, app); aliasCmd != nil {
			savedUserID := cmd.UserID
			cmd = *aliasCmd
			cmd.UserID = savedUserID
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
		var routedCmd slackCommand
		result, routedCmd, err = m.dispatchAuto(ctx, app, cmd)
		if routedCmd.Target != "" {
			cmd = routedCmd
		}
	}

	if err != nil {
		slog.Error("slack socket dispatch failed", "app", app.Name, "action", cmd.Action, "error", err)
		result = fmt.Sprintf("Error: %s", err)
	}

	return result, cmd
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

	resp, err := m.executor.Execute(ctx, skillDomain, skillName, executor.ExecuteRequest{InputData: inputData, UserID: cmd.UserID})
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

func (m *SlackSocketManager) dispatchAuto(ctx context.Context, app *config.SlackAppConfig, cmd slackCommand) (string, slackCommand, error) {
	if app.DomainScope == "" {
		return m.helpText(app) + "\n\n_Type `help` to see available commands._", cmd, nil
	}

	// Domain-scoped bots: route through triage, then chain to routed skill.
	inputData := map[string]any{"text": cmd.Text}
	resp, err := m.executor.Execute(ctx, app.DomainScope, "triage", executor.ExecuteRequest{InputData: inputData, UserID: cmd.UserID})
	if err != nil {
		slog.Warn("dispatchAuto: triage failed, falling back to data-query",
			"domain", app.DomainScope, "error", err)
	}

	routeTo := ""
	var entities map[string]any
	if err == nil {
		routeTo, entities = parseTriageRoute(resp)
	}

	// Normalize: if triage returned a bare skill name (no "/"), qualify with domain scope.
	if routeTo != "" && !strings.Contains(routeTo, "/") {
		qualified := app.DomainScope + "/" + routeTo
		slog.Info("dispatchAuto: qualifying bare triage route",
			"raw", routeTo, "qualified", qualified)
		routeTo = qualified
	}

	// If triage returned empty/null route, the message is not bot-directed — suppress response.
	if routeTo == "" {
		preview := cmd.Text
		if len(preview) > 80 {
			preview = preview[:80] + "..."
		}
		slog.Info("dispatchAuto: triage returned null route — suppressing response",
			"domain", app.DomainScope, "text_preview", preview)
		return "", cmd, nil
	}

	routeInput := map[string]any{"text": cmd.Text}
	for k, v := range entities {
		routeInput[k] = v
	}
	routedCmd := slackCommand{Action: "run", Target: routeTo, Input: routeInput, Text: cmd.Text, UserID: cmd.UserID}
	result, err := m.dispatchSkill(ctx, app, routedCmd)
	if err != nil {
		slog.Error("dispatchAuto: routed skill failed", "skill", routeTo, "error", err)
		return "", routedCmd, err
	}
	return result, routedCmd, nil
}

// checkOAuthConnections queries the executor for the user's OAuth status.
// Returns a Slack-formatted connection prompt if providers are missing, or "" if all connected.
func (m *SlackSocketManager) checkOAuthConnections(ctx context.Context, userID string) string {
	raw, err := m.executor.ProxyGet(ctx, fmt.Sprintf("/api/v1/oauth/status/%s", userID), "")
	if err != nil {
		slog.Debug("oauth status check failed", "user", userID, "error", err)
		return ""
	}

	var status struct {
		Connected    []string `json:"connected"`
		NotConnected []string `json:"not_connected"`
	}
	if err := json.Unmarshal(raw, &status); err != nil {
		return ""
	}

	if len(status.NotConnected) == 0 {
		return ""
	}

	callbackBase := os.Getenv("GATEWAY_PUBLIC_URL")
	if callbackBase == "" {
		slog.Warn("GATEWAY_PUBLIC_URL not set, OAuth links may not work")
		callbackBase = "http://localhost:3001"
	}

	var sb strings.Builder
	sb.WriteString("*Connect your accounts to use this skill:*\n")
	for _, provider := range status.NotConnected {
		link := fmt.Sprintf("%s/api/v1/oauth/connect/%s/authorize?user_id=%s&callback_base=%s",
			callbackBase, provider, userID, callbackBase)
		displayName := strings.ToUpper(provider[:1]) + provider[1:]
		sb.WriteString(fmt.Sprintf("• <%s|Connect %s>\n", link, displayName))
	}
	sb.WriteString("\n_After connecting, try your command again._")
	return sb.String()
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

func (m *SlackSocketManager) handleSocketInteractive(app *config.SlackAppConfig, evt socketmode.Event) {
	// Socket mode interactive payloads arrive as slack.InteractionCallback
	cb, ok := evt.Data.(slack.InteractionCallback)
	if !ok {
		slog.Debug("slack socket: interactive event not InteractionCallback")
		return
	}

	// Convert to our unified SlackInteractivePayload format
	payload := convertInteractionCallback(cb)

	// Route based on interaction type (matches webhook handler logic)
	switch payload.Type {
	case "block_actions":
		if len(payload.Actions) == 0 {
			return
		}
		go m.processSocketBlockAction(app, payload, cb.ResponseURL)

	case "view_submission":
		// Modal submissions need synchronous response
		resp := m.processSocketModalSubmission(app, payload)
		// Socket mode doesn't use HTTP response for modals - handled via callback
		_ = resp

	case "view_closed":
		go m.processSocketModalClosed(app, payload)

	case "message_action":
		go m.processSocketMessageAction(app, payload, cb.TriggerID)

	case "shortcut":
		go m.processSocketGlobalShortcut(app, payload, cb.TriggerID)

	default:
		slog.Debug("slack socket: unknown interaction type", "type", payload.Type)
	}
}

// convertInteractionCallback converts slack SDK InteractionCallback to our SlackInteractivePayload.
func convertInteractionCallback(cb slack.InteractionCallback) SlackInteractivePayload {
	payload := SlackInteractivePayload{
		Type:        string(cb.Type),
		CallbackID:  cb.CallbackID,
		TriggerID:   cb.TriggerID,
		ResponseURL: cb.ResponseURL,
	}

	payload.User.ID = cb.User.ID
	payload.User.Name = cb.User.Name
	payload.Team.ID = cb.Team.ID

	if cb.Channel.ID != "" {
		payload.Channel = &struct {
			ID   string `json:"id"`
			Name string `json:"name,omitempty"`
		}{ID: cb.Channel.ID, Name: cb.Channel.Name}
	}

	// Convert block actions
	if len(cb.ActionCallback.BlockActions) > 0 {
		payload.Actions = make([]struct {
			ActionID        string `json:"action_id"`
			Value           string `json:"value"`
			Type            string `json:"type"`
			SelectedOption  *struct {
				Value string `json:"value"`
				Text  struct {
					Text string `json:"text"`
				} `json:"text"`
			} `json:"selected_option,omitempty"`
			SelectedOptions []struct {
				Value string `json:"value"`
				Text  struct {
					Text string `json:"text"`
				} `json:"text"`
			} `json:"selected_options,omitempty"`
			SelectedUser    string   `json:"selected_user,omitempty"`
			SelectedUsers   []string `json:"selected_users,omitempty"`
			SelectedChannel string   `json:"selected_channel,omitempty"`
		}, len(cb.ActionCallback.BlockActions))

		for i, ba := range cb.ActionCallback.BlockActions {
			payload.Actions[i].ActionID = ba.ActionID
			payload.Actions[i].Value = ba.Value
			payload.Actions[i].Type = string(ba.Type)
			// Convert selected options for select menus
			if ba.SelectedOption.Value != "" {
				payload.Actions[i].SelectedOption = &struct {
					Value string `json:"value"`
					Text  struct {
						Text string `json:"text"`
					} `json:"text"`
				}{
					Value: ba.SelectedOption.Value,
				}
				payload.Actions[i].SelectedOption.Text.Text = ba.SelectedOption.Text.Text
			}
			payload.Actions[i].SelectedUser = ba.SelectedUser
			payload.Actions[i].SelectedChannel = ba.SelectedChannel
		}
	}

	// Convert view for modal submissions
	if cb.View.ID != "" {
		payload.View = &struct {
			ID     string `json:"id"`
			TeamID string `json:"team_id"`
			Type   string `json:"type"`
			State  struct {
				Values map[string]map[string]struct {
					Type            string `json:"type"`
					Value           string `json:"value,omitempty"`
					SelectedOption  *struct {
						Value string `json:"value"`
					} `json:"selected_option,omitempty"`
					SelectedUser    string `json:"selected_user,omitempty"`
					SelectedChannel string `json:"selected_channel,omitempty"`
				} `json:"values"`
			} `json:"state"`
			PrivateMetadata string `json:"private_metadata,omitempty"`
			CallbackID      string `json:"callback_id,omitempty"`
		}{
			ID:              cb.View.ID,
			TeamID:          cb.View.TeamID,
			Type:            string(cb.View.Type),
			PrivateMetadata: cb.View.PrivateMetadata,
			CallbackID:      cb.View.CallbackID,
		}
		// Note: View state conversion would go here if needed
	}

	// Convert message for message actions
	if cb.Message.Text != "" {
		payload.Message = &struct {
			Type string `json:"type"`
			Text string `json:"text,omitempty"`
			TS   string `json:"ts"`
		}{
			Text: cb.Message.Text,
			TS:   cb.Message.Timestamp,
		}
	}

	return payload
}

// Socket mode equivalents of webhook handlers (reuse webhook handler logic)

func (m *SlackSocketManager) processSocketBlockAction(app *config.SlackAppConfig, payload SlackInteractivePayload, responseURL string) {
	action := payload.Actions[0]
	userID := payload.User.ID

	// Handle built-in approval buttons
	switch action.ActionID {
	case "approve_execution", "reject_execution":
		m.processSocketApprovalAction(app, payload, action, responseURL)
		return
	}

	// For other actions, dispatch to interaction handler
	// TODO: Implement generic dispatch when config routing is added
	slog.Info("slack socket: block action", "action_id", action.ActionID, "user", userID)
}

func (m *SlackSocketManager) processSocketApprovalAction(app *config.SlackAppConfig, payload SlackInteractivePayload, action struct {
	ActionID        string `json:"action_id"`
	Value           string `json:"value"`
	Type            string `json:"type"`
	SelectedOption  *struct {
		Value string `json:"value"`
		Text  struct {
			Text string `json:"text"`
		} `json:"text"`
	} `json:"selected_option,omitempty"`
	SelectedOptions []struct {
		Value string `json:"value"`
		Text  struct {
			Text string `json:"text"`
		} `json:"text"`
	} `json:"selected_options,omitempty"`
	SelectedUser    string   `json:"selected_user,omitempty"`
	SelectedUsers   []string `json:"selected_users,omitempty"`
	SelectedChannel string   `json:"selected_channel,omitempty"`
}, responseURL string) {
	executionID := action.Value
	userID := payload.User.ID

	var approved bool
	switch action.ActionID {
	case "approve_execution":
		approved = true
	case "reject_execution":
		approved = false
	default:
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	approvalBody, _ := json.Marshal(map[string]any{
		"approved":       approved,
		"reviewer_notes": fmt.Sprintf("Via Slack by <@%s>", userID),
	})

	_, err := m.executor.ApproveExecution(ctx, executionID, approvalBody)

	statusText := "Approved"
	statusEmoji := ":white_check_mark:"
	if !approved {
		statusText = "Rejected"
		statusEmoji = ":x:"
	}

	var updateText string
	if err != nil {
		slog.Error("socket interactive approval failed", "execution_id", executionID, "error", err)
		updateText = fmt.Sprintf(":warning: Failed to process: %s", err)
	} else {
		updateText = fmt.Sprintf("%s %s by <@%s>", statusEmoji, statusText, userID)
	}

	var channelID, messageTS string
	if payload.Channel != nil {
		channelID = payload.Channel.ID
	}
	if payload.Message != nil {
		messageTS = payload.Message.TS
	}

	updatePayload, _ := json.Marshal(map[string]any{
		"channel": channelID,
		"ts":      messageTS,
		"text":    updateText,
		"blocks":  []map[string]any{},
	})
	if err := slackAPIPost(app.BotToken, "/chat.update", updatePayload); err != nil {
		slog.Error("failed to update slack message via socket", "error", err)
	}
}

func (m *SlackSocketManager) processSocketModalSubmission(app *config.SlackAppConfig, payload SlackInteractivePayload) map[string]any {
	// Reuse webhook handler logic
	handler := &SlackWebhookHandler{executor: m.executor, apps: []config.SlackAppConfig{*app}}
	return handler.processModalSubmission(app, payload)
}

func (m *SlackSocketManager) processSocketModalClosed(app *config.SlackAppConfig, payload SlackInteractivePayload) {
	handler := &SlackWebhookHandler{executor: m.executor, apps: []config.SlackAppConfig{*app}}
	handler.processModalClosed(app, payload)
}

func (m *SlackSocketManager) processSocketMessageAction(app *config.SlackAppConfig, payload SlackInteractivePayload, triggerID string) {
	handler := &SlackWebhookHandler{executor: m.executor, apps: []config.SlackAppConfig{*app}}
	handler.processMessageAction(app, payload)
}

func (m *SlackSocketManager) processSocketGlobalShortcut(app *config.SlackAppConfig, payload SlackInteractivePayload, triggerID string) {
	handler := &SlackWebhookHandler{executor: m.executor, apps: []config.SlackAppConfig{*app}}
	handler.processGlobalShortcut(app, payload)
}

// matchWatchBot checks if a bot message matches a configured watch_bot entry.
func matchWatchBot(app *config.SlackAppConfig, botID, channel string) *config.WatchBotConfig {
	for i := range app.WatchBots {
		wb := &app.WatchBots[i]
		if wb.BotID == botID {
			if wb.Channel == "" || wb.Channel == channel {
				return wb
			}
		}
	}
	return nil
}

// handleWatchBotMessage extracts order IDs from a watched bot's message and dispatches the configured skill.
func (m *SlackSocketManager) handleWatchBotMessage(app *config.SlackAppConfig, wb *config.WatchBotConfig, ev *slackevents.MessageEvent) {
	orderIDs := extractOrderIDs(ev.Text)
	if len(orderIDs) == 0 {
		slog.Info("watch_bot: no order IDs found in message",
			"app", app.Name, "bot_id", wb.BotID, "channel", ev.Channel, "text_len", len(ev.Text))
		return
	}

	slog.Info("watch_bot: dispatching",
		"app", app.Name,
		"bot_id", wb.BotID,
		"skill", wb.Skill,
		"order_count", len(orderIDs),
		"channel", ev.Channel,
		"thread_ts", ev.TimeStamp,
	)

	// Prepend domain scope so dispatchAndFormat gets "domain/skill" format
	target := wb.Skill
	if app.DomainScope != "" && !strings.Contains(target, "/") {
		target = app.DomainScope + "/" + target
	}

	cmd := slackCommand{
		Action: "run",
		Target: target,
		Input: map[string]any{
			"order_ids": orderIDs,
			"thread_ts": ev.TimeStamp,
			"channel":   ev.Channel,
			"trigger":   "watch_bot",
		},
		Text: ev.Text,
	}

	result, _ := m.dispatchAndFormat(app, ev.Channel, "", cmd, "", ev.TimeStamp)

	// Reply in thread under the bot's original message
	if blocks, fallback, ok := tryParseRichOutput(result); ok {
		postSlackBlocksWithTS(app.BotToken, ev.Channel, ev.TimeStamp, fallback, blocks)
	} else {
		postSlackThreadReply(app.BotToken, ev.Channel, ev.TimeStamp, result)
	}
}

// extractOrderIDs finds order ID patterns in text (e.g. AE1525IWPB00, US14UHB5BZ00, GB2201XKQR00).
func extractOrderIDs(text string) []string {
	re := regexp.MustCompile(`[A-Z]{2}\d{1,4}[A-Z0-9]{4,8}\d{2}`)
	matches := re.FindAllString(text, -1)
	// Deduplicate
	seen := make(map[string]bool, len(matches))
	var unique []string
	for _, m := range matches {
		if !seen[m] {
			seen[m] = true
			unique = append(unique, m)
		}
	}
	return unique
}

// ---------- Ops Genie: watch_bot handler (new path, does not touch ECM) ----------

// handleOpsGenieWatchBot processes Datadog alert messages for Ops Genie enrichment.
// This is a completely separate path from handleWatchBotMessage (ECM).
// The enricher is READ-ONLY — gateway handles all writes (incident store + Slack).
func (m *SlackSocketManager) handleOpsGenieWatchBot(app *config.SlackAppConfig, wb *config.WatchBotConfig, ev *slackevents.MessageEvent) {
	// Extract text from attachments (Datadog alerts have empty ev.Text, content in attachments)
	alertTitle, alertText := extractDatadogAlert(app.BotToken, ev)
	if alertTitle == "" && alertText == "" {
		slog.Debug("ops-genie: no alert content in message", "channel", ev.Channel)
		return
	}

	// Recovery message — resolve incident directly, no LLM needed ($0.00)
	if isRecoveryMessage(alertTitle) {
		slog.Info("ops-genie: recovery message detected", "title", alertTitle[:min(80, len(alertTitle))])
		// TODO: call incident-store MCP to resolve incident when MCP client is added to gateway
		return
	}

	// Noise skip list check
	if isSkippedMonitor(alertTitle, wb.SkipMonitors) {
		slog.Info("ops-genie: skipped (noise list)", "title", alertTitle[:min(80, len(alertTitle))])
		return
	}

	slog.Info("ops-genie: enriching alert",
		"app", app.Name,
		"channel", ev.Channel,
		"title", alertTitle[:min(100, len(alertTitle))],
	)

	// Dispatch to enricher skill (READ-ONLY — no write tools)
	target := wb.Skill
	if app.DomainScope != "" && !strings.Contains(target, "/") {
		target = app.DomainScope + "/" + target
	}
	parts := strings.SplitN(target, "/", 2)
	if len(parts) != 2 {
		slog.Error("ops-genie: invalid skill target", "target", target)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	// Call executor directly (bypass dispatchAndFormat to get raw JSON — Professor #3)
	rawResult, err := m.executor.Execute(ctx, parts[0], parts[1], executor.ExecuteRequest{
		InputData: map[string]any{
			"text":        alertTitle + "\n\n" + alertText,
			"alert_title": alertTitle,
			"alert_text":  alertText,
			"thread_ts":   ev.TimeStamp,
			"channel":     ev.Channel,
			"trigger":     "watch_bot",
			"mode":        "silent", // Phase 0: no Slack output
		},
	})
	if err != nil {
		slog.Error("ops-genie: enricher execution failed", "error", err, "channel", ev.Channel)
		return
	}

	// Post-process: validate + write incident + optionally post to pilot channel
	m.processOpsGenieResult(app, wb, ev, rawResult, alertTitle)
}

// processOpsGenieResult handles gateway-side validation and writes after enricher returns.
// The enricher is read-only — this function does all side effects.
func (m *SlackSocketManager) processOpsGenieResult(
	app *config.SlackAppConfig,
	wb *config.WatchBotConfig,
	ev *slackevents.MessageEvent,
	rawResult json.RawMessage,
	alertTitle string,
) {
	// Parse the executor response shape: {output: {fallback, rich_output, ...}}
	var execResult map[string]any
	if err := json.Unmarshal(rawResult, &execResult); err != nil {
		slog.Error("ops-genie: failed to parse executor response", "error", err, "raw_len", len(rawResult))
		return
	}

	// Extract the output field (where the enricher's task_complete payload lives)
	var output any
	if o, ok := execResult["output"]; ok {
		output = o
	} else {
		output = execResult
	}

	// Marshal output back to JSON string for tryParseRichOutput
	outputJSON, err := json.Marshal(output)
	if err != nil {
		slog.Error("ops-genie: failed to marshal output", "error", err)
		return
	}

	// Extract logging fields from the rich_output (enricher's structured output)
	outputMap, _ := output.(map[string]any)
	richOutput, _ := outputMap["rich_output"].(map[string]any)
	title, _ := richOutput["title"].(string)
	status, _ := richOutput["status"].(string)
	fallback, _ := outputMap["fallback"].(string)

	slog.Info("ops-genie: enrichment complete",
		"title", title,
		"status", status,
		"channel", ev.Channel,
		"alert_title", alertTitle[:min(80, len(alertTitle))],
		"fallback_preview", fallback[:min(120, len(fallback))],
	)

	// Phase 0 (silent): no Slack output if output_channel is empty
	outputChannel := wb.OutputChannel
	if outputChannel == "" {
		return
	}

	// Render rich_output as Slack Block Kit (same as ECM watch_bot does)
	if blocks, fb, ok := tryParseRichOutput(string(outputJSON)); ok {
		if fb == "" {
			fb = title
		}
		postSlackBlocksWithTS(app.BotToken, outputChannel, "", fb, blocks)
		return
	}

	// Fallback: if rich_output parsing failed, post the fallback text
	if fallback != "" {
		postSlackThreadReply(app.BotToken, outputChannel, "", fmt.Sprintf("*%s*\n%s", alertTitle, fallback))
	} else {
		postSlackThreadReply(app.BotToken, outputChannel, "", fmt.Sprintf("*%s*\n_(enrichment returned no rich_output)_", alertTitle))
	}
}

// extractDatadogAlert fetches the full message via Slack API to get attachments.
// slackevents.MessageEvent doesn't expose attachments, so we re-fetch using conversations.history.
// This adds one API call (~100ms) per alert, well within Slack rate limits.
func extractDatadogAlert(botToken string, ev *slackevents.MessageEvent) (title string, text string) {
	// If ev.Text has content, use it directly (some integrations put text there)
	if ev.Text != "" {
		return ev.Text, ""
	}

	// Fetch full message with attachments via Slack API
	api := slack.New(botToken)
	params := &slack.GetConversationHistoryParameters{
		ChannelID: ev.Channel,
		Latest:    ev.TimeStamp,
		Inclusive: true,
		Limit:     1,
	}
	history, err := api.GetConversationHistory(params)
	if err != nil {
		slog.Error("ops-genie: failed to fetch message for attachments", "error", err, "channel", ev.Channel, "ts", ev.TimeStamp)
		return "", ""
	}
	if len(history.Messages) == 0 {
		return "", ""
	}

	msg := history.Messages[0]

	// Datadog alerts: content is in attachments[0].title and attachments[0].text
	if len(msg.Attachments) > 0 {
		att := msg.Attachments[0]
		return att.Title, att.Text
	}

	// Fallback to message text
	return msg.Text, ""
}

// isRecoveryMessage checks if a Datadog alert title indicates recovery.
func isRecoveryMessage(title string) bool {
	lower := strings.ToLower(title)
	return strings.HasPrefix(lower, "recovered:") ||
		strings.HasPrefix(lower, "recovered ") ||
		strings.Contains(lower, "[recovered]")
}

// isSkippedMonitor checks if an alert title matches any pattern in the noise skip list.
func isSkippedMonitor(title string, skipPatterns []string) bool {
	lower := strings.ToLower(title)
	for _, pattern := range skipPatterns {
		if strings.Contains(lower, strings.ToLower(pattern)) {
			return true
		}
	}
	return false
}
