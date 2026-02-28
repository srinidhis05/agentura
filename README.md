# Agentura — Enterprise AI Plugin Marketplace

[![CI](https://github.com/agentura-ai/agentura/actions/workflows/ci.yml/badge.svg)](https://github.com/agentura-ai/agentura/actions/workflows/ci.yml)

> Build and deploy domain-specific AI plugins (Dev, HR, Productivity) with agent sandboxes, MCP integration, and self-improving feedback loops.

```
Correction → Test → Reflexion → Re-injection → Better output
                 (the loop that compounds)
```

## Demo

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

Agentura is an **enterprise AI plugin marketplace** — like an app store for AI agent skills across your organization:

| Concept | What It Means |
|---------|--------------|
| **Domain** | Plugin category (Dev, HR, Productivity) |
| **Skill** | A plugin (SKILL.md + config YAML) — no code required |
| **Routing** | Natural language → auto-routes to the right plugin |
| **MCP Tools** | External integrations (Slack, Jira, databases, APIs) |
| **Guardrails** | Cost budgets, rate limits, human approval thresholds |
| **Agent Skills** | Autonomous agents with sandboxed code execution and MCP tool access |
| **Events** | Unified stream (executions, corrections, reflexions) |
| **CLI** | `agentura` — manage plugins from the terminal |

**The difference**: Every execution feeds a learning loop. User corrections automatically generate regression tests, reflexion rules, and guardrails. After 6 months, your organization has 10,000+ test cases and measurable improvement trajectories — something no competitor offers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           Next.js Chat UI + Dashboard (3000)                 │
│  Chat · Domain Picker · Executions · Knowledge · Analytics   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         Go API Gateway (3001 / NodePort 30080)               │
│  Auth · CORS · Rate Limit · Metrics · SSE Streaming          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           Python Skill Executor (8000)                       │
│  Pydantic AI · Agent Executor · Skill Loader · Pipelines     │
└───────┬──────────────┬──────────────┬───────────────────────┘
        │              │              │
┌───────▼───────┐ ┌────▼────────┐ ┌──▼──────────────────────┐
│ Sandbox Pods  │ │ MCP Servers │ │ PostgreSQL + Qdrant     │
│ (per-agent    │ │ (k8s-mcp    │ │ (memory, executions,    │
│  execution)   │ │  for kubectl)│ │  vector search)         │
└───────────────┘ └─────────────┘ └─────────────────────────┘
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/agentura-ai/agentura.git
cd agentura

# 2. Set your API key
echo "OPENROUTER_API_KEY=sk-or-..." > .env

# 3a. Local development
cd sdk && pip install -e ".[dev]"
cd gateway && go build ./...
cd web && npm install && npm run dev

# 3b. Production (Kubernetes)
kubectl apply -f deploy/k8s/operator/
kubectl get pods -n agentura   # verify all pods running

# Gateway: http://localhost:30080
# Web UI: kubectl port-forward -n agentura svc/web 3000:3000
# Dashboard: http://localhost:3000/dashboard
```

## The Learning Loop (Core Differentiator)

Every correction makes the system smarter:

```
Run skill → User corrects output → Reflexion rule generated → Test auto-created
    ↑                                                              ↓
    └──────────── Rule injected into next execution ←──────────────┘
```

```bash
# 1. Run a skill
agentura run hr/interview-questions --input role.json

# 2. Correct a mistake
agentura correct hr/interview-questions \
    --execution-id EXEC-20260219 \
    --correction "Senior roles need system design questions, not just behavioral"

# 3. Next execution automatically includes the learned rule
```

See [docs/memory-system.md](docs/memory-system.md) for the full feedback loop, data schemas, and CLI reference.

## Create a Skill in 5 Minutes

A skill is a Markdown file with YAML frontmatter. No Python required.

```markdown
<!-- skills/hr/resume-screen/SKILL.md -->
---
name: resume-screen
role: specialist
domain: hr
trigger: api
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.05"
timeout: 30s
---

You are an HR resume screening specialist.

## Task
Given a resume and job description, evaluate candidate fit.

## Output Schema
Return JSON: { "fit_score": 0-100, "strengths": [...], "concerns": [...], "recommendation": "proceed|reject|discuss" }

## Guardrails
- Never consider age, gender, ethnicity, or protected characteristics
- Focus on skills match and experience relevance only
```

That's it. The platform handles execution, logging, corrections, test generation, and learning.

## Project Structure

```
agentura/
├── sdk/                          # Python SDK + Skill Executor
│   └── agentura_sdk/
│       ├── server/app.py         # FastAPI server (all endpoints)
│       ├── pipelines/
│       │   ├── engine.py         # Generic pipeline executor (YAML-driven)
│       │   └── build_deploy.py   # Backward-compat wrapper
│       ├── runner/
│       │   ├── skill_loader.py   # Loads SKILL.md + DOMAIN.md + reflexions
│       │   ├── local_runner.py   # Pydantic AI execution engine
│       │   ├── agent_executor.py # Agent loop (tool calling, write-loop detection)
│       │   ├── openrouter.py     # OpenRouter LLM provider
│       │   └── config_loader.py  # YAML config parser
│       ├── sandbox/              # Sandboxed execution backends
│       │   ├── docker_sandbox.py # Docker sandbox (local dev)
│       │   └── k8s_sandbox.py    # K8s sandbox (production)
│       ├── cli/
│       │   ├── run.py            # agentura run
│       │   └── correct.py        # agentura correct (learning loop)
│       └── testing/
│           ├── deepeval_runner.py # Auto-generate DeepEval tests
│           └── test_generator.py  # Auto-generate Promptfoo tests
│
├── gateway/                      # Go API Gateway
│   ├── cmd/server/main.go        # Entry point
│   └── internal/
│       ├── handler/              # HTTP handlers (JSON passthrough)
│       ├── adapter/executor/     # Python executor client
│       └── middleware/           # Auth, CORS, rate limit, metrics
│
├── web/                          # Next.js Chat UI + Dashboard
│   └── src/
│       ├── app/(chat)/           # Chat interface (/chat)
│       ├── app/(dashboard)/      # Admin dashboard (/dashboard/*)
│       ├── components/chat/      # Chat components (sidebar, messages, input)
│       └── lib/                  # API client, chat state, command router
│
├── skills/                       # Skill definitions (10 skills, 4 domains)
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
├── sandbox-runtime/              # Sandbox container (FastAPI tool server)
├── mcp-servers/k8s/              # K8s MCP server (kubectl operations)
├── deploy/k8s/operator/          # K8s deployment manifests
├── pipelines/                    # Pipeline definitions (YAML config)
│   └── build-deploy.yaml         # Build app → deploy to K8s
│
├── DECISIONS.md                  # Architecture Decision Records
└── GUARDRAILS.md                 # Anti-patterns and detection rules
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Skill Format](docs/skill-format.md) | SKILL.md specification — frontmatter, sections, 4-layer prompt hierarchy |
| [SDLC](docs/sdlc.md) | Skill development lifecycle — ideate, define, build, validate, learn |
| [Memory System](docs/memory-system.md) | Feedback loop, data schemas, memory store backends, CLI commands |
| [Architecture](docs/architecture.md) | Core design principles — choreography, isolation, reconciliation |
| [CLI Reference](docs/cli-reference.md) | CLI commands and operational workflows |
| [Triggers & Channels](docs/triggers-and-channels.md) | Cron scheduling, Slack integration, webhook channels |
| [Comparisons](docs/comparisons.md) | How Agentura compares to CrewAI, LangGraph, AutoGen, and others |
| [Decisions](docs/decisions.md) | Architecture Decision Records (ADRs) |

## API Endpoints

### Skills (Workloads)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/skills` | List all skills |
| GET | `/api/v1/skills/{domain}/{skill}` | Skill detail |
| POST | `/api/v1/skills/{domain}/{skill}/execute` | Execute a skill |
| POST | `/api/v1/skills/{domain}/{skill}/correct` | Submit correction |

### Knowledge (Learning Layer)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/knowledge/reflexions` | List reflexion rules |
| GET | `/api/v1/knowledge/corrections` | List corrections |
| GET | `/api/v1/knowledge/tests` | List generated tests |
| GET | `/api/v1/knowledge/stats` | Learning metrics |
| POST | `/api/v1/knowledge/validate/{domain}/{skill}` | Run tests + validate reflexions |

### Domains (Namespaces)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/domains` | List domains with health |
| GET | `/api/v1/domains/{domain}` | Domain detail + topology |

### Pipelines (Multi-Skill Workflows)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/pipelines` | List available pipelines |
| POST | `/api/v1/pipelines/{name}/execute` | Run a pipeline |
| POST | `/api/v1/pipelines/{name}/execute-stream` | Run with SSE streaming |

New pipeline = new YAML file in `pipelines/`. Zero code changes across Python, Go, or TypeScript.

### Platform
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/events` | Unified event stream |
| GET | `/api/v1/platform/health` | Component health |
| GET | `/api/v1/analytics` | Aggregate metrics |
| GET | `/api/v1/executions` | Execution history |
| GET | `/api/v1/executions/{id}` | Execution detail |

## How It Compares

| Feature | Agentura | Claude Plugins | CrewAI | LangGraph |
|---------|--------|--------|--------|-----------|
| Skills as config (no code) | SKILL.md + YAML | plugin.json + agents/ | Python (role/goal/backstory) | Python graphs |
| Multi-skill pipelines | YAML config (new pipeline = new file) | None | Python (sequential/hierarchical) | Python graphs |
| Learning loop | Correction → Test → Reflexion | None | None | None |
| Auto test generation | DeepEval + Promptfoo | None | None | None |
| Domain isolation | Domains with quotas | Per-plugin | None | None |
| MCP integration | Registry + per-skill bindings | .mcp.json | None | None |
| Role hierarchy | Manager → Specialist → Field | Single agent | Flat crew | Graph nodes |
| Agent sandbox execution | Isolated K8s pods per agent | None | Shared process | Shared process |
| Config-driven routing | LLM classifier + SKILL.md | Slash commands | Python | Python |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Skill Executor | Python 3.13, FastAPI, Pydantic AI |
| Agent Executor | Tool-calling loop with write-loop detection |
| API Gateway | Go 1.24, net/http, Prometheus |
| Dashboard + Chat | Next.js 16, React 19, TanStack Query, Tailwind, shadcn/ui |
| Sandbox Runtime | Python, FastAPI (isolated K8s pod per agent execution) |
| MCP Servers | K8s MCP (Go, kubectl operations) |
| Memory | PostgreSQL 16 (CompositeStore) + Qdrant (in-memory vector search) |
| LLM | Claude Sonnet 4.5 via OpenRouter (primary) or Anthropic SDK (fallback) |
| Runtime | Kubernetes (pods in `agentura` namespace) |
| Testing | DeepEval (Apache), Promptfoo (MIT) |

## Development

```bash
# Python SDK
cd sdk && pip install -e ".[dev]"

# Go Gateway
cd gateway && go build ./...

# Next.js Dashboard
cd web && npm install && npm run dev
```

## License

Apache 2.0

---

*Built by engineers who believe AI plugins should get smarter with every interaction, not just execute prompts.*
