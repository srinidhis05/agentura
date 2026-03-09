# Agentura — Config-Driven AI Agent Orchestrator

[![CI](https://github.com/srinidhis05/agentura/actions/workflows/ci.yml/badge.svg)](https://github.com/srinidhis05/agentura/actions/workflows/ci.yml)
[![Website](https://img.shields.io/badge/Website-agenturaai.tech-blue)](https://agenturaai.tech)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

> Self-hosted AI agent orchestrator where skills are Markdown, pipelines are YAML, and every execution feeds a learning loop that compounds. No Python required to add capabilities — just `SKILL.md` + `agentura.config.yaml`.

```
SKILL.md (behavior) + config.yaml (executor, tools, limits) = Production agent
Pipeline YAML (parallel phases, fan-in) = Multi-agent workflow
Correction → Reflexion → Prompt injection = Learning loop that compounds
```

## What's New

**18 skills across 3 public domains**, orchestrated by **5 pipelines** and **6 agents**:

- **4-Agent PR Review Fleet** — Code reviewer, test runner, SLT validator, and doc generator analyze PRs in parallel. A reporter aggregates severity-tagged findings into a single PR comment.
- **Incubator Pipeline** — Takes a Lovable prototype and produces PRs in both backend (Spring Boot) and mobile (Kotlin/Compose) repos. 7 skills across 4 pipeline phases: analyze → build → refine → ship.
- **Agency System** — Agents with personality (SOUL.md), schedules (HEARTBEAT.md), and domain context (DOMAIN.md). Hierarchical delegation with budget controls.
- **MCP Gateway Integration** — External tools (Gmail, Notion, Slack, ClickUp, Granola) connected via centralized auth broker. Skills declare tool access in config.

## Demo

### Full Platform Demo

https://github.com/srinidhis05/agentura/raw/main/docs/assets/Agentura-Final.mp4

<details>
<summary>What you're seeing</summary>

1. **Skill execution** — Config-driven skills with guardrails and MCP tool access
2. **Pipeline chaining** — Multi-skill workflows via YAML config (build → deploy)
3. **Learning loop** — Corrections → reflexion rules → auto-generated tests → smarter next run
4. **Dashboard** — Domain topology, execution history, knowledge layer
</details>

### CLI — Learning Loop in Action

https://github.com/user-attachments/assets/213bc72a-bbfe-477e-ad59-18bc1ba5360b

### Web Dashboard

https://github.com/user-attachments/assets/48519761-0369-4f5d-9d99-9e5bd9cfc146

<!-- TODO: Add screenshots of the new dashboard pages
![Agents Dashboard](docs/assets/agents-dashboard.png)
![Fleet Session](docs/assets/fleet-session.png)
![Org Chart](docs/assets/org-chart.png)
-->

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          User / Chat Client                                 │
│  Chat UI · CLI · Slack · REST API · GitHub Webhooks         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP + SSE streaming
┌──────────────────────────▼──────────────────────────────────┐
│         Go API Gateway (3001 / NodePort 30080)              │
│  Auth · CORS · Rate Limiting · SSE Streaming · Cron         │
│  Pipeline Router · Slack Socket/Webhook · GitHub Checks     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           Python Skill Executor (8000)                      │
│  Executor Router (PTC/CC/Legacy) · Skill Loader · Pipelines │
│  Memory Recall · Agency Loader · Startup Validation         │
└───────┬──────────────┬──────────────┬───────────────────────┘
        │              │              │ creates per-execution pods
┌───────▼───────┐ ┌────▼────────┐ ┌──▼──────────────────────┐
│ Agent Pods    │ │ MCP Gateway │ │ PostgreSQL              │
│ PTC Worker    │ │ kubectl     │ │ Executions, corrections │
│ CC Worker     │ │ Slack       │ │ Reflexions, agents      │
│ Deployed Apps │ │ GitHub      │ │ Fleet sessions, tickets │
└───────────────┘ │ Gmail, etc  │ └─────────────────────────┘
                  └─────────────┘
```

### Executor Types

| Executor | Config | Pod Size | Use Case |
|----------|--------|----------|----------|
| **PTC Worker** | `executor: ptc` | ~200MB | MCP tool-calling (deployer, API workflows, meeting processor) |
| **Claude Code Worker** | `executor: claude-code` | ~800MB | File I/O + bash + code gen (app builder, code reviewer, pit builder) |
| **Legacy** | No executor field | No extra pod | Simple prompt-response (summarizer, classifier) |

## Skills

### `dev/` — Developer Productivity (8 skills)

| Skill | Role | What It Does |
|-------|------|--------------|
| `triage` | Manager | Routes dev queries to the right pipeline ($0.01, Haiku) |
| `app-builder` | Agent | Builds web apps from natural language descriptions |
| `deployer` | Agent | Deploys apps to K8s via MCP kubectl tools |
| `pr-code-reviewer` | Agent | Severity-tagged code review (BLOCKER/WARNING/SUGGESTION/PRAISE) |
| `pr-test-runner` | Agent | Runs tests, reports coverage gaps with evidence |
| `pr-slt-validator` | Agent | API contract compatibility and breaking change detection |
| `pr-doc-generator` | Agent | Generates CHANGELOG entries, README patches, docstrings |
| `pr-reporter` | Specialist | Aggregates parallel PR review results into one comment |

### `incubator/` — Prototype-to-Production (7 skills)

| Skill | Role | What It Does |
|-------|------|--------------|
| `orchestrate` | Manager | Routes to analyze/build/refine/ship pipelines |
| `spec-analyzer` | Specialist | Decomposes prototypes into backend + mobile specs |
| `pit-builder` | Agent | Creates Spring Boot backend module, pushes PR |
| `mobile-builder` | Agent | Creates Kotlin/Compose feature module, pushes PR + APK |
| `quality-gate` | Agent | Clones repos at feature branch, builds, checks conventions |
| `preview-generator` | Agent | Generates phone-frame preview screenshots |
| `reporter` | Specialist | Aggregates pipeline results into PM-facing summary |

### `examples/` — Reference Implementations (3 skills)

| Skill | Pattern | What It Demonstrates |
|-------|---------|---------------------|
| `ticket-classifier` | Triage routing | Multi-route classification with entity extraction |
| `meeting-processor` | MCP integration | External tool orchestration (calendar + tasks + messaging) |
| `daily-digest` | Cron trigger | Scheduled multi-source aggregation with graceful degradation |

## Pipelines

### PR Review Fleet — 4 Agents in Parallel

```
GitHub PR Webhook (opened / synchronize)
         │
    ┌────┴────────────────────────────┐
    │       analyze (parallel)        │
    │  ┌──────────┐ ┌──────────────┐  │
    │  │ reviewer  │ │ test-runner  │  │
    │  │(required) │ │ (required)   │  │
    │  └──────────┘ └──────────────┘  │
    │  ┌──────────┐ ┌──────────────┐  │
    │  │   slt    │ │ doc-generator│  │
    │  │(optional)│ │ (optional)   │  │
    │  └──────────┘ └──────────────┘  │
    └────────────┬────────────────────┘
                 │ fan-in
    ┌────────────▼────────────────────┐
    │     report (sequential)         │
    │  ┌──────────────────────────┐   │
    │  │      pr-reporter         │   │
    │  │  Aggregated PR comment   │   │
    │  └──────────────────────────┘   │
    └─────────────────────────────────┘
```

### Incubator — Prototype to Production

```
incubator-analyze → incubator-build → incubator-refine → incubator-ship

Build phase:
  pit-builder ──┐
                ├── quality-gate ── reporter
  mobile-builder┘
  (parallel)        (sequential fan-in)
```

Each pipeline is a YAML file in `pipelines/`. New pipeline = new YAML. Zero code changes.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/srinidhis05/agentura.git
cd agentura

# 2. Configure
cp .env.example .env   # add your ANTHROPIC_API_KEY

# 3. Deploy to K8s (K3s / Kind / EKS / GKE)
kubectl apply -f deploy/k8s/operator/
kubectl get pods -n agentura

# 4. Copy skills and run
kubectl cp skills/ executor:/skills/
agentura list
agentura run dev/app-builder --input '{"description": "build a counter app"}'

# Gateway: http://localhost:30080
# Web UI: kubectl port-forward -n agentura svc/web 3000:3000
```

## The Learning Loop

Every correction makes the system smarter:

```
Run skill → User corrects output → Reflexion rule generated → Test auto-created
    ↑                                                              ↓
    └──────────── Rule injected into next execution ←──────────────┘
```

```bash
# 1. Run a skill
agentura run dev/app-builder --input '{"description": "build a todo app"}'

# 2. Correct a mistake
agentura correct dev/app-builder \
    --execution-id EXEC-20260228 \
    --correction "Always use dark theme with purple accent"

# 3. Next run automatically applies the learned reflexion
agentura run dev/app-builder --input '{"description": "build a counter app"}'
# → Dark theme applied without being told
```

## Create a Skill

A skill is `SKILL.md` (behavior) + `agentura.config.yaml` (execution). No Python required.

```markdown
---
name: deployer
role: agent
domain: dev
model: anthropic/claude-sonnet-4-5
---

# Deployer Agent
You receive app artifacts and deploy them to Kubernetes via kubectl.

## Guardrails
- Always use NodePort services
- Never deploy to the default namespace
```

```yaml
# agentura.config.yaml
agent:
  executor: ptc
  timeout: 120

mcp_tools:
  - server: k8s
    tools: [kubectl_apply, kubectl_get]

display:
  title: "Deployer"
  avatar: "DP"
  color: "#059669"
  tags: ["Agent", "K8s"]
```

See [docs/SKILL_ONBOARDING.md](docs/SKILL_ONBOARDING.md) for the full authoring guide.

## Agency System

Agents are defined as YAML + Markdown, not code:

```
agency/
  {domain}/
    {agent-name}/
      agent.yaml      # Role, skills, budget, delegation rules
      SOUL.md          # Personality and behavioral guidelines
      HEARTBEAT.md     # Scheduled check-in protocol
```

```yaml
# agency/incubator/pit-builder/agent.yaml
name: pit-builder
domain: incubator
role: field
executor: claude-code
model: anthropic/claude-sonnet-4-5-20250929
reports_to: incubator-lead
skills:
  - incubator/pit-builder
budget:
  monthly_limit_usd: 100
  per_execution_limit: 3.00
delegation:
  autonomy_level: silent
```

## Project Structure

```
agentura/
├── sdk/                              # Python SDK + Skill Executor
│   └── agentura_sdk/
│       ├── server/app.py             # FastAPI (all endpoints + startup validation)
│       ├── pipelines/engine.py       # Pipeline executor (parallel phases, fan-in)
│       ├── runner/
│       │   ├── skill_loader.py       # Loads SKILL.md + DOMAIN.md + reflexions
│       │   ├── ptc_executor.py       # PTC worker pod executor
│       │   └── claude_code_executor.py  # CC worker pod executor
│       ├── agency/                   # Agent definitions + heartbeat scheduler
│       ├── memory/                   # PostgreSQL stores (executions, reflexions, agents)
│       └── cli/                      # agentura CLI (run, deploy, correct, create, ...)
│
├── gateway/                          # Go API Gateway
│   └── internal/
│       ├── handler/                  # Skills, pipelines, Slack, GitHub, agents, heartbeats
│       └── adapter/executor/         # Python executor client (SSE streaming)
│
├── web/                              # Next.js Dashboard
│   └── src/app/(dashboard)/
│       ├── agents/                   # Agent cards + detail views
│       ├── fleet/                    # Fleet session tracking
│       ├── executions/               # Execution history + traces
│       ├── heartbeats/               # Heartbeat schedule dashboard
│       └── org-chart/                # Agency hierarchy visualization
│
├── skills/                           # Skill definitions (Markdown + YAML)
│   ├── dev/                          # 8 skills: PR fleet, app-builder, deployer, triage
│   ├── incubator/                    # 7 skills: prototype → production pipeline
│   └── examples/                     # 3 reference implementations
│
├── agency/                           # Agent definitions (YAML + SOUL.md + HEARTBEAT.md)
│   └── incubator/                    # 6 agents: lead, spec-analyzer, builders, QA, reporter
│
├── pipelines/                        # Pipeline orchestration (YAML)
│   ├── github-pr-parallel.yaml       # 4-agent PR review fleet
│   └── incubator-*.yaml              # 4-phase incubation pipeline
│
├── claude-code-worker/               # CC worker Docker image
├── ptc-worker/                       # PTC worker Docker image
├── deploy/k8s/operator/              # K8s deployment manifests
└── docs/                             # Architecture, onboarding, MCP gateway
```

## How It Compares

| Feature | Agentura | CrewAI | LangGraph | AutoGen |
|---------|----------|--------|-----------|---------|
| Skills as config (no code) | SKILL.md + YAML | Python classes | Python graphs | Python agents |
| Parallel multi-agent pipelines | YAML phases + fan-in | Sequential/hierarchical | Python graphs | Conversations |
| Learning loop | Correction → Reflexion → Test | None | None | None |
| Agent personality & schedules | SOUL.md + HEARTBEAT.md | None | None | None |
| Domain isolation | Namespace-scoped domains | None | None | None |
| MCP tool integration | Per-skill tool bindings | None | None | None |
| Agent sandbox | Isolated K8s pods per execution | Shared process | Shared process | Shared process |
| Multiple executor types | PTC / Claude Code / Legacy | Single runtime | Single runtime | Single runtime |
| Triggers | Slack, GitHub, cron, webhooks, API | Code-only | Code-only | Code-only |
| Fleet session tracking | PostgreSQL + dashboard | None | None | None |
| Self-hosted | K8s-native, Apache 2.0 | Cloud or self-host | Cloud or self-host | Self-hosted |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Skill Executor | Python 3.13, FastAPI, Pydantic AI |
| API Gateway | Go 1.24, net/http, Prometheus |
| Dashboard | Next.js 16, React 19, Tailwind, shadcn/ui |
| Agent Pods | PTC (Python) and Claude Code (Python + Node.js) workers |
| MCP Servers | K8s MCP (Go), external via MCP gateway |
| Storage | PostgreSQL 16 |
| LLM | Claude Sonnet 4.5 / Haiku 4.5 via Anthropic or OpenRouter |
| Runtime | Kubernetes (pods in `agentura` namespace) |

## Documentation

| Guide | Description |
|-------|-------------|
| [Skill Onboarding](docs/SKILL_ONBOARDING.md) | Full skill authoring lifecycle guide |
| [MCP Gateway](docs/mcp-gateway-architecture.md) | External tool integration via auth broker |
| [Open Source Edition](docs/OPENSOURCE_EDITION.md) | OSS vs Enterprise tier comparison |
| [DX Roadmap](docs/DX_ROADMAP.md) | Developer experience improvement plan |
| [Skills Reference](skills/README.md) | All 18 skills with patterns and executors |
| [Pipelines Reference](pipelines/README.md) | Pipeline architecture and examples |

## License

Apache 2.0

---

*Config-driven AI agent orchestration with memory that compounds.*
