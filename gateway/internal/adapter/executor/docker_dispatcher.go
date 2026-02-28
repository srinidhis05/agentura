package executor

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"os/exec"
	"strings"

	"github.com/agentura-ai/agentura/gateway/internal/config"
)

// DockerDispatcher runs each skill execution as an isolated Docker container.
// The skill-runner image reads the request from stdin and writes result to stdout.
type DockerDispatcher struct {
	cfg config.DockerExecConfig
}

func NewDockerDispatcher(cfg config.DockerExecConfig) *DockerDispatcher {
	return &DockerDispatcher{cfg: cfg}
}

func (d *DockerDispatcher) Dispatch(ctx context.Context, req ExecutionDispatchRequest) (json.RawMessage, error) {
	payload, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshaling execution request: %w", err)
	}

	args := d.buildDockerArgs()

	slog.Info("dispatching skill execution via docker",
		"image", d.cfg.Image,
		"domain", req.Domain,
		"skill", req.Skill,
	)

	cmd := exec.CommandContext(ctx, "docker", args...)
	cmd.Stdin = bytes.NewReader(payload)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		exitErr, ok := err.(*exec.ExitError)
		if ok && exitErr.ExitCode() == 1 {
			// Exit code 1 = skill error (result still on stdout)
			if stdout.Len() > 0 {
				return json.RawMessage(stdout.Bytes()), nil
			}
		}
		return nil, fmt.Errorf("docker execution failed (exit %d): %s", exitErr.ExitCode(), stderr.String())
	}

	result := strings.TrimSpace(stdout.String())
	if result == "" {
		return nil, fmt.Errorf("docker execution returned empty output, stderr: %s", stderr.String())
	}

	return json.RawMessage(result), nil
}

func (d *DockerDispatcher) buildDockerArgs() []string {
	args := []string{
		"run", "--rm", "-i",
		"--network", d.cfg.Network,
	}

	if d.cfg.ResourceLimits.Memory != "" {
		args = append(args, "--memory", d.cfg.ResourceLimits.Memory)
	}
	if d.cfg.ResourceLimits.CPUs != "" {
		args = append(args, "--cpus", d.cfg.ResourceLimits.CPUs)
	}

	if d.cfg.SkillsDir != "" {
		args = append(args, "-v", d.cfg.SkillsDir+":/skills:ro")
	}

	// Pass API keys from gateway environment to skill-runner
	for _, envVar := range []string{
		"ANTHROPIC_API_KEY",
		"OPENROUTER_API_KEY",
	} {
		args = append(args, "-e", envVar)
	}

	args = append(args, d.cfg.Image)
	return args
}

func (d *DockerDispatcher) HealthCheck(ctx context.Context) error {
	cmd := exec.CommandContext(ctx, "docker", "info")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("docker not available: %w", err)
	}
	return nil
}
