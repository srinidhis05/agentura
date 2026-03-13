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
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
	"github.com/agentura-ai/agentura/gateway/internal/domain"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

const deliveryTTL = 10 * time.Minute

var (
	githubWebhookRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agentura_github_webhook_requests_total",
		Help: "Total GitHub webhook requests by event, action, and status",
	}, []string{"event", "action", "status"})

	// execIDPattern matches <!-- agentura:exec:EXEC-xxx:domain/skill -->
	execIDPattern = regexp.MustCompile(`<!-- agentura:exec:(EXEC-[^:]+):([^/]+)/([^ ]+) -->`)

	// recentDeliveries deduplicates GitHub webhook retries by X-GitHub-Delivery header.
	recentDeliveries sync.Map
)

func init() {
	// Background cleanup of expired delivery IDs
	go func() {
		for {
			time.Sleep(deliveryTTL)
			now := time.Now()
			recentDeliveries.Range(func(key, value any) bool {
				if ts, ok := value.(time.Time); ok && now.Sub(ts) > deliveryTTL {
					recentDeliveries.Delete(key)
				}
				return true
			})
		}
	}()
}

func isDuplicateDelivery(deliveryID string) bool {
	if deliveryID == "" {
		return false
	}
	_, loaded := recentDeliveries.LoadOrStore(deliveryID, time.Now())
	return loaded
}

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

	if isDuplicateDelivery(deliveryID) {
		githubWebhookRequestsTotal.WithLabelValues(event, "", "duplicate").Inc()
		slog.Debug("duplicate github webhook delivery", "delivery_id", deliveryID, "event", event)
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "duplicate", "delivery_id": deliveryID})
		return
	}

	switch event {
	case "pull_request":
		h.handlePullRequest(w, body, deliveryID)
	case "issue_comment":
		h.handleIssueComment(w, body, deliveryID)
	case "issues":
		h.handleIssue(w, body, deliveryID)
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

	// Check for @agentura mention before exec ID matching
	if strings.Contains(payload.Comment.Body, "@agentura") {
		mention := domain.MentionEvent{
			DeliveryID: deliveryID,
			PRNumber:   payload.Issue.Number,
			Repo:       payload.Repository.FullName,
			Body:       payload.Comment.Body,
			Sender:     payload.Sender.Login,
			CommentID:  payload.Comment.ID,
		}

		slog.Info("github @agentura mention received",
			"delivery_id", deliveryID,
			"repo", mention.Repo,
			"pr", mention.PRNumber,
			"sender", mention.Sender,
		)

		githubWebhookRequestsTotal.WithLabelValues("issue_comment", "created", "mention").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{
			"status":      "accepted",
			"delivery_id": deliveryID,
			"type":        "mention",
		})

		go h.dispatchMention(mention)
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

func (h *GitHubWebhookHandler) handleIssue(w http.ResponseWriter, body []byte, deliveryID string) {
	var payload struct {
		Action string `json:"action"`
		Issue  struct {
			Number int    `json:"number"`
			Title  string `json:"title"`
			Body   string `json:"body"`
		} `json:"issue"`
		Label *struct {
			Name string `json:"name"`
		} `json:"label"`
		Repository struct {
			FullName string `json:"full_name"`
		} `json:"repository"`
		Sender struct {
			Login string `json:"login"`
		} `json:"sender"`
	}

	if err := json.Unmarshal(body, &payload); err != nil {
		githubWebhookRequestsTotal.WithLabelValues("issues", "", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "invalid issues payload")
		return
	}

	// Only trigger on "labeled" action with the "implement" label
	if payload.Action != "labeled" || payload.Label == nil || payload.Label.Name != "implement" {
		githubWebhookRequestsTotal.WithLabelValues("issues", payload.Action, "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "action": payload.Action})
		return
	}

	issueEvent := domain.GitHubIssueEvent{
		DeliveryID:  deliveryID,
		Action:      payload.Action,
		IssueNumber: payload.Issue.Number,
		Title:       payload.Issue.Title,
		Body:        payload.Issue.Body,
		Repo:        payload.Repository.FullName,
		Sender:      payload.Sender.Login,
		Label:       payload.Label.Name,
	}

	slog.Info("github issue implement label received",
		"delivery_id", deliveryID,
		"repo", issueEvent.Repo,
		"issue", issueEvent.IssueNumber,
		"sender", issueEvent.Sender,
	)

	githubWebhookRequestsTotal.WithLabelValues("issues", "labeled", "accepted").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{
		"status":      "accepted",
		"delivery_id": deliveryID,
	})

	go h.dispatchIssueImplementation(issueEvent)
}

func (h *GitHubWebhookHandler) dispatchIssueImplementation(event domain.GitHubIssueEvent) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	input := map[string]interface{}{
		"issue_number": event.IssueNumber,
		"title":        event.Title,
		"body":         event.Body,
		"repo":         event.Repo,
		"sender":       event.Sender,
	}

	execReq := executor.ExecuteRequest{
		InputData: input,
	}

	_, err := h.executor.Execute(ctx, "dev", "pr-code-reviewer", execReq)
	if err != nil {
		slog.Error("issue implementation dispatch failed",
			"error", err,
			"delivery_id", event.DeliveryID,
			"repo", event.Repo,
			"issue", event.IssueNumber,
		)
		return
	}

	slog.Info("issue implementation dispatch completed",
		"delivery_id", event.DeliveryID,
		"repo", event.Repo,
		"issue", event.IssueNumber,
	)
}

func (h *GitHubWebhookHandler) dispatchPRPipeline(event domain.GitHubPREvent) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	eventJSON, err := json.Marshal(event)
	if err != nil {
		slog.Error("failed to marshal PR event", "error", err, "delivery_id", event.DeliveryID)
		return
	}

	// Wrap in ExecuteRequest format (GR-009: input_data wrapper required)
	payload, err := json.Marshal(map[string]json.RawMessage{"input_data": eventJSON})
	if err != nil {
		slog.Error("failed to wrap PR event", "error", err, "delivery_id", event.DeliveryID)
		return
	}

	// Dispatch to parallel fleet pipeline (preferred) with fallback to sequential
	_, err = h.executor.PostRaw(ctx, "/api/v1/pipelines/github-pr-parallel/execute", payload)
	if err != nil {
		slog.Warn("parallel PR pipeline dispatch failed, falling back to sequential",
			"error", err,
			"delivery_id", event.DeliveryID,
		)
		_, err = h.executor.PostRaw(ctx, "/api/v1/pipelines/github-pr/execute", payload)
		if err != nil {
			slog.Error("PR pipeline dispatch failed",
				"error", err,
				"delivery_id", event.DeliveryID,
				"repo", event.Repo,
				"pr", event.PRNumber,
			)
			return
		}
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

func (h *GitHubWebhookHandler) dispatchMention(mention domain.MentionEvent) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// Execute dev/triage skill with mention context
	input := map[string]interface{}{
		"pr_number":  mention.PRNumber,
		"repo":       mention.Repo,
		"comment":    mention.Body,
		"sender":     mention.Sender,
		"comment_id": mention.CommentID,
	}

	execReq := executor.ExecuteRequest{
		InputData: input,
	}

	result, err := h.executor.Execute(ctx, "dev", "triage", execReq)
	if err != nil {
		slog.Error("mention dispatch failed",
			"error", err,
			"delivery_id", mention.DeliveryID,
			"repo", mention.Repo,
			"pr", mention.PRNumber,
		)
		return
	}

	// Post skill result as a comment reply via executor endpoint
	commentPayload, _ := json.Marshal(map[string]interface{}{
		"repo":      mention.Repo,
		"pr_number": mention.PRNumber,
		"body":      extractResultBody(result),
	})
	_, err = h.executor.PostRaw(ctx, "/api/v1/github/comment", commentPayload)
	if err != nil {
		slog.Error("failed to post mention reply comment",
			"error", err,
			"delivery_id", mention.DeliveryID,
			"repo", mention.Repo,
			"pr", mention.PRNumber,
		)
		return
	}

	slog.Info("mention dispatch completed",
		"delivery_id", mention.DeliveryID,
		"repo", mention.Repo,
		"pr", mention.PRNumber,
	)
}

// extractResultBody pulls the human-readable output from a skill execution result.
func extractResultBody(result json.RawMessage) string {
	var parsed struct {
		Output string `json:"output"`
		Result string `json:"result"`
	}
	if err := json.Unmarshal(result, &parsed); err != nil {
		return string(result)
	}
	if parsed.Output != "" {
		return parsed.Output
	}
	if parsed.Result != "" {
		return parsed.Result
	}
	return string(result)
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

