# Agentura Roadmap: From Skills Platform to Self-Driving Company OS

> **Goal**: Evolve Agentura into what Claude achieves with engineers — but for an entire organization.
> Claude Code turns one developer into a team. Agentura turns one founder into a company.

---

## The North Star

Background agents are agents that run autonomously on cloud infrastructure, triggered by events, schedules, or system signals — without a human at the keyboard. The industry is converging on three pillars:

| Pillar | Industry Standard | Agentura Status |
|--------|-------------------|-----------------|
| **Isolated Compute** | On-demand sandboxed environments | PTC + CC workers in K8s pods |
| **Event Routing** | GitHub webhooks, Slack, cron, custom triggers | Partially built (heartbeat scheduler, pipeline triggers) |
| **Governance** | Permissions, audit trails, cost controls | Ticket trace logs, cost tracking, domain isolation |

**Reference architecture** (from [background-agents.com](https://background-agents.com), [Ona](https://ona.com/stories/ai-agents-need-infrastructure), [Anthropic](https://www.anthropic.com/research/building-effective-agents)):

```
Events (GitHub, Slack, Cron, Manual)
  │
  ▼
┌─────────────────────────────┐
│  Orchestrator / Router      │  ← CEO/PM agents live here
│  (classify → prioritize →   │
│   delegate → verify)        │
└──────────┬──────────────────┘
           │ Tickets
    ┌──────┼──────┐
    ▼      ▼      ▼
 Worker  Worker  Worker        ← Dev/QA/Support agents
    │      │      │
    ▼      ▼      ▼
 PR/Artifact/Report            ← Governed output (human review gates)
```

---

## What Exists Today

### Infrastructure (Proven)
- Go gateway → Python executor (two-tier)
- PTC worker (MCP-only, ~200MB) + Claude Code worker (file I/O, ~800MB)
- PostgreSQL: agents, tickets, fleet_sessions, reflexions, failure_cases
- Pipeline engine: YAML-driven parallel/sequential phases with fan-in
- Fleet session tracking with per-agent cost + latency metrics
- Atomic ticket checkout (`FOR UPDATE SKIP LOCKED`)
- Bayesian reflexion scoring (MemRL)
- Domain-scoped memory isolation

### Skills (38 total across 10 domains)
- **dev/**: app-builder, deployer, pr-test-runner, pr-slt-validator, pr-doc-generator, pr-reporter, triage
- **ge/**: ceo-briefing, cto-briefing, daily-briefing, action-tracking, track-actions
- **pm/**: meeting-update, project-setup
- **incubator/**: spec-analyzer, pit-builder, mobile-builder, quality-gate, reporter, orchestrate, preview-generator
- **ecm/**: ecm-daily-flow, pattern-intelligence, process-stuck-order, triage-and-assign
- **product/**: trend-researcher
- **hr/**: onboarding-guide, resume-screener, triage
- **productivity/**: email-drafter, meeting-summarizer, triage
- **qa/**: reality-checker
- **support/**: exec-summary-generator, support-responder

### Agency (Agent Hierarchy)
- 14 agents registered across 4 domains (ECM, PM, Incubator, GE)
- `reports_to` hierarchy (org tree)
- Heartbeat scheduler (cron-based daemon)
- Agent delegation endpoint (`POST /agents/{id}/delegate`)

---

## Phase 1: Make What Exists Reliable (Week 1-2)

> **Principle**: "Don't build meta-learning before the core execution loop is proven." — GR-010

### 1.1 End-to-End Pipeline Smoke Test
- [ ] Deploy current `github-pr-parallel` pipeline against a real PR
- [ ] Verify: trigger → fleet session → 3 parallel agents → fan-in reporter → GitHub Check posted
- [ ] Measure: total latency, per-agent cost, failure rate
- **Done when**: One real PR reviewed by the fleet, Check posted to GitHub

### 1.2 Heartbeat Scheduler Production Run
- [ ] Pick one agent (e.g., `ge/ceo-briefing`) and run its heartbeat on a real cron schedule
- [ ] Verify: ticket created → agent executes → result stored → transcript captured
- [ ] Fix any failures in the scheduler daemon loop
- **Done when**: 5 consecutive heartbeats succeed without manual intervention

### 1.3 Ticket Lifecycle Validation
- [ ] Create ticket via API → delegate to agent → agent executes → ticket resolved with result
- [ ] Test atomic checkout under concurrent load (2+ agents competing)
- [ ] Verify trace log captures full audit trail
- **Done when**: Full ticket lifecycle works end-to-end, audit trail is complete

---

## Phase 2: Event-Driven Triggers (Week 3-4)

> **Key insight from Ona**: "The bottleneck isn't writing code anymore." The bottleneck is knowing WHAT to write and WHEN.

### 2.1 GitHub Webhook Integration
- [ ] Gateway endpoint: `POST /webhooks/github` → validate signature → classify event → create ticket
- [ ] Event types: `pull_request.opened`, `pull_request.synchronize`, `issues.opened`, `push` (to main)
- [ ] Auto-dispatch: PR events → `github-pr-parallel` pipeline
- [ ] Issue events → `dev/triage` skill
- **Done when**: Opening a PR auto-triggers the parallel review fleet

### 2.2 Slack Trigger Integration
- [ ] Gateway endpoint: `POST /webhooks/slack` → parse command → create ticket → delegate
- [ ] Commands: `/agentura run {skill}`, `/agentura status`, `/agentura brief`
- [ ] Response: Slack thread with streaming status updates
- **Done when**: `/agentura brief` in Slack triggers CEO briefing and posts result to thread

### 2.3 Cron/Schedule Engine
- [ ] Extend heartbeat scheduler to support pipeline triggers (not just single skills)
- [ ] Config: `schedule: "0 7 * * 1-5"` in pipeline YAML
- [ ] Daily briefings, weekly trend reports, nightly dependency scans
- **Done when**: Daily CEO briefing runs at 7am without anyone touching anything

---

## Phase 3: CEO & PM Agent Skills (Week 5-8)

> **The shift**: From "agents that do tasks" to "agents that decide what tasks to do."

### 3.1 CEO Agent — Strategic Orchestrator

**Identity**: The CEO agent doesn't write code. It reads signals, sets priorities, and delegates.

```
skills/ge/ceo-agent/
  SKILL.md              # Strategic decision-making protocol
  agentura.config.yaml  # executor: ptc, triggers: cron + slack + webhook
```

**Capabilities**:

| Capability | Description | Trigger |
|------------|-------------|---------|
| **Morning Brief** | Aggregate overnight: PRs merged, tickets resolved, failures, costs | Cron 7am |
| **Priority Setter** | Review open tickets, reorder by business impact, assign urgency | Cron + manual |
| **Resource Allocator** | Which agents are idle? Which are stuck? Redistribute work | Cron 15min |
| **Risk Monitor** | Flag: agent failures > threshold, cost burn rate, stuck tickets | Event-driven |
| **Weekly Retro** | What shipped, what failed, what to learn, reflexion quality | Cron Friday 5pm |

**Data Sources** (all exist in PostgreSQL today):
- `tickets` — open/resolved/escalated counts by domain
- `fleet_sessions` — pipeline success rates, costs, latencies
- `heartbeat_runs` — scheduled task health
- `reflexions` — learning quality (Bayesian scores)
- `failure_cases` — incident trends

**Output**: Structured decisions → new tickets created, priorities updated, Slack posts

### 3.2 PM Agent — Backlog & Spec Manager

**Identity**: The PM agent translates CEO priorities into executable work items.

```
skills/pm/pm-agent/
  SKILL.md              # Backlog grooming and spec writing protocol
  agentura.config.yaml  # executor: ptc, triggers: cron + slack + ticket-assigned
```

**Capabilities**:

| Capability | Description | Trigger |
|------------|-------------|---------|
| **Backlog Groomer** | Review all open tickets, add missing context, estimate complexity | Cron daily |
| **Spec Writer** | Given a ticket title, produce structured spec with acceptance criteria | Ticket assigned |
| **Sprint Planner** | Group tickets into sprint-sized batches by dependency and priority | Cron weekly |
| **Stakeholder Update** | Summarize sprint progress for CEO agent and Slack | Cron daily |
| **Retrospective Input** | Collect data for CEO weekly retro: velocity, blockers, learnings | Cron Friday |

**Key interaction pattern**:
```
CEO Agent                    PM Agent                    Dev Agents
    │                            │                           │
    │ "Priority: fix auth bug"   │                           │
    │ ──────────────────────────>│                           │
    │                            │ Create spec ticket        │
    │                            │ ─────────────────────────>│
    │                            │                           │ Execute
    │                            │          Status update    │
    │                            │ <─────────────────────────│
    │    Sprint summary          │                           │
    │ <──────────────────────────│                           │
```

### 3.3 Product Agent — Market Intelligence

**Extends existing `product/trend-researcher`**:

| Capability | Description | Trigger |
|------------|-------------|---------|
| **Competitive Scan** | Monitor competitor releases, pricing changes, feature launches | Cron weekly |
| **User Signal Aggregator** | Parse support tickets for feature requests and pain points | Cron daily |
| **Opportunity Scorer** | Rank product opportunities by effort vs. impact | On-demand |
| **Feature Proposal** | Draft feature specs from scored opportunities → PM agent | Manual |

---

## Phase 4: Hierarchical Orchestration (Week 9-12)

> **From Cursor's research**: "The breakthrough design employs a hierarchical structure: Root Planner → Subplanners → Workers."
> **From Anthropic**: "Orchestrator-Workers uses a central LLM to dynamically break down tasks and delegate to workers, then synthesize results."

### 4.1 Agent Delegation Protocol
- [ ] Extend ticket system: `created_by` agent can track delegated tickets
- [ ] Parent-child tickets already supported (`parent_id` FK) — activate for agent chains
- [ ] CEO creates parent ticket → PM creates sub-tickets → Dev agents claim sub-tickets
- [ ] Fan-in: when all sub-tickets resolved, parent auto-resolves with aggregated result
- **Done when**: CEO agent creates a priority, PM breaks it down, dev agents execute, CEO sees result

### 4.2 Agent-to-Agent Communication
- [ ] Trace log becomes the communication channel (append-only, ordered)
- [ ] Agents read trace entries from upstream agents before executing
- [ ] Context chain: CEO decision → PM spec → Dev implementation → QA validation
- **Done when**: A 4-agent chain completes a task with each agent reading prior context

### 4.3 Escalation Protocol
- [ ] Agent detects: "I can't solve this" → escalates ticket to `reports_to` agent
- [ ] Escalation reasons: budget exceeded, repeated failures, ambiguous requirements
- [ ] CEO agent as ultimate escalation target → notifies human via Slack
- **Done when**: A stuck dev agent escalates → PM re-specs → dev retries → succeeds

### 4.4 Fleet Orchestration v2
- [ ] CEO agent can trigger pipelines (not just single skills)
- [ ] Dynamic pipeline composition: CEO decides which agents to include based on ticket type
- [ ] Example: "This PR touches auth → add security-reviewer agent to the fleet"
- **Done when**: CEO agent dynamically adjusts pipeline composition based on context

---

## Phase 5: Background Agent Infrastructure (Week 13-16)

> **From Ona**: "Three pillars — isolated compute, event routing, governance — are where the enterprise tooling is consolidating."

### 5.1 Always-On Agent Loop
- [ ] Agents run as persistent processes (not request-response)
- [ ] Check for new tickets every N seconds (configurable per agent)
- [ ] Heartbeat + ticket checkout = agent work loop
- [ ] Graceful shutdown: finish current ticket before terminating
- **Done when**: CEO and PM agents run 24/7, processing tickets as they arrive

### 5.2 Parallel Fleet Scaling
- [ ] Dynamic worker pod scaling based on ticket queue depth
- [ ] K8s HPA: scale cc-worker pods 1→5 based on pending ticket count
- [ ] Fleet session tracks which pods handled which agents
- **Done when**: A burst of 10 PRs auto-scales workers and processes in parallel

### 5.3 Governance Dashboard
- [ ] Web UI: agent org chart with live status (idle/working/stuck)
- [ ] Per-agent metrics: tickets resolved, cost spent, success rate, avg latency
- [ ] Fleet session history: pipeline runs with drill-down to per-agent details
- [ ] Cost controls: daily/weekly budget limits per agent, alerts at threshold
- **Done when**: Dashboard shows real-time agent activity with cost tracking

### 5.4 Audit Trail & Compliance
- [ ] Every agent action logged: what was read, what was written, what was decided
- [ ] Trace log is immutable (append-only, no deletes)
- [ ] Export: generate audit report for any time period
- **Done when**: Can answer "what did agent X do between date A and date B?" from the UI

---

## Phase 6: Self-Improving Organization (Week 17-20)

> **From Anthropic's Agent SDK**: "The agent loop: Gather context → Take action → Verify work."
> Applied at org level: **Observe → Decide → Act → Learn.**

### 6.1 Reflexion-Driven Improvement
- [ ] CEO weekly retro analyzes reflexion quality (Bayesian scores)
- [ ] Low-scoring reflexions pruned, high-scoring ones promoted
- [ ] New reflexions generated from failure cases (DEC-067)
- **Done when**: Reflexion quality measurably improves over 4 weeks

### 6.2 Cross-Domain Learning
- [ ] PM agent identifies patterns across domains (e.g., "ECM and Support have similar triage failures")
- [ ] Propose reflexion sharing between domains (with governance approval)
- [ ] CEO agent approves cross-domain reflexion transfers
- **Done when**: A learning from ECM domain improves Support domain success rate

### 6.3 Autonomous Skill Creation
- [ ] PM agent identifies repeated manual tasks → proposes new skill
- [ ] Generates SKILL.md + config YAML from ticket patterns
- [ ] Human reviews and approves → skill deployed automatically
- **Done when**: PM agent proposes a skill that gets approved and runs successfully

### 6.4 Metrics-Driven Priority Setting
- [ ] CEO agent uses real execution data (not gut feel) for prioritization
- [ ] Inputs: ticket velocity, cost per resolution, failure rates, learning curve
- [ ] Output: ranked priority list with data justification
- **Done when**: CEO priorities correlate with measurable business outcomes

---

## The Maturity Model

| Level | Name | Description | Agentura Today |
|-------|------|-------------|----------------|
| **L0** | Manual | Human invokes skills one at a time | Mostly here |
| **L1** | Triggered | Events auto-dispatch to single agents | Heartbeat scheduler |
| **L2** | Pipeline | Multi-agent workflows with fan-in/fan-out | Fleet parallel PR pipeline |
| **L3** | Orchestrated | CEO/PM agents direct dev agents via tickets | **Target: Phase 4** |
| **L4** | Self-Driving | Agents identify work, execute, learn, improve autonomously | **Target: Phase 6** |

**Industry benchmarks** (from research):
- Stripe Minions: 1,000+ agent-authored PRs merged/week (L2-L3)
- Ramp: 57% of all merged PRs are agent-authored (L2-L3)
- Cursor's experiment: ~1,000 commits/hour with hierarchical agents (L3)

---

## CEO + PM Agent Interaction Model

```
                    ┌──────────────┐
                    │  CEO Agent   │
                    │              │
                    │ Priorities   │
                    │ Risk Monitor │
                    │ Weekly Retro │
                    └──────┬───────┘
                           │ Delegates
                    ┌──────▼───────┐
                    │  PM Agent    │
                    │              │
                    │ Spec Writer  │
                    │ Sprint Plan  │
                    │ Grooming     │
                    └──────┬───────┘
                           │ Creates tickets
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Dev Agent │ │QA Agent  │ │Support   │
        │          │ │          │ │Agent     │
        │app-build │ │reality-  │ │support-  │
        │deployer  │ │checker   │ │responder │
        │pr-fleet  │ │          │ │          │
        └──────────┘ └──────────┘ └──────────┘
              │            │            │
              ▼            ▼            ▼
         PRs/Deploys   Test Reports   Responses
```

---

## What This Achieves

**Today (L0-L1)**: You manually run `agentura run dev/app-builder "build me X"` and wait.

**Phase 4 (L3)**: You tell the CEO agent "we need to ship auth by Friday" and it:
1. Creates a priority ticket
2. PM agent breaks it into spec + implementation + test + deploy tickets
3. Dev agents claim and execute tickets in parallel
4. QA agent validates the output
5. PM agent reports progress to CEO
6. CEO agent posts summary to Slack

**Phase 6 (L4)**: The CEO agent notices from support tickets that users keep asking about password reset. Without being told, it:
1. Creates a priority: "Password reset UX is a pain point"
2. PM agent specs a redesign
3. Dev agents build it
4. The system learns from the outcome and improves its prioritization

This is the self-driving company OS — the same shift that Claude Code brought to individual engineers, applied to the entire organization.

---

## Sources

- [The Self-Driving Codebase — Background Agents](https://background-agents.com/)
- [Ona — AI Agents Need Infrastructure](https://ona.com/stories/ai-agents-need-infrastructure)
- [Ona — Visual Guide to Self-Driving Codebases](https://ona.com/stories/visual-guide-self-driving-codebases)
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)
- [Cursor — Towards Self-Driving Codebases](https://cursor.com/blog/self-driving-codebases)
- [Anthropic — Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)
