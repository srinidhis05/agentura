package handler

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
	"github.com/agentura-ai/agentura/gateway/internal/domain"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

var (
	githubWebhookRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agentura_github_webhook_requests_total",
		Help: "Total GitHub webhook requests by event, action, and status",
	}, []string{"event", "action", "status"})

	// execIDPattern matches <!-- agentura:exec:EXEC-xxx:domain/skill -->
	execIDPattern = regexp.MustCompile(`<!-- agentura:exec:(EXEC-[^:]+):([^/]+)/([^ ]+) -->`)
)

// GitHubWebhookHandler processes GitHub webhook events for PR pipelines.
type GitHubWebhookHandler struct {
	executor *executor.Client
	cfg      config.GitHubWebhookConfig
}

// NewGitHubWebhookHandler creates a handler for GitHub webhooks.
func NewGitHubWebhookHandler(exec *executor.Client, cfg config.GitHubWebhookConfig) *GitHubWebhookHandler {
	return &GitHubWebhookHandler{executor: exec, cfg: cfg}
}

// Handle processes POST /api/v1/webhooks/github.
func (h *GitHubWebhookHandler) Handle(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		githubWebhookRequestsTotal.WithLabelValues("unknown", "", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "failed to read body")
		return
	}

	// Verify signature if secret is configured
	if h.cfg.Secret != "" && !isGitHubSecretPlaceholder(h.cfg.Secret) {
		sig := r.Header.Get("X-Hub-Signature-256")
		if sig == "" {
			githubWebhookRequestsTotal.WithLabelValues("unknown", "", "unauthorized").Inc()
			httputil.RespondError(w, http.StatusUnauthorized, "missing X-Hub-Signature-256 header")
			return
		}
		if !verifyGitHubSignature(body, sig, h.cfg.Secret) {
			githubWebhookRequestsTotal.WithLabelValues("unknown", "", "unauthorized").Inc()
			httputil.RespondError(w, http.StatusUnauthorized, "invalid webhook signature")
			return
		}
	}

	event := r.Header.Get("X-GitHub-Event")
	deliveryID := r.Header.Get("X-GitHub-Delivery")

	switch event {
	case "pull_request":
		h.handlePullRequest(w, body, deliveryID)
	case "issue_comment":
		h.handleIssueComment(w, body, deliveryID)
	default:
		githubWebhookRequestsTotal.WithLabelValues(event, "", "ignored").Inc()
		slog.Debug("github webhook ignored", "event", event, "delivery_id", deliveryID)
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "event": event})
	}
}

func (h *GitHubWebhookHandler) handlePullRequest(w http.ResponseWriter, body []byte, deliveryID string) {
	var payload struct {
		Action string `json:"action"`
		Number int    `json:"number"`
		PullRequest struct {
			Title   string `json:"title"`
			Body    string `json:"body"`
			HTMLURL string `json:"html_url"`
			DiffURL string `json:"diff_url"`
			Head    struct {
				Ref string `json:"ref"`
				SHA string `json:"sha"`
			} `json:"head"`
			Base struct {
				Ref string `json:"ref"`
			} `json:"base"`
		} `json:"pull_request"`
		Repository struct {
			FullName string `json:"full_name"`
		} `json:"repository"`
		Sender struct {
			Login string `json:"login"`
		} `json:"sender"`
	}

	if err := json.Unmarshal(body, &payload); err != nil {
		githubWebhookRequestsTotal.WithLabelValues("pull_request", "", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "invalid pull_request payload")
		return
	}

	action := domain.PRAction(payload.Action)
	switch action {
	case domain.PROpened, domain.PRSynchronize, domain.PRReviewRequested:
		// Process these actions
	default:
		githubWebhookRequestsTotal.WithLabelValues("pull_request", payload.Action, "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "action": payload.Action})
		return
	}

	prEvent := domain.GitHubPREvent{
		DeliveryID: deliveryID,
		Action:     action,
		PRNumber:   payload.Number,
		PRURL:      payload.PullRequest.HTMLURL,
		PRTitle:    payload.PullRequest.Title,
		PRBody:     payload.PullRequest.Body,
		DiffURL:    payload.PullRequest.DiffURL,
		HeadBranch: payload.PullRequest.Head.Ref,
		BaseBranch: payload.PullRequest.Base.Ref,
		HeadSHA:    payload.PullRequest.Head.SHA,
		Repo:       payload.Repository.FullName,
		Sender:     payload.Sender.Login,
	}

	slog.Info("github pr webhook received",
		"delivery_id", deliveryID,
		"repo", prEvent.Repo,
		"pr", prEvent.PRNumber,
		"action", string(prEvent.Action),
		"sender", prEvent.Sender,
	)

	// Respond 200 immediately, dispatch pipeline async (GitHub requires < 10s response)
	githubWebhookRequestsTotal.WithLabelValues("pull_request", payload.Action, "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{
		"status":      "accepted",
		"delivery_id": deliveryID,
	})

	go h.dispatchPRPipeline(prEvent)
}

func (h *GitHubWebhookHandler) handleIssueComment(w http.ResponseWriter, body []byte, deliveryID string) {
	var payload struct {
		Action  string `json:"action"`
		Comment struct {
			ID   int64  `json:"id"`
			Body string `json:"body"`
		} `json:"comment"`
		Issue struct {
			Number      int `json:"number"`
			PullRequest *struct {
				URL string `json:"url"`
			} `json:"pull_request"`
		} `json:"issue"`
		Repository struct {
			FullName string `json:"full_name"`
		} `json:"repository"`
		Sender struct {
			Login string `json:"login"`
		} `json:"sender"`
	}

	if err := json.Unmarshal(body, &payload); err != nil {
		githubWebhookRequestsTotal.WithLabelValues("issue_comment", "", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "invalid issue_comment payload")
		return
	}

	// Only process "created" comments on PRs
	if payload.Action != "created" || payload.Issue.PullRequest == nil {
		githubWebhookRequestsTotal.WithLabelValues("issue_comment", payload.Action, "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored"})
		return
	}

	// Check if the comment is a reply to an agentura bot comment by looking
	// for exec ID markers in the comment body's context. The developer reply
	// itself won't contain the marker — we need the parent. For now, check if
	// the reply body references an execution ID explicitly.
	matches := execIDPattern.FindStringSubmatch(payload.Comment.Body)
	if matches == nil {
		// Not referencing an agentura execution — ignore
		githubWebhookRequestsTotal.WithLabelValues("issue_comment", "created", "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "reason": "no exec id"})
		return
	}

	execID := matches[1]
	execDomain := matches[2]
	execSkill := matches[3]

	feedback := domain.CommentFeedback{
		DeliveryID:  deliveryID,
		PRNumber:    payload.Issue.Number,
		Repo:        payload.Repository.FullName,
		CommentBody: payload.Comment.Body,
		Sender:      payload.Sender.Login,
		InReplyTo:   payload.Comment.ID,
	}

	slog.Info("github comment feedback received",
		"delivery_id", deliveryID,
		"repo", feedback.Repo,
		"pr", feedback.PRNumber,
		"exec_id", execID,
		"domain", execDomain,
		"skill", execSkill,
	)

	// Respond immediately, dispatch correction async
	githubWebhookRequestsTotal.WithLabelValues("issue_comment", "created", "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{
		"status":      "accepted",
		"delivery_id": deliveryID,
		"exec_id":     execID,
	})

	go h.dispatchCorrection(execDomain, execSkill, execID, feedback)
}

func (h *GitHubWebhookHandler) dispatchPRPipeline(event domain.GitHubPREvent) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	payload, err := json.Marshal(event)
	if err != nil {
		slog.Error("failed to marshal PR event", "error", err, "delivery_id", event.DeliveryID)
		return
	}

	_, err = h.executor.PostRaw(ctx, "/api/v1/pipelines/github-pr", payload)
	if err != nil {
		slog.Error("PR pipeline dispatch failed",
			"error", err,
			"delivery_id", event.DeliveryID,
			"repo", event.Repo,
			"pr", event.PRNumber,
		)
		return
	}

	slog.Info("PR pipeline dispatch completed",
		"delivery_id", event.DeliveryID,
		"repo", event.Repo,
		"pr", event.PRNumber,
	)
}

func (h *GitHubWebhookHandler) dispatchCorrection(execDomain, skill, execID string, feedback domain.CommentFeedback) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	correctionBody := executor.CorrectRequest{
		ExecutionID: execID,
		Correction:  feedback.CommentBody,
	}

	_, err := h.executor.Correct(ctx, execDomain, skill, correctionBody)
	if err != nil {
		slog.Error("correction dispatch failed",
			"error", err,
			"exec_id", execID,
			"domain", execDomain,
			"skill", skill,
		)
		return
	}

	slog.Info("correction dispatch completed",
		"exec_id", execID,
		"domain", execDomain,
		"skill", skill,
	)
}

// verifyGitHubSignature validates the X-Hub-Signature-256 header.
// GitHub sends "sha256=<hex>" format (differs from generic webhook raw hex).
func verifyGitHubSignature(body []byte, signature, secret string) bool {
	if !strings.HasPrefix(signature, "sha256=") {
		return false
	}
	sigHex := strings.TrimPrefix(signature, "sha256=")

	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	expected := hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(expected), []byte(sigHex))
}

func isGitHubSecretPlaceholder(s string) bool {
	return s == "${GITHUB_WEBHOOK_SECRET}"
}

// buildSignature creates a sha256= prefixed HMAC signature (for testing).
func buildSignature(body []byte, secret string) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	return "sha256=" + hex.EncodeToString(mac.Sum(nil))
}

