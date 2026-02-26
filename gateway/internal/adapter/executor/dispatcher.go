package executor

import (
	"context"
	"encoding/json"
)

// ExecutionRequest is the input for dispatching a skill execution.
type ExecutionDispatchRequest struct {
	Domain      string         `json:"domain"`
	Skill       string         `json:"skill"`
	Role        string         `json:"role,omitempty"`
	Model       string         `json:"model,omitempty"`
	Message     string         `json:"message,omitempty"`
	Parameters  map[string]any `json:"parameters,omitempty"`
	InputData   map[string]any `json:"input_data,omitempty"`
	DryRun      bool           `json:"dry_run,omitempty"`
}

// ExecutionDispatcher abstracts skill execution across different backends.
// Implementations: ProxyDispatcher (HTTP to executor), DockerDispatcher (docker run),
// K8sDispatcher (creates SkillExecution CR).
type ExecutionDispatcher interface {
	Dispatch(ctx context.Context, req ExecutionDispatchRequest) (json.RawMessage, error)
	HealthCheck(ctx context.Context) error
}
