package handler

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
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
	// recentPRReviews deduplicates PR reviews by repo+PR+headSHA to avoid posting
	// duplicate reviews when GitHub sends multiple events for the same commit.
	recentPRReviews sync.Map
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
			recentPRReviews.Range(func(key, value any) bool {
				if ts, ok := value.(time.Time); ok && now.Sub(ts) > prReviewCooldown {
					recentPRReviews.Delete(key)
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

// prReviewCooldown controls how often the same PR can be auto-reviewed.
// 8 hours: review once on open, skip subsequent pushes for a full work session.
// Manual /shipwright review bypasses this (goes through issue_comment handler, not here).
const prReviewCooldown = 8 * time.Hour

// isDuplicatePRReview checks if we've dispatched a review for this repo+PR
// within the cooldown window. Uses both in-memory cache AND persistent DB check
// so the dedup survives gateway restarts.
func isDuplicatePRReview(repo string, prNumber int, headSHA string) bool {
	if repo == "" {
		return false
	}
	key := fmt.Sprintf("%s#%d", repo, prNumber)
	now := time.Now()

	// In-memory fast path
	if prev, loaded := recentPRReviews.Load(key); loaded {
		if ts, ok := prev.(time.Time); ok && now.Sub(ts) < prReviewCooldown {
			slog.Info("skipping duplicate PR review (in-memory cooldown)",
				"repo", repo, "pr", prNumber, "sha", headSHA[:7],
				"last_review_ago", now.Sub(ts).Round(time.Second))
			return true
		}
	}

	// Persistent check: query executor for recent fleet sessions for this PR.
	// This survives gateway restarts — the in-memory check is just a fast path.
	if isDuplicateInFleetStore(repo, prNumber) {
		slog.Info("skipping duplicate PR review (fleet store cooldown)",
			"repo", repo, "pr", prNumber, "sha", headSHA[:7])
		recentPRReviews.Store(key, now) // warm the in-memory cache
		return true
	}

	recentPRReviews.Store(key, now)
	return false
}

// isDuplicateInFleetStore checks the executor's fleet store for a recent
// session for this repo+PR. Returns true if a session was created in the
// last 5 minutes (meaning a review is already in progress or just completed).
func isDuplicateInFleetStore(repo string, prNumber int) bool {
	// Query the executor's fleet sessions API
	url := fmt.Sprintf("http://executor:8000/api/v1/fleet/sessions?repo=%s&pr=%d&limit=1",
		repo, prNumber)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return false
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return false // executor unreachable — allow the review
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return false
	}

	var sessions []struct {
		CreatedAt string `json:"created_at"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&sessions); err != nil {
		return false
	}
	if len(sessions) == 0 {
		return false
	}

	// Check if the most recent session was created within cooldown
	created, err := time.Parse(time.RFC3339Nano, sessions[0].CreatedAt)
	if err != nil {
		// Try alternate format
		created, err = time.Parse("2006-01-02T15:04:05.999999-07:00", sessions[0].CreatedAt)
		if err != nil {
			return false
		}
	}
	return time.Since(created) < prReviewCooldown
}

// GitHubTokenProvider generates fresh GitHub API tokens on demand.
type GitHubTokenProvider interface {
	Token(ctx context.Context) (string, error)
}

// GitHubWebhookHandler processes GitHub webhook events for PR pipelines.
type GitHubWebhookHandler struct {
	executor      *executor.Client
	cfg           config.GitHubWebhookConfig
	tokenProvider GitHubTokenProvider
}

// NewGitHubWebhookHandler creates a handler for GitHub webhooks.
func NewGitHubWebhookHandler(exec *executor.Client, cfg config.GitHubWebhookConfig, tokenProvider GitHubTokenProvider) *GitHubWebhookHandler {
	return &GitHubWebhookHandler{executor: exec, cfg: cfg, tokenProvider: tokenProvider}
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
	case "pull_request_review":
		h.handlePullRequestReview(w, body, deliveryID)
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
			FullName      string `json:"full_name"`
			DefaultBranch string `json:"default_branch"`
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

	// Handle "ready-to-merge" label → trigger deep review
	if action == domain.PRLabeled {
		var labelPayload struct {
			Label *struct {
				Name string `json:"name"`
			} `json:"label"`
		}
		_ = json.Unmarshal(body, &labelPayload)
		if labelPayload.Label != nil && labelPayload.Label.Name == "ready-to-merge" {
			slog.Info("github ready-to-merge label added",
				"delivery_id", deliveryID,
				"repo", payload.Repository.FullName,
				"pr", payload.Number,
			)
			githubWebhookRequestsTotal.WithLabelValues("pull_request", "labeled", "deep-review").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{
				"status":      "accepted",
				"delivery_id": deliveryID,
				"type":        "deep-review",
			})
			go h.dispatchDeepReview(deliveryID, payload.Repository.FullName, payload.Number, payload.Sender.Login)
			return
		}
		githubWebhookRequestsTotal.WithLabelValues("pull_request", "labeled", "ignored").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ignored", "action": "labeled"})
		return
	}

	switch action {
	case domain.PROpened:
		// Always review on PR open — first look at the code
	case domain.PRSynchronize:
		// Review on push — but dedup check in executor will skip posting
		// if findings are unchanged from last review
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
		"base_branch", prEvent.BaseBranch,
		"sender", prEvent.Sender,
	)

	// Auto-review filter: repos with auto_review: false in .shipwright.yaml
	// only get reviewed via /shipwright review comments, not on PR open/synchronize.
	if h.isAutoReviewDisabled(prEvent.Repo) {
		slog.Info("skipping auto-review — repo has auto_review: false",
			"repo", prEvent.Repo, "pr", prEvent.PRNumber)
		githubWebhookRequestsTotal.WithLabelValues("pull_request", payload.Action, "auto_disabled").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{
			"status": "skipped",
			"reason": "auto_review disabled — use /shipwright review to trigger manually",
		})
		return
	}

	// Base branch filter: only review PRs targeting configured branches.
	// Uses .shipwright.yaml review_targets if available, otherwise repo default branch.
	if !h.shouldReviewBranch(prEvent.Repo, prEvent.BaseBranch, payload.Repository.DefaultBranch) {
		slog.Info("skipping PR — base branch not in review targets",
			"repo", prEvent.Repo, "pr", prEvent.PRNumber,
			"base_branch", prEvent.BaseBranch,
			"default_branch", payload.Repository.DefaultBranch,
		)
		githubWebhookRequestsTotal.WithLabelValues("pull_request", payload.Action, "branch_filtered").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{
			"status":      "skipped",
			"reason":      "base branch not in review targets",
			"base_branch": prEvent.BaseBranch,
		})
		return
	}

	// Dedup: skip if we've already dispatched a review for this repo+PR+SHA
	if isDuplicatePRReview(prEvent.Repo, prEvent.PRNumber, prEvent.HeadSHA) {
		githubWebhookRequestsTotal.WithLabelValues("pull_request", payload.Action, "duplicate").Inc()
		httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "duplicate", "delivery_id": deliveryID})
		return
	}

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

	// Check for review commands on PRs
	commentBody := strings.TrimSpace(payload.Comment.Body)
	if payload.Issue.PullRequest != nil {
		// Deep review: /deep-review or /shipwright deep-review
		if commentBody == "/deep-review" || commentBody == "/shipwright deep-review" {
			slog.Info("github deep-review command received",
				"delivery_id", deliveryID,
				"repo", payload.Repository.FullName,
				"pr", payload.Issue.Number,
				"sender", payload.Sender.Login,
				"command", commentBody,
			)

			githubWebhookRequestsTotal.WithLabelValues("issue_comment", "created", "deep-review").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{
				"status":      "accepted",
				"delivery_id": deliveryID,
				"type":        "deep-review",
			})

			go h.dispatchDeepReview(deliveryID, payload.Repository.FullName, payload.Issue.Number, payload.Sender.Login)
			return
		}

		// Diff review: /shipwright review — triggers the parallel review pipeline
		if commentBody == "/shipwright review" {
			slog.Info("github shipwright review command received",
				"delivery_id", deliveryID,
				"repo", payload.Repository.FullName,
				"pr", payload.Issue.Number,
				"sender", payload.Sender.Login,
			)

			githubWebhookRequestsTotal.WithLabelValues("issue_comment", "created", "shipwright-review").Inc()
			httputil.RespondJSON(w, http.StatusOK, map[string]string{
				"status":      "accepted",
				"delivery_id": deliveryID,
				"type":        "review",
			})

			go h.dispatchReviewFromComment(deliveryID, payload.Repository.FullName, payload.Issue.Number, payload.Sender.Login)
			return
		}
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
		"issue_number":  event.IssueNumber,
		"title":         event.Title,
		"body":          event.Body,
		"repo":          event.Repo,
		"sender":        event.Sender,
		"github_token":  h.resolveToken(ctx),
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

	// Create GitHub check run — developer sees "Shipwright is reviewing" immediately
	checkRunID := h.createCheckRun(ctx, event.Repo, event.HeadSHA, "shipwright/review", "in_progress")

	// Fetch diff content and changed files from GitHub API
	h.enrichPREvent(ctx, &event)

	inputData := h.buildInputData(ctx, event)
	if inputData == nil {
		slog.Error("failed to build input data", "delivery_id", event.DeliveryID)
		h.completeCheckRun(ctx, event.Repo, checkRunID, "neutral", "Shipwright Review — Error", "Failed to build input data. This does not block merge.")
		return
	}

	// Wrap in ExecuteRequest format (GR-009: input_data wrapper required)
	inputJSON, err := json.Marshal(inputData)
	if err != nil {
		slog.Error("failed to marshal input data", "error", err, "delivery_id", event.DeliveryID)
		h.completeCheckRun(ctx, event.Repo, checkRunID, "neutral", "Shipwright Review — Error", "Internal error. This does not block merge.")
		return
	}
	payload, err := json.Marshal(map[string]json.RawMessage{"input_data": inputJSON})
	if err != nil {
		slog.Error("failed to wrap PR event", "error", err, "delivery_id", event.DeliveryID)
		h.completeCheckRun(ctx, event.Repo, checkRunID, "neutral", "Shipwright Review — Error", "Internal error. This does not block merge.")
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
			h.completeCheckRun(ctx, event.Repo, checkRunID, "neutral", "Shipwright Review — Incomplete", "Pipeline execution failed. Re-trigger with /shipwright review. This does not block merge.")
			return
		}
	}

	h.completeCheckRun(ctx, event.Repo, checkRunID, "success", "Shipwright Review — Complete", "Review posted as a PR comment.")

	// Add "shipwright-reviewed" label to trigger post-merge learning pipeline
	h.addLabel(ctx, event.Repo, event.PRNumber, "shipwright-reviewed")

	slog.Info("PR pipeline dispatch completed",
		"delivery_id", event.DeliveryID,
		"repo", event.Repo,
		"pr", event.PRNumber,
		"diff_size", len(event.Diff),
		"changed_files", len(event.ChangedFiles),
	)
}

// handlePullRequestReview handles pull_request_review events.
// When a reviewer approves, trigger the deep review merge gate pipeline.
func (h *GitHubWebhookHandler) handlePullRequestReview(w http.ResponseWriter, body []byte, deliveryID string) {
	var payload struct {
		Action string `json:"action"`
		Review struct {
			State string `json:"state"`
		} `json:"review"`
		PullRequest struct {
			Number  int    `json:"number"`
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
		githubWebhookRequestsTotal.WithLabelValues("pull_request_review", "", "error").Inc()
		httputil.RespondError(w, http.StatusBadRequest, "invalid pull_request_review payload")
		return
	}

	// Deep review is manual-only: /shipwright deep-review command.
	// Auto-trigger on approval is disabled — too noisy during beta.
	// To re-enable: check .shipwright.yaml deep_review.auto_trigger_on_approval
	githubWebhookRequestsTotal.WithLabelValues("pull_request_review", payload.Action, "skipped").Inc()
	httputil.RespondJSON(w, http.StatusOK, map[string]string{
		"status": "skipped",
		"reason": "deep review is manual-only — use /shipwright deep-review",
	})
}

// dispatchDeepReview fetches PR data and dispatches the merge gate pipeline.
// dispatchReviewFromComment triggers the parallel review pipeline from a /shipwright review comment.
func (h *GitHubWebhookHandler) dispatchReviewFromComment(deliveryID, repo string, prNumber int, sender string) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	prData, err := h.fetchPRDetails(ctx, repo, prNumber)
	if err != nil {
		slog.Error("failed to fetch PR details for review command",
			"error", err, "delivery_id", deliveryID, "repo", repo, "pr", prNumber)
		return
	}

	event := domain.GitHubPREvent{
		DeliveryID: deliveryID,
		Action:     "review_command",
		PRNumber:   prNumber,
		PRURL:      prData.HTMLURL,
		PRTitle:    prData.Title,
		PRBody:     prData.Body,
		DiffURL:    prData.DiffURL,
		HeadBranch: prData.HeadRef,
		BaseBranch: prData.BaseRef,
		HeadSHA:    prData.HeadSHA,
		Repo:       repo,
		Sender:     sender,
	}

	h.dispatchPRPipeline(event)
}

func (h *GitHubWebhookHandler) dispatchDeepReview(deliveryID, repo string, prNumber int, sender string) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	// Fetch PR details from GitHub API to build the event
	prData, err := h.fetchPRDetails(ctx, repo, prNumber)
	if err != nil {
		slog.Error("failed to fetch PR details for deep review",
			"error", err,
			"delivery_id", deliveryID,
			"repo", repo,
			"pr", prNumber,
		)
		return
	}

	// Create GitHub check run — developer sees "Deep review in progress" immediately
	checkRunID := h.createCheckRun(ctx, repo, prData.HeadSHA, "shipwright/deep-review", "in_progress")

	event := domain.GitHubPREvent{
		DeliveryID: deliveryID,
		Action:     "deep_review",
		PRNumber:   prNumber,
		PRURL:      prData.HTMLURL,
		PRTitle:    prData.Title,
		PRBody:     prData.Body,
		DiffURL:    prData.DiffURL,
		HeadBranch: prData.HeadRef,
		BaseBranch: prData.BaseRef,
		HeadSHA:    prData.HeadSHA,
		Repo:       repo,
		Sender:     sender,
	}

	// Enrich with diff and changed files
	h.enrichPREvent(ctx, &event)

	inputData := h.buildInputData(ctx, event)
	if inputData == nil {
		slog.Error("failed to build deep review input data", "delivery_id", deliveryID)
		h.completeCheckRun(ctx, repo, checkRunID, "neutral", "Deep Review — Error", "Failed to build input data. This does not block merge.")
		return
	}

	inputJSON, err := json.Marshal(inputData)
	if err != nil {
		slog.Error("failed to marshal deep review input data", "error", err, "delivery_id", deliveryID)
		h.completeCheckRun(ctx, repo, checkRunID, "neutral", "Deep Review — Error", "Internal error. This does not block merge.")
		return
	}

	payload, err := json.Marshal(map[string]json.RawMessage{"input_data": inputJSON})
	if err != nil {
		slog.Error("failed to wrap deep review event", "error", err, "delivery_id", deliveryID)
		h.completeCheckRun(ctx, repo, checkRunID, "neutral", "Deep Review — Error", "Internal error. This does not block merge.")
		return
	}

	_, err = h.executor.PostRaw(ctx, "/api/v1/pipelines/github-pr-merge-gate/execute", payload)
	if err != nil {
		slog.Error("deep review pipeline dispatch failed",
			"error", err,
			"delivery_id", deliveryID,
			"repo", repo,
			"pr", prNumber,
		)
		h.completeCheckRun(ctx, repo, checkRunID, "neutral", "Deep Review — Incomplete", "Pipeline execution failed. Re-trigger with /shipwright deep-review. This does not block merge.")
		return
	}

	h.completeCheckRun(ctx, repo, checkRunID, "success", "Deep Review — Complete", "Deep review posted as a PR comment.")

	slog.Info("deep review pipeline dispatch completed",
		"delivery_id", deliveryID,
		"repo", repo,
		"pr", prNumber,
		"diff_size", len(event.Diff),
	)
}

// enrichPREvent fetches the diff content and changed files from GitHub and populates the event.
func (h *GitHubWebhookHandler) enrichPREvent(ctx context.Context, event *domain.GitHubPREvent) {
	token := h.resolveToken(ctx)

	if event.Repo != "" && event.PRNumber > 0 {
		diff, err := fetchDiff(ctx, event.Repo, event.PRNumber, token)
		if err != nil {
			slog.Warn("failed to fetch PR diff, proceeding without it",
				"error", err,
				"repo", event.Repo,
				"pr", event.PRNumber,
			)
		} else {
			event.Diff = diff
			slog.Info("fetched PR diff",
				"repo", event.Repo,
				"pr", event.PRNumber,
				"diff_bytes", len(diff),
			)
		}
	}

	if event.Repo != "" && event.PRNumber > 0 {
		files, err := fetchChangedFiles(ctx, event.Repo, event.PRNumber, token)
		if err != nil {
			slog.Warn("failed to fetch changed files, proceeding without them",
				"error", err,
				"repo", event.Repo,
				"pr", event.PRNumber,
			)
		} else {
			event.ChangedFiles = files
			slog.Info("fetched changed files",
				"repo", event.Repo,
				"pr", event.PRNumber,
				"file_count", len(files),
			)
		}
	}
}

// prDetails holds the minimal PR info needed to construct a GitHubPREvent from the API.
type prDetails struct {
	HTMLURL string
	Title   string
	Body    string
	DiffURL string
	HeadRef string
	BaseRef string
	HeadSHA string
}

// fetchPRDetails fetches PR metadata from the GitHub API.
func (h *GitHubWebhookHandler) fetchPRDetails(ctx context.Context, repo string, prNumber int) (*prDetails, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/pulls/%d", repo, prNumber)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("creating PR details request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github.v3+json")
	if token := h.resolveToken(ctx); token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetching PR details: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("PR details returned %d", resp.StatusCode)
	}

	var pr struct {
		HTMLURL string `json:"html_url"`
		Title   string `json:"title"`
		Body    string `json:"body"`
		DiffURL string `json:"diff_url"`
		Head    struct {
			Ref string `json:"ref"`
			SHA string `json:"sha"`
		} `json:"head"`
		Base struct {
			Ref string `json:"ref"`
		} `json:"base"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&pr); err != nil {
		return nil, fmt.Errorf("decoding PR details: %w", err)
	}

	return &prDetails{
		HTMLURL: pr.HTMLURL,
		Title:   pr.Title,
		Body:    pr.Body,
		DiffURL: pr.DiffURL,
		HeadRef: pr.Head.Ref,
		BaseRef: pr.Base.Ref,
		HeadSHA: pr.Head.SHA,
	}, nil
}

// fetchDiff fetches the raw unified diff via the GitHub API (works for private repos).
// Uses the API endpoint with Accept: application/vnd.github.diff instead of the web diff URL.
func fetchDiff(ctx context.Context, repo string, prNumber int, token string) (string, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/pulls/%d", repo, prNumber)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return "", fmt.Errorf("creating diff request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github.diff")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("fetching diff: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("diff fetch returned %d", resp.StatusCode)
	}

	// Cap at 1MB to avoid blowing up the payload
	body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return "", fmt.Errorf("reading diff body: %w", err)
	}

	return string(body), nil
}

// fetchChangedFiles fetches the structured list of changed files from the GitHub API.
func fetchChangedFiles(ctx context.Context, repo string, prNumber int, token string) ([]domain.PRFile, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/pulls/%d/files?per_page=100", repo, prNumber)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("creating changed-files request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github.v3+json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetching changed files: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("changed-files fetch returned %d", resp.StatusCode)
	}

	var ghFiles []struct {
		Filename  string `json:"filename"`
		Status    string `json:"status"`
		Additions int    `json:"additions"`
		Deletions int    `json:"deletions"`
		Patch     string `json:"patch"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&ghFiles); err != nil {
		return nil, fmt.Errorf("decoding changed files: %w", err)
	}

	files := make([]domain.PRFile, len(ghFiles))
	for i, f := range ghFiles {
		files[i] = domain.PRFile{
			Filename:  f.Filename,
			Status:    f.Status,
			Additions: f.Additions,
			Deletions: f.Deletions,
			Patch:     f.Patch,
		}
	}
	return files, nil
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
		"pr_number":    mention.PRNumber,
		"repo":         mention.Repo,
		"comment":      mention.Body,
		"sender":       mention.Sender,
		"comment_id":   mention.CommentID,
		"github_token": h.resolveToken(ctx),
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

// buildInputData marshals an event struct to a map and injects the github_token.
func (h *GitHubWebhookHandler) buildInputData(ctx context.Context, event any) map[string]interface{} {
	raw, err := json.Marshal(event)
	if err != nil {
		return nil
	}
	var m map[string]interface{}
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil
	}
	token := h.resolveToken(ctx)
	if token != "" {
		m["github_token"] = token
	}

	// Fetch .shipwright.yaml from repo — drives agent skipping, severity, lint config
	repo, _ := m["Repo"].(string)
	if repo == "" {
		repo, _ = m["repo"].(string)
	}
	if cfg := fetchShipwrightConfig(ctx, repo, token); cfg != nil {
		m["shipwright_config"] = cfg
		// Pre-compute skip_agents so triage and pipeline engine can use it directly
		if skipList := skipAgentsFromConfig(cfg); len(skipList) > 0 {
			m["skip_agents"] = skipList
		}
	}

	return m
}

// resolveToken returns a fresh GitHub API token, preferring the TokenProvider
// over the static config token.
func (h *GitHubWebhookHandler) resolveToken(ctx context.Context) string {
	if h.tokenProvider != nil {
		token, err := h.tokenProvider.Token(ctx)
		if err != nil {
			slog.Warn("failed to generate GitHub App token, falling back to static token", "error", err)
		} else {
			return token
		}
	}
	return h.cfg.Token
}

// buildSignature creates a sha256= prefixed HMAC signature (for testing).
func buildSignature(body []byte, secret string) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	return "sha256=" + hex.EncodeToString(mac.Sum(nil))
}

