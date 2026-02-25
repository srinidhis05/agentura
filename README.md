# Agentura — Kubernetes for AI Agent Swarms

[![CI](https://github.com/agentura-ai/agentura/actions/workflows/ci.yml/badge.svg)](https://github.com/agentura-ai/agentura/actions/workflows/ci.yml)

> Deploy, orchestrate, and improve AI agent skills across your entire organization. Config-driven. Self-improving. Observable.

```
Correction → Test → Reflexion → Re-injection → Better output
                 (the loop that compounds)
```

## Demo

### CLI — The Learning Loop in Action

<video src="https://raw.githubusercontent.com/srinidhis05/agentura/main/docs/assets/cli-demo.mp4" controls width="100%"></video>

<details>
<summary>What you're seeing</summary>

1. **List skills** — 18 skills across 4 domains, deployed as config
2. **Run a skill** — HR interview questions generated via Claude Sonnet
3. **Correct a mistake** — "Need more system design depth" → reflexion rule + test auto-generated
4. **Re-run** — Same skill now includes the learned rule in its prompt
</details>

### Web UI — Chat + Dashboard

<video src="https://raw.githubusercontent.com/srinidhis05/agentura/main/docs/assets/ui-demo.mp4" controls width="100%"></video>

<details>
<summary>What you're seeing</summary>

1. **Chat interface** — Natural language routing to the right skill
2. **Dashboard** — Domain topology, execution history, knowledge layer
3. **Skill detail** — Full SKILL.md rendered with config, guardrails, and metrics
</details>

## What Is This?

Agentura is an **agentic AI platform** that treats AI skills like Kubernetes treats workloads:

| Kubernetes | Agentura |
|------------|--------|
| Namespace | Domain (Dev, Finance, HR, Productivity) |
| Pod/Deployment | Skill (SKILL.md + config YAML) |
| Service/Ingress | Routing (LLM classifier → manager → specialist → field) |
| ConfigMap | DOMAIN.md, plugin.yaml, agentura.config.yaml |
| ResourceQuota | Cost budgets, rate limits, human approval thresholds |
| Events | Unified event stream (executions, corrections, reflexions) |
| kubectl | `agentura` CLI (verb-resource pattern) |

**The difference**: Every execution feeds a learning loop. User corrections automatically generate regression tests, reflexion rules, and guardrails. After 6 months, your organization has 10,000+ test cases and measurable improvement trajectories — something no competitor offers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard (3000)                  │
│  Domains · Skills · Executions · Knowledge · Events · Analytics │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Go API Gateway (3001)                           │
│  Auth · CORS · Rate Limit · Metrics · JSON passthrough      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           Python Skill Executor (8000)                       │
│  Pydantic AI · Skill Loader · Knowledge Layer · Test Gen    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Skills Directory                           │
│  skills/{domain}/{skill}/SKILL.md + fixtures + tests         │
│  .agentura/ (episodic_memory, corrections, reflexions)        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/agentura-ai/agentura.git
cd agentura

# 2. Set your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Start everything
docker compose up

# Chat UI: http://localhost:3002
# Dashboard: http://localhost:3002/dashboard
# API Gateway: http://localhost:3001
# Executor: http://localhost:8000
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
│       ├── runner/
│       │   ├── skill_loader.py   # Loads SKILL.md + DOMAIN.md + reflexions
│       │   ├── local_runner.py   # Pydantic AI execution engine
│       │   └── config_loader.py  # YAML config parser
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
├── skills/                       # Skill definitions (the workloads)
│   ├── platform/classifier/      # Routes to correct domain
│   ├── dev/github-pr-reviewer/   # Code review
│   ├── finance/expense-analyzer/ # Expense analysis
│   └── hr/interview-questions/   # Interview prep
│
├── .agentura/                      # Knowledge layer (learning state)
│   ├── episodic_memory.json      # Execution history
│   ├── corrections.json          # User corrections
│   └── reflexion_entries.json    # Learned rules
│
├── docker-compose.yml            # Full stack: executor + gateway + web + postgres
├── DECISIONS.md                  # Architecture Decision Records (25 ADRs)
└── GUARDRAILS.md                 # Anti-patterns and detection rules
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Skill Format](docs/skill-format.md) | SKILL.md specification — frontmatter, sections, 4-layer prompt hierarchy |
| [SDLC](docs/sdlc.md) | Skill development lifecycle — ideate, define, build, validate, learn |
| [Memory System](docs/memory-system.md) | Feedback loop, data schemas, memory store backends, CLI commands |
| [Architecture](docs/architecture.md) | Core design principles — choreography, isolation, reconciliation |
| [CLI Reference](docs/cli-reference.md) | kubectl-style CLI commands and operational workflows |
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

### Platform
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/events` | Unified event stream |
| GET | `/api/v1/platform/health` | Component health |
| GET | `/api/v1/analytics` | Aggregate metrics |
| GET | `/api/v1/executions` | Execution history |
| GET | `/api/v1/executions/{id}` | Execution detail |

## How It Compares

| Feature | Agentura | Swarms | CrewAI | LangGraph |
|---------|--------|--------|--------|-----------|
| Skills as config (no code) | SKILL.md + YAML | Python classes (6K LOC agent.py) | Python (role/goal/backstory) | Python graphs |
| Learning loop | Correction → Test → Reflexion | None | None | None |
| Auto test generation | DeepEval + Promptfoo | None | None | None |
| Domain isolation | Namespaces with quotas | None | None | None |
| Operational dashboard | K8s-style control plane | None | Monitoring only | LangSmith |
| Role hierarchy | Manager → Specialist → Field | Single agent | Flat crew | Graph nodes |
| Config-driven routing | LLM classifier + SKILL.md | Python if-else | Python | Python |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Skill Executor | Python 3.13, FastAPI, Pydantic AI |
| API Gateway | Go 1.24, net/http, Prometheus |
| Dashboard | Next.js 16, React 19, TanStack Query, Tailwind, shadcn/ui |
| Database | PostgreSQL 16 |
| LLM | Anthropic Claude (via Pydantic AI) |
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

*Built by engineers who believe AI agents should get smarter with every interaction, not just execute prompts.*
