package handler

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

var (
	webhookRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agentura_webhook_requests_total",
		Help: "Total inbound webhook requests by channel and status",
	}, []string{"channel", "status"})
)

// WebhookHandler processes inbound messages from external channels.
type WebhookHandler struct {
	executor *executor.Client
	cfg      config.WebhookConfig
}

// NewWebhookHandler creates a handler for channel webhooks.
func NewWebhookHandler(exec *executor.Client, cfg config.WebhookConfig) *WebhookHandler {
	return &WebhookHandler{executor: exec, cfg: cfg}
}

// inboundRequest is the JSON body for POST /api/v1/channels/{channel}/inbound.
type inboundRequest struct {
	Source   string         `json:"source"`
	UserID   string         `json:"user_id,omitempty"`
	Text     string         `json:"text"`
	Domain   string         `json:"domain,omitempty"`
	Skill    string         `json:"skill,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// Inbound handles POST /api/v1/channels/{channel}/inbound.
func (h *WebhookHandler) Inbound(w http.ResponseWriter, r *http.Request) {
	channel := r.PathValue("channel")
	if channel == "" {
		webhookRequestsTotal.WithLabelValues("unknown", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "missing channel name")
		return
	}

	// Read body once for both HMAC verification and JSON decode
	body, err := io.ReadAll(r.Body)
	if err != nil {
		webhookRequestsTotal.WithLabelValues(channel, "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "failed to read body")
		return
	}

	// HMAC signature verification (optional — skipped if no secret configured)
	if h.cfg.Secret != "" && !isSecretPlaceholder(h.cfg.Secret) {
		sig := r.Header.Get("X-Webhook-Signature")
		if sig == "" {
			webhookRequestsTotal.WithLabelValues(channel, "unauthorized").Inc()
			httputil.RespondError(w, http.StatusUnauthorized, "missing X-Webhook-Signature header")
			return
		}
		if !verifyHMAC(body, sig, h.cfg.Secret) {
			webhookRequestsTotal.WithLabelValues(channel, "unauthorized").Inc()
			httputil.RespondError(w, http.StatusUnauthorized, "invalid webhook signature")
			return
		}
	}

	var req inboundRequest
	if err := json.Unmarshal(body, &req); err != nil {
		webhookRequestsTotal.WithLabelValues(channel, "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	slog.Info("webhook inbound",
		"channel", channel,
		"source", req.Source,
		"domain", req.Domain,
		"skill", req.Skill,
		"text_len", len(req.Text),
	)

	inputData := map[string]any{
		"trigger":  "webhook",
		"channel":  channel,
		"text":     req.Text,
		"user_id":  req.UserID,
		"metadata": req.Metadata,
	}

	if req.Domain != "" && req.Skill != "" {
		// Direct execution: domain + skill provided
		result, err := h.executor.Execute(r.Context(), req.Domain, req.Skill, executor.ExecuteRequest{
			InputData: inputData,
		})
		if err != nil {
			webhookRequestsTotal.WithLabelValues(channel, "error").Inc()
			slog.Error("webhook execution failed",
				"channel", channel, "domain", req.Domain,
				"skill", req.Skill, "error", err)
			httputil.RespondError(w, http.StatusBadGateway, "skill execution failed: "+err.Error())
			return
		}
		webhookRequestsTotal.WithLabelValues(channel, "success").Inc()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(result))
		return
	}

	// Auto-route through platform/classifier
	result, err := h.executor.Execute(r.Context(), "platform", "classifier", executor.ExecuteRequest{
		InputData: inputData,
	})
	if err != nil {
		webhookRequestsTotal.WithLabelValues(channel, "routed_error").Inc()
		slog.Error("webhook classifier failed", "channel", channel, "error", err)
		httputil.RespondError(w, http.StatusBadGateway, "classifier failed: "+err.Error())
		return
	}
	webhookRequestsTotal.WithLabelValues(channel, "routed").Inc()
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(result))
}

func verifyHMAC(body []byte, signature, secret string) bool {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	expected := hex.EncodeToString(mac.Sum(nil))
	return hmac.Equal([]byte(expected), []byte(signature))
}

func isSecretPlaceholder(s string) bool {
	return s == "${WEBHOOK_SECRET}"
}
