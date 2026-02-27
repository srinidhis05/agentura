package executor

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// SkillInfo is returned by the executor's list-skills endpoint.
type SkillInfo struct {
	Domain  string `json:"domain"`
	Name    string `json:"name"`
	Role    string `json:"role"`
	Model   string `json:"model"`
	Trigger string `json:"trigger"`
}

// ExecuteRequest is the body sent to the executor's execute endpoint.
type ExecuteRequest struct {
	InputData     map[string]any `json:"input_data"`
	ModelOverride *string        `json:"model_override,omitempty"`
	DryRun        bool           `json:"dry_run"`
}

// CorrectRequest is the body sent to the executor's correct endpoint.
type CorrectRequest struct {
	ExecutionID string `json:"execution_id"`
	Correction  string `json:"correction"`
}

// Client calls the Python skill executor over HTTP.
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// NewClient creates an executor client.
func NewClient(baseURL string, timeout time.Duration) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: timeout,
		},
	}
}

// CreateSkill scaffolds a new skill on the executor.
func (c *Client) CreateSkill(ctx context.Context, body json.RawMessage) (json.RawMessage, error) {
	return c.postJSON(ctx, "/api/v1/skills", body)
}

// ListSkills returns all available skills from the executor as raw JSON passthrough.
func (c *Client) ListSkills(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/skills")
}

// GetSkill returns full detail for a single skill as raw JSON passthrough.
func (c *Client) GetSkill(ctx context.Context, domain, skill string) (json.RawMessage, error) {
	return c.getJSON(ctx, fmt.Sprintf("/api/v1/skills/%s/%s", domain, skill))
}

func (c *Client) getJSON(ctx context.Context, path string) (json.RawMessage, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+path, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("calling executor: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("reading response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("executor returned %d: %s", resp.StatusCode, body)
	}

	return json.RawMessage(body), nil
}

// ListExecutions returns execution history as raw JSON passthrough.
func (c *Client) ListExecutions(ctx context.Context, query string) (json.RawMessage, error) {
	path := "/api/v1/executions"
	if query != "" {
		path += "?" + query
	}
	return c.getJSON(ctx, path)
}

// GetExecution returns execution detail with linked corrections/reflexions.
func (c *Client) GetExecution(ctx context.Context, executionID string) (json.RawMessage, error) {
	return c.getJSON(ctx, fmt.Sprintf("/api/v1/executions/%s", executionID))
}

// GetAnalytics returns aggregate platform metrics.
func (c *Client) GetAnalytics(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/analytics")
}

// Execute runs a skill on the executor.
func (c *Client) Execute(ctx context.Context, domain, skill string, body ExecuteRequest) (json.RawMessage, error) {
	return c.postJSON(ctx, fmt.Sprintf("/api/v1/skills/%s/%s/execute", domain, skill), body)
}

// Correct sends a correction to the executor.
func (c *Client) Correct(ctx context.Context, domain, skill string, body CorrectRequest) (json.RawMessage, error) {
	return c.postJSON(ctx, fmt.Sprintf("/api/v1/skills/%s/%s/correct", domain, skill), body)
}

// ListReflexions returns knowledge reflexions as raw JSON passthrough.
func (c *Client) ListReflexions(ctx context.Context, query string) (json.RawMessage, error) {
	path := "/api/v1/knowledge/reflexions"
	if query != "" {
		path += "?" + query
	}
	return c.getJSON(ctx, path)
}

// ListCorrections returns knowledge corrections as raw JSON passthrough.
func (c *Client) ListCorrections(ctx context.Context, query string) (json.RawMessage, error) {
	path := "/api/v1/knowledge/corrections"
	if query != "" {
		path += "?" + query
	}
	return c.getJSON(ctx, path)
}

// ListTests returns knowledge tests as raw JSON passthrough.
func (c *Client) ListTests(ctx context.Context, query string) (json.RawMessage, error) {
	path := "/api/v1/knowledge/tests"
	if query != "" {
		path += "?" + query
	}
	return c.getJSON(ctx, path)
}

// GetKnowledgeStats returns learning metrics as raw JSON passthrough.
func (c *Client) GetKnowledgeStats(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/knowledge/stats")
}

// ListPipelines returns all available pipeline definitions as raw JSON passthrough.
func (c *Client) ListPipelines(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/pipelines")
}

// ListDomains returns all domains with health metrics as raw JSON passthrough.
func (c *Client) ListDomains(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/domains")
}

// GetDomain returns domain detail with skill topology as raw JSON passthrough.
func (c *Client) GetDomain(ctx context.Context, domain string) (json.RawMessage, error) {
	return c.getJSON(ctx, fmt.Sprintf("/api/v1/domains/%s", domain))
}

// GetPlatformHealth returns component health statuses as raw JSON passthrough.
func (c *Client) GetPlatformHealth(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/platform/health")
}

// ValidateTests runs tests for a skill and updates reflexion validation status.
func (c *Client) ValidateTests(ctx context.Context, domain, skill string) (json.RawMessage, error) {
	return c.postJSON(ctx, fmt.Sprintf("/api/v1/knowledge/validate/%s/%s", domain, skill), struct{}{})
}

// SemanticSearch performs vector search across knowledge for a skill.
func (c *Client) SemanticSearch(ctx context.Context, domain, skill string, body json.RawMessage) (json.RawMessage, error) {
	return c.postJSON(ctx, fmt.Sprintf("/api/v1/knowledge/search/%s/%s", domain, skill), body)
}

// GetMemoryStatus returns memory backend status as raw JSON passthrough.
func (c *Client) GetMemoryStatus(ctx context.Context) (json.RawMessage, error) {
	return c.getJSON(ctx, "/api/v1/memory/status")
}

// MemorySearch performs cross-domain semantic search across all memories.
func (c *Client) MemorySearch(ctx context.Context, body json.RawMessage) (json.RawMessage, error) {
	return c.postJSON(ctx, "/api/v1/memory/search", body)
}

// GetPromptAssembly returns the 3-layer prompt assembly for a skill.
func (c *Client) GetPromptAssembly(ctx context.Context, domain, skill string) (json.RawMessage, error) {
	return c.getJSON(ctx, fmt.Sprintf("/api/v1/memory/prompt-assembly/%s/%s", domain, skill))
}

// ApproveExecution approves or rejects a pending execution as raw JSON passthrough.
func (c *Client) ApproveExecution(ctx context.Context, executionID string, body json.RawMessage) (json.RawMessage, error) {
	return c.postJSON(ctx, fmt.Sprintf("/api/v1/executions/%s/approve", executionID), body)
}

// ListEvents returns unified event stream as raw JSON passthrough.
func (c *Client) ListEvents(ctx context.Context, query string) (json.RawMessage, error) {
	path := "/api/v1/events"
	if query != "" {
		path += "?" + query
	}
	return c.getJSON(ctx, path)
}

// TriggerDetail is a single trigger definition from the executor.
type TriggerDetail struct {
	Type        string `json:"type"`
	Schedule    string `json:"schedule,omitempty"`
	Pattern     string `json:"pattern,omitempty"`
	Description string `json:"description,omitempty"`
}

// TriggerInfo groups all triggers for a skill, returned by GET /api/v1/triggers.
type TriggerInfo struct {
	Domain   string          `json:"domain"`
	Skill    string          `json:"skill"`
	Triggers []TriggerDetail `json:"triggers"`
}

// FetchTriggers returns all skill trigger definitions from the executor.
func (c *Client) FetchTriggers(ctx context.Context) ([]TriggerInfo, error) {
	raw, err := c.getJSON(ctx, "/api/v1/triggers")
	if err != nil {
		return nil, fmt.Errorf("fetching triggers: %w", err)
	}
	var triggers []TriggerInfo
	if err := json.Unmarshal(raw, &triggers); err != nil {
		return nil, fmt.Errorf("parsing triggers response: %w", err)
	}
	return triggers, nil
}

// StreamPost sends a POST and returns the raw *http.Response for SSE streaming.
// The caller is responsible for closing resp.Body.
func (c *Client) StreamPost(ctx context.Context, path string, payload []byte) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("calling executor: %w", err)
	}

	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("executor returned %d: %s", resp.StatusCode, body)
	}

	return resp, nil
}

// BaseURL returns the executor base URL (used by webhook handler for routing).
func (c *Client) BaseURL() string {
	return c.baseURL
}

// PostRaw sends a raw JSON payload to the executor and returns the response.
func (c *Client) PostRaw(ctx context.Context, path string, payload []byte) (json.RawMessage, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("calling executor: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("reading response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("executor returned %d: %s", resp.StatusCode, respBody)
	}

	return json.RawMessage(respBody), nil
}

func (c *Client) postJSON(ctx context.Context, path string, body any) (json.RawMessage, error) {
	payload, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("marshaling request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("calling executor: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("reading response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("executor returned %d: %s", resp.StatusCode, respBody)
	}

	return json.RawMessage(respBody), nil
}
