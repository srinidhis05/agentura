package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
)

var (
	heartbeatExecutionsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agentura_heartbeat_executions_total",
		Help: "Total heartbeat executions by domain and status",
	}, []string{"domain", "status"})

	heartbeatExecutionDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "agentura_heartbeat_execution_duration_seconds",
		Help:    "Duration of heartbeat executions",
		Buckets: prometheus.DefBuckets,
	}, []string{"domain"})

	heartbeatSuppressedTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agentura_heartbeat_suppressed_total",
		Help: "Total suppressed heartbeat outputs (HEARTBEAT_OK)",
	}, []string{"domain"})
)

// HeartbeatRunner manages periodic heartbeat executions for agent coordinators.
type HeartbeatRunner struct {
	executor  *executor.Client
	agents    []config.AgentHeartbeatEntry
	slackApps []config.SlackAppConfig
	mu        sync.RWMutex
	running   bool
	stopCh    chan struct{}
}

// NewHeartbeatRunner creates a runner for agent heartbeats.
func NewHeartbeatRunner(exec *executor.Client, agents []config.AgentHeartbeatEntry, slackApps []config.SlackAppConfig) *HeartbeatRunner {
	return &HeartbeatRunner{
		executor:  exec,
		agents:    agents,
		slackApps: slackApps,
		stopCh:    make(chan struct{}),
	}
}

// Start launches heartbeat timers for each configured agent.
func (h *HeartbeatRunner) Start(ctx context.Context) {
	if len(h.agents) == 0 {
		slog.Info("heartbeat runner: no agents configured")
		return
	}

	h.mu.Lock()
	h.running = true
	h.mu.Unlock()

	for _, agent := range h.agents {
		interval, err := time.ParseDuration(agent.Heartbeat.Every)
		if err != nil {
			slog.Error("heartbeat runner: invalid interval",
				"domain", agent.Domain, "every", agent.Heartbeat.Every, "error", err)
			continue
		}

		slog.Info("heartbeat runner: starting",
			"domain", agent.Domain,
			"coordinator", agent.Coordinator,
			"interval", interval,
			"target", agent.Heartbeat.Target,
			"active_hours", fmt.Sprintf("%s-%s %s",
				agent.Heartbeat.ActiveHours.Start,
				agent.Heartbeat.ActiveHours.End,
				agent.Heartbeat.ActiveHours.Timezone),
		)

		go h.runLoop(ctx, agent, interval)
	}
}

// Stop shuts down all heartbeat timers.
func (h *HeartbeatRunner) Stop() {
	h.mu.Lock()
	defer h.mu.Unlock()

	if !h.running {
		return
	}
	h.running = false
	close(h.stopCh)
	slog.Info("heartbeat runner stopped")
}

// IsRunning returns whether the runner is active.
func (h *HeartbeatRunner) IsRunning() bool {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.running
}

// AgentCount returns the number of configured agents.
func (h *HeartbeatRunner) AgentCount() int {
	return len(h.agents)
}

func (h *HeartbeatRunner) runLoop(ctx context.Context, agent config.AgentHeartbeatEntry, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			h.runHeartbeat(ctx, agent)
		case <-h.stopCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

func (h *HeartbeatRunner) runHeartbeat(ctx context.Context, agent config.AgentHeartbeatEntry) {
	domain := agent.Domain

	if !isWithinActiveHours(agent.Heartbeat.ActiveHours) {
		slog.Debug("heartbeat: outside active hours, skipping",
			"domain", domain)
		return
	}

	slog.Info("heartbeat: executing",
		"domain", domain,
		"coordinator", agent.Coordinator)

	start := time.Now()
	execCtx, cancel := context.WithTimeout(ctx, 10*time.Minute)
	defer cancel()

	req := executor.ExecuteRequest{
		InputData: map[string]any{
			"trigger":          "heartbeat",
			"light_context":    agent.Heartbeat.LightContext,
			"isolated_session": agent.Heartbeat.IsolatedSession,
		},
	}

	resp, err := h.executor.Execute(execCtx, domain, "heartbeat", req)
	duration := time.Since(start).Seconds()
	heartbeatExecutionDuration.WithLabelValues(domain).Observe(duration)

	if err != nil {
		heartbeatExecutionsTotal.WithLabelValues(domain, "error").Inc()
		slog.Error("heartbeat: execution failed",
			"domain", domain, "duration_s", duration, "error", err)
		if ch := agent.Heartbeat.Observe; ch != "" {
			if token := h.findBotToken(domain); token != "" {
				postSlackMessageFromService(token, ch,
					fmt.Sprintf(":x: *%s* heartbeat failed (%.1fs): %s", domain, duration, err.Error()))
			}
		}
		return
	}

	output := extractHeartbeatOutput(resp)

	if isExecutorError(output) {
		heartbeatExecutionsTotal.WithLabelValues(domain, "error").Inc()
		slog.Error("heartbeat: executor returned error in output",
			"domain", domain, "duration_s", duration,
			"output_preview", truncateOutput(output, 200))
		if ch := agent.Heartbeat.Observe; ch != "" {
			if token := h.findBotToken(domain); token != "" {
				postSlackMessageFromService(token, ch,
					fmt.Sprintf(":x: *%s* heartbeat executor error (%.1fs): %s", domain, duration, truncateOutput(output, 300)))
			}
		}
		return
	}

	if isHeartbeatOK(output, agent.Heartbeat.AckMaxChars) {
		heartbeatExecutionsTotal.WithLabelValues(domain, "ok").Inc()
		heartbeatSuppressedTotal.WithLabelValues(domain).Inc()
		slog.Info("heartbeat: HEARTBEAT_OK — suppressed",
			"domain", domain, "duration_s", duration)
		// Notify observe channel even when suppressed
		if ch := agent.Heartbeat.Observe; ch != "" {
			if token := h.findBotToken(domain); token != "" {
				postSlackMessageFromService(token, ch,
					fmt.Sprintf(":white_check_mark: *%s* heartbeat OK (%.1fs)", domain, duration))
			}
		}
		return
	}

	heartbeatExecutionsTotal.WithLabelValues(domain, "alert").Inc()
	slog.Info("heartbeat: alert detected, delivering",
		"domain", domain, "duration_s", duration,
		"output_len", len(output))

	h.deliverAlert(agent, output)
}

// extractHeartbeatOutput pulls the output from the executor response.
// If the output contains rich_output, returns it as JSON for Block Kit rendering.
// Otherwise returns raw text for plain posting.
func extractHeartbeatOutput(resp json.RawMessage) string {
	var result map[string]any
	if err := json.Unmarshal(resp, &result); err != nil {
		return string(resp)
	}

	if output, ok := result["output"].(map[string]any); ok {
		// If output has rich_output, return it as JSON so Block Kit renderer picks it up
		if _, hasRich := output["rich_output"]; hasRich {
			b, err := json.Marshal(output)
			if err == nil {
				return string(b)
			}
		}
		if raw, ok := output["raw_output"].(string); ok && raw != "" {
			return raw
		}
		if summary, ok := output["summary"].(string); ok && summary != "" {
			return summary
		}
	}

	if response, ok := result["response"].(string); ok {
		return response
	}

	return string(resp)
}

// isExecutorError detects when executor output contains an upstream API/runtime error
// rather than actual skill output. Prevents raw errors from being posted to Slack.
func isExecutorError(output string) bool {
	errorPatterns := []string{
		"Error code: 4",           // HTTP 4xx from Anthropic/OpenRouter
		"Error code: 5",           // HTTP 5xx
		"credit balance is too low",
		"rate_limit_error",
		"authentication_error",
		"overloaded_error",
		"Traceback (most recent",  // Python stack trace from executor
	}
	for _, p := range errorPatterns {
		if strings.Contains(output, p) {
			return true
		}
	}
	return false
}

// isHeartbeatOK returns true if the response indicates nothing needs attention.
// Suppresses if HEARTBEAT_OK appears anywhere and there's no "due" payload.
func isHeartbeatOK(response string, ackMaxChars int) bool {
	if strings.Contains(response, "HEARTBEAT_OK") && !strings.Contains(response, "\"due\"") {
		return true
	}
	return false
}

// heartbeatDuePayload is the JSON structure returned by the heartbeat skill.
type heartbeatDuePayload struct {
	Due     []string `json:"due"`
	Message string   `json:"message"`
}

// deliverAlert parses the heartbeat output, posts a formatted Slack message,
// and triggers each due skill.
func (h *HeartbeatRunner) deliverAlert(agent config.AgentHeartbeatEntry, output string) {
	target := agent.Heartbeat.Target
	if target == "" || target == "none" {
		return
	}

	botToken := h.findBotToken(agent.Domain)
	if botToken == "" {
		slog.Error("heartbeat: no bot token found", "domain", agent.Domain)
		return
	}

	// Try to parse the due payload — strip markdown fences and backticks
	var payload heartbeatDuePayload
	cleaned := strings.TrimSpace(output)
	cleaned = strings.TrimPrefix(cleaned, "```json")
	cleaned = strings.TrimPrefix(cleaned, "```")
	cleaned = strings.TrimSuffix(cleaned, "```")
	cleaned = strings.Trim(cleaned, "` \n\r\t")

	// Observe channel gets operational notifications; target gets only skill output
	observeChannel := agent.Heartbeat.Observe

	if err := json.Unmarshal([]byte(cleaned), &payload); err != nil || len(payload.Due) == 0 {
		// Couldn't parse — log it, post to observe only
		if observeChannel != "" {
			postSlackMessageFromService(botToken, observeChannel,
				fmt.Sprintf(":warning: *%s* heartbeat returned unparseable output (%d chars)", agent.Domain, len(output)))
		}
		slog.Info("heartbeat: alert delivered (raw)", "domain", agent.Domain)
		return
	}

	// Post "skills due" notification to observe channel only (operational noise)
	skillList := strings.Join(payload.Due, ", ")
	msg := fmt.Sprintf(":heartbeat: *%d skill(s) due:* %s", len(payload.Due), skillList)
	if observeChannel != "" {
		postSlackMessageFromService(botToken, observeChannel, msg)
	}
	slog.Info("heartbeat: skills due", "domain", agent.Domain, "skills", skillList)

	// Trigger each due skill — deliver output to target channel, failures to observe
	for _, skill := range payload.Due {
		go h.triggerDueSkill(agent.Domain, skill, target, observeChannel, botToken)
	}

	slog.Info("heartbeat: dispatched due skills",
		"domain", agent.Domain, "skills", payload.Due)
}

// triggerDueSkill executes a single due skill and delivers its output to Slack.
// Skills that call task_complete with rich_output get Block Kit rendering.
// Skills with Slack MCP tools may also self-post (canvas updates, etc.).
func (h *HeartbeatRunner) triggerDueSkill(domain, skill, targetChannel, observeChannel, botToken string) {
	slog.Info("heartbeat: triggering skill", "domain", domain, "skill", skill)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	req := executor.ExecuteRequest{
		InputData: map[string]any{
			"trigger": "heartbeat",
		},
	}

	resp, err := h.executor.Execute(ctx, domain, skill, req)
	if err != nil {
		slog.Error("heartbeat: skill execution failed",
			"domain", domain, "skill", skill, "error", err)
		if observeChannel != "" {
			postSlackMessageFromService(botToken, observeChannel,
				fmt.Sprintf(":x: *%s* failed: %s", skill, err.Error()))
		}
		return
	}

	slog.Info("heartbeat: skill completed", "domain", domain, "skill", skill)

	// Deliver skill output to the target channel (Block Kit if rich_output present)
	if targetChannel != "" && botToken != "" {
		output := extractHeartbeatOutput(resp)
		if output != "" && !isHeartbeatOK(output, 0) {
			postSkillOutputToSlack(botToken, targetChannel, skill, output)
		}
	}
}

// findBotToken looks up the Slack bot token for a domain from configured apps.
func (h *HeartbeatRunner) findBotToken(domain string) string {
	for _, app := range h.slackApps {
		if app.DomainScope == domain {
			if app.BotToken != "" && !isPlaceholder(app.BotToken) {
				return app.BotToken
			}
		}
	}
	return ""
}

// isWithinActiveHours checks if the current time falls within the configured window.
func isWithinActiveHours(ah config.ActiveHoursConfig) bool {
	if ah.Start == "" && ah.End == "" {
		return true // no restriction
	}

	loc, err := time.LoadLocation(ah.Timezone)
	if err != nil {
		loc = time.UTC
	}

	now := time.Now().In(loc)
	startH, startM := parseHHMM(ah.Start)
	endH, endM := parseHHMM(ah.End)

	nowMinutes := now.Hour()*60 + now.Minute()
	startMinutes := startH*60 + startM
	endMinutes := endH*60 + endM

	if startMinutes <= endMinutes {
		return nowMinutes >= startMinutes && nowMinutes <= endMinutes
	}
	// Wraps midnight (e.g. 22:00 - 06:00)
	return nowMinutes >= startMinutes || nowMinutes <= endMinutes
}

// parseHHMM parses "HH:MM" to hours and minutes.
func parseHHMM(s string) (int, int) {
	var h, m int
	fmt.Sscanf(s, "%d:%d", &h, &m)
	return h, m
}

// truncateOutput trims output to maxLen characters for Slack posting.
func truncateOutput(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "\n... (truncated)"
}

// isPlaceholder checks if a string is an unresolved env var placeholder.
func isPlaceholder(s string) bool {
	return strings.HasPrefix(s, "${") && strings.HasSuffix(s, "}")
}
