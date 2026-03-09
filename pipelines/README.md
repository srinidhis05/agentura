# Pipelines

Multi-agent orchestration pipelines for the Agentura platform. Each YAML file defines a workflow that coordinates multiple skills.

## Structure

```yaml
name: my-pipeline
description: What this pipeline does
trigger:
  type: github_pr | webhook | cron | manual
  actions: [opened, synchronize]  # for github_pr

phases:
  - name: analyze
    type: parallel          # all steps run concurrently
    steps:
      - skill: domain/skill
        agent_id: unique-id  # used to reference results in fan-in
        required: true       # pipeline fails if this skill fails

  - name: report
    type: sequential
    fan_in_from: analyze     # receives all results from analyze phase
    steps:
      - skill: domain/reporter
```

## Included Pipelines

### `github-pr-parallel.yaml` — PR Review Fleet

4 agents analyze a PR in parallel, then a reporter aggregates results:

```
┌─────────────────────────────────────────────┐
│              GitHub PR Webhook               │
│         (opened / synchronize)               │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │   analyze (parallel)│
         ├────────────────────┤
         │ ┌────────────────┐ │
         │ │ code-reviewer  │ │  Severity-tagged findings
         │ │ (required)     │ │  BLOCKER / WARNING / SUGGESTION
         │ └────────────────┘ │
         │ ┌────────────────┐ │
         │ │ test-runner    │ │  Run tests, report coverage gaps
         │ │ (required)     │ │
         │ └────────────────┘ │
         │ ┌────────────────┐ │
         │ │ slt-validator  │ │  API contract & breaking changes
         │ │ (optional)     │ │
         │ └────────────────┘ │
         │ ┌────────────────┐ │
         │ │ doc-generator  │ │  CHANGELOG, README patches
         │ │ (optional)     │ │
         │ └────────────────┘ │
         └────────┬───────────┘
                  │ fan-in
         ┌────────┴───────────┐
         │  report (sequential)│
         │ ┌────────────────┐ │
         │ │  pr-reporter   │ │  Aggregated PR comment
         │ └────────────────┘ │
         └────────────────────┘
```

## Using Your Own Pipelines

```bash
# Point to your pipelines directory
export PIPELINES_DIR=~/my-workspace/pipelines

# Or mount in K8s
# See deploy/k8s/operator/executor.yaml — pipelines volume
```
