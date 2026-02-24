package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
)

// mockExecutor is a test HTTP server that mimics the Python executor.
func mockExecutor(t *testing.T, responses map[string]string) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := r.Method + " " + r.URL.Path
		resp, ok := responses[key]
		if !ok {
			t.Logf("mock executor: unhandled %s", key)
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintf(w, `{"error":"not found: %s"}`, key)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(resp))
	}))
}

// newTestMux creates a minimal mux with only executor-proxied routes.
// This avoids needing stubs for Market/Risk/Portfolio domain handlers.
func newTestMux(t *testing.T, mock *httptest.Server) http.Handler {
	t.Helper()
	client := executor.NewClient(mock.URL, 0)

	mux := http.NewServeMux()

	health := NewHealthHandler(func() error { return nil })
	mux.HandleFunc("GET /healthz", health.Healthz)
	mux.HandleFunc("GET /readyz", health.Readyz)

	skill := NewSkillHandler(client)
	mux.HandleFunc("POST /api/v1/skills", skill.CreateSkill)
	mux.HandleFunc("GET /api/v1/skills", skill.ListSkills)
	mux.HandleFunc("GET /api/v1/skills/{domain}/{skill}", skill.GetSkill)
	mux.HandleFunc("POST /api/v1/skills/{domain}/{skill}/execute", skill.ExecuteSkill)
	mux.HandleFunc("POST /api/v1/skills/{domain}/{skill}/correct", skill.Correct)
	mux.HandleFunc("GET /api/v1/executions", skill.ListExecutions)
	mux.HandleFunc("GET /api/v1/executions/{execution_id}", skill.GetExecution)
	mux.HandleFunc("GET /api/v1/analytics", skill.GetAnalytics)

	knowledge := NewKnowledgeHandler(client)
	mux.HandleFunc("GET /api/v1/knowledge/reflexions", knowledge.ListReflexions)
	mux.HandleFunc("GET /api/v1/knowledge/corrections", knowledge.ListCorrections)
	mux.HandleFunc("GET /api/v1/knowledge/tests", knowledge.ListTests)
	mux.HandleFunc("GET /api/v1/knowledge/stats", knowledge.GetStats)
	mux.HandleFunc("POST /api/v1/knowledge/search/{domain}/{skill}", knowledge.SemanticSearch)
	mux.HandleFunc("POST /api/v1/knowledge/validate/{domain}/{skill}", knowledge.ValidateTests)

	domain := NewDomainHandler(client)
	mux.HandleFunc("GET /api/v1/domains", domain.ListDomains)
	mux.HandleFunc("GET /api/v1/domains/{domain}", domain.GetDomain)

	events := NewEventsHandler(client)
	mux.HandleFunc("GET /api/v1/events", events.ListEvents)

	platform := NewPlatformHandler(client)
	mux.HandleFunc("GET /api/v1/platform/health", platform.GetHealth)

	return mux
}

func TestRoutes(t *testing.T) {
	tests := []struct {
		name       string
		method     string
		path       string
		mockKey    string
		mockResp   string
		body       string
		wantStatus int
	}{
		{
			name:       "healthz",
			method:     "GET",
			path:       "/healthz",
			wantStatus: http.StatusOK,
		},
		{
			name:       "create skill",
			method:     "POST",
			path:       "/api/v1/skills",
			mockKey:    "POST /api/v1/skills",
			mockResp:   `{"domain":"hr","name":"resume-screen","skill_path":"hr/resume-screen","is_new_domain":true}`,
			body:       `{"domain":"hr","name":"resume-screen","role":"specialist"}`,
			wantStatus: http.StatusCreated,
		},
		{
			name:       "list skills",
			method:     "GET",
			path:       "/api/v1/skills",
			mockKey:    "GET /api/v1/skills",
			mockResp:   `[{"name":"test","domain":"ecm"}]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "get skill detail",
			method:     "GET",
			path:       "/api/v1/skills/ecm/order-details",
			mockKey:    "GET /api/v1/skills/ecm/order-details",
			mockResp:   `{"name":"order-details","domain":"ecm"}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "list executions",
			method:     "GET",
			path:       "/api/v1/executions",
			mockKey:    "GET /api/v1/executions",
			mockResp:   `[]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "get analytics",
			method:     "GET",
			path:       "/api/v1/analytics",
			mockKey:    "GET /api/v1/analytics",
			mockResp:   `{"total_executions":5}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "list reflexions",
			method:     "GET",
			path:       "/api/v1/knowledge/reflexions",
			mockKey:    "GET /api/v1/knowledge/reflexions",
			mockResp:   `[{"reflexion_id":"REFL-001"}]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "list corrections",
			method:     "GET",
			path:       "/api/v1/knowledge/corrections",
			mockKey:    "GET /api/v1/knowledge/corrections",
			mockResp:   `[]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "list tests",
			method:     "GET",
			path:       "/api/v1/knowledge/tests",
			mockKey:    "GET /api/v1/knowledge/tests",
			mockResp:   `[]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "knowledge stats",
			method:     "GET",
			path:       "/api/v1/knowledge/stats",
			mockKey:    "GET /api/v1/knowledge/stats",
			mockResp:   `{"total_corrections":3}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "list domains",
			method:     "GET",
			path:       "/api/v1/domains",
			mockKey:    "GET /api/v1/domains",
			mockResp:   `[{"name":"ecm"}]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "get domain detail",
			method:     "GET",
			path:       "/api/v1/domains/ecm",
			mockKey:    "GET /api/v1/domains/ecm",
			mockResp:   `{"name":"ecm","skills_count":3}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "list events",
			method:     "GET",
			path:       "/api/v1/events",
			mockKey:    "GET /api/v1/events",
			mockResp:   `[]`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "platform health",
			method:     "GET",
			path:       "/api/v1/platform/health",
			mockKey:    "GET /api/v1/platform/health",
			mockResp:   `{"gateway":{"status":"healthy"}}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "execute skill",
			method:     "POST",
			path:       "/api/v1/skills/ecm/order-details/execute",
			mockKey:    "POST /api/v1/skills/ecm/order-details/execute",
			mockResp:   `{"skill_name":"order-details","success":true}`,
			body:       `{"input_data":{"query":"test"},"dry_run":true}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "correct skill",
			method:     "POST",
			path:       "/api/v1/skills/ecm/order-details/correct",
			mockKey:    "POST /api/v1/skills/ecm/order-details/correct",
			mockResp:   `{"correction_id":"CORR-001","reflexion_id":"REFL-001"}`,
			body:       `{"execution_id":"EXEC-001","correction":"fix this"}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "semantic search",
			method:     "POST",
			path:       "/api/v1/knowledge/search/ecm/order-details",
			mockKey:    "POST /api/v1/knowledge/search/ecm/order-details",
			mockResp:   `{"results":[{"rule":"Check compliance"}],"backend":"mem0"}`,
			body:       `{"query":"compliance","limit":5}`,
			wantStatus: http.StatusOK,
		},
		{
			name:       "validate tests",
			method:     "POST",
			path:       "/api/v1/knowledge/validate/ecm/order-details",
			mockKey:    "POST /api/v1/knowledge/validate/ecm/order-details",
			mockResp:   `{"skill":"ecm/order-details","tests_run":2,"tests_passed":2}`,
			body:       `{}`,
			wantStatus: http.StatusOK,
		},
	}

	// Build combined mock responses
	responses := make(map[string]string)
	for _, tt := range tests {
		if tt.mockKey != "" {
			responses[tt.mockKey] = tt.mockResp
		}
	}

	mock := mockExecutor(t, responses)
	defer mock.Close()

	router := newTestMux(t, mock)

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var req *http.Request
			if tt.body != "" {
				req = httptest.NewRequest(tt.method, tt.path, strings.NewReader(tt.body))
				req.Header.Set("Content-Type", "application/json")
			} else {
				req = httptest.NewRequest(tt.method, tt.path, nil)
			}

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tt.wantStatus {
				t.Errorf("got status %d, want %d (body: %s)", w.Code, tt.wantStatus, w.Body.String())
			}

			// Verify JSON response for API routes
			if tt.mockResp != "" && w.Code == http.StatusOK {
				ct := w.Header().Get("Content-Type")
				if ct != "application/json" {
					t.Errorf("got content-type %q, want application/json", ct)
				}
				// Verify response is valid JSON
				if !json.Valid(w.Body.Bytes()) {
					t.Errorf("response is not valid JSON: %s", w.Body.String())
				}
			}
		})
	}
}

func TestExecutorError(t *testing.T) {
	// Mock that returns errors
	mock := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"error":"executor down"}`))
	}))
	defer mock.Close()

	router := newTestMux(t, mock)

	req := httptest.NewRequest("GET", "/api/v1/skills", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// Gateway should return 502 when executor fails
	if w.Code != http.StatusBadGateway {
		t.Errorf("got status %d, want 502 (body: %s)", w.Code, w.Body.String())
	}
}
