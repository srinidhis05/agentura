# Aspora Architecture Principles — Building K8s for AI Agents

> **Purpose**: Map Kubernetes design principles to Aspora. Every future decision gets checked against this.
> **Date**: 2026-02-20
> **Source**: K8s Borg/Omega papers, Aspora DECISIONS.md (DEC-001 to DEC-023), runlayer MCP gateway

---

## The Core Insight

Google learned from 10 years of Borg: **choreography beats orchestration in distributed systems.** Instead of one central brain, you build many small controllers that each pursue a simple goal. A shared API server provides the state they coordinate through. Reconciliation loops make each controller robust to failures. CRDs let anyone add new controllers for new domains.

Aspora applies this to AI agents: instead of one monolithic agent per department, you deploy many small skills that each do one thing well. A shared gateway provides the routing and state they coordinate through. The correction→test→reflexion loop makes each skill improve over failures. New domains (HR, Engineering, Treasury) plug in as namespaces with config, not code.

---

## Principle 1: Declarative Configuration (SKILL.md + YAML = Manifest)

### K8s
Every workload is a YAML manifest with `metadata/spec/status`. You declare WHAT you want, not HOW to achieve it. `kubectl apply` computes the diff and converges.

### Aspora — BUILT (DEC-023)
Every skill is a Markdown manifest (SKILL.md) + config (aspora.config.yaml):

| K8s Concept | Aspora Equivalent |
|-------------|-------------------|
| `metadata` (name, namespace, labels) | SKILL.md frontmatter (name, domain, role, trigger) |
| `spec` (desired state) | SKILL.md body (task description, output format, guardrails) |
| `status` (actual state) | `.aspora/` knowledge layer (episodic memory, accept rate) |
| `aspora.config.yaml` | Deployment + Service + NetworkPolicy combined |

**Constraint (from DEC-023)**: If a business analyst can't create it, the abstraction is wrong. Skills are Markdown, not Python.

### Gap: `aspora apply`
The CLI can `run` and `validate` locally but cannot declaratively deploy to the gateway. Need:
```
aspora apply -f skills/ecm/order-details/    # Deploy skill to gateway
aspora apply -f skills/ecm/                   # Deploy entire domain
```

---

## Principle 2: API Server as Single Gateway

### K8s
Every interaction goes through kube-apiserver. No component touches etcd directly. The API server provides auth, admission control, validation, versioning, and watch.

### Aspora — BUILT
Go gateway is the single entry point. All traffic flows through `/api/v1/`:

```
Client (CLI/Dashboard/Slack/WhatsApp)
  → Go Gateway (auth, routing, rate limiting)
    → Python Executor (skill loading, Pydantic AI execution)
      → MCP Tools (Redshift, Slack, Notion via MCP protocol)
```

**Auth pipeline** (maps to K8s request pipeline):

| K8s Layer | Aspora Layer | Status |
|-----------|-------------|--------|
| Authentication (who are you?) | API key / OAuth | Designed |
| Authorization (can you do this?) | Domain RBAC (role-based skill access) | Designed (DEC-011) |
| Mutating admission | mcp-guard PII redaction | Built (runlayer) |
| Validating admission | mcp-guard injection/secrets scanning | Built (runlayer) |
| etcd write | `.aspora/` knowledge layer write | Built |

---

## Principle 3: Level-Triggered Reconciliation (The Correction Loop)

### K8s
Controllers compare desired state (spec) vs actual state (status), correct gaps, repeat. Level-triggered, not edge-triggered — missed events don't matter because controllers always look at current state.

### Aspora — BUILT (DEC-006)
The correction→test→reflexion loop IS a reconciliation controller:

```
Desired state: Skill produces correct output (validated by tests + user acceptance)
Actual state:  Skill produced wrong output (user correction submitted)
Reconciliation:
  1. Correction stored → episodic memory updated
  2. DeepEval + Promptfoo test auto-generated → test suite grows
  3. Reflexion entry created → skill learns the rule
  4. Next execution applies reflexion → output improves
  5. Accept rate converges toward 100%
```

**Level-triggered property**: If the correction event is lost (system crash mid-correction), the skill's accept rate stays low, the reconciler (human reviewer) notices, and the correction is re-submitted. The loop is self-healing.

### Gap: Continuous Health Controller
K8s has liveness/readiness probes. Aspora needs skill health probes:
- Accept rate dropping below threshold → alert
- Cost exceeding budget → throttle/pause
- Latency spike → auto-scale or fallback model

---

## Principle 4: Namespace Isolation (Domain = Namespace)

### K8s
Namespaces partition the control plane. Each namespace has its own pods, services, RBAC. Soft isolation by default, hard isolation with NetworkPolicies.

### Aspora — BUILT (DEC-011, DEC-017)

| K8s | Aspora |
|-----|--------|
| Namespace | Domain (ecm/, frm/, wealth/, hr/) |
| Pod | Skill (individual execution unit) |
| Deployment | SKILL.md + aspora.config.yaml (desired state) |
| Service | Trigger patterns (command, cron, alert, always) |
| NetworkPolicy | Routing rules (classifier → domain → skill) |
| ResourceQuota | cost_budget, rate_limits per domain |
| RBAC | Role hierarchy: manager → specialist → field |

**Isolation enforced at runtime (DEC-011)**:
- Manager skills NEVER load field resources (runbooks)
- Field skills NEVER compute batch scores
- Each skill execution gets isolated Firecracker VM (DEC-009)
- MCP tools scoped per skill in aspora.config.yaml

### Gap: Cross-Domain Policy
K8s NetworkPolicies are additive (deny-all + allow specific). Aspora needs:
- Default: skills cannot call skills in other domains
- Explicit: `routing.when.domain: ecm → then.forward_to: frm/escalation` in config

---

## Principle 5: Policy Enforcement (mcp-guard = Admission Controller)

### K8s
Admission controllers intercept every API write. OPA/Gatekeeper lets users define policy as config, not code. PSP failure taught: match complexity to users (3 fixed tiers, not unbounded API).

### Aspora — PARTIALLY BUILT

**Built (runlayer/mcp-guard)**:
- PII scanning (8 categories, Luhn-validated credit cards, IBAN, Aadhaar)
- Secrets detection (15+ credential types: AWS, GitHub, Slack, JWT, GCP, Azure, OpenAI, Anthropic)
- Injection prevention (10+ vectors: role hijacking, invisible text, cross-tool exfiltration)
- Configurable mode: `block` (403) or `warn` (200 + log)
- Fail-open policy (scanning bug ≠ block all MCP)

**Built (runlayer/agent — Rust daemon)**:
- Shadow MCP server detection (scanning processes + config files)
- Config compliance monitoring (watches Cursor, Claude Desktop, VS Code, Windsurf configs)
- Allowlist enforcement (only approved MCP servers)
- Event reporting (batched, retried, structured JSON)

**Gap**: Skill deployment admission
Currently mcp-guard scans MCP tool calls at runtime. Need to also validate at deployment time:
- Does this skill have tests? (reject if no tests)
- Does the cost budget exceed domain limits?
- Are the MCP tools approved for this domain?
- Is the model allowed for this role? (Haiku for routing, Sonnet for execution)

---

## Principle 6: Uniform Object Model (metadata/spec/status)

### K8s
Every object has the same structure. Every tool can operate generically on any resource. `kubectl get` works the same for pods, services, CRDs.

### Aspora — BUILT
Every skill has the same structure:

```
skills/{domain}/{skill-name}/
  SKILL.md              # metadata (frontmatter) + spec (body)
  aspora.config.yaml    # deployment config (routing, guardrails, mcp, feedback)
  DECISIONS.md          # domain-level decisions
  GUARDRAILS.md         # domain-level anti-patterns
  code/handler.{py,ts,go}  # execution handler
  tests/                # DeepEval + Promptfoo tests
  fixtures/             # Sample inputs
```

**Uniform interface (DEC-005)**: Every handler implements `SkillContext → SkillResult`, regardless of language (Python, TypeScript, Go).

---

## Principle 7: Extensibility (New Domain = New Namespace)

### K8s
CRDs let you extend the API with custom resource types. Operators encode domain knowledge into controllers. kubectl works automatically with CRDs.

### Aspora — BUILT (DEC-004)
New domain = new folder + SKILL.md + config. No code changes to the platform:

```bash
aspora create skill hr/resume-screen --role specialist --lang python
# Creates: skills/hr/resume-screen/SKILL.md, aspora.config.yaml, tests/, fixtures/
# Platform automatically discovers and routes to it
```

**Operator pattern**: Each domain can have a manager skill that acts as the domain's "operator" — it understands the domain's resources and routes to specialist skills:
- `platform/classifier` → routes to domains (the kube-scheduler equivalent)
- `ecm/manager` → routes to ecm/order-details, ecm/triage-and-assign
- `frm/manager` → routes to frm/rule-simulation, frm/alert-review

---

## Principle 8: State Store (.aspora/ = etcd)

### K8s
etcd is the consistent state store. Only the API server reads/writes it. Watch API enables controllers. Optimistic concurrency prevents lost updates.

### Aspora — BUILT

```
.aspora/
  episodic_memory.json    # Execution history (etcd equivalent for runtime state)
  corrections.json        # User corrections (change requests)
  reflexion_entries.json  # Learned rules (derived state from corrections)
```

**Access pattern**: Only the Python executor and CLI read/write `.aspora/`. The Go gateway and dashboard access it through the API server (executor endpoints).

### Gap: Persistent Store
Currently JSON files. Production needs PostgreSQL (DEC-007) with:
- ACID guarantees for concurrent writes
- Rich querying for skill discovery
- Versioning/rollback for skill deployments
- Watch/event stream for real-time updates

---

## Principle 9: CLI Design (aspora = kubectl)

### K8s kubectl Pattern
```
kubectl <verb> <resource> [name] [flags]
```
Verbs are reusable across all resource types. Supports both declarative (`apply`) and imperative (`create`/`run`).

### Aspora CLI — BUILT + GAPS

**Built (local operations)**:
```bash
aspora list                           # List all skills
aspora create skill ecm/new-skill     # Scaffold skill
aspora validate ecm/order-details     # Validate structure
aspora run ecm/order-details          # Execute locally
aspora run ecm/order-details --dry-run # Validate without calling model
aspora correct ecm/order-details      # Submit correction → auto-gen tests
aspora test ecm/order-details         # Run DeepEval + Promptfoo
```

**Needed (gateway operations)**:
```bash
# Resource-verb pattern (kubectl style)
aspora get skills                     # List from gateway (not just local)
aspora get skills -d ecm              # Filter by domain (namespace)
aspora get executions                 # List execution history
aspora get executions --skill ecm/order-details
aspora get reflexions                 # List learned rules
aspora get domains                    # List domains with health

aspora describe skill ecm/order-details   # Full detail view
aspora describe execution EXEC-20260218   # Execution trace + corrections

aspora logs EXEC-20260218120000       # Reasoning trace for an execution

aspora apply -f skills/ecm/           # Deploy domain to gateway
aspora apply -f skills/               # Deploy everything

aspora status                         # Platform health (gateway + executor)

# Memory operations (Mem0-style)
aspora memory list                    # Show all memory entries
aspora memory list --level firm       # Firm-level memories
aspora memory list --level domain --domain ecm  # Domain memories
aspora memory search "UAE corridor"   # Search across memory hierarchy
```

---

## Principle 10: Organizational Memory (Mem0 → Aspora Knowledge Layer)

### The Gap No One Else Fills
Mem0 showed: organizations need memory at 4 levels. Currently platforms-ai has 6 orchestrators with zero shared memory between them.

### Aspora Memory Hierarchy

| Level | K8s Equivalent | Content | Scope |
|-------|---------------|---------|-------|
| **Firm** | Cluster-wide ConfigMap | Company policies, regulatory rules, escalation paths | All domains |
| **Domain** | Namespace-scoped ConfigMap | DOMAIN.md, domain DECISIONS.md, domain GUARDRAILS.md | Single domain |
| **Skill** | Pod annotation | SKILL.md, reflexion entries, test results, correction history | Single skill |
| **Session** | Ephemeral volume | Conversation context, intermediate reasoning, routed context | Single execution |

### Connected Sources (the data plane)

| Source | MCP Server | Used By |
|--------|-----------|---------|
| Redshift | `redshift` MCP | ECM (order queries), FRM (rule simulation) |
| Slack | `slack` MCP | Alerts, notifications, escalations |
| Notion | `notion` MCP | Runbooks, process docs |
| Metabase | `metabase` MCP | Analytics dashboards, report generation |
| Google Sheets | `gsheets` MCP | Capacity planning, manual trackers |
| GitHub | `github` MCP | PR review, code analysis |
| Redis | `redis` MCP | Hot cache, session state |
| PostgreSQL | `postgres` MCP | Skill registry, execution logs |
| ChromaDB | `chromadb` MCP | Vector search for precedent matching |

**Key principle (DEC-022)**: MCP for structured data (exact SQL), Skills for knowledge (context injection), RAG only for unstructured docs exceeding context.

---

## Implementation Priority

### Phase 1: CLI Gateway Connection (make `aspora` talk to the gateway)
1. `aspora status` — health check against gateway
2. `aspora get skills/executions/domains` — query gateway API
3. `aspora describe skill/execution` — detailed view from gateway
4. `aspora logs <execution-id>` — reasoning trace
5. `aspora apply -f` — deploy skill to gateway

### Phase 2: Admission Control (policy enforcement on deploy)
1. Pre-deploy validation (tests exist, budget within limits, model approved)
2. mcp-guard integration for skill content scanning
3. Shadow mode canary for batch skills (DEC-012)

### Phase 3: Organizational Memory (Mem0-style)
1. `aspora memory` commands for memory CRUD
2. Firm/domain/skill/session hierarchy in PostgreSQL
3. Cross-orchestrator memory sharing (the 6-orchestrator gap)
4. Memory search via pgvector (vector) + Neo4j (graph, DEC-016)

### Phase 4: Continuous Controllers (self-healing)
1. Skill health probes (accept rate, cost, latency monitoring)
2. Auto-rollback on degradation (DEC-010)
3. Shadow mode canary (DEC-012)
4. Cost budget enforcement (throttle/pause/notify)
5. Event stream / watch API for real-time updates

---

## Verification Checklist

For every new feature, check against these principles:
- [ ] Is it declarative? (config, not code)
- [ ] Does it go through the API server? (gateway, not direct)
- [ ] Does it follow the reconciliation pattern? (desired vs actual, idempotent)
- [ ] Is it isolated by domain? (namespace-scoped)
- [ ] Is it policy-enforced? (admission control)
- [ ] Does it use the uniform object model? (SkillContext → SkillResult)
- [ ] Can it be extended without code changes? (new domain = new folder)
- [ ] Does it persist to the knowledge layer? (state store)
- [ ] Can it be operated via CLI AND dashboard? (both interfaces)
- [ ] Does it feed the memory hierarchy? (firm → domain → skill → session)
