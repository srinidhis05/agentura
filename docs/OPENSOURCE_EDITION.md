# Agentura Open-Source Edition

What ships open-source, what stays proprietary, and why.

---

## Positioning

**Agentura OSS** = the open-source orchestration layer for running AI agent organizations on your own infrastructure.

Think of it as: **Paperclip.ing meets Claude Code** — Paperclip's org-chart-driven agent orchestration combined with Claude-grade code generation, all config-driven and self-hosted.

| Competitor | What They Do | What Agentura Adds |
|------------|-------------|-------------------|
| **Paperclip.ing** | Org charts, budgets, delegation for agents | Actual skill execution engine + MCP tool binding + pipeline parallelism |
| **CrewAI** | Multi-agent framework (Python code) | Config-driven (YAML, not Python), K8s-native isolation, persistent learning |
| **LangGraph** | Agent workflow graphs (code) | Zero-code skill authoring (SKILL.md), fleet sessions, cost tracking |
| **AutoGen** | Multi-agent conversations | Hierarchical orchestration (CEO→PM→Dev), not peer-to-peer chat |

**One sentence**: Agentura is what you get when you stop building agent frameworks and start building agent organizations.

---

## Open-Source Tier (MIT License)

Everything needed to run an AI agent organization on your own K8s cluster.

### Core Engine

| Component | What It Does | Key Files |
|-----------|-------------|-----------|
| **Go Gateway** | HTTP routing, webhook handling, SSE streaming, Slack integration | `gateway/` |
| **Python Executor** | Skill loading, context injection, execution dispatch, cost tracking | `sdk/agentura_sdk/` |
| **Pipeline Engine** | YAML-driven parallel/sequential multi-agent workflows | `sdk/agentura_sdk/pipelines/engine.py` |
| **Fleet Sessions** | Track parallel agent executions with per-agent cost/latency | `sdk/agentura_sdk/memory/pg_store.py` |

### Skill SDK

| Component | What It Does | Key Files |
|-----------|-------------|-----------|
| **CLI** (`agentura`) | `create`, `validate`, `run`, `list`, `test`, `correct` | `sdk/agentura_sdk/cli/` |
| **Skill Loader** | SKILL.md parsing, 5-layer context injection, reflexion loading | `sdk/agentura_sdk/runner/skill_loader.py` |
| **Config System** | YAML normalization, type-safe config parsing | `sdk/agentura_sdk/runner/config_loader.py` |
| **Templates** | Jinja2 scaffolding for new skills (SKILL.md, config, handler, tests) | `sdk/agentura_sdk/templates/` |

### Execution Layer

| Component | What It Does | Key Files |
|-----------|-------------|-----------|
| **PTC Worker** | Lightweight MCP-only agent executor (~200MB image) | `ptc-worker/` |
| **Claude Code Worker** | Full file I/O + code generation executor (~800MB image) | `claude-code-worker/` |
| **Sandbox Factory** | K8s/Docker backend selection via `SANDBOX_BACKEND` env | `sdk/agentura_sdk/sandbox/` |

### Agent Organization

| Component | What It Does | Key Files |
|-----------|-------------|-----------|
| **Agency System** | Org chart, `reports_to` hierarchy, delegation, autonomy levels | `sdk/agentura_sdk/agency/` |
| **Ticket System** | Create → assign → execute → resolve with audit trails | `gateway/internal/handler/ticket.go` |
| **Heartbeat Scheduler** | Cron-based scheduled agent executions | `gateway/internal/handler/heartbeat.go` |
| **Domain Isolation** | Scoped memory, per-domain triage, config-driven routing | Built into skill loader + gateway |

### Triggers & Integrations

| Trigger | How It Works |
|---------|-------------|
| **GitHub Webhooks** | PR opened/sync → pipeline auto-dispatch |
| **Slack Commands** | Pattern matching → skill execution → thread response |
| **Cron/Heartbeat** | Scheduled agent wake-ups (daily briefings, status checks) |
| **Manual API** | `POST /api/v1/skills/{domain}/{name}/execute` |
| **Pipeline Chaining** | `context_for_next` passes output between pipeline steps |

### Learning System

| Component | What It Does |
|-----------|-------------|
| **Corrections** | User corrects agent output → stored for future context |
| **Reflexions** | Synthesized rules from corrections, Bayesian utility scoring |
| **Failure Cases** | Failed executions → auto-generated regression tests |
| **Memory Store** | PostgreSQL-backed with CompositeStore pattern |

### Web Dashboard

| Feature | What It Shows |
|---------|--------------|
| **Skills Browser** | All skills with domain/role/cost metadata |
| **Execution History** | Per-execution cost, latency, output, reasoning trace |
| **Fleet Sessions** | Parallel pipeline runs with per-agent drill-down |
| **Agent Org Chart** | Hierarchy visualization with live status |
| **Memory Explorer** | Reflexions, corrections, failure cases |

### Reference Skills (Included)

These skills ship with the OSS edition as working examples:

| Domain | Skills | Purpose |
|--------|--------|---------|
| **dev** | pr-code-reviewer, pr-test-runner, pr-slt-validator, pr-doc-generator, pr-reporter, app-builder, deployer, triage | Full PR review fleet + app building |
| **pm** | meeting-update, project-setup, pm-heartbeat, triage | Meeting processing + status digests |
| **support** | support-responder, exec-summary-generator | Ticket auto-response |
| **hr** | resume-screener, onboarding-guide, triage | Hiring automation |
| **qa** | reality-checker | Output validation |
| **productivity** | email-drafter, meeting-summarizer, triage | Personal productivity |

### Pipelines (Included)

| Pipeline | What It Does |
|----------|-------------|
| `github-pr-parallel` | 4-agent parallel PR review (reviewer + testing + SLT + docs → reporter) |
| `build-deploy` | Sequential: build → test → deploy |

### Infrastructure (Included)

| Component | What It Does |
|-----------|-------------|
| **K8s Manifests** | Deployment YAMLs for executor, gateway, web, postgres |
| **Docker Compose** | Local development fallback |
| **MCP Server (K8s)** | kubectl operations via MCP protocol |

---

## Enterprise Tier (Paid)

Features that matter at scale — multi-team, compliance, and managed operations.

### Multi-Tenancy

| Feature | Description |
|---------|-------------|
| **Workspace Isolation** | Multiple teams/orgs on one cluster with full data isolation |
| **RBAC** | Role-based access to skills, agents, and pipelines per team |
| **SSO/SAML** | Enterprise identity provider integration |
| **API Keys** | Scoped API keys per team with rate limits |

### Advanced Governance

| Feature | Description |
|---------|-------------|
| **Approval Workflows** | Multi-level approval gates (manager → director → VP) |
| **Compliance Export** | Audit trail export in SOC2/ISO27001 formats |
| **PII Detection** | Auto-flag and redact PII in agent outputs before posting |
| **Cost Allocation** | Per-team cost attribution with chargeback reporting |

### Managed Operations

| Feature | Description |
|---------|-------------|
| **Auto-Scaling** | HPA-driven worker pod scaling based on ticket queue depth |
| **Health Monitoring** | Agent health scoring, SLA tracking, auto-restart on failure |
| **Managed MCP Gateway** | Pre-built MCP server connectors (Jira, Salesforce, SAP, ServiceNow) |
| **Priority Support** | Dedicated Slack channel, SLA-backed response times |

### Advanced Learning

| Feature | Description |
|---------|-------------|
| **Cross-Domain Learning** | Reflexion sharing between domains (with governance approval) |
| **Skill Marketplace** | Browse and install community-built skills |
| **Custom Model Routing** | Route skills to different LLM providers based on cost/quality trade-offs |
| **A/B Testing** | Run two versions of a skill, measure quality, auto-promote winner |

---

## The Line: Why Here?

The OSS/Enterprise split follows one principle: **everything needed to run agents ships free; everything needed to run agents at enterprise scale is paid.**

| Dimension | OSS | Enterprise |
|-----------|-----|------------|
| **Skills** | Unlimited | Unlimited |
| **Agents** | Unlimited | Unlimited |
| **Pipelines** | Unlimited | Unlimited |
| **Teams** | Single team | Multi-team with isolation |
| **Governance** | Cost budgets + audit trails | RBAC + approval workflows + compliance |
| **Scaling** | Manual pod management | Auto-scaling + health monitoring |
| **MCP Connectors** | BYO MCP servers | Pre-built enterprise connectors |
| **Support** | Community (GitHub Issues) | Priority (SLA-backed) |

A solo founder or small team gets the full platform free. A 500-person org that needs multi-team isolation, compliance, and managed operations pays for it.

---

## Getting Started (OSS)

```bash
# Clone
git clone https://github.com/srinidhis05/agentura.git
cd agentura

# Set up API keys
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env

# Deploy to K8s
kubectl apply -f deploy/k8s/

# Create your first skill
cd sdk && pip install -e .
agentura create skill mycompany/my-first-skill --role agent

# Edit, validate, deploy
agentura validate mycompany/my-first-skill
kubectl cp skills/mycompany/my-first-skill executor-pod:/skills/mycompany/my-first-skill

# Execute
curl -X POST http://localhost:30080/api/v1/skills/mycompany/my-first-skill/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"task": "Hello world"}}'
```

---

## Comparison Matrix

| Feature | Agentura OSS | Paperclip | CrewAI | LangGraph | AutoGen |
|---------|-------------|-----------|--------|-----------|---------|
| **Skill authoring** | YAML + Markdown (zero code) | BYO agent (code) | Python classes | Python code | Python code |
| **Org hierarchy** | Yes (reports_to, delegation) | Yes (org chart) | Crews (flat) | No | No |
| **Pipeline engine** | YAML parallel/sequential | No | Sequential | Graph-based | No |
| **K8s-native** | Yes (pod-per-execution) | Self-hosted | No | No | No |
| **MCP tools** | Built-in (PTC executor) | Via adapters | No | No | No |
| **Cost tracking** | Per-execution, per-agent | Per-agent budgets | No | No | No |
| **Persistent learning** | Bayesian reflexions | No | No | Checkpointing | No |
| **Fleet sessions** | Yes (parallel tracking) | No | No | No | No |
| **Slack integration** | Built-in (commands + threads) | Webhook adapters | No | No | No |
| **License** | MIT | MIT | Apache 2.0 | MIT | MIT |
