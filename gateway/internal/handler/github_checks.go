package handler

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"
)

// checkRunRequest is the GitHub API payload for creating/updating a check run.
type checkRunRequest struct {
	Name       string          `json:"name"`
	HeadSHA    string          `json:"head_sha"`
	Status     string          `json:"status"`               // "queued", "in_progress", "completed"
	Conclusion string          `json:"conclusion,omitempty"`  // "success", "failure", "action_required", "neutral"
	StartedAt  string          `json:"started_at,omitempty"`
	CompletedAt string         `json:"completed_at,omitempty"`
	Output     *checkRunOutput `json:"output,omitempty"`
}

type checkRunOutput struct {
	Title   string `json:"title"`
	Summary string `json:"summary"`
}

// createCheckRun creates a GitHub check run and returns its ID.
// Returns 0 on error (non-fatal — review still runs, just no status indicator).
func (h *GitHubWebhookHandler) createCheckRun(ctx context.Context, repo, headSHA, name, status string) int64 {
	token := h.resolveToken(ctx)
	if token == "" {
		slog.Debug("no github token — skipping check run creation")
		return 0
	}

	body := checkRunRequest{
		Name:      name,
		HeadSHA:   headSHA,
		Status:    status,
		StartedAt: time.Now().UTC().Format(time.RFC3339),
		Output: &checkRunOutput{
			Title:   name + " — in progress",
			Summary: "Shipwright is reviewing this PR. Results will be posted as a comment when complete.",
		},
	}

	payload, _ := json.Marshal(body)
	url := fmt.Sprintf("https://api.github.com/repos/%s/check-runs", repo)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		slog.Warn("failed to create check run request", "error", err)
		return 0
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		slog.Warn("failed to create check run", "error", err, "repo", repo)
		return 0
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		respBody, _ := io.ReadAll(resp.Body)
		slog.Warn("check run creation failed",
			"status", resp.StatusCode,
			"repo", repo,
			"response", string(respBody[:minInt(len(respBody), 200)]),
		)
		return 0
	}

	var result struct {
		ID int64 `json:"id"`
	}
	json.NewDecoder(resp.Body).Decode(&result)

	slog.Info("check run created", "repo", repo, "check_run_id", result.ID, "name", name)
	return result.ID
}

// completeCheckRun updates an existing check run to completed status.
func (h *GitHubWebhookHandler) completeCheckRun(ctx context.Context, repo string, checkRunID int64, conclusion, title, summary string) {
	if checkRunID == 0 {
		return
	}

	token := h.resolveToken(ctx)
	if token == "" {
		return
	}

	body := map[string]any{
		"status":       "completed",
		"conclusion":   conclusion,
		"completed_at": time.Now().UTC().Format(time.RFC3339),
		"output": map[string]string{
			"title":   title,
			"summary": summary,
		},
	}

	payload, _ := json.Marshal(body)
	url := fmt.Sprintf("https://api.github.com/repos/%s/check-runs/%d", repo, checkRunID)
	req, err := http.NewRequestWithContext(ctx, http.MethodPatch, url, bytes.NewReader(payload))
	if err != nil {
		slog.Warn("failed to build check run update request", "error", err)
		return
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		slog.Warn("failed to update check run", "error", err, "repo", repo, "check_run_id", checkRunID)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		slog.Warn("check run update failed",
			"status", resp.StatusCode,
			"repo", repo,
			"check_run_id", checkRunID,
			"response", string(respBody[:minInt(len(respBody), 200)]),
		)
		return
	}

	slog.Info("check run completed", "repo", repo, "check_run_id", checkRunID, "conclusion", conclusion)
}

// addLabel adds a label to a PR via GitHub API. Non-fatal on failure.
func (h *GitHubWebhookHandler) addLabel(ctx context.Context, repo string, prNumber int, label string) {
	token := h.resolveToken(ctx)
	if token == "" {
		return
	}

	url := fmt.Sprintf("https://api.github.com/repos/%s/issues/%d/labels", repo, prNumber)
	payload, _ := json.Marshal(map[string][]string{"labels": {label}})

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		slog.Debug("failed to add label", "error", err, "repo", repo, "pr", prNumber)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode < 300 {
		slog.Info("added label to PR", "repo", repo, "pr", prNumber, "label", label)
	}
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}
