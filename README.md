# Agentura — AI That Gets Smarter, And Stays Yours

[![CI](https://github.com/srinidhis05/agentura/actions/workflows/ci.yml/badge.svg)](https://github.com/srinidhis05/agentura/actions/workflows/ci.yml)
[![Website](https://img.shields.io/badge/Website-agenturaai.tech-blue)](https://agenturaai.tech)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

> Self-hosted AI agent orchestrator with config-driven skills, isolated K8s execution, and a learning loop that compounds. Corrections become reflexion rules, reflexions become system prompts, and every execution deepens a knowledge base that lives on your infrastructure.

```
Correction → Reflexion → Prompt Injection → Better output
              (the loop that compounds)
```

## Demo

### Full Demo — Skills, Pipelines & Learning Loop

https://github.com/srinidhis05/agentura/raw/main/docs/assets/Agentura-Final.mp4

<details>
<summary>What you're seeing</summary>

1. **Skill execution** — Config-driven skills with guardrails and MCP tool access
2. **Pipeline chaining** — Multi-skill workflows via YAML config (build → deploy)
3. **Learning loop** — Corrections → reflexion rules → auto-generated tests → smarter next run
4. **Dashboard** — Domain topology, execution history, knowledge layer
</details>

### CLI — The Learning Loop in Action

https://github.com/user-attachments/assets/213bc72a-bbfe-477e-ad59-18bc1ba5360b

<details>
<summary>What you're seeing</summary>

1. **List skills** — 10 skills across 4 domains, deployed as config
2. **Run a skill** — HR interview questions generated via Claude Sonnet
3. **Correct a mistake** — "Need more system design depth" → reflexion rule + test auto-generated
4. **Re-run** — Same skill now includes the learned rule in its prompt
</details>

### Web UI — Chat + Dashboard

https://github.com/user-attachments/assets/48519761-0369-4f5d-9d99-9e5bd9cfc146

<details>
<summary>What you're seeing</summary>

1. **Chat interface** — Natural language routing to the right skill
2. **Dashboard** — Domain topology, execution history, knowledge layer
3. **Skill detail** — Full SKILL.md rendered with config, guardrails, and metrics
</details>

## What Is This?

Cloud AI forgets you between sessions. Agentura remembers everything.

Skills are **Markdown + YAML config** — not Python code. You define behavior in `SKILL.md`, wire executor types, MCP tools, and guardrails in `agentura.config.yaml`, and chain skills into pipelines with a YAML file. The platform handles execution in isolated K8s pods, memory recall, and the learning loop.

| Concept | What It Means |
|---------|--------------|
| **Skill** | SKILL.md (behavior) + config YAML (executor, tools, limits) — no code |
| **Executor** | How the skill runs: `ptc` (tool-calling), `claude-code` (sandbox), or legacy (in-process) |
| **Pipeline** | Multi-skill workflow in YAML — each step's output flows to the next |
| **Domain** | Namespace for isolation (dev/, hr/, productivity/) |
| **MCP Tools** | External integrations (kubectl, Slack, GitHub, databases) scoped per skill |
| **Learning Loop** | Correction → reflexion rule → test → prompt injection on next run |
| **Triggers** | Slack, GitHub webhooks, cron, REST API, CLI |

**The difference**: Every execution feeds a learning loop. Corrections generate reflexion rules that get injected into future prompts, plus DeepEval regression tests. Over time, your skills accumulate domain-specific guardrails stored in PostgreSQL — searchable, versioned, and yours.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          User / Chat Client                                   │
│  Chat UI · CLI · Slack · REST API · GitHub Webhooks           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP + SSE streaming
┌──────────────────────────▼──────────────────────────────────┐
│         Go API Gateway (3001 / NodePort 30080)               │
│  Auth · CORS · Rate Limiting (RPS + Burst) · SSE Streaming   │
│  Pipeline Router · Cron Scheduler · Webhook Handler           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           Python Skill Executor (8000)                       │
│  Executor Router (PTC/CC/Legacy) · Skill Loader · Pipelines  │
│  Memory Recall (prompt injection) · Pipeline Engine           │
└───────┬──────────────┬──────────────┬───────────────────────┘
        │              │              │ creates per-execution pods
┌───────▼───────┐ ┌────▼────────┐ ┌──▼──────────────────────┐
│ Agent Pods    │ │ MCP Servers │ │ PostgreSQL + Qdrant     │
│ PTC Worker    │ │ kubectl     │ │ Executions, corrections │
│ CC Worker     │ │ Slack       │ │ Reflexions, vector      │
│ Deployed Apps │ │ GitHub      │ │ search (semantic recall)│
└───────────────┘ └─────────────┘ └─────────────────────────┘
```

### Three Executor Types

| Executor | Config | Pod Size | Use Case |
|----------|--------|----------|----------|
| **PTC Worker** | `executor: ptc` | ~200MB, 1 CPU | Tool-calling via MCP (K8s deployer, API workflows) |
| **Claude Code Worker** | `executor: claude-code` | ~800MB, 2 CPU | File I/O + bash + code editing (app builder, code gen) |
| **Legacy** | No executor field | No extra pod | Simple prompt-response (email drafter, summarizer) |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/srinidhis05/agentura.git
cd agentura

# 2. Configure
cp .env.example .env   # add your ANTHROPIC_API_KEY or OPENROUTER_API_KEY

# 3. Deploy to K8s (K3s / Kind / EKS / GKE)
kubectl apply -f deploy/k8s/operator/
kubectl get pods -n agentura   # verify all pods running

# 4. Copy skills and start building
kubectl cp skills/ executor:/skills/
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

# What happens:
# ✓ Correction stored in PostgreSQL
# ✓ Reflexion generated: "User prefers dark mode with purple accent (#8b5cf6)"
# ✓ Regression test written to tests/generated/test_correction_3.py

# 3. Next execution automatically recalls the reflexion and injects it into the prompt
agentura run dev/app-builder --input '{"description": "build a counter app"}'
# → Agent now applies dark theme without being told
```

See [docs/memory-system.md](docs/memory-system.md) for the full feedback loop, data schemas, and CLI reference.

## Create a Skill

A skill is a Markdown file (`SKILL.md`) + config YAML (`agentura.config.yaml`). No Python required.

**SKILL.md** — defines behavior:

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
- Always use NodePort services for external access
- Never deploy to the default namespace
```

**agentura.config.yaml** — defines execution config:

```yaml
agent:
  executor: ptc              # or claude-code, or omit for legacy
  timeout: 120
  max_iterations: 15
  max_tokens: 16384

mcp_tools:
  - server: k8s
    tools: [kubectl_apply, kubectl_get, kubectl_delete]

triggers:
  - type: api
  - type: cron
    schedule: "0 9 * * 1-5"

display:
  icon: "rocket"
  color: "#f59e0b"
  conversation_starters:
    - "Deploy the latest build to staging"
```

**Pipeline YAML** — chain skills into workflows:

```yaml
# pipelines/build-deploy.yaml
name: build-deploy
steps:
  - skill: dev/app-builder    # builds the app
  - skill: dev/deployer       # deploys to K8s
# app-builder artifacts automatically flow to deployer as input
```

New pipeline = new YAML file in `pipelines/`. Zero code changes.

## Triggers

Skills and pipelines can be triggered from multiple sources:

| Trigger | How | Config |
|---------|-----|--------|
| **CLI** | `agentura run dev/app-builder` | Always available |
| **REST API** | `POST /api/v1/skills/{domain}/{skill}/execute` | Always available |
| **Slack** | @mention, DM, or `/agentura` slash command | `type: slack` in config |
| **GitHub** | PR opened/updated triggers review pipeline | Webhook handler in gateway |
| **Cron** | Gateway discovers cron triggers from config | `type: cron` + schedule |
| **Webhooks** | HMAC-signed inbound from any external system | `POST /api/v1/channels/{channel}/inbound` |

## Project Structure

```
agentura/
├── sdk/                          # Python SDK + Skill Executor
│   └── agentura_sdk/
│       ├── server/app.py         # FastAPI server (all endpoints)
│       ├── pipelines/engine.py   # Generic pipeline executor (YAML-driven)
│       ├── runner/
│       │   ├── skill_loader.py   # Loads SKILL.md + DOMAIN.md + reflexions
│       │   ├── local_runner.py   # Pydantic AI execution engine
│       │   ├── agent_executor.py # Agent loop (tool calling, write-loop detection)
│       │   ├── claude_code_executor.py  # Claude Code worker pod executor
│       │   └── openrouter.py     # OpenRouter LLM provider
│       ├── sandbox/
│       │   ├── k8s_sandbox.py    # K8s sandbox (production)
│       │   └── claude_code_worker.py   # Worker pod lifecycle
│       ├── memory/mem0_store.py  # CompositeStore (PostgreSQL + Qdrant)
│       ├── cli/
│       │   ├── run.py            # agentura run
│       │   └── correct.py        # agentura correct (learning loop)
│       └── testing/
│           └── deepeval_runner.py # Auto-generate DeepEval tests
│
├── gateway/                      # Go API Gateway
│   ├── cmd/server/main.go
│   └── internal/
│       ├── handler/              # HTTP handlers (skills, pipelines, webhooks)
│       ├── adapter/executor/     # Python executor client (SSE streaming)
│       └── middleware/           # Auth, CORS, rate limit, metrics
│
├── web/                          # Next.js Dashboard + Landing Page
│   └── src/
│       ├── app/(marketing)/      # Landing page (agenturaai.tech)
│       ├── app/(chat)/           # Chat interface (/chat)
│       ├── app/(dashboard)/      # Admin dashboard (/dashboard/*)
│       └── lib/                  # API client, chat state
│
├── skills/                       # Skill definitions (config, not code)
│   ├── platform/classifier/      # Routes to correct domain
│   ├── dev/
│   │   ├── triage/               # Domain router
│   │   ├── app-builder/          # Agent: builds apps in sandbox
│   │   └── deployer/             # Agent: deploys to K8s via MCP
│   ├── hr/
│   │   ├── triage/               # Domain router
│   │   ├── resume-screener/      # Resume evaluation
│   │   └── onboarding-guide/     # 30-day onboarding plans
│   └── productivity/
│       ├── triage/               # Domain router
│       ├── meeting-summarizer/   # Meeting notes + action items
│       └── email-drafter/        # Professional email drafting
│
├── mcp-servers/k8s/              # K8s MCP server (kubectl operations)
├── deploy/k8s/operator/          # K8s deployment manifests
├── pipelines/                    # Pipeline definitions (YAML config)
│   └── build-deploy.yaml         # Build app → deploy to K8s
│
├── DECISIONS.md                  # Architecture Decision Records
└── GUARDRAILS.md                 # Anti-patterns and detection rules
```

## Security

| Feature | Status |
|---------|--------|
| HMAC webhook verification (SHA-256) | Built |
| JWT + domain-scoped RBAC | Built |
| Ephemeral agent pods (created per-execution, destroyed after) | Built |
| Rate limiting (RPS + burst control) | Built |
| Scoped MCP tool bindings (per-skill tool access) | Built |
| Memory governance (ACL, PII scanning, retention/TTL, audit) | Roadmap |

## How It Compares

| Feature | Agentura | CrewAI | LangGraph | AutoGen |
|---------|----------|--------|-----------|---------|
| Skills as config (no code) | SKILL.md + YAML | Python classes | Python graphs | Python agents |
| Multi-skill pipelines | YAML config | Python (sequential/hierarchical) | Python graphs | Python conversations |
| Learning loop | Correction → Reflexion → Test | None | None | None |
| Auto test generation | DeepEval regression tests | None | None | None |
| Domain isolation | Namespace-scoped domains | None | None | None |
| MCP integration | Per-skill tool bindings | None | None | None |
| Agent sandbox | Isolated K8s pods per execution | Shared process | Shared process | Shared process |
| Multiple executor types | PTC / Claude Code / Legacy | Single runtime | Single runtime | Single runtime |
| Trigger sources | Slack, GitHub, cron, webhooks, API | Code-only | Code-only | Code-only |
| Self-hosted | K8s-native, Apache 2.0 | Cloud or self-hosted | Cloud or self-hosted | Self-hosted |

## API Endpoints

### Skills
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/skills` | List all skills |
| GET | `/api/v1/skills/{domain}/{skill}` | Skill detail |
| POST | `/api/v1/skills/{domain}/{skill}/execute` | Execute a skill |
| POST | `/api/v1/skills/{domain}/{skill}/correct` | Submit correction |

### Pipelines
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/pipelines` | List available pipelines |
| POST | `/api/v1/pipelines/{name}/execute` | Run a pipeline |
| POST | `/api/v1/pipelines/{name}/execute-stream` | Run with SSE streaming |

### Knowledge
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/knowledge/reflexions` | List reflexion rules |
| GET | `/api/v1/knowledge/corrections` | List corrections |
| GET | `/api/v1/knowledge/tests` | List generated tests |
| GET | `/api/v1/knowledge/stats` | Learning metrics |

### Platform
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/domains` | List domains with health |
| GET | `/api/v1/executions` | Execution history |
| GET | `/api/v1/events` | Unified event stream |
| GET | `/api/v1/platform/health` | Component health |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Skill Executor | Python 3.13, FastAPI, Pydantic AI |
| API Gateway | Go 1.24, net/http, Prometheus |
| Dashboard | Next.js 16, React 19, Tailwind, shadcn/ui |
| Agent Pods | PTC (Python) and Claude Code (Python + Node.js 20) workers |
| MCP Servers | K8s MCP (Go, kubectl operations) |
| Memory | PostgreSQL 16 + Qdrant (semantic vector search) |
| LLM | Claude Sonnet 4.5 via OpenRouter or Anthropic SDK |
| Runtime | Kubernetes (pods in `agentura` namespace) |
| Testing | DeepEval (auto-generated regression tests) |

## Documentation

| Guide | Description |
|-------|-------------|
| [Architecture](docs/architecture.md) | Core design principles — choreography, isolation, reconciliation |
| [Skill Format](docs/skill-format.md) | SKILL.md specification — frontmatter, sections, prompt hierarchy |
| [Memory System](docs/memory-system.md) | Feedback loop, data schemas, memory store backends |
| [CLI Reference](docs/cli-reference.md) | CLI commands and operational workflows |
| [Triggers & Channels](docs/triggers-and-channels.md) | Cron, Slack, webhooks |
| [Comparisons](docs/comparisons.md) | Agentura vs CrewAI, LangGraph, AutoGen |

## License

Apache 2.0

---

*Self-hostable AI agent orchestration with memory that compounds.*
