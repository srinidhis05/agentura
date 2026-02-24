# Agentura Platform — Architecture Decision Record

> **Purpose**: Preserve key decisions to prevent re-litigation and guide future work.
> **Format**: `DEC-NNN: Chose X Over Y Because Z (Constraint: C)`

---

## DEC-001: Pydantic AI Over OpenClaw for Agent Framework

**Chose**: Pydantic AI (ai.pydantic.dev)
**Over**: OpenClaw
**Why**: OpenClaw launched Jan 2026 (too new, unaudited). Security-conscious approach requires proven frameworks. Pydantic AI has type-safe structured outputs, MCP support, and mature Python ecosystem.
**Constraint**: NO unproven agentic frameworks in production.
**Date**: 2026-02-16

---

## DEC-002: Custom Communication Gateway Over OpenClaw Built-In

**Chose**: Custom gateway using official SDKs (Slack Bolt, Meta WhatsApp)
**Over**: OpenClaw's native communication layer
**Why**: Need full control over multi-channel routing, trigger system (cron, alerts, commands), and security. OpenClaw pattern (unified message handling) is good, but implementation must be ours.
**Constraint**: All external integrations use official vendor SDKs (NOT third-party wrappers).
**Date**: 2026-02-16

---

## DEC-003: OpenRouter Over Direct Anthropic/OpenAI API

**Chose**: OpenRouter as model gateway
**Over**: Direct Anthropic API or OpenAI API
**Why**:
- Auto-fallback across providers (if Claude down, use GPT-4o)
- Cost optimization (auto-select Haiku for routing, Sonnet for execution)
- Unified billing/monitoring across multiple LLM providers
- Future-proof (easy to add Gemini, Llama, custom models)

**Constraint**: Must track cost per skill with budget alerts.
**Date**: 2026-02-16

---

## DEC-004: Skill Marketplace Model Over Monolithic Application

**Chose**: Platform architecture where teams independently onboard skills
**Over**: Single application with all features built by core team
**Why**:
- Scales to 6+ domains (Wealth, Fraud, ECM, Retention, Support, Ops)
- Teams can build/test/deploy without blocking each other
- Marketplace model creates ecosystem (like Shopify apps)
- Developer SDK (CLI, multi-language) enables external contributions

**Constraint**: All skills MUST include DECISIONS.md + GUARDRAILS.md as "Decision Record Room" for agent memory.
**Date**: 2026-02-16

---

## DEC-005: Multi-Language Support (TypeScript, Python, Go)

**Chose**: Support TypeScript/Python/Go skill handlers via common SDK
**Over**: Single language (TypeScript-only or Python-only)
**Why**:
- Wealth team prefers TypeScript (Next.js existing codebase)
- Data science team prefers Python (Pydantic AI ecosystem)
- High-performance teams may prefer Go (fraud detection, ECM indexing)
- Platform provides language-agnostic interface via `agentura.config.yaml`

**Constraint**: All handlers MUST implement same interface (`SkillContext → SkillResult`).
**Date**: 2026-02-16

---

## DEC-006: Feedback Loop as Competitive Moat

**Chose**: User corrections → auto test generation → continuous improvement
**Over**: Static test suites
**Why**:
- DeepEval + Promptfoo + Opik + Langfuse form testing moat
- Each correction becomes regression test
- After 6 months: 10,000+ test cases vs competitor's 0
- Licensing (Apache/MIT) + compliance audit (AGPL Langfuse) = trust signal

**Constraint**: Every skill MUST log user corrections to `skill_executions.user_correction`.
**Date**: 2026-02-16

---

## DEC-007: PostgreSQL Skill Registry Over Redis/In-Memory

**Chose**: PostgreSQL for skill metadata, triggers, permissions, execution logs
**Over**: Redis or in-memory registry
**Why**:
- ACID guarantees for skill deployment/versioning
- Rich querying for discovery (LLM searches skills by description)
- Existing Prisma setup in wealth-copilot codebase
- Versioning/rollback requires relational integrity

**Constraint**: Redis ONLY for hot skill cache (LRU eviction), NOT source of truth.
**Date**: 2026-02-16

---

## DEC-008: Three-Tier Observability (Platform → Domain → Skill)

**Chose**: Hierarchical monitoring with Prometheus + Grafana
**Over**: Flat per-skill metrics
**Why**:
- Platform level: Total executions, success rate, cost (for leadership)
- Domain level: Per-domain metrics (Wealth vs Fraud vs ECM)
- Skill level: Detailed latency, cost, user satisfaction (for debugging)

**Constraint**: All alerts MUST include runbook link (no "error rate high" without "how to fix").
**Date**: 2026-02-16

---

## DEC-009: Firecracker VMs Over Docker Containers for Sandboxing

**Chose**: Firecracker microVMs for skill execution
**Over**: Docker containers or process isolation
**Why**:
- Stronger security boundary (kernel-level isolation)
- Fast startup (< 125ms, comparable to containers)
- Used by AWS Lambda (battle-tested at scale)
- Prevents malicious skills from accessing other tenants' data

**Constraint**: Each skill execution gets isolated VM with CPU/memory caps from `agentura.config.yaml`.
**Date**: 2026-02-16

---

## DEC-010: Canary Deployments with Auto-Rollback

**Chose**: 10% canary → monitor success rate → auto-rollback if degrades
**Over**: Blue-green or all-at-once deployments
**Why**:
- LLM outputs are non-deterministic (version may seem good in tests but fail in prod)
- Gradual rollout limits blast radius
- Auto-rollback prevents manual incident response

**Constraint**: Rollback triggered if canary success rate < 95% of previous version.
**Date**: 2026-02-16

---

## When to Add New Decisions

- **Architecture choice** → DEC-NNN
- **Technology selection** → DEC-NNN
- **Security/compliance** → DEC-NNN
- **Developer workflow** → DEC-NNN

**Max 20 decisions per project.** Constraints should be binary with reasoning.

---

## DEC-011: Role-Based Skill Isolation Over Monolithic Agent

**Chose**: Domain → Role → Skill hierarchy with RBAC enforcement
**Over**: Single agent per domain with all skills loaded
**Why**:
- **Validated by ECM Operations** (manager/ vs field/ separation, Feb 2026)
- Context bloat: Loading triage scoring + 25 runbooks consumed 40K+ tokens
- Role confusion: Same agent routed both manager (batch) and field (interactive) operations
- Deployment mismatch: K8s CronJob vs Claude Code interactive
- Resource access control: Manager NEVER loads runbooks, Field NEVER computes priority scores

**Constraint**: Skills MUST declare `role` field. Platform MUST enforce `blocked_resources` at runtime.
**Date**: 2026-02-16
**Source**: ECM Operations production deployment (ecm-operations/DECISIONS.md DEC-011)

---

## DEC-012: Shadow Mode Canary for Batch Skills

**Chose**: Shadow mode (parallel execution + diff) for cron/scheduled skills
**Over**: Traffic-split canary (works only for interactive skills)
**Why**:
- Batch skills run 3x daily (low sample size for statistical confidence)
- Cannot A/B test cron jobs (no user traffic to split)
- Shadow mode: New version runs alongside old, writes to `_canary` output, compare diffs
- If diff < 5%, promote to 100%; if diff > 5%, investigate before rollout

**Constraint**: Shadow mode canary REQUIRED for skills with `trigger_type: cron|alert`.
**Date**: 2026-02-16
**Source**: ECM triage-and-assign skill (runs 3x daily, cannot use traffic split)

---

## DEC-013: ReAct + Reflexion Intelligence Layer Over Pure Retrieval

**Chose**: Hybrid intelligence layer (ReAct for reasoning + Reflexion for learning + Vector search for precedents)
**Over**: Simple CRUD skills OR Pure CoT reasoning OR LATS tree search
**Why**:
- ECM/FinCrime domains need pattern detection beyond data retrieval (e.g., "Why are 50% of tickets stuck >24h?")
- Manager/analyst skills require root cause analysis, not just data display
- ReAct grounds reasoning in tool calls, prevents hallucination (reasoning → action → observation loop)
- Reflexion enables learning from user corrections (feedback loop moat): "You recommended X but issue was Y"
- Vector search retrieves similar past cases for precedent-based reasoning
- Feasible in 12-16h vs LATS at 10-14h with higher complexity
- Builds on existing testing moat (DeepEval, Opik, Langfuse track reasoning quality)

**Constraint**:
- Every execution MUST log reasoning trace + actions to pgvector (episodic memory)
- User corrections MUST generate Reflexion entries (`<mistake> + <correction> + <revised_approach>`)
- Observability via Langfuse REQUIRED for debugging multi-step reasoning
- Initial 100+ past executions needed to seed vector DB for pattern matching
- ReAct loop limited to 5 iterations (prevent infinite reasoning loops)

**Date**: 2026-02-17
**Source**: Intelligence layer research for hackathon Track 1 (Skills Executor)

---

## DEC-016: GraphRAG (Neo4j + Vector Hybrid) Over Pure Vector Search

**Chose**: GraphRAG with Neo4j knowledge graph + pgvector hybrid
**Over**: Pure vector search with PostgreSQL/pgvector OR Graph-only without vectors

**Why**:
- **Uber precedent**: "Knowledge graph had biggest impact on accuracy, way more than prompt engineering" (2 engineers, 12 weeks, production-ready)
- **Causal reasoning**: Graph provides DETERMINISTIC causal chains vs probabilistic vector similarity
- **Explainability**: Can show exact path (Ticket → Policy → Bottleneck → Solution) with confidence scores
- **Multi-hop reasoning**: "Why stuck?" requires traversing Ticket → Manager → Capacity → Policy relationships
- **Learning at scale**: Corrections stored as graph nodes, agent learns by traversing (Execution)-[:CORRECTED_BY]->(Correction)-[:REFINED]->(Solution) paths
- **Competitive moat**: Graph structure = 6 months of accumulated causal relationships, cannot be replicated without production usage

**Constraint**:
- Vector search REQUIRED for entry point (semantic similarity)
- Graph traversal REQUIRED for causal reasoning (deterministic)
- All executions MUST store both embedding (vector) AND causal relationships (graph edges)
- MCP server pattern (Uber's approach) for agent access to graph queries
- Initial setup 16-20h (vs 12-16h for pure vector), but higher accuracy (90-95% vs 75-85%)

**Date**: 2026-02-17
**Source**: Uber Neo4j case study + Agent Swarm architecture research

---

## DEC-017: "Kubernetes for AI Agent Swarms" Positioning Over "Docker for Skills"

**Chose**: Platform positioned as orchestration layer for multi-agent swarms (K8s analogy)
**Over**: Individual skill containerization (Docker analogy)
**Why**:
- Docker analogy limits to single-skill execution (already done by CrewAI, LangGraph)
- K8s analogy captures routing, scaling, health checks, canary, and multi-domain orchestration
- Swarms/ClawSwarm claims "multi-agent" but is single-agent chatbot (`max_loops=1`) — real gap exists
- OpenClaw is personal assistant (WhatsApp); this is enterprise orchestration (Kubernetes)

**Constraint**: All positioning materials MUST use orchestration vocabulary (deploy, route, scale), not container vocabulary (build, ship).
**Date**: 2026-02-17
**Source**: Competitive analysis of OpenClaw, Swarms, ClawSwarm, CrewAI, LangGraph

---

## DEC-018: Correction→Test→Reflexion Pipeline as Hackathon Demo Primitive

**Chose**: Single correction loop as the ONE demo primitive
**Over**: Multi-domain breadth demo (14 skills across 3 domains)
**Why**:
- NOBODY does corrections → auto-regression tests → reflexion → measurable improvement
- 14 skills = impressive slides, 0 working demos. 1 loop = working proof of moat.
- Persist-or-pivot assessment: 4/5 HIGH. The moat IS the feedback loop (DEC-006).
- Breadth can be shown via slides; depth can only be shown via live demo.

**Constraint**: Friday primitive MUST demonstrate: skill runs → user corrects → test auto-generated → skill re-runs → measurably better.
**Date**: 2026-02-17
**Source**: Stockdale Paradox analysis + persist-or-pivot heuristics

---

## DEC-019: Project Reorganized — Planning Docs Archived, Showcase Created

**Chose**: 38 planning docs → `archive/`, clean root + `showcase/` with realistic data
**Over**: All docs in project root
**Why**:
- 37+ MD files in root made project unnavigable for new developers
- Showcase folder has realistic fixtures (NRI profiles, TRM alerts, fraud transactions)
- Archive preserves all architecture thinking for reference
- Root now: README.md, DECISIONS.md, ENGINEERING_BRAIN.md, sdk/, showcase/

**Constraint**: New planning docs go in `archive/` or `docs/`. Root stays clean.
**Date**: 2026-02-17

---

## DEC-020: Config Loader Handles Simplified YAML Format

**Chose**: `_normalize_config()` in config_loader.py handles both full and shorthand YAML
**Over**: Requiring all configs to use verbose SkillConfig-compatible format
**Why**:
- Showcase/onboarding configs use simpler format (`domain: "wealth"` vs nested object)
- Production configs use full format with descriptions
- Normalization layer means ONE parser handles both
- Reduces friction for new skill authors

**Constraint**: Both formats MUST produce identical SkillConfig objects.
**Date**: 2026-02-17

---

## DEC-021: Routing Is LLM-Based (Skill), Not Python Code

**Chose**: Domain classification and routing via skills (SKILL.md + plugin.yaml triggers) executed by Pydantic AI
**Over**: Python router classes with if-else/pattern matching code
**Why**:
- ECM SKILL.md already proves routing-as-a-skill works in production (12 trigger patterns, 6 sub-skills)
- plugin.yaml declares triggers declaratively — no code needed
- Platform classifier = Pydantic AI agent with Haiku (fast, cheap) that returns domain name
- Domain manager = SKILL.md that routes to sub-skills based on command matching
- Python code for routing contradicts "everything is a skill" principle
- Building Python routers is an antipattern to the platform we're building

**Constraint**: Python/Pydantic AI is ONLY the execution engine (load SKILL.md → call LLM → return result). ALL routing, domain logic, business rules live in skills + config.
**Date**: 2026-02-18
**Source**: User correction + ECM production SKILL.md + ASPORA_PLATFORM_DESIGN.md architecture

---

## DEC-022: MCP for Structured Data, Skills for Knowledge, RAG Only for Unstructured

**Chose**: Four-layer information stack: Weights → Skills (context injection) → MCP (precise queries) → RAG (similarity search)
**Over**: RAG-first approach for all data access
**Why**:
- ECM uses Redshift via MCP (precise SQL) — no RAG needed
- FRM uses Redshift via MCP for rule simulation — no RAG needed
- Skills provide structured knowledge (diagnosis-mapping.yaml, stuck-reasons.yaml) via context injection
- RAG enters ONLY when unstructured knowledge exceeds context window
- MCP is deterministic (exact query → exact result), RAG is probabilistic (approximate similarity)

**Constraint**: When data is in Redshift/Databricks/PostgreSQL, ALWAYS use MCP (SQL). When knowledge fits in SKILL.md context, use skills. RAG only for unstructured docs that exceed context.
**Date**: 2026-02-18
**Source**: ECM and FRM production data flows + first-principles analysis

---

## DEC-023: Config-Driven Skills Over Code-Driven Agents (Swarms/CrewAI Differentiation)

**Chose**: Skills defined in Markdown + YAML (SKILL.md, DOMAIN.md, plugin.yaml) with Python as execution engine only
**Over**: Swarms model (Agent class with 60+ Python params), CrewAI model (role/goal/backstory in Python)
**Why**:
- Swarms source code review: agent.py = 6,167-line god class, CI not green, single maintainer (1,303/4,800 commits)
- Swarms agents require Python developers. Our skills require Markdown authors (business teams).
- Swarms has 16 orchestration patterns but zero domain knowledge architecture (no DOMAIN.md, no config YAMLs)
- Swarms has zero learning loop (same mistake forever). We have corrections → auto-tests → measurable improvement.
- Swarms Solana crypto token (with "pump" in contract address) incompatible with enterprise credibility.
- Borrowed from Swarms: named orchestration patterns as vocabulary, factory router concept, marketplace metadata structure.

**Constraint**: Agents/skills MUST be definable without writing Python. If a business analyst can't create it, the abstraction is wrong.
**Date**: 2026-02-18
**Source**: Deep source code review of github.com/kyegomez/swarms + swarms.world marketplace

---

## DEC-024: CLI Follows kubectl Verb-Resource Pattern

**Chose**: `agentura <verb> <resource> [name] [flags]` pattern (kubectl-style)
**Over**: Flat commands (e.g., `agentura list-skills`, `agentura show-execution`)
**Why**:
- Verbs reusable across all resources: `get skills`, `get domains`, `get executions`, `get reflexions`
- Users learn verbs once, apply everywhere (same as K8s learning curve)
- Supports both local (`run`, `create`, `validate`, `test`) and gateway (`get`, `describe`, `logs`, `status`) operations
- `apply -f` enables declarative deployment (GitOps-compatible)
- `describe` and `logs` map directly to debugging workflows

**Constraint**: Every new resource type MUST work with `get` and `describe`. Local operations use imperative verbs (`run`, `test`), gateway operations use kubectl pattern.
**Date**: 2026-02-20
**Source**: Kubernetes kubectl design + Architecture Principles doc

---

## DEC-025: mcp-guard as Admission Controller Layer

**Chose**: Runlayer mcp-guard (Go webhook) + monitor agent (Rust daemon) as the policy enforcement layer
**Over**: Building custom admission logic in Go gateway
**Why**:
- Already built and tested: PII (8 categories), secrets (15+ types), injection (10+ vectors)
- Rust agent monitors shadow MCP servers + config compliance across 5 IDE clients
- Fail-open policy: scanning bug ≠ block all MCP (DEC-008 from runlayer)
- Configurable mode: block (403) or warn (200 + log)
- Runs as sidecar webhook to Obot gateway — zero coupling to Agentura gateway

**Constraint**: All MCP tool calls MUST pass through mcp-guard before execution. Skill deployment validation (tests exist, budget OK, model approved) runs as pre-apply admission in the CLI.
**Date**: 2026-02-20
**Source**: runlayer/agent codebase analysis + Architecture Principles doc

---

## DEC-026: Platform Renamed to "Agentura" Over Other Candidates

**Chose**: Agentura (derived from "agency" in Romance/Slavic languages)
**Over**: Volition, Sovren, Autonoma, Aspora (original name), various skill/craft names
**Because**: Name captures agency and autonomy — the platform's core value prop. "Skill" is an implementation detail; the brand should reflect autonomous AI agents that act with their own authority. The word is distinctive, unmistakable in context, and not taken in the AI tooling space.
**Constraint**: Must work as CLI command (`agentura run`), package name (`agentura-sdk`), and brand simultaneously.

**Scope**: Full rename — Python package (`agentura_sdk`), CLI (`agentura`), config files (`agentura.config.yaml`), runtime dir (`.agentura/`), env vars (`AGENTURA_*` with backward-compatible ASPORA fallbacks), K8s manifests, Docker configs, web UI, docs.

---

## DEC-027: PostgreSQL as Production Memory Store Over JSON Files

**Chose**: PostgreSQL with domain + workspace columns
**Over**: JSON files on disk
**Why**: Domain isolation requires column-level filtering. JSON files can't enforce cross-domain boundaries. PG supports concurrent access and ACID.
**Constraint**: JSON fallback must remain for local dev without DATABASE_URL.
**Date**: 2026-02-21

---

## DEC-028: OpenRouter for Multi-Model Routing Over Direct Provider SDKs

**Chose**: OpenRouter as unified model gateway
**Over**: Direct Anthropic/OpenAI SDK calls
**Why**: Single API for 200+ models, automatic fallback chains (claude-sonnet → claude-haiku → gpt-4o-mini), unified billing.
**Constraint**: Requires OPENROUTER_API_KEY. Falls back to direct Pydantic AI when not set.
**Date**: 2026-02-21

---

## DEC-029: DomainScopedStore Wrapper Over Modifying MemoryStore Protocol

**Chose**: Composition wrapper (`DomainScopedStore`) around any MemoryStore
**Over**: Adding domain filtering to every MemoryStore implementation
**Why**: Backward compatible, single enforcement point, any backend gets isolation for free.
**Constraint**: All server endpoints must use `Depends(_get_domain_scope)` + `_filter_by_domain()`.
**Date**: 2026-02-21

---

## DEC-030: JWT+JWKS for Gateway Auth Over API Keys

**Chose**: RS256 JWT validation with JWKS key rotation (1hr cache)
**Over**: Static API keys or session tokens
**Why**: Standard, supports key rotation, carries domain_scope + workspace_id claims. Dev mode auto-injects safe defaults.
**Constraint**: Requires JWKS_URL configured for production.
**Date**: 2026-02-21

---

## DEC-031: MCP Registry Auto-Discovery Over Manual Configuration

**Chose**: Auto-discover MCP servers from skill config files + environment variables
**Over**: Manual registry configuration file
**Why**: Zero-config for local dev. Skill configs already declare which MCP tools they need. Registry merges all declarations and tracks domain usage.
**Constraint**: Well-known servers (redshift, google-sheets, jira) can also be registered via MCP_*_URL env vars.
**Date**: 2026-02-21

---

## DEC-032: Open-Source Apache 2.0 Over Proprietary

**Chose**: Open-source under Apache 2.0 before market is ready
**Over**: Keeping proprietary until product-market fit
**Why**: K8s pattern — ship before market needs it, capture mindshare. Correction→reflexion→test pipeline is the hook. Community builds ecosystem faster than one team.
**Constraint**: Must remove internal domain skills (wealth/ecm/frm/hr) from public repo or move to examples/. No real API keys or customer data.
**Date**: 2026-02-23

---

## DEC-033: Task Prompts (No Code Execution) Over Tool Instructions

**Chose**: Skills produce text/JSON only (task prompts) — no shell commands, no code execution
**Over**: Tool instructions model (OpenClaw/ClawHub — skills execute shell commands)
**Why**: ClawHavoc incident: 341 malicious skills with shell access in ClawHub. Snyk article showed shell access from SKILL.md in 3 lines. Task-only = categorically safer. Tradeoff: need MCP bridge for real-world actions.
**Constraint**: Skills REASON (safe). MCP tools ACT (governed by mcp-guard). Never mix execution into skills.
**Date**: 2026-02-23

---

## DEC-034: ClawHub Skill Compatibility Over Proprietary Format

**Chose**: Compatible SKILL.md format that can import/wrap ClawHub skills
**Over**: Building proprietary skill marketplace from scratch
**Why**: 3,286 existing ClawHub skills, same SKILL.md + YAML frontmatter format. Runtime semantics differ (tool vs task) but format is near-identical. Adapter layer translates tool instructions to task prompts.
**Constraint**: Runtime adapter needed. ClawHub tool instructions must be converted to task prompts (strip shell commands, keep knowledge).
**Date**: 2026-02-23

---

## DEC-035: Bundle with Obot + mcp-guard Over Building Custom Security

**Chose**: Integrate Obot (MCP gateway + registry + RBAC) and mcp-guard (PII/secrets/injection scanning)
**Over**: Building custom MCP security layer from scratch
**Why**: Already running in runlayer repo. Covers 5/7 Ailoitte enterprise requirements without new code. Obot handles auth + RBAC + audit, mcp-guard handles policy enforcement.
**Constraint**: Need shared auth (JWT) and unified docker-compose. Obot on :8080, mcp-guard on :8081, Agentura executor on :8000.
**Date**: 2026-02-23

---

## DEC-036: Declarative Prompt Reasoning Over Imperative Tool Execution

**Chose**: Declarative single-shot LLM call (system_prompt + input → structured output) via Pydantic AI
**Over**: Imperative ReAct loop (reason → act → observe → repeat) used by OpenClaw
**Why**:
- Formal distinction: **imperative** (Turing-complete, agent loops shell commands) vs **declarative** (bounded, single LLM call produces text). IBM PDL research validates declarative agent patterns (67% faster dev, 74% less code).
- Agentura uses Pydantic AI with **zero `@agent.tool` decorators** — `Agent(model, system_prompt)` → `agent.run(prompt)` → JSON output. No tool registration, no execution loop.
- OpenClaw uses ReAct loop: LLM picks tools → executes shell/API → observes result → loops. Skills are tool manuals.
- Security: imperative = Turing-complete execution surface (ClawHavoc: 341 malicious skills). Declarative = bounded text transformation (worst case: wrong JSON).
- Halting guarantee: single LLM call always terminates. ReAct loop may loop indefinitely (OpenClaw caps at N iterations).
- Agentura's "agent" is the **learning loop** (corrections → tests → reflexion), not the LLM execution.

**Constraint**: Pydantic AI Agent MUST have zero tool registrations. Skills produce text only. Actions go through MCP layer (separate security boundary governed by mcp-guard).
**Date**: 2026-02-23
**Source**: IBM Prompt Declaration Language research, OpenClaw system prompt docs, Agentura local_runner.py L152-158
