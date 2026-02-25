# Agentura Architecture Principles

> **Purpose**: Core design principles that guide Agentura's architecture. Every new feature should be checked against these.

---

## The Core Insight

In large distributed systems, **choreography beats orchestration**. Instead of one central brain, you build many small controllers that each pursue a simple goal. A shared API provides the state they coordinate through. Reconciliation loops make each controller robust to failures.

Agentura applies this to AI skills: instead of one monolithic agent per department, you deploy many small skills that each do one thing well. A shared gateway provides the routing and state they coordinate through. The correction→test→reflexion loop makes each skill improve over time.

---

## Principle 1: Declarative Configuration

Every skill is a Markdown manifest (SKILL.md) + config (agentura.config.yaml):

| Concept | Agentura |
|---------|----------|
| Identity (name, namespace, labels) | SKILL.md frontmatter (name, domain, role, trigger) |
| Desired behavior | SKILL.md body (task description, output format, guardrails) |
| Runtime state | `.agentura/` knowledge layer (episodic memory, accept rate) |
| Deployment config | `agentura.config.yaml` (routing, guardrails, tools, observability) |

**Principle**: If a business analyst can't create it, the abstraction is wrong. Skills are Markdown, not Python.

---

## Principle 2: Single Gateway

Every interaction goes through the Go gateway. No component touches the data store directly. The gateway provides auth, routing, and rate limiting. An MCP gateway layer (planned) will add policy enforcement for tool calls.

```
Client (CLI / Dashboard / Slack / WhatsApp)
  → Go Gateway (auth, routing, rate limiting)
    → Python Executor (skill loading, Pydantic AI execution)
      → [MCP Gateway] → MCP Tools (databases, Slack, Notion via MCP protocol)
```

The MCP gateway sits between the executor and MCP tool servers. It intercepts tool calls and applies policy (PII redaction, secrets scanning, injection prevention) before they reach external systems. This is planned as a future integration point.

**Request pipeline**:

| Layer | Purpose | Status |
|-------|---------|--------|
| Authentication (who are you?) | API key / OAuth | Designed |
| Authorization (can you do this?) | Domain RBAC (role-based skill access) | Designed |
| MCP policy enforcement | PII redaction, secrets/injection scanning | Planned |
| State write | `.agentura/` knowledge layer | Built |

---

## Principle 3: Level-Triggered Reconciliation (The Correction Loop)

Controllers compare desired state vs actual state, correct gaps, repeat. Missed events don't matter because controllers always look at current state.

The correction→test→reflexion loop is Agentura's reconciliation controller:

```
Desired state: Skill produces correct output (validated by tests + user acceptance)
Actual state:  Skill produced wrong output (user correction submitted)
Reconciliation:
  1. Correction stored → episodic memory updated
  2. Test auto-generated → test suite grows
  3. Reflexion entry created → skill learns the rule
  4. Next execution applies reflexion → output improves
  5. Accept rate converges toward 100%
```

**Level-triggered property**: If the correction event is lost (system crash), the skill's accept rate stays low, the reconciler (human reviewer) notices, and the correction is re-submitted. The loop is self-healing.

### Gap: Continuous Health Controller
Need skill health probes:
- Accept rate dropping below threshold → alert
- Cost exceeding budget → throttle/pause
- Latency spike → auto-scale or fallback model

---

## Principle 4: Namespace Isolation (Domain = Namespace)

Domains partition the control plane. Each domain has its own skills, roles, RBAC, and resource quotas.

| Concept | Agentura |
|---------|----------|
| Namespace | Domain (dev/, finance/, hr/, productivity/) |
| Pod | Skill (individual execution unit) |
| Deployment | SKILL.md + agentura.config.yaml |
| Service | Trigger patterns (command, cron, alert, always) |
| Network policy | Routing rules (classifier → domain → skill) |
| Resource quota | cost_budget, rate_limits per domain |
| RBAC | Role hierarchy: manager → specialist → field |

**Isolation enforced at runtime**:
- Manager skills never load field resources (runbooks)
- Field skills never compute batch scores
- Each skill execution gets isolated VM (ADR-018, planned)
- MCP tools scoped per skill in agentura.config.yaml

### Gap: Cross-Domain Policy
Need additive policies:
- Default: skills cannot call skills in other domains
- Explicit: `routing.when.domain: finance → then.forward_to: hr/triage` in config

---

## Principle 5: Policy Enforcement (Admission Control)

Admission controllers intercept tool calls before they reach external systems. Policy is config, not code.

**MCP Gateway (planned)**:
An MCP gateway layer will sit between the executor and MCP tool servers, providing:
- PII scanning and redaction
- Secrets detection (API keys, tokens, credentials in tool call payloads)
- Prompt injection prevention
- Configurable mode: `block` or `warn`
- Fail-open policy (scanning bug should not block all MCP calls)

**Skill deployment admission (planned)**:
Pre-deploy validation before a skill goes live:
- Does this skill have tests? (reject if no tests)
- Does the cost budget exceed domain limits?
- Are the MCP tools approved for this domain?
- Is the model allowed for this role?

---

## Principle 6: Uniform Object Model

Every skill has the same structure. Every tool can operate generically on any skill.

```
skills/{domain}/{skill-name}/
  SKILL.md                   # metadata (frontmatter) + behavior (body)
  agentura.config.yaml       # deployment config
  code/handler.{py,ts,go}    # execution handler
  tests/                     # quality + regression tests
  fixtures/                  # sample inputs
```

**Uniform interface (ADR-014)**: Every handler implements `SkillContext → SkillResult`, regardless of language (Python, TypeScript, Go).

---

## Principle 7: Extensibility (New Domain = New Folder)

New domain = new folder + SKILL.md + config. No code changes to the platform:

```bash
agentura create skill hr/resume-screen --role specialist --lang python
# Creates: skills/hr/resume-screen/SKILL.md, agentura.config.yaml, tests/, fixtures/
# Platform automatically discovers and routes to it
```

**Operator pattern**: Each domain can have a manager skill that acts as the domain's "operator" — it understands the domain's resources and routes to specialist skills:
- `platform/classifier` → routes to domains
- `hr/triage` → routes to hr/resume-screen, hr/interview-questions, hr/leave-policy
- `finance/triage` → routes to finance/expense-analyzer, finance/invoice-reviewer

---

## Principle 8: State Store

```
.agentura/
  episodic_memory.json    # Execution history
  corrections.json        # User corrections
  reflexion_entries.json  # Learned rules (derived from corrections)
```

**Access pattern**: Only the Python executor and CLI read/write `.agentura/`. The Go gateway and dashboard access it through the API.

### Gap: Persistent Store
Currently JSON files. Production needs PostgreSQL (ADR-008) with:
- ACID guarantees for concurrent writes
- Rich querying for skill discovery
- Versioning/rollback for skill deployments
- Watch/event stream for real-time updates

---

## Principle 9: CLI Design

```
agentura <verb> <resource> [name] [flags]
```

Verbs are reusable across all resource types. Supports both declarative (`apply`) and imperative (`create`/`run`).

**Built (local operations)**:
```bash
agentura list                           # List all skills
agentura create skill hr/new-skill      # Scaffold skill
agentura validate hr/interview-questions # Validate structure
agentura run hr/interview-questions     # Execute locally
agentura run hr/interview-questions --dry-run # Validate without calling model
agentura correct hr/interview-questions # Submit correction → auto-gen tests
agentura test hr/interview-questions    # Run tests
```

**Needed (gateway operations)**:
```bash
agentura get skills                     # List from gateway
agentura get skills -d hr               # Filter by domain
agentura get executions                 # List execution history
agentura describe skill hr/interview-questions # Full detail view
agentura logs EXEC-20260218120000       # Reasoning trace
agentura apply -f skills/hr/            # Deploy domain to gateway
agentura status                         # Platform health
agentura memory list                    # Show memory entries
agentura memory search "stuck payout"   # Search across memory
```

---

## Principle 10: Organizational Memory

Organizations need memory at multiple levels. Agentura provides a 4-level hierarchy:

| Level | Content | Scope |
|-------|---------|-------|
| **Firm** | Company policies, regulatory rules, escalation paths | All domains |
| **Domain** | DOMAIN.md, domain decisions, domain guardrails | Single domain |
| **Skill** | SKILL.md, reflexion entries, test results, correction history | Single skill |
| **Session** | Conversation context, intermediate reasoning | Single execution |

### Connected Sources (the data plane)

| Source | Access Via | Example Use |
|--------|-----------|-------------|
| Databases | MCP server | Order queries, rule simulation |
| Slack | MCP server | Alerts, notifications |
| Notion | MCP server | Runbooks, process docs |
| Google Sheets | MCP server | Manual trackers |
| GitHub | MCP server | PR review, code analysis |
| PostgreSQL | MCP server | Skill registry, execution logs |
| Vector DB | MCP server | Precedent matching |

**Key principle (ADR-006)**: MCP for structured data (exact SQL), Skills for knowledge (context injection), RAG only for unstructured docs exceeding context.

---

## Implementation Priority

### Phase 1: CLI Gateway Connection
1. `agentura status` — health check
2. `agentura get skills/executions/domains` — query gateway
3. `agentura describe skill/execution` — detailed views
4. `agentura logs <execution-id>` — reasoning traces
5. `agentura apply -f` — deploy skills to gateway

### Phase 2: Admission Control
1. Pre-deploy validation (tests exist, budget within limits, model approved)
2. MCP gateway integration for tool call policy enforcement
3. Shadow mode canary for batch skills

### Phase 3: Organizational Memory
1. `agentura memory` commands
2. Firm/domain/skill/session hierarchy in PostgreSQL
3. Memory search via vector embeddings

### Phase 4: Continuous Controllers (self-healing)
1. Skill health probes (accept rate, cost, latency monitoring)
2. Auto-rollback on degradation (ADR-017)
3. Shadow mode canary
4. Cost budget enforcement (throttle/pause/notify)
5. Event stream for real-time updates

---

## Verification Checklist

For every new feature, check against these principles:
- [ ] Is it declarative? (config, not code)
- [ ] Does it go through the gateway? (single entry point)
- [ ] Does it follow the reconciliation pattern? (desired vs actual, idempotent)
- [ ] Is it isolated by domain? (namespace-scoped)
- [ ] Is it policy-enforced? (admission control)
- [ ] Does it use the uniform object model? (SkillContext → SkillResult)
- [ ] Can it be extended without code changes? (new domain = new folder)
- [ ] Does it persist to the knowledge layer? (state store)
- [ ] Can it be operated via CLI AND dashboard? (both interfaces)
- [ ] Does it feed the memory hierarchy? (firm → domain → skill → session)
