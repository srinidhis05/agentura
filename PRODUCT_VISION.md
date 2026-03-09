# Agentura — Product Vision (Amazon-Style Working Backwards)

---

## PRESS RELEASE

**FOR IMMEDIATE RELEASE**

### Agentura Ships Self-Driving Development Teams — Software That Builds, Reviews, and Ships Itself

*Background agents replace the 90% of software delivery that isn't creative problem-solving*

**LONDON** — Agentura today announced the general availability of its self-driving development platform, which uses hierarchical AI agents to autonomously handle the complete software delivery lifecycle — from backlog grooming to code generation, testing, review, and deployment.

Unlike coding assistants that help individual developers write code faster, Agentura operates as a complete engineering organization. A CEO agent reads business signals and sets priorities. A PM agent breaks priorities into specs. Dev agents build and test in parallel. QA agents validate. The entire loop runs in the background — on K8s, on schedule, on events — without a human at the keyboard.

"The bottleneck in software isn't writing code anymore," said the founding team. "It's everything around the code — deciding what to build, reviewing what was built, testing it, documenting it, deploying it. We automated the whole loop."

Early results show a single founder operating a full product development cycle: idea → spec → implementation → test → deploy → learn, with human involvement only at strategic decision points.

**Agentura is open-source and available at [github].**

---

## THE CUSTOMER PROBLEM

### Who is the customer?

**Primary**: Solo founders and small teams (1-5 people) building software products who can't afford to hire a 20-person engineering org but need one.

**Secondary**: Engineering leaders at mid-size companies drowning in undifferentiated work — PR reviews, dependency updates, test coverage, documentation — that never makes the sprint.

### What is the problem?

#### Problem 1: The Talent Gap
You have the vision for a product. You can describe what needs to be built. But between "idea" and "shipped feature" there are 15 roles: product manager, architect, frontend dev, backend dev, QA, DevOps, technical writer, code reviewer, project manager...

No solo founder or small team can fill all those seats. So things ship slow, ship broken, or don't ship at all.

#### Problem 2: The Undifferentiated Work Problem
Even at funded companies, engineers spend **60-70% of their time on work that isn't creative problem-solving**:

- Reviewing PRs (reading, commenting, requesting changes, re-reviewing)
- Writing tests for obvious edge cases
- Updating dependencies and fixing what breaks
- Writing documentation nobody reads but auditors require
- Triaging bugs and routing tickets
- Migrating to new framework versions

This work is necessary but not differentiated. It's the tax you pay to ship software. Today, humans pay it. Tomorrow, agents do.

#### Problem 3: The Coordination Tax
The bigger the team, the more time goes to coordination, not creation:
- Standup meetings to sync status
- Sprint planning to slice work
- Retrospectives to learn from mistakes
- Stakeholder updates to keep leadership informed
- Backlog grooming to keep the queue healthy

Each of these is a knowledge-synthesis task — exactly what LLMs excel at.

### How are customers solving this today?

| Solution | What it does | What it doesn't do |
|----------|-------------|-------------------|
| **Claude Code / Cursor** | One developer writes code faster | Doesn't review, test, deploy, or decide what to build |
| **GitHub Copilot** | Autocompletes lines of code | Doesn't understand the project, business context, or priorities |
| **CI/CD (GitHub Actions)** | Runs predefined scripts on triggers | Doesn't reason, adapt, or write the scripts |
| **Hiring** | Fills seats | Costs $150K+/year per seat, takes months, requires management |
| **Outsourcing** | Fills seats cheaper | Quality variance, timezone gaps, context loss |

**The gap**: No solution today provides an autonomous, coordinated software team that works in the background.

---

## THE SOLUTION

### Agentura: A Self-Driving Engineering Organization

Agentura is an open-source platform that runs AI agents as a hierarchical organization — CEO, PM, Dev, QA, Support — executing the full software delivery lifecycle autonomously on Kubernetes.

**One sentence**: It's what you get when you apply the "background agents" pattern (from Stripe, Ramp, Cursor) not just to code generation, but to the entire company operating system.

### How is this different from Claude Code?

| Dimension | Claude Code | Agentura |
|-----------|-------------|----------|
| **Unit of work** | Single coding task | Business objective |
| **Who drives** | Human types a prompt | CEO agent reads signals, sets priorities |
| **Parallelism** | One agent, one task | Fleet of agents, parallel pipelines |
| **Memory** | Per-session context | Persistent PostgreSQL with Bayesian learning |
| **Trigger** | Human invocation | Events, webhooks, cron, Slack |
| **Output** | Code changes in local repo | PRs, deployments, reports, Slack posts |
| **Governance** | User approves each action | Audit trails, cost controls, domain isolation |
| **Scope** | Developer productivity | Organization productivity |

Claude Code is the engine. Agentura is the car — with steering, navigation, and a driver.

---

## THE CUSTOMER EXPERIENCE

### Experience 1: Morning Autopilot

**7:00 AM** — You haven't touched your laptop yet.

The CEO agent wakes up on cron. It queries PostgreSQL:
- 3 PRs were opened overnight by the incubator agents
- The `pr-test-runner` fleet reviewed all 3: 2 passed, 1 failed tests
- Support ticket volume spiked for the "password reset" flow
- Yesterday's deployment of `auth-service` has a 2.3% error rate (up from 0.1%)

It creates 3 tickets:
1. **P0**: "Investigate auth-service error spike" → assigned to `dev/triage`
2. **P1**: "Fix failing PR #47 tests" → assigned to `dev/app-builder`
3. **P2**: "Password reset UX — investigate support ticket pattern" → assigned to `product/trend-researcher`

It posts a morning brief to `#engineering` in Slack.

**7:02 AM** — The PM agent picks up. It reads the 3 new tickets:
- P0 gets a spec: "Check error logs for auth-service pod, identify root cause, propose fix"
- P1 gets context: "PR #47 test failures are in `test_auth_flow.py`, lines 42-67"
- P2 gets scope: "Pull last 30 days of support tickets mentioning 'password' or 'reset'"

**7:05 AM** — Dev agents claim tickets via atomic checkout (`FOR UPDATE SKIP LOCKED`). Three workers spin up in parallel.

**8:30 AM** — You open your laptop. Slack shows:
- P0: "Root cause identified — expired JWT signing key. Fix PR #52 opened, tests passing."
- P1: "PR #47 tests fixed, re-review requested."
- P2: "Report ready — 47 tickets in 30 days, 82% mention 'email not received'. Recommendation: add email delivery status tracking."

You review 2 PRs, merge them, and make a product decision on #3. Total human time: 20 minutes. Total agent time: 90 minutes of parallel work.

### Experience 2: PR Opened → Fleet Reviews

A developer pushes a PR. GitHub webhook fires.

```
GitHub → Gateway webhook → create ticket → trigger github-pr-parallel pipeline
```

Three agents spin up in parallel:
1. **pr-test-runner**: Clones repo, runs test suite, reports pass/fail with details
2. **pr-slt-validator**: Checks code against team standards (naming, architecture, patterns)
3. **pr-doc-generator**: Generates/updates documentation for changed APIs

All three complete. The **pr-reporter** fan-in agent aggregates results and posts a single GitHub Check:

```
PR Review Fleet — 3/3 agents completed

Tests: 142 passed, 0 failed
Standards: 2 warnings (method too long in auth.go:47, missing error wrap in handler.go:92)
Docs: API docs updated for /api/v1/users endpoint

Recommendation: APPROVE with minor fixes
```

Total time: 3 minutes. No human reviewer needed for the first pass.

### Experience 3: "Ship auth by Friday"

You type in Slack: `/agentura priority "Ship passwordless auth by Friday"`

**CEO agent** receives via Slack webhook:
- Creates parent ticket: "Passwordless auth — target Friday"
- Sets priority: P0
- Delegates to PM agent

**PM agent** breaks it down (4 sub-tickets):
1. "Design: passwordless auth flow (magic link vs. passkey)" → `product/trend-researcher`
2. "Implement: auth backend changes" → `dev/app-builder`
3. "Test: auth flow integration tests" → `qa/reality-checker`
4. "Deploy: auth-service to staging → production" → `dev/deployer`

Tickets are ordered by dependency: 1 → 2 → 3 → 4.

Each agent claims its ticket when the previous one resolves. The PM agent posts daily progress to Slack. By Thursday evening:

```
Passwordless Auth — Sprint Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] Design: Magic link chosen (simpler, wider device support)
[x] Implement: PR #58 merged (backend + email service)
[x] Test: 23 integration tests passing
[ ] Deploy: Staged for Friday 9am rollout

Status: ON TRACK
Cost: $4.20 (across 4 agents, 7 executions)
```

### Experience 4: Weekly Retro (Self-Improvement)

**Friday 5:00 PM** — CEO agent runs weekly retro automatically.

It queries the learning system:
- **Reflexions created this week**: 5 new learnings
- **Top-performing reflexion**: "Always run `go vet` before `go test`" (utility score: 0.89, helped 8/9 times)
- **Worst reflexion**: "Prefer PostgreSQL over SQLite for all services" (utility score: 0.33, helped 1/4 times — too broad)
- **Failure cases logged**: 2 (auth-service error spike, flaky test in PR #47)

It generates:
```
Weekly Engineering Retro — March 7, 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Shipped: 12 tickets resolved, 8 PRs merged, 2 deployments
Cost:    $18.40 total ($2.30/ticket avg)
Quality: 92% first-attempt success rate (up from 85% last week)

Top Learning: Pre-validation (vet/lint before test) saves 40% retry cost
Action: Promote to all dev agent skills

Concern: "Prefer PostgreSQL over SQLite" reflexion is too broad — demoting
Action: Rewrite as "Use PostgreSQL when concurrent writes expected"

Incidents: 2 → converted to regression test cases
```

The system literally gets better every week, without anyone telling it to.

---

## ARCHITECTURE

### The Three Pillars

Every background agent platform needs three things. Here's how Agentura implements each:

#### Pillar 1: Isolated Compute

```
┌──────────────────────────────────────────────────┐
│                 Kubernetes Cluster                 │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │PTC Worker│  │CC Worker │  │CC Worker │  ...    │
│  │ ~200MB   │  │ ~800MB   │  │ ~800MB   │        │
│  │ MCP-only │  │ File I/O │  │ File I/O │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                    │
│  Each skill execution = fresh pod                  │
│  No shared state between executions                │
│  Network-isolated, resource-bounded                │
└──────────────────────────────────────────────────┘
```

- **PTC workers** (~200MB): Lightweight, MCP-only tasks (deployer, infra ops, briefings)
- **CC workers** (~800MB): Full Claude Code environment for code generation and file I/O
- Workers are disposable — created per execution, destroyed after
- No skill-specific Docker images (GR-001) — one image, many skills via YAML config

#### Pillar 2: Event Routing

```
Events                          Routing                    Execution
─────                          ───────                    ─────────
GitHub webhook    ──┐
Slack command     ──┼──→  Gateway  ──→  Ticket  ──→  Pipeline/Skill
Cron schedule     ──┤      (Go)        (PgSQL)       (Python SDK)
Manual API call   ──┘
```

- **Gateway** (Go): Receives events, validates, classifies, creates tickets
- **Tickets**: Unit of work with priority, assignment, trace log, cost tracking
- **Pipelines**: YAML-defined multi-agent workflows with parallel/sequential phases
- **Heartbeats**: Cron-based scheduled agent executions

#### Pillar 3: Governance

| Layer | Mechanism | Status |
|-------|-----------|--------|
| **Cost control** | Per-agent budget limits, per-execution tracking | Built |
| **Audit trail** | Immutable trace log on every ticket (append-only) | Built |
| **Domain isolation** | Scoped memory — agents can't read other domains' data | Built |
| **Human review gates** | All outputs via PRs or approval prompts | Built |
| **Org hierarchy** | `reports_to` chain, escalation to manager agents | Built |
| **Atomic work claims** | `FOR UPDATE SKIP LOCKED` — no race conditions | Built |

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STRATEGY LAYER                        │
│                                                          │
│   CEO Agent ──→ PM Agent ──→ Product Agent               │
│   (prioritize)  (spec)       (research)                  │
│                                                          │
│   Reads: tickets, fleet_sessions, reflexions, failures   │
│   Writes: new tickets, priority updates, Slack posts     │
└─────────────────────────┬───────────────────────────────┘
                          │ Tickets (delegated)
┌─────────────────────────▼───────────────────────────────┐
│                    EXECUTION LAYER                        │
│                                                          │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│   │Dev Fleet│ │QA Agent │ │Support  │ │Deployer │     │
│   │(parallel│ │(validate│ │(respond)│ │(ship)   │     │
│   │ workers)│ │  )      │ │         │ │         │     │
│   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘     │
│        │           │           │           │            │
│   PRs/Code    Test Reports  Responses   Deployments     │
└─────────────────────────┬───────────────────────────────┘
                          │ Results
┌─────────────────────────▼───────────────────────────────┐
│                    LEARNING LAYER                         │
│                                                          │
│   Reflexions (Bayesian scored)                           │
│   Failure cases → regression tests                       │
│   Cross-domain pattern detection                         │
│   Weekly retro → prune bad learnings, promote good ones  │
└─────────────────────────────────────────────────────────┘
```

---

## TENETS (IN ORDER OF PRIORITY)

1. **Ship real output, not reports about output.** Every agent execution must produce a tangible artifact: a PR, a deployment, a test report, a Slack message. If it only produces "analysis," it's not done.

2. **Human-on-the-loop, not human-in-the-loop.** Humans set direction and review results. They don't babysit each step. If an agent needs human input for every action, the automation has failed.

3. **Config over code.** Adding a new agent, skill, pipeline, or trigger should require zero code changes. YAML config + a SKILL.md prompt is the only deliverable.

4. **Prove at every layer before building the next.** Don't build the CEO agent until the dev agents reliably ship PRs. Don't build cross-domain learning until single-domain reflexions work. Foundation up, not vision down.

5. **Cost is a first-class metric.** Every execution tracks cost. Every agent has a budget. The CEO agent monitors burn rate. If the agents cost more than the engineers they replace, the product has failed.

6. **Learn from production, not from prompts.** Reflexions are scored by Bayesian utility (did it actually help?), not by how clever the prompt sounds. Bad learnings get pruned. Good learnings get promoted. The system improves from data, not from vibes.

---

## KEY METRICS (WHAT WE MEASURE)

### North Star Metric
**Tickets resolved per human-hour** — How much useful work gets done per unit of human attention.

### Supporting Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **First-attempt success rate** | % of agent executions that succeed without retry | > 85% |
| **Cost per ticket** | Average $ spent across all agent executions for one ticket | < $5.00 |
| **Time to resolution** | Ticket created → ticket resolved (automated) | < 30 min for P1-P2 |
| **Human review time** | Time human spends reviewing agent output before merge/approve | < 5 min/PR |
| **Reflexion utility score** | Bayesian (h+2)/(n+4) across all active reflexions | > 0.60 avg |
| **Agent uptime** | % of scheduled heartbeats that execute successfully | > 99% |
| **Pipeline throughput** | Parallel PRs processed per hour | > 10 |

### Anti-Metrics (What We Explicitly Don't Optimize)

- **Lines of code generated** — More code is not better code
- **Number of agents running** — Complexity for complexity's sake
- **Token consumption** — Efficiency matters, but not at the expense of output quality

---

## FAQ

### Customer FAQ

**Q: Is this just a wrapper around Claude?**
A: Claude (via the Agent SDK) is the reasoning engine inside each worker. Agentura is the organizational layer on top — the ticketing system, pipeline engine, fleet orchestration, memory/learning, governance, and the strategy agents (CEO/PM) that decide what work to do. You wouldn't call a car "just a wrapper around an engine."

**Q: How is this different from GitHub Actions + Copilot?**
A: GitHub Actions runs predefined scripts you write. Agentura agents receive a goal, reason about the problem, write code, run tests, iterate on failures, and open PRs — all without a predefined script. The CEO agent even decides which goals to pursue based on business signals.

**Q: What if an agent produces bad code?**
A: Every agent output goes through human review gates — PRs for code, approval prompts for messages, staging for deployments. Agents also have cost budgets, iteration limits, and domain isolation. The learning system actively prunes bad patterns via Bayesian scoring.

**Q: How much does this cost to run?**
A: Depends on workload. A typical PR review fleet (3 agents in parallel) costs ~$0.50-1.00 per PR. A full day of CEO + PM + Dev agent operations runs $15-25. Compare to $800/day for a single senior engineer.

**Q: Can I use my own LLM provider?**
A: Yes. Agentura supports OpenRouter (primary) and Anthropic (direct) with fallback. Any provider accessible via OpenRouter — OpenAI, Mistral, Llama, etc. — works out of the box.

**Q: Do I need Kubernetes?**
A: For production background agents, yes — K8s provides the isolated compute, scaling, and lifecycle management. For local development and testing, Docker works as a fallback.

### Internal FAQ

**Q: Why not just use Claude Code's built-in `/batch` command?**
A: Claude Code's batch mode is for a single developer parallelizing coding tasks within one repo. Agentura solves the organizational problem — multiple agents across multiple domains (dev, QA, product, PM) coordinating via tickets, with persistent memory, governance, and business-level decision-making. Claude Code is the best tool for writing code. Agentura is the system that tells it what code to write, reviews the result, and learns from the outcome.

**Q: Why build CEO/PM agents instead of just more dev agents?**
A: More dev agents without direction is a stampede, not a team. The industry data is clear — Cursor's hierarchical planner (Root Planner → Subplanners → Workers) outperformed flat agent swarms by orders of magnitude. Stripe and Ramp succeed because they have orchestration deciding which PRs to generate, not just agents generating PRs. The CEO/PM layer is the steering wheel.

**Q: Why tickets instead of direct agent-to-agent calls?**
A: Tickets are auditable, persistent, prioritizable, and claimable. Direct calls are fire-and-forget. When the CEO agent creates a ticket, it has a trace log, cost tracking, status lifecycle, and parent-child relationships. If an agent fails, the ticket stays open for retry or escalation. If you use direct calls, you lose all of that. Tickets are the organizational primitive.

**Q: What prevents this from becoming an expensive token furnace?**
A: Three controls: (1) Per-agent budget limits — hard caps per execution and per day. (2) CEO agent monitors aggregate burn rate and flags anomalies. (3) Bayesian reflexion scoring ensures the learning system improves efficiency over time — agents that learn from past executions spend fewer tokens on subsequent runs.

**Q: How do you handle the "agents talking to agents" scaling problem?**
A: Hierarchy, not mesh. The CEO talks to the PM. The PM talks to Dev agents. Dev agents don't talk to each other — they claim independent tickets from a shared queue. This is the Cursor insight: hierarchical planning scales; peer-to-peer coordination doesn't. Maximum fan-out is bounded by pipeline definition, not by agent initiative.

---

## COMPETITIVE LANDSCAPE

```
                        High autonomy
                             ▲
                             │
                    Agentura │ Ona
                    (target) │ (infra)
                             │
        ─────────────────────┼─────────────────────▶
        Single agent         │           Multi-agent
                             │           organization
                             │
             Claude Code     │  GitHub Copilot
             Cursor          │  Workspace
             Devin           │
                             │
                        Low autonomy
```

| Competitor | Strength | Gap Agentura fills |
|------------|----------|-------------------|
| **Claude Code** | Best-in-class code generation | No organizational layer, no background execution |
| **Cursor** | IDE integration, background agents | Single-repo focus, no cross-domain coordination |
| **Devin** | Full autonomy marketing | Closed source, expensive, no self-hosting |
| **Ona/Gitpod** | Infrastructure for agent compute | No agent logic, no strategy layer |
| **GitHub Copilot** | Distribution (every dev has it) | Autocomplete, not autonomous |

**Agentura's moat**: It's the only open-source platform that combines Claude-grade code generation with organizational orchestration (CEO/PM/Dev hierarchy), persistent learning (Bayesian reflexions), and enterprise governance (audit trails, cost controls, domain isolation) — all running on your own K8s cluster.

---

## WHAT DOES V1 LOOK LIKE?

V1 is not the full vision. V1 is the smallest thing that proves the core thesis: **agents can run a development cycle without continuous human intervention.**

### V1 Scope (8 weeks)

| Component | Description | Exists? |
|-----------|-------------|---------|
| Fleet PR review | 3 agents review every PR in parallel | 80% built |
| GitHub webhook trigger | PR opened → fleet auto-dispatched | Needs wiring |
| Heartbeat scheduler | CEO briefing runs daily on cron | 70% built |
| Ticket lifecycle | Create → assign → execute → resolve with audit trail | 90% built |
| Cost dashboard | See per-agent, per-pipeline costs in web UI | 40% built |
| CEO morning brief | Summarize overnight activity, create priority tickets | Skill exists, needs integration |
| PM spec writer | Given a ticket, produce structured spec | Needs building |
| One end-to-end flow | Slack command → CEO priority → PM spec → Dev build → PR | Needs orchestration |

### V1 Does NOT Include
- Self-improving reflexion loops (Phase 6)
- Dynamic pipeline composition (Phase 4.4)
- Auto-scaling workers (Phase 5.2)
- Cross-domain learning (Phase 6.2)
- Autonomous skill creation (Phase 6.3)

### V1 Success Criteria
1. A PR triggers fleet review and posts a GitHub Check — zero human involvement
2. CEO agent runs daily, creates tickets from real signals
3. A Slack command flows through CEO → PM → Dev → PR in under 30 minutes
4. Total cost for a day of background operation is under $25
5. Every agent action has a complete audit trail in the ticket trace log

---

## APPENDIX: INDUSTRY DATA

- **Stripe Minions**: 1,000+ agent-authored PRs merged per week (source: industry reports)
- **Ramp**: 57% of all merged PRs are agent-authored (source: Ramp engineering blog)
- **Cursor experiment**: ~1,000 commits/hour with hierarchical multi-agent system building a web browser (source: [Cursor blog](https://cursor.com/blog/self-driving-codebases))
- **Claude Code adoption**: 99.9th percentile autonomous turn duration nearly doubled from <25 min to >45 min between Oct 2025 and Jan 2026 (source: [Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices))
- **Background agent infrastructure**: Three pillars — isolated compute, event routing, governance (source: [background-agents.com](https://background-agents.com), [Ona](https://ona.com/stories/ai-agents-need-infrastructure))
