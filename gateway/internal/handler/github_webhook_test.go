package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
)

func TestVerifyGitHubSignature(t *testing.T) {
	secret := "test-secret-123"
	body := []byte(`{"action":"opened","number":42}`)

	tests := []struct {
		name string
		sig  string
		want bool
	}{
		{
			name: "valid signature",
			sig:  buildSignature(body, secret),
			want: true,
		},
		{
			name: "invalid signature",
			sig:  "sha256=0000000000000000000000000000000000000000000000000000000000000000",
			want: false,
		},
		{
			name: "missing sha256 prefix",
			sig:  "abc123",
			want: false,
		},
		{
			name: "empty signature",
			sig:  "",
			want: false,
		},
		{
			name: "wrong secret",
			sig:  buildSignature(body, "wrong-secret"),
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := verifyGitHubSignature(body, tt.sig, secret)
			if got != tt.want {
				t.Errorf("verifyGitHubSignature() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGitHubWebhookHandler_PullRequest(t *testing.T) {
	prPayload := `{
		"action": "opened",
		"number": 42,
		"pull_request": {
			"title": "feat: add new feature",
			"body": "This PR adds a new feature",
			"html_url": "https://github.com/owner/repo/pull/42",
			"diff_url": "https://github.com/owner/repo/pull/42.diff",
			"head": {"ref": "feat/new-feature", "sha": "abc123"},
			"base": {"ref": "main"}
		},
		"repository": {"full_name": "owner/repo"},
		"sender": {"login": "developer"}
	}`

	tests := []struct {
		name       string
		event      string
		action     string
		body       string
		secret     string
		addSig     bool
		wantStatus int
		wantBody   string
	}{
		{
			name:       "opened PR accepted",
			event:      "pull_request",
			action:     "opened",
			body:       prPayload,
			secret:     "test-secret",
			addSig:     true,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"accepted"`,
		},
		{
			name:       "synchronize PR accepted",
			event:      "pull_request",
			body:       strings.Replace(prPayload, `"opened"`, `"synchronize"`, 1),
			secret:     "test-secret",
			addSig:     true,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"accepted"`,
		},
		{
			name:       "closed PR ignored",
			event:      "pull_request",
			body:       strings.Replace(prPayload, `"opened"`, `"closed"`, 1),
			secret:     "test-secret",
			addSig:     true,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"ignored"`,
		},
		{
			name:       "missing signature returns 401",
			event:      "pull_request",
			body:       prPayload,
			secret:     "test-secret",
			addSig:     false,
			wantStatus: http.StatusUnauthorized,
		},
		{
			name:       "unknown event ignored",
			event:      "push",
			body:       `{}`,
			secret:     "test-secret",
			addSig:     true,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"ignored"`,
		},
		{
			name:       "no secret configured skips verification",
			event:      "pull_request",
			body:       prPayload,
			secret:     "",
			addSig:     false,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"accepted"`,
		},
		{
			name:       "placeholder secret skips verification",
			event:      "pull_request",
			body:       prPayload,
			secret:     "${GITHUB_WEBHOOK_SECRET}",
			addSig:     false,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"accepted"`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Mock executor that accepts pipeline dispatch
			mock := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusOK)
				w.Write([]byte(`{"status":"ok"}`))
			}))
			defer mock.Close()

			client := executor.NewClient(mock.URL, 30*time.Second)
			h := NewGitHubWebhookHandler(client, config.GitHubWebhookConfig{
				Enabled: true,
				Secret:  tt.secret,
			})

			req := httptest.NewRequest("POST", "/api/v1/webhooks/github", strings.NewReader(tt.body))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("X-GitHub-Event", tt.event)
			req.Header.Set("X-GitHub-Delivery", "test-delivery-123")

			if tt.addSig && tt.secret != "" && !isGitHubSecretPlaceholder(tt.secret) {
				req.Header.Set("X-Hub-Signature-256", buildSignature([]byte(tt.body), tt.secret))
			}

			w := httptest.NewRecorder()
			h.Handle(w, req)

			if w.Code != tt.wantStatus {
				t.Errorf("got status %d, want %d (body: %s)", w.Code, tt.wantStatus, w.Body.String())
			}

			if tt.wantBody != "" && !strings.Contains(w.Body.String(), tt.wantBody) {
				t.Errorf("body %q does not contain %q", w.Body.String(), tt.wantBody)
			}
		})
	}
}

func TestGitHubWebhookHandler_IssueComment(t *testing.T) {
	tests := []struct {
		name       string
		body       string
		wantStatus int
		wantBody   string
	}{
		{
			name: "comment with exec ID accepted",
			body: `{
				"action": "created",
				"comment": {
					"id": 12345,
					"body": "This review was wrong. <!-- agentura:exec:EXEC-20250226:dev/github-pr-reviewer -->"
				},
				"issue": {
					"number": 42,
					"pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/42"}
				},
				"repository": {"full_name": "owner/repo"},
				"sender": {"login": "developer"}
			}`,
			wantStatus: http.StatusOK,
			wantBody:   `"exec_id":"EXEC-20250226"`,
		},
		{
			name: "comment without exec ID ignored",
			body: `{
				"action": "created",
				"comment": {"id": 12345, "body": "Looks good to me!"},
				"issue": {
					"number": 42,
					"pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/42"}
				},
				"repository": {"full_name": "owner/repo"},
				"sender": {"login": "developer"}
			}`,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"ignored"`,
		},
		{
			name: "comment on issue (not PR) ignored",
			body: `{
				"action": "created",
				"comment": {"id": 12345, "body": "hello"},
				"issue": {"number": 10},
				"repository": {"full_name": "owner/repo"},
				"sender": {"login": "developer"}
			}`,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"ignored"`,
		},
		{
			name: "edited comment ignored",
			body: `{
				"action": "edited",
				"comment": {"id": 12345, "body": "updated text"},
				"issue": {
					"number": 42,
					"pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/42"}
				},
				"repository": {"full_name": "owner/repo"},
				"sender": {"login": "developer"}
			}`,
			wantStatus: http.StatusOK,
			wantBody:   `"status":"ignored"`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusOK)
				w.Write([]byte(`{"status":"ok"}`))
			}))
			defer mock.Close()

			client := executor.NewClient(mock.URL, 30*time.Second)
			h := NewGitHubWebhookHandler(client, config.GitHubWebhookConfig{
				Enabled: true,
				Secret:  "", // No signature check for comment tests
			})

			req := httptest.NewRequest("POST", "/api/v1/webhooks/github", strings.NewReader(tt.body))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("X-GitHub-Event", "issue_comment")
			req.Header.Set("X-GitHub-Delivery", "test-delivery-456")

			w := httptest.NewRecorder()
			h.Handle(w, req)

			if w.Code != tt.wantStatus {
				t.Errorf("got status %d, want %d (body: %s)", w.Code, tt.wantStatus, w.Body.String())
			}

			if tt.wantBody != "" && !strings.Contains(w.Body.String(), tt.wantBody) {
				t.Errorf("body %q does not contain %q", w.Body.String(), tt.wantBody)
			}
		})
	}
}

func TestExecIDPattern(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		wantMatch bool
		wantExec  string
		wantDom   string
		wantSkill string
	}{
		{
			name:      "standard marker",
			input:     "<!-- agentura:exec:EXEC-20250226120000:dev/github-pr-reviewer -->",
			wantMatch: true,
			wantExec:  "EXEC-20250226120000",
			wantDom:   "dev",
			wantSkill: "github-pr-reviewer",
		},
		{
			name:      "marker embedded in comment",
			input:     "This was wrong. <!-- agentura:exec:EXEC-123:dev/pr-doc-generator --> Please fix.",
			wantMatch: true,
			wantExec:  "EXEC-123",
			wantDom:   "dev",
			wantSkill: "pr-doc-generator",
		},
		{
			name:      "no marker",
			input:     "Just a normal comment",
			wantMatch: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			matches := execIDPattern.FindStringSubmatch(tt.input)
			if tt.wantMatch {
				if matches == nil {
					t.Fatal("expected match but got none")
				}
				if matches[1] != tt.wantExec {
					t.Errorf("exec_id = %q, want %q", matches[1], tt.wantExec)
				}
				if matches[2] != tt.wantDom {
					t.Errorf("domain = %q, want %q", matches[2], tt.wantDom)
				}
				if matches[3] != tt.wantSkill {
					t.Errorf("skill = %q, want %q", matches[3], tt.wantSkill)
				}
			} else {
				if matches != nil {
					t.Errorf("expected no match but got %v", matches)
				}
			}
		})
	}
}

// Ensure json import is used (via test helpers above).
var _ = json.Valid
