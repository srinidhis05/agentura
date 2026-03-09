# LinkedIn Post Draft

---

## Option A: CEO Narrative (Recommended)

**We just shipped a 4-agent parallel PR review pipeline. Here's what that means.**

Every time a pull request opens on our repo, four AI agents wake up simultaneously:

- A **Code Reviewer** scans the diff for blockers, warnings, and security issues — every finding cites file:line with a code snippet
- A **Test Runner** detects the language and framework, runs the test suite, and reports evidence-backed results
- An **SLT Validator** checks code against team standards and API contracts
- A **Doc Generator** classifies the change type and produces CHANGELOG entries, README patches, and docstring stubs

All four run in parallel. A fifth agent aggregates their outputs into a single PR comment. Total time: ~90 seconds. Total cost: ~$0.80.

No human reviewer needed for the first pass.

**But here's the part that matters more than the PR pipeline:**

Adding each of those agents required zero code changes. Zero Docker images. Zero infrastructure work.

Each agent is two files:
1. A `SKILL.md` — a structured prompt with phases, guardrails, and output format
2. An `agentura.config.yaml` — executor type, cost budget, MCP tool bindings

That's it. Drop them in a folder, they appear in the platform. Add one line to a pipeline YAML, they run in parallel.

We also shipped a **PM Heartbeat** that runs daily at 6 PM — it checks Granola for unprocessed meetings, ClickUp for overdue tasks, and posts a project status digest to Slack. Again: two files, no code.

**This is what I mean by "config-driven agent orchestration."**

The industry is converging on agent platforms. Paperclip.ing does org charts for agents. CrewAI and LangGraph let you code agent workflows in Python. OpenAI just showed Harness Engineering building custom tools for their agents.

Agentura takes a different bet: **the skill is the unit of work, and it's authored in markdown, not code.**

A SKILL.md is a structured prompt — task, execution phases, output schema, guardrails. An agentura.config.yaml specifies which executor runs it (lightweight PTC for API calls, full Claude Code for code generation), what MCP tools it can access, and what budget it has.

New domain? New SKILL.md + config. Not a new microservice.

We're open-sourcing the full platform — Go gateway, Python executor, pipeline engine, fleet sessions, persistent learning, K8s-native execution — because the moat isn't the orchestration layer. The moat is the skills your organization builds on top of it.

Stripe ships 1,000+ agent-authored PRs per week. Ramp's codebase is 57% agent-written. The question isn't whether AI agents will do software delivery — it's whether your agents will be duct-taped scripts or a governed, learning organization.

We're building the second one.

**Agentura**: github.com/srinidhis05/agentura

#AIAgents #BackgroundAgents #DevTools #OpenSource #SoftwareEngineering #AgentOrchestration

---

## Option B: Technical Deep-Dive

**Adding a new AI agent to our platform takes 2 files and 0 lines of code. Here's the architecture.**

[Use if audience is more technical / engineering leaders]

We run AI agents as a hierarchical organization on Kubernetes. CEO agent sets priorities. PM agent specs work. Dev agents build in parallel. Each agent is a "skill" — a markdown prompt + YAML config.

This week we shipped:

**PR Review Fleet (4 agents, parallel)**
```
GitHub PR opened
  → Code Reviewer (severity-tagged findings)
  → Test Runner (evidence-based, not fabricated)
  → SLT Validator (contract checking)
  → Doc Generator (CHANGELOG + README patches)
  → Reporter (aggregates → single PR comment)
```

**PM Heartbeat (daily, cron-triggered)**
```
6 PM daily
  → Check Granola (unprocessed meetings)
  → Check ClickUp (overdue tasks)
  → Post digest to Slack
  → Graceful degradation if any MCP server is down
```

The architecture:
- **Go gateway** handles webhooks, Slack, cron, routing
- **Python executor** loads skills, injects 5-layer context (workspace → domain → reflexions → prompt → input), dispatches to workers
- **PTC workers** (~200MB pods) for MCP-only skills
- **Claude Code workers** (~800MB pods) for code generation
- **Pipeline engine** runs parallel/sequential phases with fan-in
- **Fleet sessions** track per-agent cost, latency, and output

What makes this different from CrewAI/LangGraph/AutoGen:
1. **YAML, not Python** — new agent = SKILL.md + config, not a new class
2. **K8s-native** — each execution is an isolated pod, not a thread
3. **Persistent learning** — Bayesian-scored reflexions improve agents over time
4. **Cost governance** — per-agent budgets, per-execution tracking, cost dashboards

Open-sourcing the full stack. MIT license.

github.com/srinidhis05/agentura

---

## Option C: Short & Punchy

**4 AI agents review every PR we open. In parallel. In 90 seconds. For $0.80.**

Code review. Test execution. Standards validation. Documentation generation.

Each agent is a markdown file (the prompt) and a YAML file (the config). No code. No Docker images. Drop two files, they appear in the platform.

We also have a PM agent that runs daily — checks Granola for unprocessed meetings, ClickUp for overdue tasks, posts a digest to Slack. Cron-triggered, zero human involvement.

Open-sourcing the full platform: Go gateway, Python executor, pipeline engine, K8s-native isolation, persistent learning.

New agent = new skill. New skill = 2 files.

github.com/srinidhis05/agentura

#AIAgents #OpenSource #DevTools
