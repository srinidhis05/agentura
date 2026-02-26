# Agentura — Architecture Decision Records

> **Purpose**: Preserve key architecture decisions to guide contributors and prevent re-litigation.
> **Format**: `ADR-NNN: Chose X Over Y Because Z`

---

## ADR-001: Pydantic AI as Execution Engine

**Chose**: Pydantic AI
**Over**: Pi.dev, building custom LLM execution layer
**Why**: Type-safe structured outputs, native MCP support, mature Python ecosystem. Pydantic AI is the execution engine underneath the skill runner — the platform handles orchestration, routing, and learning on top. Pi.dev (minimal terminal coding harness) was evaluated but targets a different use case — it's a developer coding agent with "primitives, not features" philosophy, not an embeddable execution engine for a platform. Agentura needs a library it can call programmatically, not a terminal tool.
**Constraint**: No unproven agentic frameworks in production.

---

## ADR-002: Custom Communication Gateway Over Embedded Messaging

**Chose**: Custom gateway using official vendor SDKs (Slack Bolt, Meta WhatsApp)
**Over**: Embedding communication into the agent framework
**Why**: Full control over multi-channel routing, trigger system (cron, alerts, commands), and security boundaries.
**Constraint**: All external integrations use official vendor SDKs (not third-party wrappers).

---

## ADR-003: OpenRouter as Model Gateway

**Chose**: OpenRouter as unified model gateway
**Over**: Direct Anthropic/OpenAI API calls
**Why**:
- Single API for 200+ models with automatic fallback chains (claude-sonnet → claude-haiku → gpt-4o-mini)
- Cost optimization (Haiku for routing, Sonnet for execution)
- Unified billing/monitoring across providers
- Easy to add new models (Gemini, Llama, custom)

**Constraint**: Requires OPENROUTER_API_KEY. Falls back to direct Pydantic AI when not set. Must track cost per skill execution with budget alerts.

---

## ADR-004: Config Loader Handles Simplified YAML Format

**Chose**: `_normalize_config()` handles both full and shorthand YAML
**Over**: Requiring verbose SkillConfig-compatible format everywhere
**Why**: Onboarding configs use simpler format (`domain: "finance"` vs nested object). Normalization layer means one parser handles both. Reduces friction for new skill authors.
**Constraint**: Both formats MUST produce identical SkillConfig objects.

---

## ADR-005: Routing Is LLM-Based (Skill), Not Python Code

**Chose**: Domain classification and routing via skills (SKILL.md + config triggers) executed by Pydantic AI
**Over**: Python router classes with if-else/pattern matching
**Why**: Config declares triggers declaratively — no code needed. Platform classifier uses a fast model (Haiku) that returns domain name. Python code for routing contradicts "everything is a skill" principle.
**Constraint**: Python/Pydantic AI is ONLY the execution engine. ALL routing, domain logic, business rules live in skills + config.

---

## ADR-006: MCP for Structured Data, Skills for Knowledge, RAG for Unstructured

**Chose**: Four-layer information stack: Weights → Skills (context injection) → MCP (precise queries) → RAG (similarity search)
**Over**: RAG-first approach for all data access
**Why**:
- Structured data in databases → MCP (deterministic SQL queries)
- Domain knowledge that fits in context → skill prompt injection
- RAG only when unstructured knowledge exceeds context window
- MCP is deterministic, RAG is probabilistic — use the right tool

**Constraint**: Database data uses MCP (SQL). In-context knowledge uses skills. RAG only for unstructured docs exceeding context.

---

## ADR-007: CLI Follows Verb-Resource Pattern

**Chose**: `agentura <verb> <resource> [name] [flags]` (verb-resource pattern)
**Over**: Flat commands (`agentura list-skills`, `agentura show-execution`)
**Why**:
- Verbs reusable across resources: `get skills`, `get domains`, `get executions`
- Users learn verbs once, apply everywhere
- Supports local (`run`, `create`, `validate`, `test`) and gateway (`get`, `describe`, `logs`) operations
- `apply -f` enables declarative deployment (GitOps-compatible)

**Constraint**: Every new resource type MUST work with `get` and `describe`.

---

## ADR-008: PostgreSQL as Production Memory Store

**Chose**: PostgreSQL with domain + workspace columns
**Over**: JSON files on disk
**Why**: Domain isolation requires column-level filtering. JSON files can't enforce cross-domain boundaries. PostgreSQL supports concurrent access and ACID.
**Constraint**: JSON fallback must remain for local dev without DATABASE_URL.

---

## ADR-009: DomainScopedStore Wrapper Over Modifying MemoryStore Protocol

**Chose**: Composition wrapper (`DomainScopedStore`) around any MemoryStore
**Over**: Adding domain filtering to every MemoryStore implementation
**Why**: Backward compatible, single enforcement point, any backend gets isolation for free.
**Constraint**: All server endpoints must use domain-scoped access.

---

## ADR-010: JWT+JWKS for Gateway Auth

**Chose**: RS256 JWT validation with JWKS key rotation (1hr cache)
**Over**: Static API keys or session tokens
**Why**: Standard, supports key rotation, carries domain_scope + workspace_id claims. Dev mode auto-injects safe defaults.
**Constraint**: Requires JWKS_URL configured for production.

---

## ADR-011: MCP Registry Auto-Discovery

**Chose**: Auto-discover MCP servers from skill config files + environment variables
**Over**: Manual registry configuration file
**Why**: Zero-config for local dev. Skill configs already declare which MCP tools they need. Registry merges all declarations.
**Constraint**: Well-known servers can also be registered via `MCP_*_URL` env vars.

---

## ADR-012: Task Prompts (No Code Execution) Over Tool Instructions

**Chose**: Skills produce text/JSON only — no shell commands, no code execution
**Over**: Skills that can execute shell commands or call APIs directly
**Why**: Allowing shell access from skill definitions creates an unacceptable attack surface. Task-only output is categorically safer. Real-world actions go through MCP tools via a separate boundary.
**Constraint**: Skills REASON (safe text). MCP tools ACT (separate security boundary). Never mix execution into skills.

---

## ADR-013: Declarative Single-Shot Over Imperative ReAct Loop

**Chose**: Declarative single-shot LLM call (system_prompt + input → structured output) via Pydantic AI
**Over**: Imperative ReAct loop (reason → act → observe → repeat)
**Why**:
- Declarative = bounded text transformation (worst case: wrong JSON)
- Imperative = Turing-complete execution surface (unbounded risk)
- Halting guarantee: single LLM call always terminates
- The "agent" intelligence is in the **learning loop** (corrections → tests → reflexion), not in execution-time tool loops

**Constraint**: Pydantic AI Agent has zero tool registrations. Skills produce text only. Actions go through MCP layer (separate security boundary).

---

## Future / Planned

Decisions that have been made architecturally but are not yet implemented. These represent the intended direction — contributions welcome.

---

### ADR-014: Multi-Language Skill Handlers (TypeScript, Python, Go)

**Chose**: Support TypeScript/Python/Go skill handlers via common SDK
**Over**: Single language only
**Why**: Different teams have different strengths. Platform provides language-agnostic interface via `agentura.config.yaml`. All handlers implement the same `SkillContext → SkillResult` interface.
**Status**: Python handler works. TypeScript and Go handlers are template stubs only.
**Constraint**: All handlers MUST implement the same interface regardless of language.

---

### ADR-015: Three-Tier Observability (Platform → Domain → Skill)

**Chose**: Hierarchical monitoring with Prometheus + Grafana
**Over**: Flat per-skill metrics
**Why**:
- Platform level: Total executions, success rate, cost (leadership view)
- Domain level: Per-domain metrics (cross-domain comparison)
- Skill level: Detailed latency, cost, satisfaction (debugging)

**Status**: Gateway has basic Prometheus metrics (request count, duration, errors, in-flight). The full three-tier hierarchy (platform → domain → skill) is not yet built.
**Constraint**: All alerts MUST include runbook links.

---

### ADR-016: Role-Based Skill Isolation

**Chose**: Domain → Role → Skill hierarchy with RBAC enforcement
**Over**: Single agent per domain with all skills loaded
**Why**:
- Context bloat: Loading all skills consumed 40K+ tokens
- Role confusion: Same agent handled both batch and interactive operations
- Deployment mismatch: CronJob vs interactive need different lifecycles
- Least privilege: Each role sees only the skills and resources it needs

**Status**: Skills declare a `role` field in SKILL.md. Runtime enforcement of `blocked_resources` is not yet implemented.
**Constraint**: Skills MUST declare `role` field. Platform MUST enforce `blocked_resources` at runtime.

---

### ADR-017: Canary Deployments with Auto-Rollback

**Chose**: 10% canary → monitor success rate → auto-rollback on degradation
**Over**: Blue-green or all-at-once deployments
**Why**: LLM outputs are non-deterministic — a version may pass tests but fail in production. Gradual rollout limits blast radius. Auto-rollback prevents manual incident response.
**Status**: A `deploy_status` field exists (active/canary/shadow/disabled) but no canary logic is implemented.
**Constraint**: Rollback triggered if canary success rate < 95% of previous version.

---

### ADR-018: Firecracker VMs for Skill Sandboxing

**Chose**: Firecracker microVMs for skill execution isolation
**Over**: Docker containers or process isolation
**Why**:
- Stronger security boundary (kernel-level isolation)
- Fast startup (< 125ms, comparable to containers)
- Battle-tested at scale (AWS Lambda uses Firecracker)
- Prevents skills from accessing other tenants' data

**Status**: Not implemented. Skills currently run as direct Pydantic AI calls in the executor process.
**Constraint**: Each skill execution gets an isolated VM with CPU/memory caps from `agentura.config.yaml`.

---

### ADR-019: MCP Gateway for Tool Call Policy Enforcement

**Chose**: Dedicated MCP gateway layer between executor and MCP tool servers
**Over**: Building admission logic directly in the Go gateway
**Why**:
- Separates concerns: routing gateway handles auth/routing, MCP gateway handles tool call policy
- Scans for PII, secrets, and prompt injection before tool calls reach external systems
- Configurable mode: block or warn
- Fail-open policy: scanning bug should not block all MCP calls
- Runs independently — zero coupling to the routing gateway

**Status**: Planned. The architecture supports this as a future integration point.
**Constraint**: All MCP tool calls should pass through the MCP gateway before execution.

---

## When to Add New Decisions

- **Architecture choice** → ADR-NNN
- **Technology selection** → ADR-NNN
- **Security/compliance** → ADR-NNN
- **Developer workflow** → ADR-NNN

Keep decisions concise. Constraints should be binary with reasoning.
