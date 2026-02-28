package executor

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/agentura-ai/agentura/gateway/internal/config"
)

// K8sDispatcher creates SkillExecution custom resources in Kubernetes
// and polls for completion. The operator handles Job creation and result extraction.
//
// This dispatcher communicates with the K8s API server to:
// 1. Create a SkillExecution CR with the execution request
// 2. Poll the CR status until it reaches a terminal phase
// 3. Return the result from the CR status
//
// Requires: K8s cluster with agentura-operator deployed and CRDs installed.
type K8sDispatcher struct {
	cfg config.KubernetesExecConfig
}

func NewK8sDispatcher(cfg config.KubernetesExecConfig) *K8sDispatcher {
	return &K8sDispatcher{cfg: cfg}
}

// skillExecutionCR is the minimal representation of a SkillExecution CR
// for creating and reading via the K8s dynamic client.
type skillExecutionCR struct {
	APIVersion string                 `json:"apiVersion"`
	Kind       string                 `json:"kind"`
	Metadata   map[string]any         `json:"metadata"`
	Spec       map[string]any         `json:"spec"`
	Status     map[string]any         `json:"status,omitempty"`
}

func (d *K8sDispatcher) Dispatch(ctx context.Context, req ExecutionDispatchRequest) (json.RawMessage, error) {
	execName := fmt.Sprintf("exec-%d", time.Now().UnixNano())

	slog.Info("dispatching skill execution via kubernetes",
		"name", execName,
		"namespace", d.cfg.Namespace,
		"domain", req.Domain,
		"skill", req.Skill,
	)

	cr := d.buildCR(execName, req)

	crJSON, err := json.Marshal(cr)
	if err != nil {
		return nil, fmt.Errorf("marshaling SkillExecution CR: %w", err)
	}

	// Create the CR via kubectl apply (avoids pulling in the full K8s client-go dependency in the gateway)
	if err := d.applyCR(ctx, crJSON); err != nil {
		return nil, fmt.Errorf("creating SkillExecution CR: %w", err)
	}

	// Poll for completion
	timeout, err := time.ParseDuration(d.cfg.Timeout)
	if err != nil {
		timeout = 5 * time.Minute
	}

	result, err := d.waitForCompletion(ctx, execName, timeout)
	if err != nil {
		return nil, fmt.Errorf("waiting for execution %s: %w", execName, err)
	}

	return result, nil
}

func (d *K8sDispatcher) buildCR(name string, req ExecutionDispatchRequest) skillExecutionCR {
	spec := map[string]any{
		"skill": map[string]any{
			"domain": req.Domain,
			"name":   req.Skill,
			"role":   req.Role,
		},
		"input": map[string]any{
			"message":    req.Message,
			"parameters": req.Parameters,
		},
		"runner": map[string]any{
			"image":   d.cfg.Image,
			"timeout": d.cfg.Timeout,
			"resources": map[string]any{
				"limits": map[string]string{
					"memory": d.cfg.ResourceLimits.Memory,
					"cpu":    d.cfg.ResourceLimits.CPU,
				},
			},
		},
	}

	if d.cfg.RuntimeClass != "" {
		spec["runner"].(map[string]any)["runtimeClassName"] = d.cfg.RuntimeClass
	}

	return skillExecutionCR{
		APIVersion: "agentura.io/v1alpha1",
		Kind:       "SkillExecution",
		Metadata: map[string]any{
			"name":      name,
			"namespace": d.cfg.Namespace,
		},
		Spec: spec,
	}
}

func (d *K8sDispatcher) applyCR(ctx context.Context, crJSON []byte) error {
	// Use kubectl to apply the CR — keeps gateway free of K8s client-go dependency
	cmd := execCommand(ctx, "kubectl", "apply", "-f", "-")
	cmd.Stdin = bytesReader(crJSON)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("kubectl apply failed: %s: %w", output, err)
	}
	return nil
}

func (d *K8sDispatcher) waitForCompletion(ctx context.Context, name string, timeout time.Duration) (json.RawMessage, error) {
	deadline := time.After(timeout)
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-deadline:
			return nil, fmt.Errorf("execution %s timed out after %v", name, timeout)
		case <-ticker.C:
			result, done, err := d.checkStatus(ctx, name)
			if err != nil {
				slog.Warn("error checking execution status", "name", name, "error", err)
				continue
			}
			if done {
				return result, nil
			}
		}
	}
}

func (d *K8sDispatcher) checkStatus(ctx context.Context, name string) (json.RawMessage, bool, error) {
	cmd := execCommand(ctx, "kubectl", "get", "skillexecution", name,
		"-n", d.cfg.Namespace, "-o", "json")
	output, err := cmd.Output()
	if err != nil {
		return nil, false, fmt.Errorf("kubectl get failed: %w", err)
	}

	var cr skillExecutionCR
	if err := json.Unmarshal(output, &cr); err != nil {
		return nil, false, fmt.Errorf("parsing CR status: %w", err)
	}

	phase, _ := cr.Status["phase"].(string)
	switch phase {
	case "Succeeded":
		result, _ := cr.Status["result"].(string)
		return json.RawMessage(result), true, nil
	case "Failed":
		msg, _ := cr.Status["message"].(string)
		return nil, true, fmt.Errorf("execution failed: %s", msg)
	default:
		return nil, false, nil
	}
}

func (d *K8sDispatcher) HealthCheck(ctx context.Context) error {
	cmd := execCommand(ctx, "kubectl", "get", "crd", "skillexecutions.agentura.io")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("SkillExecution CRD not found: %w", err)
	}
	return nil
}
