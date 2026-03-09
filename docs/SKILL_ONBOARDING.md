# Skill Onboarding Guide

How to add a new skill to Agentura — from scaffolding to production execution.

---

## Quick Start (5 minutes)

```bash
# 1. Scaffold
agentura create skill support/ticket-responder --role agent

# 2. Edit the two files that matter
$EDITOR skills/support/ticket-responder/SKILL.md
$EDITOR skills/support/ticket-responder/agentura.config.yaml

# 3. Validate
agentura validate support/ticket-responder

# 4. Test locally (specialist skills only)
agentura run support/ticket-responder --input fixtures/sample_input.json

# 5. Deploy to K8s
kubectl cp skills/support/ticket-responder \
  $(kubectl get pod -n agentura -l app=executor -o name):/skills/support/ticket-responder
```

**Zero Python/Go/TS code changes.** A skill is two files: a prompt (SKILL.md) and a config (agentura.config.yaml).

---

## What Gets Created

```
skills/
  {domain}/
    DOMAIN.md                    # Domain context (auto-loaded into every skill in this domain)
    DECISIONS.md                 # Domain-specific decisions (optional)
    GUARDRAILS.md                # Domain-specific anti-patterns (optional)
    {skill-name}/
      SKILL.md                   # REQUIRED — prompt + metadata frontmatter
      agentura.config.yaml       # REQUIRED — executor, budget, MCP tools, verify criteria
      code/
        handler.py               # Optional — custom Python handler (SkillContext → SkillResult)
      tests/
        test_deepeval.py          # Test template (deepeval framework)
        test_promptfoo.yaml       # Test template (promptfoo framework)
      fixtures/
        sample_input.json         # Sample input for local testing
```

### The Two Files That Matter

**SKILL.md** — The prompt. This is what the LLM sees.

```markdown
---
name: ticket-responder
role: agent
domain: support
trigger: api
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.50"
timeout: "120s"
---

# Ticket Responder

## Task
You respond to support tickets by...

## Input
You receive:
- `ticket_id` — ...
- `message` — ...

## Execution Protocol
### Phase 1: ...

## Output Format
```json
{ ... }
```

## Guardrails
- NEVER offer follow-up options — this is a single-shot execution.
- NEVER fabricate data...
```

**agentura.config.yaml** — The runtime config. This is what the executor reads.

```yaml
domain:
  name: support
  description: "Customer support automation"
  owner: "support-team"

skills:
  - name: ticket-responder
    path: ticket-responder
    role: agent
    model: anthropic/claude-sonnet-4-5-20250929
    cost_budget: "$0.50"
    triggers:
      - type: api
      - type: slack
        pattern: "respond to ticket {id}"

agent:
  executor: ptc          # or claude-code
  max_iterations: 20
  timeout: 120

guardrails:
  budget:
    max_per_execution: "$0.50"
    alert_at: "$0.35"

feedback:
  capture_corrections: true
  capture_failure_cases: true

verify:
  enabled: true
  criteria:
    - "Response addresses the customer's actual question"
    - "No PII exposed in the response"

mcp_tools:                   # Only for agent-role skills
  - server: zendesk
    tools: ["*"]

display:
  title: "Ticket Responder"
  subtitle: "Auto-respond to support tickets"
  avatar: "TR"
  color: "#f59e0b"
  tags: ["Agent", "Support"]
```

---

## Choosing an Executor

| Executor | Config Value | Use When | Image Size | Resource Limit |
|----------|-------------|----------|------------|----------------|
| **PTC** | `executor: ptc` | MCP-only skills (API calls, data fetching, Slack posting) | ~200MB | 512Mi / 1 CPU |
| **Claude Code** | `executor: claude-code` | File I/O, code generation, git operations | ~800MB | 2Gi / 2 CPU |
| *(none)* | omit `agent:` section | Specialist/manager roles (single-turn, no sandbox) | N/A | In-process |

**Rule of thumb**: If your skill calls external APIs via MCP tools and doesn't write files, use `ptc`. If it generates code, reads/writes files, or runs tests, use `claude-code`.

---

## The Full Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  1. CREATE                                               │
│     agentura create skill {domain}/{name}                │
│     → Scaffolds SKILL.md + config + tests + fixtures     │
│                                                          │
│  2. AUTHOR                                               │
│     Edit SKILL.md (prompt) + config.yaml (runtime)       │
│     → This is where you spend 90% of your time           │
│                                                          │
│  3. VALIDATE                                             │
│     agentura validate {domain}/{name}                    │
│     → Checks: syntax, role/executor match, GR-018/019    │
│                                                          │
│  4. TEST LOCALLY                                         │
│     agentura run {domain}/{name} --input fixture.json    │
│     → Specialist: runs in-process                        │
│     → Agent: --dry-run only (no local executor)          │
│                                                          │
│  5. DEPLOY                                               │
│     kubectl cp skills/{domain}/{name} executor-pod:/...  │
│     → No Docker rebuild needed (GR-001)                  │
│     → Filesystem discovery — no registration step        │
│                                                          │
│  6. EXECUTE                                              │
│     POST /api/v1/skills/{domain}/{name}/execute          │
│     → Or: trigger via pipeline, Slack command, cron      │
│     → Agent skills: worker pod spins up, executes, dies  │
│                                                          │
│  7. ITERATE                                              │
│     POST /api/v1/skills/{domain}/{name}/correct          │
│     → Correction → reflexion → auto-test generation      │
│     → Reflexions injected into future executions          │
└─────────────────────────────────────────────────────────┘
```

---

## Context Injection (Automatic)

Every skill execution automatically gets 5 layers of context injected:

| Layer | Source | Purpose |
|-------|--------|---------|
| **Workspace** | `skills/WORKSPACE.md` | Org-wide context (shared across all domains) |
| **Domain** | `skills/{domain}/DOMAIN.md` | Domain-specific terminology and conventions |
| **Reflexion** | PostgreSQL / mem0 / JSON | Learned rules from past corrections (Bayesian scored) |
| **Skill** | `SKILL.md` body | The actual prompt |
| **Input** | API request / fixture | The user's input data |

You don't wire this — it happens automatically via `load_skill_md()`.

---

## Adding a Skill to a Pipeline

Pipelines are YAML files in `pipelines/`. To add your skill to an existing pipeline:

```yaml
# pipelines/github-pr-parallel.yaml
phases:
  - name: analyze
    type: parallel
    steps:
      - skill: dev/pr-code-reviewer    # ← add one line
        agent_id: reviewer
        required: true
```

To create a new pipeline:

```yaml
# pipelines/support-triage.yaml
name: support-triage
description: "Auto-triage and respond to support tickets"
trigger:
  type: webhook
  source: zendesk

phases:
  - name: classify
    type: sequential
    steps:
      - skill: support/triage
        agent_id: classifier

  - name: respond
    type: sequential
    fan_in_from: classify
    steps:
      - skill: support/ticket-responder
        agent_id: responder
```

---

## Adding Slack Commands

Edit `gateway/config/config.yaml` under the relevant Slack app's `commands:` section:

```yaml
commands:
  - pattern: "respond to ticket {id}"
    skill: "ticket-responder"
    extract: {"ticket_id": "{id}"}
    description: "Auto-respond to a support ticket"
```

Unmatched messages auto-route to `{domain}/triage` via DEC-079.

---

## Common Mistakes (from GUARDRAILS.md)

| Mistake | What Happens | How to Avoid |
|---------|-------------|--------------|
| `mcp_tools: ["zendesk"]` | Zero tools bound, no error | Use `[{server: "zendesk", tools: ["*"]}]` (GR-018) |
| `tools: ["*"]` not handled | All tools filtered out | Executor handles this — just use `["*"]` in config (GR-021) |
| Missing `input_data` wrapper | Skill gets `{}`, no error | Always `{"input_data": {...}}` in API calls (GR-009) |
| Skill offers "Would you like me to..." | User clicks, bot can't continue | Add "NEVER offer follow-up options" guardrail (GR-019) |
| Editing skills locally, forgetting `kubectl cp` | Pod uses stale config | Always sync after edit (GR-006) |
| Custom Dockerfile per skill | Violates DEC-043, wastes time | One image, many skills via config (GR-001) |
| `max_tokens` too low for structured output | Tool calls silently truncated | Use SandboxConfig.max_tokens >= 8192 (GR-008) |

---

## Validation Checklist

Run `agentura validate {domain}/{name}` to check these automatically:

- [ ] SKILL.md exists with valid frontmatter
- [ ] agentura.config.yaml exists with valid YAML
- [ ] `mcp_tools` uses dict format (not string list)
- [ ] Agent-role skills have `agent:` section with `executor:`
- [ ] "NEVER offer follow-up options" in guardrails
- [ ] Prompt length > 50 characters
- [ ] Skill name is not "unnamed-skill"

### Manual Checks (Not Yet Automated)

- [ ] Output format is valid JSON schema (parseable by downstream consumers)
- [ ] Cost budget is realistic for the model + max_iterations
- [ ] MCP server URLs are configured (`MCP_{SERVER}_URL` env vars)
- [ ] Fixtures cover happy path + error path
- [ ] Skill is added to domain's agent.yaml if part of an agency

---

## Estimated Time by Skill Type

| Skill Type | Example | Author Time | Iteration Cycles |
|------------|---------|-------------|------------------|
| **Specialist** (single-turn) | Triage router, reporter | 30 min | 1-2 (local testing) |
| **Agent + MCP** (multi-turn, API calls) | Meeting update, heartbeat | 1-2 hours | 3-5 (remote testing) |
| **Agent + Claude Code** (code generation) | App builder, test runner | 2-4 hours | 5-10 (remote testing) |
| **Pipeline** (multi-agent workflow) | PR review fleet | 30 min (per agent already exists) | 2-3 (integration) |

The bottleneck for agent skills is iteration — no local agent testing means every cycle costs money and requires `kubectl cp`.

---

## What's Coming

| Improvement | Impact | Status |
|-------------|--------|--------|
| `agentura deploy` command | Eliminates GR-006 (forgot kubectl cp) | Planned |
| Fail-fast validation on server boot | Catches broken configs before first LLM call | Planned |
| Local agent mock executor | Test agent skills without K8s cluster | Planned |
| Strict `input_data` validation | Catches GR-009 before LLM spend | Planned |
| `agentura test` command | Run fixtures → execute → assert output schema | Planned |
