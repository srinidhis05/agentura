# Skills

This directory contains skill definitions for the Agentura platform. Each skill is a self-contained AI agent capability defined by a `SKILL.md` prompt and an `agentura.config.yaml` configuration file.

## Structure

```
skills/
  {domain}/
    DOMAIN.md                   # Shared domain context (injected into every skill)
    {skill-name}/
      SKILL.md                  # Skill prompt + execution protocol
      agentura.config.yaml      # Config (model, triggers, budget, MCP tools)
      fixtures/                 # Sample inputs for testing
      evals/                    # Evaluation YAML files
```

## Included Skills

### `dev/` — Developer Productivity

| Skill | Role | Executor | What It Does |
|-------|------|----------|--------------|
| `triage` | Manager | — | Routes dev queries to the right pipeline ($0.01, Haiku) |
| `app-builder` | Agent | Claude Code | Builds web apps from natural language descriptions |
| `deployer` | Agent | PTC | Deploys apps to K8s via MCP kubectl tools |
| `pr-code-reviewer` | Agent | Claude Code | Severity-tagged code review (BLOCKER/WARNING/SUGGESTION/PRAISE) |
| `pr-test-runner` | Agent | Claude Code | Runs tests, reports coverage gaps with evidence |
| `pr-slt-validator` | Agent | Claude Code | API contract compatibility and breaking change detection |
| `pr-doc-generator` | Agent | Claude Code | Generates CHANGELOG entries, README patches, docstrings |
| `pr-reporter` | Specialist | — | Aggregates parallel PR review results into a single comment |

The `dev/pr-*` skills work together via the `github-pr-parallel` pipeline — 4 agents analyze in parallel, then the reporter aggregates.

### `examples/` — Reference Implementations

| Skill | Pattern | Executor | What It Demonstrates |
|-------|---------|----------|---------------------|
| `ticket-classifier` | Triage routing | — | Multi-route classification with entity extraction |
| `meeting-processor` | MCP integration | PTC | External tool orchestration (calendar + tasks + messaging) |
| `daily-digest` | Cron trigger | PTC | Scheduled multi-source aggregation with graceful degradation |

These are generic templates. Copy one, rename the domain, and adapt the prompt for your use case.

### `incubator/` — Feature Incubation Pipeline

| Skill | Role | Executor | What It Does |
|-------|------|----------|--------------|
| `orchestrate` | Manager | — | Routes feature requests to analyze/build/refine/ship pipelines |
| `spec-analyzer` | Specialist | — | Decomposes Lovable prototypes into backend + mobile specs |
| `pit-builder` | Agent | Claude Code | Creates Spring Boot backend module from spec, pushes PR |
| `mobile-builder` | Agent | Claude Code | Creates Kotlin/Compose feature module from spec, pushes PR |
| `quality-gate` | Agent | Claude Code | Clones both repos at feature branch, runs builds, checks conventions |
| `preview-generator` | Agent | Claude Code | Generates phone-frame previews of the mobile feature |
| `reporter` | Specialist | — | Aggregates pipeline results into PM-facing summary |

The incubator skills work together via 4 pipelines: `incubator-analyze` → `incubator-build` → `incubator-refine` → `incubator-ship`. Backend and mobile builders run in parallel, then quality-gate verifies, then reporter summarizes.

## Key Concepts

### Roles

- **Manager** — Lightweight classifier ($0.01). Routes queries to specialist/agent skills.
- **Specialist** — Single-shot prompt execution. No tools, no sandbox. Fast and cheap.
- **Agent** — Full execution environment with tools. Runs in a sandbox (PTC or Claude Code worker pod).

### Executors

- **PTC** (Prompt-Tool-Complete) — Lightweight (~200MB). For MCP-only skills that call external APIs.
- **Claude Code** — Full sandbox (~800MB). For skills that need file I/O, code generation, git operations.

### DOMAIN.md

Each domain can have a `DOMAIN.md` file that provides shared context (identity, voice, principles). This is automatically injected into every skill in that domain at execution time.

## Using Your Own Skills

```bash
# Local dev
export SKILLS_DIR=~/my-skills
agentura list
agentura run my-domain/my-skill --input '{"message": "hello"}'

# K8s production — mount via hostPath or git-sync
# See deploy/k8s/skills-sync.yaml
```
