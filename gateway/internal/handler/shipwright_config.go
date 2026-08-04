package handler

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"

	"gopkg.in/yaml.v3"
)

// ShipwrightConfig represents the .shipwright.yaml file in a repo.
type ShipwrightConfig struct {
	Version int `yaml:"version" json:"version"`

	Review struct {
		AutoReview *bool           `yaml:"auto_review" json:"auto_review"` // nil = true (default). false = manual only (/shipwright review)
		Agents     map[string]bool `yaml:"agents" json:"agents"`

		Severity struct {
			Profile     string `yaml:"profile" json:"profile"`
			MaxNitpicks int    `yaml:"max_nitpicks" json:"max_nitpicks"`
		} `yaml:"severity" json:"severity"`

		Focus     []string `yaml:"focus" json:"focus"`
		Standards []string `yaml:"standards" json:"standards"`
	} `yaml:"review" json:"review"`

	Lint struct {
		Commands []struct {
			Name     string `yaml:"name" json:"name"`
			Command  string `yaml:"command" json:"command"`
			Timeout  string `yaml:"timeout" json:"timeout"`
			Required bool   `yaml:"required" json:"required"`
		} `yaml:"commands" json:"commands"`
	} `yaml:"lint" json:"lint"`

	DeepReview struct {
		Enabled              bool     `yaml:"enabled" json:"enabled"`
		AutoTriggerOnApproval bool    `yaml:"auto_trigger_on_approval" json:"auto_trigger_on_approval"`
		CloneDepth           int      `yaml:"clone_depth" json:"clone_depth"`
		Checks               []string `yaml:"checks" json:"checks"`
	} `yaml:"deep_review" json:"deep_review"`

	Ignore []string `yaml:"ignore" json:"ignore"`

	Branches struct {
		Default       string   `yaml:"default" json:"default"`
		Production    string   `yaml:"production" json:"production"`
		ReviewTargets []string `yaml:"review_targets" json:"review_targets"`
	} `yaml:"branches" json:"branches"`
}

// fetchShipwrightConfig fetches .shipwright.yaml from the repo's default branch.
// Returns nil (not an error) if the file doesn't exist — repos without config
// get default behavior.
func fetchShipwrightConfig(ctx context.Context, repo, token string) *ShipwrightConfig {
	if repo == "" || token == "" {
		return nil
	}

	url := fmt.Sprintf("https://api.github.com/repos/%s/contents/.shipwright.yaml", repo)
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github+json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		slog.Debug("failed to fetch .shipwright.yaml", "error", err, "repo", repo)
		return nil
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		// No config file — use defaults
		return nil
	}
	if resp.StatusCode != http.StatusOK {
		slog.Debug(".shipwright.yaml fetch failed", "status", resp.StatusCode, "repo", repo)
		return nil
	}

	// GitHub Contents API returns base64-encoded content
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil
	}

	var ghFile struct {
		Content  string `json:"content"`
		Encoding string `json:"encoding"`
	}
	if err := json.Unmarshal(body, &ghFile); err != nil {
		return nil
	}

	var rawContent []byte
	if ghFile.Encoding == "base64" {
		rawContent, err = base64.StdEncoding.DecodeString(ghFile.Content)
		if err != nil {
			slog.Warn("failed to decode .shipwright.yaml content", "error", err, "repo", repo)
			return nil
		}
	} else {
		rawContent = []byte(ghFile.Content)
	}

	var cfg ShipwrightConfig
	if err := yaml.Unmarshal(rawContent, &cfg); err != nil {
		slog.Warn("failed to parse .shipwright.yaml", "error", err, "repo", repo)
		return nil
	}

	slog.Info("loaded .shipwright.yaml",
		"repo", repo,
		"agents", cfg.Review.Agents,
		"severity_profile", cfg.Review.Severity.Profile,
		"lint_commands", len(cfg.Lint.Commands),
		"ignore_patterns", len(cfg.Ignore),
	)
	return &cfg
}

// skipAgentsFromConfig converts the .shipwright.yaml agents map to a skip list.
// Agents set to false are added to the skip list.
func skipAgentsFromConfig(cfg *ShipwrightConfig) []string {
	if cfg == nil {
		return nil
	}

	// Map config agent names to pipeline agent IDs
	nameToID := map[string]string{
		"test-advisor":  "test-advisor",
		"doc-generator": "docs",
		"lint-runner":   "lint-runner",
		"code-reviewer": "reviewer",
	}

	var skip []string
	for name, enabled := range cfg.Review.Agents {
		if !enabled {
			if id, ok := nameToID[name]; ok {
				skip = append(skip, id)
			}
		}
	}
	return skip
}

// isAutoReviewDisabled checks if the repo has auto_review: false in .shipwright.yaml.
// Returns true if auto-review is disabled (manual trigger only).
func (h *GitHubWebhookHandler) isAutoReviewDisabled(repo string) bool {
	token := h.resolveToken(context.Background())
	cfg := fetchShipwrightConfig(context.Background(), repo, token)
	if cfg == nil {
		return false // no config = auto-review enabled (default)
	}
	if cfg.Review.AutoReview == nil {
		return false // nil = default = enabled
	}
	return !*cfg.Review.AutoReview
}

// shouldReviewBranch checks if a PR's base branch should be reviewed.
// Priority: .shipwright.yaml review_targets > repo default branch.
// This prevents reviewing PRs to non-primary branches (e.g., stage→main
// promotions in repos where stage is the default, or feature→feature PRs).
func (h *GitHubWebhookHandler) shouldReviewBranch(repo, baseBranch, repoDefaultBranch string) bool {
	// Fetch .shipwright.yaml to check configured review targets
	token := h.resolveToken(context.Background())
	if cfg := fetchShipwrightConfig(context.Background(), repo, token); cfg != nil {
		targets := cfg.Branches.ReviewTargets
		if len(targets) > 0 {
			for _, t := range targets {
				if t == baseBranch {
					return true
				}
			}
			slog.Debug("base branch not in .shipwright.yaml review_targets",
				"repo", repo, "base", baseBranch, "targets", targets)
			return false
		}
		// If review_targets is empty but default is set, use that
		if cfg.Branches.Default != "" {
			return baseBranch == cfg.Branches.Default
		}
	}

	// Fallback: only review PRs targeting the repo's default branch
	if repoDefaultBranch != "" {
		return baseBranch == repoDefaultBranch
	}

	// If we can't determine, allow (don't block)
	return true
}
