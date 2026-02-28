package executor

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

// ProxyDispatcher dispatches skill executions to the Python executor via HTTP.
// This wraps the existing Client.Execute() — zero behavior change from the
// original passthrough architecture.
type ProxyDispatcher struct {
	client *Client
}

func NewProxyDispatcher(client *Client) *ProxyDispatcher {
	return &ProxyDispatcher{client: client}
}

func (d *ProxyDispatcher) Dispatch(ctx context.Context, req ExecutionDispatchRequest) (json.RawMessage, error) {
	execReq := ExecuteRequest{
		InputData: req.InputData,
		DryRun:    req.DryRun,
	}
	if execReq.InputData == nil {
		execReq.InputData = make(map[string]any)
	}
	if req.Message != "" {
		execReq.InputData["message"] = req.Message
	}
	for k, v := range req.Parameters {
		execReq.InputData[k] = v
	}
	if req.Model != "" {
		execReq.InputData["model_override"] = req.Model
	}

	return d.client.Execute(ctx, req.Domain, req.Skill, execReq)
}

func (d *ProxyDispatcher) HealthCheck(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, d.client.BaseURL()+"/health", nil)
	if err != nil {
		return fmt.Errorf("creating health request: %w", err)
	}
	resp, err := d.client.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("executor health check: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("executor unhealthy: status %d", resp.StatusCode)
	}
	return nil
}
