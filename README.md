# Agentura — Kubernetes for AI Agent Swarms

[![CI](https://github.com/agentura-ai/agentura/actions/workflows/ci.yml/badge.svg)](https://github.com/agentura-ai/agentura/actions/workflows/ci.yml)

> Deploy, orchestrate, and improve AI agent skills across your entire organization. Config-driven. Self-improving. Observable.

```
Correction → Test → Reflexion → Re-injection → Better output
                 (the loop that compounds)
```

## What Is This?

Agentura is an **agentic AI platform** that treats AI skills like Kubernetes treats workloads:

| Kubernetes | Agentura |
|------------|--------|
| Namespace | Domain (ECM, Wealth, FRM, HR, DevOps) |
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

This is the moat. Every correction makes the system smarter:

```
1. USER RUNS SKILL
   $ agentura run ecm/order-details --input order.json
   → Model generates output
   → Logged to .agentura/episodic_memory.json

2. USER CORRECTS MISTAKE
   $ agentura correct ecm/order-details \
       --execution-id EXEC-20260219 \
       --correction "UAE corridor orders need LULU escalation, not standard path"
   → Stored in .agentura/corrections.json
   → Reflexion rule generated in .agentura/reflexion_entries.json
   → DeepEval regression test auto-generated
   → Promptfoo regression test auto-generated
   → GUARDRAILS.md updated

3. NEXT EXECUTION — SKILL IS SMARTER
   System prompt now includes:
   ## Learned Rules (from past corrections)
   - **REFL-001**: UAE corridor orders need LULU escalation...
     _Applies when_: ecm/order-details with order_id, query inputs.
   → Model sees the learned rule and applies it
   → Accept rate improves over time

4. TEST VALIDATION CLOSES THE LOOP
   POST /api/v1/knowledge/validate/ecm/order-details
   → Runs generated tests
   → Marks reflexion as validated (backed by passing test)
   → Confidence increases
```

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
│       ├── app/(chat)/           # Chat-first interface (/)
│       ├── app/(dashboard)/      # Admin dashboard (/dashboard/*)
│       ├── components/chat/      # Chat components (sidebar, messages, input)
│       └── lib/                  # API client, chat state, command router
│
├── skills/                       # Skill definitions (the workloads)
│   ├── platform/classifier/      # Routes to correct domain
│   ├── ecm/order-details/        # ECM order diagnosis
│   ├── wealth/suggest-allocation/ # Portfolio allocation
│   └── frm/rule-simulation/      # Fraud rule simulation
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
