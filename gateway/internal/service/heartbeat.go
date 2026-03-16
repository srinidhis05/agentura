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
		return
	}

	output := extractHeartbeatOutput(resp)

	if isHeartbeatOK(output, agent.Heartbeat.AckMaxChars) {
		heartbeatExecutionsTotal.WithLabelValues(domain, "ok").Inc()
		heartbeatSuppressedTotal.WithLabelValues(domain).Inc()
		slog.Info("heartbeat: HEARTBEAT_OK — suppressed",
			"domain", domain, "duration_s", duration)
		return
	}

	heartbeatExecutionsTotal.WithLabelValues(domain, "alert").Inc()
	slog.Info("heartbeat: alert detected, delivering",
		"domain", domain, "duration_s", duration,
		"output_len", len(output))

	h.deliverAlert(agent, output)
}

// extractHeartbeatOutput pulls the raw text output from the executor response.
func extractHeartbeatOutput(resp json.RawMessage) string {
	var result map[string]any
	if err := json.Unmarshal(resp, &result); err != nil {
		return string(resp)
	}

	if output, ok := result["output"].(map[string]any); ok {
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

// isHeartbeatOK returns true if the response indicates nothing needs attention.
func isHeartbeatOK(response string, ackMaxChars int) bool {
	trimmed := strings.TrimSpace(response)

	if trimmed == "HEARTBEAT_OK" {
		return true
	}

	// Check if response starts or ends with HEARTBEAT_OK with minimal content
	cleaned := trimmed
	cleaned = strings.TrimPrefix(cleaned, "HEARTBEAT_OK")
	cleaned = strings.TrimSuffix(cleaned, "HEARTBEAT_OK")
	cleaned = strings.TrimSpace(cleaned)

	if strings.Contains(trimmed, "HEARTBEAT_OK") && len(cleaned) <= ackMaxChars {
		return true
	}

	return false
}

// deliverAlert posts the heartbeat output to the configured Slack channel.
func (h *HeartbeatRunner) deliverAlert(agent config.AgentHeartbeatEntry, output string) {
	target := agent.Heartbeat.Target
	if target == "" || target == "none" {
		slog.Debug("heartbeat: no delivery target configured",
			"domain", agent.Domain)
		return
	}

	botToken := h.findBotToken(agent.Domain)
	if botToken == "" {
		slog.Error("heartbeat: no bot token found for domain",
			"domain", agent.Domain)
		return
	}

	_, err := postSlackMessageFromService(botToken, target, output)
	if err != nil {
		slog.Error("heartbeat: failed to deliver alert",
			"domain", agent.Domain,
			"target", target,
			"error", err)
		return
	}

	slog.Info("heartbeat: alert delivered",
		"domain", agent.Domain, "target", target)
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

// isPlaceholder checks if a string is an unresolved env var placeholder.
func isPlaceholder(s string) bool {
	return strings.HasPrefix(s, "${") && strings.HasSuffix(s, "}")
}
