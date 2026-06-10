# Agentura Harness v2 — Engineering Plan

**Date**: 2026-06
**Status**: Work in progress — research-backed design document
**Input sources**:
- Agentura v1 production learnings
- arXiv:2605.18747 "Code as Agent Harness" (UIUC/Meta/Stanford, 102-page survey, full PDF read)
- Stripe Minions (production SDLC harness, 1,300 PRs/week)
- Razorpay Slash (enterprise agent platform)
- PlayerZero (predictive quality + SRE automation)
- Shopify AI Platform (23,000 engineers, 90% autonomous coding target)
- Anthropic Three-Agent Harness (InfoQ Apr 2026)
- AutoHarness (github.com/aiming-lab/AutoHarness)
- OpenHarness (github.com/HKUDS/OpenHarness)
- devstack pattern (github.com/razorpay/devstack)
- Canonical logging + ClickHouse observability infrastructure

**Note**: Sections marked `[Paper §]` cite specific mechanisms from arXiv:2605.18747. This document is a living design specification — some sections describe what is running in production, others describe the v2 roadmap.

> GitHub: [github.com/Vance-Club/agentura](https://github.com/Vance-Club/agentura) | Site: [agenturaai.tech](https://agenturaai.tech)

---

## 0. Strategic Direction

### Primary Goal: SDLC Harness Engineering

> **Agentura's primary job is to solve the engineering problems that Minions, PlayerZero, Devin, and OpenHands solve — a complete, reliable, self-improving harness for the software development lifecycle. Multi-domain (PM, Finance, Growth) is a differentiated layer on top, not the core product.**

This is a deliberate reframe from v1. In v1, Agentura was an enterprise operations platform that happened to do coding. In v2, Agentura is an SDLC harness platform that happens to also automate enterprise domains. The engineering harness is the primary investment. Multi-domain skills ride the same rails.

**Why**: The engineering harness is where the research, the reliability requirements, and the compounding value live. Every improvement to the harness (deterministic gates, behavioral simulation, memory, telemetry) benefits coding AND PM AND finance skills equally. Multi-domain is additive — it demonstrates the platform's breadth but doesn't require separate infrastructure investment.

**What "SDLC Harness Engineering" means concretely**:

```
THE FOUR SDLC LOOPS AGENTURA MUST OWN

Loop 1 — BUILD           Loop 2 — QUALITY
Ticket → Spec            Code change →
→ Code                   Behavioral simulation
→ Deterministic gates    → Impact prediction
→ Tests → PR             → Risk score
(Minions-equivalent)     (PlayerZero-equivalent)

Loop 3 — REVIEW          Loop 4 — RELIABILITY
PR → Parallel review     Monitor → Anomaly
→ Security scan          → Code root cause
→ Test coverage          → Fix PR → Deploy
→ Consensus → Merge      (PlayerZero SRE-equivalent)
(existing, enhanced)
```

Multi-domain skills (PM, Finance, Growth) run on the same harness infrastructure. They benefit from every improvement to memory, telemetry, and harness control. They are not a separate track.

### Competitive Targets

| Competitor | What they solve | What Agentura must match |
|-----------|----------------|-------------------------|
| **Minions (Stripe)** | Deterministic coding execution harness | Blueprint nodes: linter/tests always run in code, not prompts |
| **PlayerZero** | Predictive quality + SRE incident loop | Behavioral simulation + anomaly → fix PR loop |
| **Slash (Razorpay)** | Enterprise knowledge graph + repo readiness | Discover v2 + skill/repo readiness scoring |
| **OpenHands** | Full PEV harness, 72% SWE-bench | Typed harness contracts + PipelineContext |
| **Augment Code** | Deep codebase intelligence | AST-indexed semantic memory for dev skills |
| **Devin** | End-to-end autonomous coding | Full Build Loop (ticket → spec → code → PR) |

**The moat**: none of these have MemRL + self-improving harness + multi-domain scope. That combination is Agentura's unique position. But the moat only matters if the baseline SDLC harness is reliable enough to be trusted with engineering work.

### Infrastructure Already in Place

Two infrastructure investments directly power the harness v2 plan. These are not new builds — they are existing infrastructure the harness layers on top of.

**Devstack (github.com/razorpay/devstack) → Isolated Execution Environment**
- Kubernetes-native local environment that mirrors production service topology
- Same DB schema, same dependency graph, same service wiring — no production access
- This is the `execution_environment: isolated` tier in the harness plan
- Build Loop (Loop 1) agents build and test code in devstack before any PR is opened
- Equivalent to Stripe's "pre-warmed devboxes — same machines as human engineers"

**Canonical Logging + ClickHouse  → Observability Data Layer**
- Wide events: every log line enriched with `x_user_id`, `x_country`, `x_app_version`, `x_txn_id`, `x_build_id`
- ClickHouse as query engine: SQL on structured events, not aggregate metrics proxies
- eBPF (Beyla/Coroot): zero-code infrastructure traces — DB query latency, service graph, SQL rows scanned
- signoz-mcp: already-built MCP interface to ClickHouse — the tool interface for Loop 4 agents
- Vector DaemonSet: deployed on production K8s cluster

The combination: devstack (where agents work safely) + ClickHouse (what agents query for evidence) + harness v2 (what orchestrates agents) = a complete SDLC platform, not three separate projects.

---

## 1. Situation Assessment

### What Agentura v1 Built (and proved)

| Capability | Status | Evidence |
|-----------|--------|---------|
| Skill execution (SKILL.md + agentura.config.yaml) | ✅ Production | PM, Growth, ECM, GE, HR, Finance domains live |
| Agent personalities (SOUL.md + HEARTBEAT.md) | ✅ Production | 6 domains, scheduled heartbeats running |
| Pipeline orchestration | ✅ Production | PR review parallel pipeline, incubator 4-stage pipeline |
| MemRL (reflexion + Bayesian scoring) | ✅ Production | 170 executions analyzed, 3 rules synthesized, daily CronJob |
| MCP tool integration | ✅ Production | Slack, Notion, Databricks, GitHub, Gmail, Metabase |
| Executor model (PTC vs Claude Code) | ✅ Production | Two-tier: lightweight vs full sandbox |
| Parallel skill dispatch in pipelines | ✅ Production | PR review: 4 agents in parallel → reporter |

### What v1 Did Not Solve

1. **Memory is reactive only.** MemRL captures failure patterns post-hoc but has no episodic, declarative, or procedural layers. A skill that runs 100 times has no richer world model than one that ran once.
2. **Skills are natural language, not verifiable.** SKILL.md prompts are interpreted by the LLM at runtime. There is no typed contract — input schema, output schema, and tool permissions are implicit. A skill can silently drift.
3. **No cross-skill knowledge.** Learnings from finance skills cannot inform pm skills. Each domain is an island. The knowledge graph that Razorpay's Discover system provides does not exist here.
4. **No skill quality measurement.** There is no framework to answer "is this skill getting better?" beyond binary success/failure logged in MemRL.
5. **No shared pipeline state.** Agents in a pipeline pass results as unstructured Slack messages or JSON blobs. There is no typed context object that flows through stages.
6. **Skill readiness is unmeasured.** There is no equivalent to Razorpay's "Agent Ready" scoring (80% threshold = compounding returns). We do not know which skills are brittle.
7. **Skills cannot self-improve.** Reflexion rules accumulate but never feed back into the SKILL.md itself. The skill author must manually absorb what the machine learned.
8. **No centralized cost/usage visibility.** There is no gateway-level analytics layer. We cannot answer "which skill costs the most?", "which model performs best per dollar?", or "where is the token budget going?" without ad-hoc log queries.
9. **No bash-level execution guardrails.** Tool permissions exist in environment.yaml but are advisory. There is no platform-enforced allow/deny list for shell commands in Claude Code executor pods — an agent could run destructive commands if the SKILL.md doesn't explicitly prohibit them.

### SDLC-Specific Gaps (from Competitive Analysis)

10. **No deterministic gates in coding skills.** SKILL.md says "run the linter." The LLM decides whether to comply. Minions' blueprint hardcodes the linter as a deterministic pipeline node — it runs regardless of LLM judgment. Under context pressure, our agents skip steps. Minions can't.
11. **No codebase intelligence layer.** Coding skills (pit-builder, mobile-builder) start cold on every run, rediscovering structure via grep. Minions uses Sourcegraph with 400+ tools. Augment Code builds deep call graphs. We have neither.
12. **No Build Loop (ticket → spec → code → tests → PR).** The incubator pipeline covers one path (Lovable prototype → backend + mobile). There is no general "take a Jira ticket and produce a PR" capability. Devin, OpenHands, and GitHub Copilot Workspace all solve this. We don't.
13. **No behavioral simulation.** We discover failures after they happen. PlayerZero's Sim-1 predicts codebase behavior before execution — no tests required. We have no equivalent. The QualityFlow [253] "Imagined Execution" (LLM simulating interpreter step-by-step at 98%+ precision) is a lighter version we can implement.
14. **No SRE/incident loop.** Growth heartbeat detects anomalies and posts to Slack. The loop ends there. PlayerZero's Autopilot SRE traces anomaly → code root cause → fix PR. The "anomaly detected → PR proposed" path is entirely manual in Agentura.
15. **No repository readiness scoring for external repos.** Skill Readiness Score covers skills. We have no equivalent for the repos our coding agents work on. Slash's "Agent Ready" (80% threshold = compounding returns) is a repo-side score. Without it, we don't know which repos will produce reliable agent output.
16. **Memory is a black box.** MemRL is our strongest differentiator but engineers can't see it. No UI, no API, no explanation of what the system believes. PlayerZero's "living model" is inspectable. Ours isn't.
17. **No Agentic Quality Lifecycle.** Slash's next phase: agents generate test suites from PR diffs, run parallel against dev environments, triage failures, assess shipping readiness. We have pr-test-runner (reports coverage gaps) but no test generation from diffs.
18. **Pipeline stages pass raw JSON, not structured handoff artifacts.** Anthropic's three-agent harness (Apr 2026) proved that context compression between stages causes models to grow cautious and lose intent. The fix: each stage produces a formal `HandoffArtifact` — task spec, progress, open questions, verification criteria — not a JSON blob. The next agent reads the artifact, not the history.
19. **Tool call responses are unsanitized.** MCP tool responses enter the LLM context verbatim — including file paths, secrets, internal URLs, and noise. AutoHarness enforces an output sanitization step after every tool call: strip credentials, compact large logs, remove irrelevant metadata before the response reaches the model. We have none of this.
20. **No tool-call-level governance pipeline.** Every tool call is: invoke → result. There is no intermediate risk classification, per-call permission check, or audit log. AutoHarness implements a 6-step pipeline per tool call. Our advisory `environment.yaml` is not the same thing — it's declared intent, not enforced execution.
21. **No dry-run mode.** There is no way to preview what context, tools, permissions, and memory a skill will have before it runs in production. OpenHarness implements `oh --dry-run` which resolves and prints all settings without executing. We discover misconfigurations in production.
22. **Build Loop agents have no isolated execution environment.** Coding agents (pit-builder, mobile-builder) run tests inside the executor pod itself or against production services. There is no devstack-equivalent environment where agents build and test safely against real service topology. This is why CI pass rates on agent PRs are variable.
23. **Loop 4 uses metric inference, not event-level evidence.** The alert-enricher skill has an explicit limitation: The agent gets aggregate error rates rather than event-level stack traces. It infers root cause from timing, not build_id proof. A canonical logging + ClickHouse infrastructure closes this gap — it is not yet connected to the harness.
24. **Harness telemetry is not in ClickHouse.** Skill execution events are not routed through the canonical logging pipeline. We cannot query "which skills are failing this week" or "which reflexion rules are actually helping" with SQL. The same infrastructure that captures application events can capture harness events — not yet wired.

---

## 2. Research Thesis

> **Code-as-harness is the substrate, not the output. The primary job is a reliable, executable, self-improving SDLC harness. Multi-domain skills are the differentiated layer on top. Natural language prompts are harness v0 — deterministic gates + typed contracts + behavioral simulation is harness v2.**

Four insights driving v2:

**From Stripe Minions (production SDLC harness)**
- Interleave deterministic hardcoded gates with LLM steps. The linter always runs. The test runner always runs. The git commit format is always enforced. These are code, not prompts. The LLM cannot skip them.
- Blueprint templates (deterministic node + agentic node alternating) are the execution model. Not SKILL.md-only.
- Hard cap on feedback loops (max 2 CI rounds). If it can't fix in 2 attempts, escalate. Don't waste compute.
- Pre-warmed isolated devboxes = same environment as human engineers. The agent sees what a human would see.

**From PlayerZero (predictive quality + SRE)**
- The real value is not fixing bugs after they're found — it's predicting behavior before code ships.
- Build a living model of how the software behaves (code + tickets + logs + deployments unified). Then predict impact of changes against that model.
- Close the SRE loop: monitoring → anomaly → code root cause → fix PR. Every step automated.
- Memory is only valuable if it's inspectable and correctable. A black-box memory is a liability.

**From Anthropic's Three-Agent Harness (production, Apr 2026)**
- Separating the agent doing the work from the agent judging it is the single strongest reliability lever. Self-assessment is biased. Independent evaluation is not.
- Replace context compression with **structured handoff artifacts**. Compressing context makes models cautious near limits. Handoff artifacts give each new agent a clean, authoritative start: task spec (original intent), progress, constraints, open questions, verification criteria. Sessions run up to 4 hours without degradation.
- The evaluator must execute the output, not just read it. For code: run it. For UI: navigate it via Playwright. Evaluation without execution is opinion, not measurement.
- 5–15 iterations per pipeline run is normal for complex tasks. Don't terminate early — iterate to quality.

**From AutoHarness (open-source governance reference)**
- Every tool call is a state transition that must be governed: classify risk, check permission, execute, sanitize output, audit. The current "invoke → result" is harness v0.
- Output sanitization is not optional for production: MCP responses contain file paths, auth tokens, internal URLs, and noise that pollute LLM context when passed through verbatim.
- The AutoHarness philosophy: `Agent = Model + Harness`. Reliability comes from the governance pipeline, not from better prompts.

**From arXiv:2605.18747 + References**
- The harness must operate at three layers: interface (typed contracts), mechanisms (planning + memory + tools + feedback), multi-agent coordination.
- MemGovern: ungoverned episodic memory introduces noise. Quality-gate what gets stored.
- EvoMAC: separate failure attribution (which step broke?) from harness revision (what should change?).
- L2MAC: targeted context views per agent. Don't flood each agent with full pipeline history.

**From Agentura v1 production**
- MemRL works but is one-dimensional and invisible. It needs four layers and an explanation API.
- SOUL.md constraints matter more than prompt engineering. Keep them; strengthen them.
- Pipeline coordination requires typed shared state. Slack blobs don't scale to 5+ stage pipelines.

---

## 3. V2 Architecture — Four Pillars

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              HARNESS V2                                      │
│                                                                              │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────┐  ┌────────┐ │
│  │  PILLAR 0        │  │  PILLAR 1       │  │  PILLAR 2      │  │PILLAR 3│ │
│  │  SDLC Harness    │  │  Code-First     │  │  Memory v2     │  │Skills  │ │
│  │  Engineering     │  │  Harness        │  │  (4-layer)     │  │at Scale│ │
│  │  (PRIMARY)       │  │  Interface      │  │                │  │        │ │
│  └──────────────────┘  └─────────────────┘  └────────────────┘  └────────┘ │
│                                                                              │
│  4 SDLC loops:        Typed I/O contracts  Episodic+Declarative Readiness  │
│  Build/Quality        Deterministic gates  Procedural+Reflexion Discovery  │
│  Review/Reliability   PEV loop             Self-improving      Flywheel    │
│  (Minions+PlayerZero  (OpenHands ref)      (MemGovern ref)     (Slash ref) │
│   parity target)                                                            │
└──────────────────────────────────────────────────────────────────────────────┘

Multi-domain skills (PM, Finance, Growth, ECM) ride Pillar 0 rails.
They are not a separate pillar. They are tenants of the SDLC harness.
```

---

## 4. Pillar 0 — SDLC Harness Engineering

This is the new primary pillar. Everything in Pillars 1–3 is infrastructure that makes Pillar 0 reliable.

### 4.0 The Four Loops

```
                    INFRASTRUCTURE LAYER
┌─────────────────────────────────────────────────────────────────┐
│  DEVSTACK (isolated K8s)     │  CLICKHOUSE (wide events + eBPF) │
│  → Loop 1: agents build      │  → Loop 4: agents query for RCA  │
│    and test here safely      │  → All loops: deep telemetry      │
│  → Loop 2: diff tests run    │    substrate for harness AHE      │
│    against real services     │  → signoz-mcp: MCP interface      │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    LOOP 1: BUILD                               │
│  Trigger → Spec → Code → [Lint Gate] → [Test Gate] → PR       │
│  Execution env: DEVSTACK (isolated, same topology as prod)     │
│  Skills: dev/spec-analyzer, dev/code-builder,                  │
│          dev/test-generator, dev/pr-opener                     │
└────────────────────────────────────────────────────────────────┘
         ↓ (PR opened)
┌────────────────────────────────────────────────────────────────┐
│                    LOOP 2: QUALITY                             │
│  PR diff → Behavioral simulation → Impact score →              │
│  Risk tier → Gate (merge / hold / escalate)                    │
│  Execution env: DEVSTACK (differential testing vs real APIs)   │
│  Skills: dev/impact-predictor, dev/risk-scorer,                │
│          dev/adversarial-tester, dev/refactor-verifier         │
└────────────────────────────────────────────────────────────────┘
         ↓ (running in parallel with Loop 2)
┌────────────────────────────────────────────────────────────────┐
│                    LOOP 3: REVIEW                              │
│  PR → [Bug] [Security] [Tests] [Design] → Consensus → Merge   │
│  Skills: dev/pr-code-reviewer, dev/security-scanner,          │
│          dev/oracle-synthesizer, dev/pr-doc-generator         │
└────────────────────────────────────────────────────────────────┘
         ↓ (code merged → deployed → monitored)
┌────────────────────────────────────────────────────────────────┐
│                    LOOP 4: RELIABILITY                         │
│  ClickHouse alert → Anomaly → SQL root cause → Fix PR          │
│  Data source: CLICKHOUSE wide events via signoz-mcp            │
│  (replaces metric inference with event-level SQL proof)        │
│  Skills: dev/incident-detector, dev/root-cause-tracer,        │
│          dev/fix-proposer, dev/regression-capturer             │
└────────────────────────────────────────────────────────────────┘
```

### 4.1 Loop 1 — Build Loop (Minions-equivalent)

The Build Loop replaces and generalizes the incubator pipeline. Instead of Lovable-prototype-specific, it handles any task that arrives as a ticket, Slack message, or spec document.

**Blueprint Architecture** (from Stripe Minions — the critical insight):

```python
# skills/dev/code-builder/harness.py
from agentura.harness import Harness, AgenticNode, DeterministicNode

class CodeBuilderHarness(Harness):
    """
    Blueprint: deterministic gates ALWAYS run after LLM steps.
    The LLM cannot skip lint, test, or commit format.
    This is the core difference from SKILL.md-only approaches.
    """
    planning_mode = "linear_decomposition"
    max_pipeline_retries = 2      # Stripe's lesson: 2 max, then escalate

    pipeline = [
        AgenticNode("understand_task",
            input="ticket + repo_context",
            output="implementation_plan"),

        AgenticNode("implement_code",
            input="implementation_plan + codebase_index",
            output="code_diff"),

        DeterministicNode("lint",
            command="./gradlew detekt --auto-correct || npm run lint --fix",
            on_fail="send_to_agentic_fix_lint",
            always_runs=True),          # Cannot be skipped

        AgenticNode("fix_lint_errors",
            condition="lint_failed",
            input="lint_output + code_diff",
            output="fixed_code_diff"),

        DeterministicNode("unit_tests",
            command="./gradlew test || npm test",
            on_fail="send_to_agentic_fix_tests",
            always_runs=True),          # Cannot be skipped

        AgenticNode("fix_failing_tests",
            condition="tests_failed",
            max_iterations=2,           # Hard cap: don't spiral
            input="test_failure_output + code_diff",
            output="fixed_code_diff"),

        DeterministicNode("commit",
            command="git add -A && git commit -m '{conventional_commit}'",
            format_enforced=True,       # Conventional commits, always
            always_runs=True),

        DeterministicNode("open_pr",
            command="gh pr create --title '{title}' --body '{body}'",
            always_runs=True),
    ]

    def escalate(self, reason: str):
        """Called when max_pipeline_retries exceeded."""
        # Post to Slack, assign back to human, stop
```

**Key design principles from Minions**:
- `always_runs=True` nodes are hardcoded in the executor, not in the LLM's context
- Feedback shift-left: local lint (< 5s) always before CI
- Max 2 retry cycles. Not 3, not 4. If broken after 2, it's a human problem.
- Same devbox environment as human engineers (no special "AI environment")

**Devstack as the Build Loop execution environment**:

A Kubernetes-native local development environment (devstack pattern, see github.com/razorpay/devstack) provides the same environment as Stripe's pre-warmed devboxes. It provides a local K8s environment with the full service topology — same Postgres schema, same downstream mocks, same dependency graph — without production access.

```yaml
# agentura.config.yaml for dev/code-builder
execution_environment: isolated   # runs in devstack, not production
devstack_profile: backend         # which service fleet to spin up
pre_execution:
  - start_devstack(profile="backend", services=["service-a", "postgres", "redis"])
  - await_healthy(timeout_seconds=30)  # devstack pre-warms in ~10s
post_execution:
  - teardown_devstack()
```

This matters because DeterministicNode tests run against real devstack services:
- `./gradlew test` hits a real Postgres instance in devstack — not H2 mocks
- Integration tests call real downstream services running locally
- The agent sees the same failure modes a human engineer would see

Without devstack, agents either test against weak mocks (miss integration failures) or test against production (dangerous). Devstack is the third option that Stripe explicitly chose as the right one.

**Codebase Intelligence** (pre-execution, closes Sourcegraph gap):
```python
class CodeBuilderHarness(Harness):
    pre_execution = [
        IndexCodebase(
            type="ast_graph",       # function/class/import relationships
            scope=["src/", "app/", "lib/"],
            cache_ttl="1h",         # re-index if repo changed in last hour
            inject_as="repo_context"
        ),
        LoadRepoMemory(             # MemCoder [190] pattern
            scope="this_repo",      # repo-specific patterns from past PRs
            inject_as="repo_patterns"
        ),
    ]
```

---

### 4.2 Loop 2 — Quality Loop (PlayerZero-equivalent)

The Quality Loop predicts behavior before code ships. Two maturity tiers:

**Tier A — Imagined Execution** (achievable in Phase 2, QualityFlow [253] pattern)

LLM simulates execution step-by-step without running code. 98%+ precision on common failure modes. Cheaper than CI. Catches: null pointer paths, missing error handling, API contract violations, type mismatches.

```python
# skills/dev/impact-predictor/harness.py
class ImpactPredictorHarness(Harness):
    planning_mode = "deliberative"   # Think before acting
    execution_environment = "simulated"

    def predict_impact(self, pr_diff: str, repo_context: dict) -> ImpactReport:
        """
        LLM traces each changed function's call graph.
        Predicts: which existing tests will fail, which paths are newly uncovered,
        which API contracts may break, estimated risk tier.
        No actual test execution — imagined execution only.
        """
        return ImpactReport(
            risk_tier="low|medium|high|critical",
            predicted_test_failures=["TestPaymentFlow.testRefund"],
            uncovered_paths=["error path in line 47"],
            api_contract_changes=[],
            confidence=0.87,
        )
```

**Tier B — Behavioral Simulation** (Phase 4, PlayerZero Sim-1 direction)

A trained model (fine-tuned on our execution traces) predicts codebase behavior for a given change. Inputs: diff + repo structure + historical failure patterns. Output: probability distributions over failure modes.

This is the research angle (R7 extended): can a model trained on Agentura's execution episodes predict skill and code failures before they happen?

---

### 4.2a Testing Depth Layer — The Research Foundation

> See full analysis in `TESTING_RESEARCH.md`. Summary here.

The most important research finding for Agentura's testing layer:

> **100% code coverage but only 4% mutation score is useless.** — MUTGEN (IEEE TSE)

Coverage is the wrong signal. The right signals, in order of depth:

| Depth | What it catches | Cost | When to use |
|-------|----------------|------|------------|
| **Coverage** | Obvious crashes, null paths | Cheap | Always (DeterministicNode) |
| **Mutation score** | Behavioral equivalence failures, off-by-one | Medium | Medium+ risk changes |
| **Property-based** | Invariant violations, wide input range failures | Medium | High+ risk, API contracts |
| **Oracle synthesis** | Semantic misalignment between intent and behavior | Expensive | Money/auth/state functions |
| **Fuzzing** | Crashes, input validation, security | Expensive | API endpoints, on-demand |

**Risk-tiered routing** — the harness decides depth, not the LLM:
```python
change_risk = classify_risk(pr_diff)  # based on files touched

if change_risk == LOW:    run [coverage]
if change_risk == MEDIUM: run [coverage, mutation]
if change_risk == HIGH:   run [coverage, mutation, property]
if change_risk == CRITICAL: run [coverage, mutation, property, oracle, fuzz]
```

`CRITICAL` = payment processing, authentication, ledger entries, authorization checks.

**New skills** (see full specs in TESTING_RESEARCH.md):

- `dev/mutation-tester` — generates mutants of PR diff → generates tests to kill them → mutation score. Based on MUTGEN (arXiv:2506.02954) + Scientific Debugging (arXiv:2503.08182).
- `dev/property-tester` — 6-step PBT cycle: analyze → understand → infer invariants → synthesize Hypothesis tests → execute + triage → report. Based on Agentic PBT (arXiv:2510.09907). $9.93 per valid bug.
- `dev/oracle-synthesizer` — 4 specialist agents (correctness / robustness / security / performance) deliberate on oracle correctness → execution-grounded validation → self-refinement. Based on Nexus (arXiv:2510.26423). Bug detection 95.45%, APR success 69.32%.
- `dev/fuzz-harness-generator` — 5-agent pipeline: research → synthesis → compile repair → coverage analysis → refinement. Based on HarnessAgent (arXiv:2512.03420). 87% C / 81% C++ success rate.
- `dev/flaky-test-repairer` — dynamic call graph traversal to flakiness-inducing node → selective context injection → LLM fix. Based on FlakyGuard (ASE 2025). 47.6% repair rate.

**Convergence criteria** replace binary pass/fail:
```
tier 1 (always):  compilation ok + unit tests pass
tier 2 (medium):  mutation_score >= 0.60
tier 3 (high):    invariant_violations == 0
tier 4 (critical): fuzz_crashes == 0 + oracle_validated == true
```

**The hybrid test strategy** (arXiv:2510.25297):
- Agent EBT (example-based): 68.75% bug detection
- Agent PBT (property-based): 68.75% bug detection
- Hybrid: **81.25%** — they catch different bugs
- Agent explicitly reports "missed boundaries" → prompts targeted human test authoring for critical paths

---

### 4.3 Loop 3 — Review Loop (existing, enhanced)

Existing: 4 parallel agents (bug/security/tests/docs) → reporter.

Enhancements from competitive analysis:

**Consensus mode for BLOCKERs** (CANDOR [342] pattern, solves our severity calibration problem):
```yaml
# skills/dev/pr-code-reviewer/agentura.config.yaml
review:
  blocker_consensus_required: 2   # Two independent reviewers must both flag BLOCKER
  false_positive_penalty: true    # Track reviewers that over-escalate, down-weight them
```

**Agentic Quality Lifecycle** (Slash's next phase):
```
PR diff → dev/test-generator skill
  → Generates test cases for uncovered paths in the diff
  → Runs them in isolated devbox
  → Reports: "3 of 7 generated tests fail. Specific failures: [...]"
  → Attaches generated tests as PR artifacts (optional: auto-commit to test branch)
```

This is new. Not in v1. It closes the gap between "we reviewed the code" and "we know it works."

---

### 4.4 Loop 4 — Reliability Loop (PlayerZero SRE-equivalent)

The loop from production signal to fix PR. The key enabler is already built: canonical logging + ClickHouse gives agents SQL access to event-level evidence rather than aggregate metrics.

**The gap this closes**:

| Investigation Step | Without ClickHouse | With ClickHouse (signoz-mcp) |
|-------------------|-------------------|------------------------------|
| What is the error? | Error rate: 3.2% | `AppException: invalid write key at RudderStackService.java:196` |
| Who is affected? | Pod count: 4/4 | `uniqExact(x_user_id)` = 198 users, IN only, Android 5.2.1 |
| Did the deploy cause it? | Timestamp inference (guess) | `build_id abc123: 100% errors vs def456: 0.2%` (proof) |
| Why is it slow? | p95 latency: 1,280ms | eBPF: Postgres query scanned 450k rows — missing index |
| Suggested action | "Check external dependency" | "Fix the misconfigured environment variable in ConfigMap for build abc123" |

```
dev/incident-detector:
  Trigger: ClickHouse alert (error rate threshold) OR Datadog alert OR growth heartbeat anomaly
  Tool: signoz-mcp.triage_errors(minutes_back=15, namespace=k8s_namespace)
  Output: incident_record {
    service, error_class, error_message, stack_trace,  ← actual error, not just rate
    blast_radius: { user_count, countries, app_versions },
    onset_time
  }

dev/root-cause-tracer:
  Input: incident_record
  Tool sequence:
    1. signoz-mcp.run_sql(build_id regression query)
       → "build abc123: 100% errors, build def456: 0.2%" — PROOF not inference
    2. signoz-mcp.error_trace_join(trace_id)
       → link stack trace to span → link span to downstream latency
    3. git log --since=onset_time (if build_id regression confirmed)
       → find the commit that introduced build abc123
  Output: root_cause {
    type: "build_regression" | "config_change" | "db_degradation" | "dependency",
    evidence: { build_id, error_rate_before, error_rate_after },
    suspect_commit, suspect_file, confidence
  }

dev/fix-proposer:
  Input: root_cause
  For build_regression: generate rollback PR (revert suspect commit)
  For config_change: generate ConfigMap patch PR (e.g. update write key)
  For db_degradation: generate migration PR (e.g. add missing index)
  Routes to Loop 1 (DeterministicNode gates) before opening PR
  Output: PR url + fix_type + risk_tier + incident_summary
```

**eBPF-specific capability**: when root cause tracer finds a DB slow query via eBPF traces (Beyla/Coroot), the fix-proposer can distinguish between a code bug and an infrastructure bug:
- `avg_ms: 1,987ms + max_rows_scanned: 450,000` → missing index → migration PR
- `error: AppException + build_id regression` → code bug → rollback or forward-fix PR

Without eBPF (which the logging infrastructure already captures), the fix-proposer always defaults to code-level fixes and misses infrastructure root causes.

**Repository Readiness Score** (for external repos, Slash-equivalent):

Before running any Loop 1 agent on a repo, score it:
```
repo_readiness = {
  "context_score":    has AGENTS.md + scoped skills + documented conventions,
  "testing_score":    unit + integration coverage % + test execution time,
  "cicd_score":       automated linting + PR checks + deployment hooks,
  "agent_ready":      all three scores > 70%,
  "recommendation":   what to improve for better agent performance
}
```

Skills on repos below 70% agent-readiness carry a warning: "This repo has low test coverage. Loop 1 output will be lower confidence. Recommend improving test_score before enabling autonomous coding."

---

### 4.5 Cross-Loop Memory: The Living Model

PlayerZero calls it a "living model." Agentura's equivalent is the Cortex — but it needs to become inspectable and multi-modal. The canonical logging infrastructure provides the substrate.

```
┌──────────────────────────────────────────────────────────────────┐
│                  AGENTURA CORTEX (LIVING MODEL)                  │
│                                                                  │
│  Code layer       Execution layer       Operational layer        │
│  ──────────       ────────────          ──────────────────       │
│  Repo AST index   Episode traces        Reflexion rules          │
│  Call graphs      Step-level logs       Declarative facts        │
│  Dep graphs       Behavioral preds      Procedural patterns      │
│  Repo patterns    Failure attribution   SKILL.md patches         │
│                                                                  │
│  ← CLICKHOUSE IS THE EXECUTION LAYER STORAGE →                  │
│  Skill execution wide events stored alongside application        │
│  wide events. Same query engine. Same schema pattern.            │
│  x_skill_id, x_execution_id, x_cost_usd, x_success,             │
│  x_reflexions_injected — queryable with the same SQL.            │
│                                                                  │
│  Query: "Has anything in the payment module failed in the        │
│  last 30 days after a deploy on a Friday?"                       │
│  → Joins app wide events (ClickHouse) + skill episodes (Cortex)  │
│  → Cross-layer answer in < 2s                                    │
│                                                                  │
│  Inspectable: GET /api/v1/cortex/explain?scope=dev               │
│  Correctable: POST /api/v1/cortex/correct                        │
└──────────────────────────────────────────────────────────────────┘
```

**ClickHouse as harness telemetry** (paper §3.5 "Deep Telemetry as Optimization Substrate"):

Skill execution events route through the same Vector DaemonSet → ClickHouse pipeline as application logs. Every execution becomes a wide event:

```json
{
  "timestamp": "2026-06-03T09:15:00Z",
  "service": "agentura-executor",
  "x_skill_id": "growth/weekly-review",
  "x_execution_id": "exec-abc123",
  "x_pipeline_id": "pipe-xyz",
  "x_trigger": "heartbeat",
  "x_domain": "growth",
  "x_model": "claude-sonnet-4-6",
  "x_cost_usd": "0.11",
  "x_duration_ms": "43200",
  "x_success": "true",
  "x_tools_called": "databricks:7,slack:1",
  "x_reflexions_injected": "2",
  "x_anomalies_flagged": "1"
}
```

This means the same ClickHouse instance used for application observability serves as Agentura's harness telemetry store. No separate Langfuse instance required — the observability infrastructure you've already built handles both.

Queries that become possible:
```sql
-- Cost per domain, last 30 days
SELECT x_domain, sum(x_cost_usd), count() AS executions
FROM wide_events WHERE service = 'agentura-executor'
  AND timestamp > now() - INTERVAL 30 DAY
GROUP BY x_domain ORDER BY sum(x_cost_usd) DESC;

-- Which reflexion rules are actually helping?
SELECT x_reflexion_id,
  countIf(x_success='true') * 100.0 / count() AS utility_pct
FROM wide_events WHERE service = 'agentura-executor'
  AND x_reflexion_id != ''
GROUP BY x_reflexion_id ORDER BY utility_pct DESC;

-- Correlate skill failure with application events
SELECT e.x_skill_id, a.x_build_id, count() AS co_occurrences
FROM wide_events e JOIN wide_events a
  ON e.x_pipeline_id = a.x_txn_id  -- same transaction
WHERE e.service = 'agentura-executor' AND e.x_success = 'false'
  AND a.service != 'agentura-executor'
GROUP BY e.x_skill_id, a.x_build_id ORDER BY co_occurrences DESC;
```

The third query is especially powerful: it shows which application events (deploys, config changes, error spikes) are correlated with skill failures — automatically. This is the evidence base for the Evolution Agent's harness revision proposals.

### 4.6 Infrastructure Integration Map

```
DEVSTACK                     CLICKHOUSE + CANONICAL LOGGING
(canonical logging spec)     (observability upgrade spec)
       │                                      │
       │                                      │
       ▼                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LOOP 1: BUILD                                 │
│  dev/code-builder → spins up devstack profile                   │
│  DeterministicNode(lint) → runs in devstack (real services)     │
│  DeterministicNode(tests) → hits real Postgres in devstack      │
│  Agent sees same failures a human engineer would see            │
└──────────────────────────────────────────────────────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LOOP 2: QUALITY                               │
│  dev/refactor-verifier → runs diff tests in devstack            │
│  (real API calls, not mocks — catches semantic divergence)      │
│  dev/concolic-explorer → runs against devstack payment service  │
│  (exhaustive path coverage against real service wiring)         │
└──────────────────────────────────────────────────────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LOOP 4: RELIABILITY                           │
│  dev/incident-detector → triggered by ClickHouse alert          │
│  dev/root-cause-tracer → queries via signoz-mcp:                │
│    triage_errors() → actual stack trace, not error rate %       │
│    blast_radius() → users × country × app_version              │
│    build_regression_query() → build_id proof, not time infer.  │
│    ebpf_db_query() → rows_scanned, query latency via eBPF      │
│  dev/fix-proposer → fix type driven by root cause type:         │
│    build_regression → rollback PR                               │
│    config_change   → ConfigMap patch PR                         │
│    db_degradation  → migration PR (add index)                   │
└──────────────────────────────────────────────────────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│              CROSS-LOOP: HARNESS TELEMETRY                      │
│  Skill execution events → Vector DaemonSet → ClickHouse          │
│  Same pipeline as application logs                               │
│  x_skill_id + x_cost_usd + x_success + x_reflexions_injected    │
│  Replaces need for separate Langfuse instance                    │
│  Evolution Agent reads ClickHouse to propose SKILL.md patches   │
└──────────────────────────────────────────────────────────────────┘
```

**The three-layer architecture**:
- **Devstack** = where agents do work safely
- **ClickHouse** = what agents query for evidence + where harness telemetry lives
- **Harness v2** = what orchestrates agents and improves from the evidence

---

---

## 4. Pillar 1 — Code-First Harness Interface

### 4.1 The Problem with SKILL.md as the Harness

Today, a skill's contract lives in unstructured markdown. The LLM interprets it at runtime. This means:
- No static validation of inputs before execution
- No guaranteed output schema — downstream agents parse whatever the LLM produces
- Tool permissions are advisory (mentioned in SKILL.md) not enforced
- No execution-based verification — the harness cannot check if the skill produced correct output

### 4.2 Planning Mode Declaration [Paper §: Planning Approaches]

The full PDF distinguishes three planning modes. Skills should declare which one they use — this affects how the executor runs them and how execution traces are collected:

| Mode | When | Execution pattern |
|------|------|------------------|
| **Reactive** | Execution tasks — run SQL, post Slack, create PR | Generate → Execute → Observe error → Revise. Minimal lookahead. Current default. |
| **Deliberative** | Reasoning tasks — architecture, risk, analysis | Explore full problem space before first tool call. Maps to `CritiqueLoop` harness type. |
| **Coarse-to-fine** | Complex multi-step workflows | Decompose into sub-skill calls first, then execute each. Maps to pipeline orchestration. |

```yaml
# agentura.config.yaml
planning_mode: reactive    # reactive | deliberative | coarse_to_fine
```

This is metadata for the executor — reactive skills get standard ReAct loops (the paper's baseline), deliberative skills get critique rounds, coarse-to-fine skills get sub-skill decomposition before execution.

### 4.3 Typed Harness Contract

Each skill gets a `harness.py` (or `harness.yaml` for non-code executors) alongside SKILL.md. The harness declares:

```python
# skills/growth/weekly-review/harness.py

from agentura.harness import Harness, InputSchema, OutputSchema, ToolPermissions

class WeeklyReviewHarness(Harness):
    name = "growth/weekly-review"
    version = "2.0"

    class Input(InputSchema):
        target_date: date          # required
        regions: list[str]         # required, must be subset of KNOWN_REGIONS
        lookback_days: int = 7     # optional, default 7

    class Output(OutputSchema):
        slack_canvas_url: str      # required
        metrics_by_region: dict    # required
        anomalies: list[dict]      # required (can be empty)
        sql_queries_executed: int  # required (for cost auditing)

    tools = ToolPermissions(
        read=["databricks", "notion"],
        write=["slack"],
        deny=["gmail", "github"],   # explicit deny list
    )

    def verify(self, output: Output, input: Input) -> VerificationResult:
        """Execution-based verification — runs after skill produces output."""
        if not output.slack_canvas_url.startswith("https://app.slack.com"):
            return VerificationResult.fail("Canvas URL invalid")
        if output.sql_queries_executed == 0:
            return VerificationResult.fail("No SQL executed — likely hallucinated data")
        return VerificationResult.ok()

    def learned_verifier_features(self, input: Input) -> dict:
        """
        Features extracted from input for the learned verifier model.
        The platform runs the learned verifier BEFORE execution to predict
        likelihood of success. Low-confidence inputs are flagged for human
        review before wasting tokens on a likely-failing execution.
        [Paper §: Learned Verifiers — neural models predicting code correctness
        before execution]
        """
        return {
            "has_all_required_regions": len(input.regions) > 0,
            "target_date_is_past": input.target_date < date.today(),
            "lookback_days_reasonable": 1 <= input.lookback_days <= 30,
        }
```

**What this buys:**
- Static validation at skill invocation (bad input fails fast, before tokens spent)
- Output schema enforcement (downstream pipeline agents get typed data, not parsed markdown)
- Tool permission enforcement at the SDK level (not just prompting)
- Execution-based verification (verify() runs post-execution, before result is passed to next stage)
- **Learned verifier hook** (pre-execution confidence prediction — prevents spending tokens on inputs likely to fail)
- Machine-readable contracts for skill discovery and compatibility checking

### 4.3 HandoffArtifact — Replacing Raw Pipeline State

**The problem with PipelineContext**: passing raw stage results between agents is context compression in disguise. Each downstream agent must reconstruct intent from accumulated output. When context gets long, the model grows cautious, misses earlier constraints, and loses the original task specification.

**Anthropic's finding**: structured handoff artifacts fix this. Each stage produces a formal `HandoffArtifact` that captures *everything the next agent needs to start fresh*, not a summary of everything that happened.

```python
# platform/handoff.py — produced by every pipeline stage, read by the next

@dataclass
class HandoffArtifact:
    # Identity — never changes across stages
    pipeline_id: str
    triggered_by: str               # slack_mention | github_ci | heartbeat
    task_spec: TaskSpec             # original intent in full — NEVER compressed

    # Progress — what this stage completed
    stage: str                      # which stage produced this artifact
    completed_at: str               # ISO timestamp
    outputs: dict                   # typed outputs from this stage
    artifacts_written: list[str]    # file paths, PR URLs, Notion pages created

    # Forward contract — what the next stage must honour
    constraints: list[str]          # invariants the next agent must not violate
    open_questions: list[str]       # things the next agent must resolve
    verification_criteria: list[str]# how the evaluator judges completion

    # Cost + health
    cost_usd: float
    iterations_used: int
    escalation_risk: str            # low | medium | high

@dataclass
class TaskSpec:
    """Original task intent — unchanged from first stage to last."""
    description: str                # plain English task
    acceptance_criteria: list[str]  # what done looks like
    constraints: list[str]          # hard limits (don't touch prod, stay in feature branch)
    domain_facts: dict              # relevant DOMAIN_FACTS injected at task start
    requester: str                  # who triggered this
```

**The critical design rule** (from Anthropic's production system): the next agent reads `artifact.task_spec` to understand the original intent, `artifact.outputs` to understand progress, and `artifact.open_questions` to understand what it must resolve. It **never** reads the conversation history of the previous agent. Context resets. Intent persists.

**How this changes the incubator pipeline**:

```
spec-analyzer produces HandoffArtifact {
  task_spec: { description: "Add Stripe SCA compliance to payment flow", ... }
  outputs: { backend_spec: {...}, mobile_spec: {...} }
  open_questions: ["Which Stripe API version supports SCA in AE?", "Does iOS handle 3DS natively?"]
  verification_criteria: ["Backend compiles", "All existing tests pass", "SCA flow triggers on 3DS cards"]
}
     ↓
pit-builder reads artifact.task_spec + artifact.outputs.backend_spec
  → builds against verification_criteria (knows success conditions upfront)
  → produces HandoffArtifact { outputs: { pr_url, diff_summary, test_results } }

mobile-builder reads artifact.task_spec + artifact.outputs.mobile_spec
  → same pattern, parallel to pit-builder
     ↓
quality-gate reads BOTH pit-builder + mobile-builder HandoffArtifacts
  → checks EACH artifact's verification_criteria
  → does NOT need to re-read the whole pipeline history
     ↓
evaluator-agent (new, Anthropic pattern) reads all HandoffArtifacts
  → executes the code: runs tests, navigates the PR, checks CI status
  → produces final HandoffArtifact { verdict, next_action: merge|iterate|escalate }
```

**The evaluator agent** is the key addition from Anthropic. It is separate from all builder agents and makes no code changes — it only judges. It navigates the live output (PR, running app, test results) rather than reading static artifacts. For coding tasks: runs the tests, reads CI output, checks lint score. Its verdict drives the next iteration or terminates the pipeline.

### 4.3a Tool-Call Governance Pipeline (AutoHarness Pattern)

**The problem**: every MCP tool call today is `invoke → result`. No risk classification. No permission enforcement at call time. No output sanitization. Raw tool responses — including file paths, tokens, internal URLs, large logs — enter LLM context verbatim.

AutoHarness (open-source reference: github.com/aiming-lab/AutoHarness) implements a 6–14 step governance pipeline per tool call. Every tool call flows through it.

**V2: enforce this pipeline in the Agentura executor SDK**:

```python
# platform/executor/tool_governance.py

class ToolGovernancePipeline:
    """
    Every MCP tool call passes through all 6 steps.
    Steps 1-3 run PRE-execution. Steps 4-6 run POST-execution.
    A tool call blocked at step 3 never reaches the MCP server.
    """

    def execute(self, tool_call: ToolCall, agent_context: AgentContext) -> ToolResult:

        # STEP 1 — Parse & Validate
        validated = self.parse_and_validate(tool_call)
        # Reject malformed inputs, wrong argument types, missing required fields

        # STEP 2 — Risk Classify
        risk = self.classify_risk(validated, agent_context)
        # Patterns: rm -rf / → CRITICAL, secret in arg → BLOCK, path traversal → BLOCK
        # Prompt injection in tool args → BLOCK
        # Cross-domain data access → ESCALATE (finance skill calling growth MCP)

        # STEP 3 — Permission Check
        permitted = self.check_permissions(validated, risk, agent_context.permissions)
        # Against permissions.json: allow list, deny list, risk-tier gates
        # CRITICAL risk always requires human gate regardless of permissions

        # STEP 4 — Execute
        raw_result = self.mcp_server.call(permitted)

        # STEP 5 — Output Sanitize  ← NEW: not in our current executor
        clean_result = self.sanitize_output(raw_result, agent_context)
        # Strip: credentials, tokens, file paths outside declared scope
        # Compact: logs > 2KB → compress to key lines + link to full log
        # Redact: PII fields from API responses (governed by DOMAIN.md rules)
        # Finance domain: never pass P&L numbers through verbatim → structured summary only

        # STEP 6 — Audit Log
        self.audit_log.append(AuditEntry(
            tool=tool_call.name,
            args_hash=hash(str(tool_call.args)),   # hash, not raw args (secrets)
            risk_level=risk,
            permitted=permitted is not None,
            result_size_bytes=len(str(clean_result)),
            agent_id=agent_context.agent_id,
            pipeline_id=agent_context.pipeline_id,
            timestamp=now_utc()
        ))

        return clean_result
```

**Three governance modes** (matching AutoHarness):

| Mode | Steps | When |
|------|-------|------|
| `core` | 6-step | Single-domain specialist skills (PM, Growth) |
| `standard` | 8-step (+ pre/post hooks) | Agent skills with file I/O and git |
| `enhanced` | 14-step (+ turn governor, alias resolution) | Multi-agent pipelines, finance/compliance |

Finance and compliance skills always run `enhanced`. Development skills run `standard`. Manager/classifier skills run `core`.

**The output sanitize step specifically** — what gets stripped and why:

```python
SANITIZE_RULES = {
    "databricks": {
        "strip": ["cluster_id", "workspace_url", "token"],
        "compact_if_rows_gt": 1000,    # → return first 50 + "... (950 more rows)"
        "redact": ["user_email", "user_id"],
    },
    "slack": {
        "strip": ["bot_token", "webhook_url"],
        "compact_messages_gt": 20,     # → return last 20 messages
    },
    "notion": {
        "strip": ["api_key", "workspace_id"],
        "redact_if_domain": "finance",  # strip P&L, salaries from finance skill responses
    },
    "github": {
        "strip": ["access_token", "ssh_key"],
        "compact_diff_lines_gt": 500,  # → diff summary + link to full diff
    },
}
```

**Adopt AutoHarness as the executor governance layer** rather than building from scratch. It wraps any client with two lines and is MIT licensed. Study the Enhanced mode patterns (informed by Claude Code's architecture) as the reference implementation.

### 4.3b Dry-Run Mode (OpenHarness Pattern)

Before a skill runs in production, `agentura dry-run <skill>` resolves and prints everything without executing:

```bash
$ agentura dry-run skills/finance/invoice-processor

DRY RUN — skills/finance/invoice-processor
──────────────────────────────────────────
Model:        claude-sonnet-4-6 (via LiteLLM → Anthropic)
Budget:       $0.50 max per execution
Planning:     reactive
Env:          integrated  ← writes to production systems

Context injected:
  SKILL.md              2,847 tokens  [cached ✓]
  SOUL.md                 412 tokens  [cached ✓]
  DOMAIN_FACTS.yaml       891 tokens  [cached ✓]
  Top reflexions (3)      234 tokens
  Top episodes (2)        312 tokens
  ──────────────────────────────────
  Total context         4,696 tokens  ($0.014 at cache hit rate)

Tools permitted (standard governance):
  ✓ gmail.search         (read, dedicated bot email inbox)
  ✓ notion.fetch         (read, vendor-registry)
  ✓ notion.create_page   (write, invoice-log)
  ✓ slack.post_message   (write, #wg-asap-agent-pilot)
  ✗ gmail.send           (BLOCKED — not in allow list)
  ✗ databricks.*         (BLOCKED — not declared in environment.yaml)

Invariants declared:
  vendor must exist in vendor-registry before invoice is processed
  invoice total must match extracted line items within 2%

Handoff outputs expected:
  invoice_record: InvoiceRecord (typed)
  slack_summary: str
  approval_required: bool

Readiness score: 68 / 100  ← WARNING: below Agent Ready threshold (75)
  Context:    22/30  (missing harness.py — implicit contract only)
  Execution:  28/40  (12 episodes, 75% success rate)
  Feedback:   18/30  (1 reflexion rule, no evals yet)

Recommendation: add harness.py with typed I/O before enabling autonomous mode.
```

This single command replaces production discovery of misconfigurations. Engineers can verify skill state before enabling autonomous execution.

### 4.5 Execution Environment Classification [Paper §: Execution Environment Taxonomy]

The paper classifies execution environments into three types. Every Agentura skill falls into exactly one:

| Type | Paper definition | Agentura mapping | Risk level |
|------|----------------|-----------------|-----------|
| **Isolated** | Sandboxed execution, timeouts, resource limits | Claude Code executor pod — file I/O, git, tests | Medium — reversible within the sandbox |
| **Integrated** | Live API calls to real external systems | PTC executor — Slack, Notion, Databricks, Gmail | High — writes to production systems |
| **Simulated** | Synthetic/fixture task environments | Eval runner against `fixtures/` | None — safe for CI |

This classification belongs in `agentura.config.yaml`:
```yaml
executor: claude-code
execution_environment: isolated   # isolated | integrated | simulated
```

The executor uses this to:
- Set appropriate timeouts and resource limits per type
- Apply stricter `permissions.json` for Integrated skills (no exploratory bash)
- Route Simulated runs to the eval runner, never to production MCP servers

### 4.6 Environment Modeling

Each skill declares its world model — the systems it reads and writes, and the invariants it assumes:

```yaml
# skills/finance/invoice-processor/environment.yaml
reads:
  - system: gmail
    scope: "dedicated bot email inbox"
    staleness_tolerance: 1h
  - system: notion
    scope: "vendor-registry database"
    staleness_tolerance: 24h
writes:
  - system: notion
    scope: "invoice-log database"
  - system: slack
    scope: "#wg-asap-agent-pilot"
invariants:
  - "vendor must exist in vendor-registry before invoice is processed"
  - "invoice total must match extracted line items within 2%"
```

This enables:
- Pre-flight checks before execution (is Gmail accessible? is Notion reachable?)
- Post-execution audit (did the skill only touch declared systems?)
- Dependency graph generation (which skills must run before this one?)

---

## 5. Pillar 2 — Memory Architecture v2

### 5.1 Current State

MemRL v1 has one layer: **reflexion rules** (procedural, failure-derived, Bayesian scored). It synthesizes patterns from failures. It decays stale rules. It injects top-K rules at skill execution time.

**MemRL v1 blind spot — binary scoring** [Paper §: Execution Trace Rewards]:

The paper argues for step-level trace rewards, not just end-result scoring. Currently MemRL records: execution passed/failed. But in a 7-step skill, knowing "step 4 (Databricks query) returned empty, step 5 (Slack post) was skipped" is far more actionable than knowing the whole execution failed.

**V2 trace format:**
```json
{
  "execution_id": "exec-abc123",
  "skill": "growth/weekly-review",
  "steps": [
    {"step": 1, "tool": "databricks", "query_id": "Q1", "result": "ok", "rows_returned": 847},
    {"step": 2, "tool": "databricks", "query_id": "Q2", "result": "ok", "rows_returned": 0},
    {"step": 3, "tool": "databricks", "query_id": "Q3", "result": "error", "error": "timeout after 30s"},
    {"step": 4, "tool": "slack", "result": "skipped", "reason": "upstream_error"}
  ],
  "failure_step": 3,
  "failure_type": "tool_timeout",
  "overall": "failed"
}
```

Reflexion synthesis now operates at step level: "Step 3 Databricks Q3 fails 60% of the time on Tuesdays between 14:00–16:00 UTC. Avoid or add retry logic." This is higher precision than "weekly-review fails on Tuesdays."

This is necessary but insufficient. A mature agent needs four memory layers.

### 5.2 Four-Layer Memory Model

```
┌─────────────────────────────────────────────────────────────┐
│                    CORTEX MEMORY v2                         │
│                                                             │
│  Layer 4: REFLEXION    "Don't query Databricks at 3am UTC"  │
│  (current MemRL)       Failure-derived, decaying, scored    │
│                                                             │
│  Layer 3: PROCEDURAL   "Weekly review always runs SQL A,    │
│  (learned workflows)    then SQL B, then posts canvas"      │
│                        Sequence templates learned from      │
│                        successful executions                │
│                                                             │
│  Layer 2: DECLARATIVE  "Vendor Stripe uses JP Morgan bank"    │
│  (domain facts)        "Region AU launched 2025-11-03"     │
│                        Structured facts, human-authored     │
│                        or agent-extracted, versioned        │
│                                                             │
│  Layer 1: EPISODIC     "On 2026-05-15, weekly-review ran   │
│  (execution traces)     with input {regions: [AE, GB]},    │
│                         took 4m, cost $0.12, output: ..."  │
│                        Compressed summaries of past runs   │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Episodic Memory

**What it is**: Compressed summaries of every skill execution — inputs, outputs, cost, duration, tool calls made, verification result.

**Why it matters**: An agent that ran `weekly-review` 100 times has far more context than one running cold. Episodic memory is how the agent knows "last Tuesday we had a Databricks outage at 2pm" without a human telling it.

**Implementation**:
```
POST /api/v1/cortex/episode
{
  "skill": "growth/weekly-review",
  "execution_id": "exec-abc123",
  "input_hash": "sha256:...",
  "input_summary": "target_date=2026-05-13, regions=[AE,GB,EUR,US,CA]",
  "output_summary": "AE NTU -8% WoW (anomaly), all other regions green. Canvas posted.",
  "tool_calls": [{"tool": "databricks", "count": 7}, {"tool": "slack", "count": 1}],
  "duration_seconds": 243,
  "cost_usd": 0.11,
  "verification": "ok",
  "anomalies_flagged": 1
}
```

At next execution, top-K relevant episodes are injected: "Last 3 times you ran this skill: [summaries]"

**Retrieval strategy — problem-structure similarity, not recency** [Paper §: Exemplar Selection]:

The paper demonstrates that exemplar selection by problem structure similarity outperforms temporal or generic semantic similarity. For Agentura, this means:

```python
def score_episode_relevance(episode: Episode, current_input: dict) -> float:
    # Structure match: same input schema shape? (highest weight)
    schema_match = jaccard(episode.input_keys, current_input.keys())

    # Tool match: same MCP tools used in the episode?
    tool_match = jaccard(episode.tools_used, skill_config.tools)

    # Context match: same domain, trigger type, day-of-week
    context_match = (
        0.4 * (episode.trigger == current_trigger) +
        0.3 * (episode.day_of_week == current_day_of_week) +
        0.3 * semantic_similarity(episode.input_summary, current_input_summary)
    )

    return 0.5 * schema_match + 0.3 * tool_match + 0.2 * context_match
```

Recency is a tiebreaker only. A structurally similar episode from 3 months ago beats a recent but structurally different one.

### 5.4 Declarative Memory

**What it is**: Structured domain facts that skills should know but cannot derive from tool calls alone.

**Why it matters**: Skills currently re-discover facts from raw tool outputs every run. "Which bank does vendor X use?" shouldn't require a Notion query every time — it should be a pre-loaded fact.

**Implementation**: `DOMAIN_FACTS.yaml` per domain, version-controlled, loaded at skill startup:

```yaml
# skills/finance/DOMAIN_FACTS.yaml
vendors:
  stripe:
    bank: JP Morgan
    entity: "Company US Ltd"
    agreement_expiry: 2026-12-31
  adyen:
    bank: Barclays
    entity: "Company UK Ltd"
    agreement_expiry: 2027-03-15

regions:
  AE:
    currency: AED
    launched: 2024-06-01
    tier: primary
  AU:
    currency: AUD
    launched: 2025-11-03
    tier: emerging
```

Agent-extracted declarative facts (found during skill execution and marked as "stable knowledge") are written back with human approval via a `POST /api/v1/cortex/declare` endpoint.

### 5.5 Procedural Memory

**What it is**: Successful execution sequences, learned from episodic traces, distilled into reusable step templates.

**Why it matters**: When a skill succeeds consistently with a particular tool call sequence, that sequence should become the default plan — not re-derived from the prompt each time.

**Implementation**: Procedural synthesis runs alongside reflexion synthesis in the daily CronJob:

```
synthesize_procedures():
  1. Find skills with ≥10 successful executions
  2. Extract tool call sequences from episodic traces (ordered list)
  3. Cluster similar sequences (edit distance on tool call names)
  4. Most frequent cluster → candidate procedure
  5. Store as: { "skill": "growth/weekly-review", "procedure": ["sql.query(A)", "sql.query(B)", "slack.canvas_update()"], "confidence": 0.87 }
```

At execution time, the agent is told: "Past successful runs followed this sequence: [procedure]. Deviate only if context requires."

### 5.6 Self-Improving Skills

The highest-leverage capability: reflexion rules that are strong enough (confidence > 0.8, utility > 0.7, confirmed > 5 times) get proposed as SKILL.md patches.

```
MemRL maintenance CronJob:
  → For each skill:
      → Collect top reflexions (confidence > 0.8, utility > 0.7)
      → LLM generates: "Here is a proposed change to the SKILL.md based on
         learned patterns: [diff]"
      → Creates GitHub PR to agentura-skills repo
      → PR description: which executions triggered the reflexion,
         utility scores, proposed wording change
      → Human reviews + merges → skill improved permanently
```

This closes the loop: execution → failure → synthesis → reflexion → confirmed → skill patch → better execution.

---

## 6. Pillar 3 — Skills at Scale

### 6.1 Skill Readiness Framework

Inspired by Razorpay's repo readiness scoring. Every skill is scored on three dimensions:

**Context Score (0–100)**
- Has `harness.py` with typed I/O contract: +30
- Has `DOMAIN_FACTS.yaml` with ≥5 facts: +20
- Has `environment.yaml` declared: +20
- Has ≥3 fixture inputs in `fixtures/`: +15
- Has `SOUL.md` (for agent-type skills): +15

**Execution Score (0–100)**
- ≥10 episodic traces in memory: +25
- Last 10 executions: success rate ×40
- Average verification.ok() rate ×35

**Feedback Score (0–100)**
- ≥1 reflexion rule applied (utility > 0.5): +20
- ≥1 declarative fact contributed back: +20
- ≥1 eval defined in `evals/`: +30
- User-submitted correction applied: +30

**Agent Ready threshold: 75+ across all three.**

Skills below 75 are flagged in the weekly platform digest. Skills above 90 are "Elite" — their patterns are candidates for cross-domain knowledge transfer.

### 6.2 Cross-Skill Knowledge Graph (Discover)

The Razorpay insight that matters most: the knowledge graph is what makes an agent organization-aware, not just skill-aware.

**Phase 1 — Execution-aware search**
Index all episodic memory across all skills. Query: "Has any skill ever encountered vendor X refusing a payment?" → returns episodic traces from finance skills, ECM skills, and support skills that match.

**Phase 2 — Cross-system search**
Index: Slack threads (via MCP), Notion pages (via MCP), GitHub PRs and comments, Databricks query history, skill execution summaries.

Query interface:
```
GET /api/v1/discover?q=what+did+we+learn+about+Databricks+outages+in+2026
→ Returns: ranked results from episodic memory + Slack threads + GitHub issues
```

**Phase 3 — Proactive injection**
Before executing a skill, the platform runs a Discover query against the skill's input. Relevant results are injected into context:

```
"Before you run: relevant context from organizational memory:
 - Finance skill (2026-04-12): Vendor Stripe payment rejected due to 3DS mismatch
 - Slack #team-growth (2026-05-01): Databricks cluster maintenance 2-4am UTC Tuesdays
 - GitHub PR #244: invoice-processor updated to handle multi-currency invoices"
```

### 6.3 Skill Contribution Flywheel

Razorpay's Slash grew from a core team's catalog to hundreds of skills contributed by engineers across the org. The mechanism: making contribution frictionless.

**Scaffold generator**:
```bash
agentura create skill --domain finance --name vendor-reconciler
# → Creates: SKILL.md template, harness.py skeleton, environment.yaml, fixtures/ dir
# → Asks 5 questions: trigger, tools needed, input shape, output shape, verification rule
# → Generates first draft SKILL.md from answers
```

**Skill validation gate** (CI on agentura-skills repo):
- Schema validation of harness.py and agentura.config.yaml
- Fixture execution: run skill against all files in `fixtures/` and check output matches expected schema
- Readiness score calculated and posted as PR comment
- Skills below 50 readiness cannot merge

**Skill marketplace** (internal):
- `GET /api/v1/skills/catalog` → browsable, searchable index
- Skills tagged by domain, trigger type, tool dependencies, readiness score
- Usage metrics: how many times invoked, average cost, average success rate

---

## 7. Evaluation Framework

The paper (arXiv:2605.18747) identifies evaluation beyond task completion as an open problem. Here is the v2 answer:

### 7.1 Skill Quality Metrics

| Metric | Definition | Measured How |
|--------|-----------|-------------|
| **Task Success Rate** | % executions passing verification | harness.verify() result |
| **Output Precision** | % output fields matching declared schema | Automated schema check |
| **Cost Efficiency** | Cost per successful execution (USD) | episodic trace |
| **Latency P95** | 95th percentile execution time | episodic trace |
| **Tool Accuracy** | % of tool calls that returned useful data | Flagged in traces when tools return empty/error |
| **Reflexion Utility** | Average utility score of active reflexions | MemRL scorer |
| **Human Override Rate** | % of executions where human corrected output | Correction pipeline |
| **Freshness** | Days since last successful execution | episodic trace |

### 7.2 Regression Prevention

When a SKILL.md patch (from self-improvement) is proposed:
1. Run the skill against all `fixtures/` with the new prompt
2. Compare output quality score against baseline (pre-patch)
3. If any fixture regresses (quality drops > 10%), block the PR
4. If all fixtures pass or improve, mark PR as "regression-safe"

### 7.3 Eval-as-Code

Each skill gets an `evals/` directory with declarative evaluation cases:

```yaml
# skills/growth/weekly-review/evals/normal-week.yaml
input:
  target_date: "2026-05-13"
  regions: ["AE", "GB", "EUR"]
expected:
  slack_canvas_url: present
  metrics_by_region:
    AE: present
    GB: present
    EUR: present
  anomalies: list  # can be empty — structural check only
  sql_queries_executed: ">= 3"
verification: strict_schema
```

Evals run in CI on every SKILL.md change and on a weekly cadence against production to catch drift.

---

## 8. Research Angles

These are the v2 capabilities that are novel enough to constitute research contributions:

### R1: MemRL with Contextual Bandits
Current MemRL uses Bayesian scoring. V2 upgrade: contextual multi-armed bandit where the context is the skill input features (domain, day-of-week, region set, trigger type). The bandit learns which reflexion rules are useful in which contexts, not just globally.

**Research question**: Does context-conditioned reflexion injection outperform global top-K injection? Metric: task success rate, cost-per-success.

### R2: Procedure Synthesis from Episodic Traces
Learning reusable tool call sequences from successful execution histories — unsupervised, from production data.

**Research question**: Do synthesized procedures reduce execution cost and latency without hurting success rate? (Hypothesis: yes, because the agent spends fewer tokens exploring the tool space.)

### R3: Cross-Skill Knowledge Transfer
Can declarative facts and procedural patterns from one domain inform skills in another? Specifically: can finance domain learnings about vendor behavior improve ECM domain skills that interact with the same vendors?

**Research question**: What is the transfer efficiency (measured in reduction of error rate) for cross-domain knowledge injection vs. domain-isolated memory?

### R4: Harness Self-Improvement Loop
The full loop: execution → failure → reflexion → confirmed → SKILL.md patch → regression test → merge.

**Research question**: Over 90 days with self-improvement enabled, does skill quality (precision + success rate + cost) converge upward? What is the failure rate of proposed patches (regression-introducing patches that should have been blocked)?

### R5: Code-as-Harness vs. Prompt-as-Harness
Run the same underlying skill with SKILL.md-only (current) vs. SKILL.md + harness.py (v2). Measure: success rate, output schema compliance, hallucination rate (outputs that don't match declared schema), cost.

**Hypothesis**: harness.py enforcement reduces hallucination rate by >30% at equal or lower cost.

### R6: Critique Loop Calibration (from Shopify pattern)
Force the agent to critique its own output N rounds before delivering. Does this produce better reasoning-task outputs? Does the agent's self-assessed confidence score calibrate to actual correctness?

**Research question**: What is the optimal critique round count (1, 2, 3) for reasoning tasks before returns diminish? What is the cost/quality trade-off per round?

**Metric**: Human expert rating of output quality (1–5), cost per execution, confidence calibration (predicted confidence vs. actual correctness across 50 tasks).

### R7: Learned Verifier Pre-Execution Filtering [Paper §: Learned Verifiers]

The paper cites neural models that *predict* whether generated code/output will be correct *before* running it. Applied to Agentura: train a lightweight classifier on historical execution features (input schema completeness, tool availability, day-of-week, domain) to predict execution success probability.

**Research question**: Can a learned verifier trained on 500+ episodic traces predict execution failure with >70% precision? At what confidence threshold does gating executions (requiring human review before running) produce net cost savings vs. just letting executions fail?

**Metric**: Verifier precision/recall on held-out execution history. Cost delta between ungated and gated execution across a 30-day window.

### R8: Mutation Score as Merge Gate

**Research question**: Does requiring mutation score ≥ 0.6 before merge reduce post-merge defect rate? What is the cost (PR cycle time, token cost) vs. benefit (defects caught) trade-off at each threshold (0.4, 0.6, 0.8)?

**Hypothesis**: mutation-gated merges reduce post-merge defects by >30% vs coverage-only gates, with < 20% increase in PR cycle time for medium-risk changes.

### R9: PBT + EBT Hybrid Detection Rate on Agentura Skills

The PBT + EBT research (arXiv:2510.25297) shows 81.25% combined detection vs 68.75% for either alone — on HumanEval benchmarks. Does this hold for enterprise business logic (payment processing, ledger entries, currency conversion)?

**Research question**: On Agentura's finance and backend skills, does the PBT + EBT hybrid achieve meaningfully higher bug detection than coverage-only tests? Measured on 30 deliberately introduced defects.

### R10: Oracle Quality vs. Test Quantity

**Research question**: Is one Nexus-quality oracle more valuable than 10 coverage-optimized test cases? Measured by bug detection rate on a controlled defect set.

**Hypothesis**: Nexus-style oracle synthesis on payment functions catches more real bugs per token spent than coverage-based test generation, above a minimum test count threshold.

---

## 9. Implementation Roadmap

**Sequencing principle**: SDLC harness reliability first. Every phase has a primary SDLC deliverable and a secondary multi-domain deliverable. Never the reverse.

---

### Phase 0 — Platform Foundation (2 weeks)
*Goal: Baseline reliability infrastructure before any new features*

**SDLC (primary)**:
- [ ] Deploy LiteLLM as model routing gateway (replaces direct Anthropic calls)
- [ ] Route skill execution wide events through Vector → ClickHouse (same pipeline as application logs) — replaces Langfuse as separate telemetry store
- [ ] Implement 6-step tool governance pipeline in executor SDK (AutoHarness pattern: parse → risk classify → permission check → execute → output sanitize → audit log)
- [ ] Implement output sanitization rules per MCP server (strip credentials, compact large responses, redact PII per domain rules)
- [ ] Implement `permissions.json` enforcement (bash-level guardrails replacing advisory environment.yaml)
- [ ] Design `harness.py` with `AgenticNode` + `DeterministicNode` types
- [ ] Implement planning_mode + execution_environment fields in agentura.config.yaml
- [ ] Add prompt caching (`cache_control: ephemeral`) to SKILL.md + DOMAIN_FACTS.yaml system prompt blocks (90% cost reduction on repeated executions)
- [ ] Connect `dev/incident-detector` to signoz-mcp (already built) — replace Datadog metrics proxy with ClickHouse event queries

**Multi-domain (secondary)**:
- [ ] Replace `PipelineContext` JSON blob with typed `HandoffArtifact` (Anthropic three-agent pattern: task_spec + progress + constraints + open_questions + verification_criteria)
- [ ] Add `evaluator-agent` role to pipeline topology: separate agent that executes and judges output, never produces it
- [ ] Implement `agentura dry-run <skill>` command (resolves context, tools, permissions, readiness score without executing — OpenHarness pattern)
- [ ] Define `environment.yaml` spec

**Done when**: Skill execution events visible in ClickHouse alongside application logs. `incident-detector` returns stack trace + blast radius, not just error rate. Every tool call passes through governance pipeline. Prompt caching active on all heartbeat skills.

---

### Phase 1 — Build Loop (3 weeks)
*Goal: Minions-equivalent coding capability. Deterministic gates always fire.*

**SDLC (primary)**:
- [ ] `DeterministicNode` implemented in executor (runs regardless of LLM state)
- [ ] Devstack integration: `dev/code-builder` spins up devstack profile before running, tears down after — agents test against real services in isolation
- [ ] Blueprint for pit-builder: implement → lint gate → test gate (devstack) → commit → PR
- [ ] Blueprint for mobile-builder: same pattern for Kotlin/Compose
- [ ] Max 2 retry budget per pipeline (hard cap, escalate after)
- [ ] AST-based codebase pre-indexing for isolated-environment skills
- [ ] `dev/spec-analyzer` generalized: accept Jira ticket, Slack thread, or doc → structured spec
- [ ] `dev/code-builder` generalized: any spec → code diff (not just incubator use case)

**Multi-domain (secondary)**:
- [ ] Implement episodic trace recording (POST /api/v1/cortex/episode)
- [ ] Implement DOMAIN_FACTS.yaml loading with quality gate (MemGovern pattern)

**Done when**: A Jira ticket can trigger `dev/code-builder`, produce a diff, pass lint + test gates deterministically, and open a PR. CI pass rate on agent PRs measurably higher than v1.

---

### Phase 2 — Quality + Review Loop (3 weeks)
*Goal: PlayerZero Tier A (imagined execution) + enhanced review pipeline*

**SDLC (primary)**:
- [ ] `dev/risk-scorer` skill: classify change risk (low/medium/high/critical) based on diff content + files touched
- [ ] Risk-tiered test routing: harness routes to test depth based on risk_tier (not LLM judgment)
- [ ] `dev/impact-predictor` skill: LLM-simulated execution on PR diffs (QualityFlow [253] pattern)
- [ ] Assertion strength gate (harness gate, 2h effort): reject tests with null-checks/trivially-true assertions — `assertNotNull` is not a guard (arXiv:2602.07900)
- [ ] `dev/mutant-prioritizer` skill: ML ranking of mutants via subsumption graph before generation (PRIMG, arXiv:2505.05584)
- [ ] `dev/adversarial-tester` skill: Test Agent vs Mutant Agent co-evolution, 63.30% better than EvoSuite (AdverTest, arXiv:2602.08146)
- [ ] Convergence criteria v2: tier 1 always + tier 2 mutation_score≥0.6 for medium+ + tier 3-4 for critical
- [ ] `dev/stale-test-detector` skill: find tests that pass but no longer validate current behavior (TEBench, arXiv:2605.06125)
- [ ] `dev/refactor-verifier` skill: differential fuzzing on refactor PRs — 19-35% LLM refactorings are semantically wrong (arXiv:2602.15761)
- [ ] `dev/property-tester` skill: 6-step PBT + doc-oracle mode using DOMAIN_FACTS.yaml (arXiv:2510.09907 + 2602.10471)
- [ ] `dev/oracle-synthesizer` skill: 4-agent deliberation for money/auth/state functions (Nexus, arXiv:2510.26423)
- [ ] `dev/security-scanner` skill: multi-agent SAST + LLM false positive triage (Argus, arXiv:2604.06633)
- [ ] Consensus mode for BLOCKERs: 2 independent reviewers must agree (CANDOR [342] pattern)
- [ ] Repository readiness score: context + testing + CICD axes for external repos
- [ ] `GET /api/v1/cortex/explain` endpoint (memory transparency — make MemRL inspectable)

**Multi-domain (secondary)**:
- [ ] Implement Skill Readiness Score calculator
- [ ] Build scaffold generator (`agentura create skill`)
- [ ] Add CI validation gate to agentura-skills repo
- [ ] Episodic retrieval with abstract state scoring (Synapse [414] pattern)

**Done when**: Risk classification fires on every PR. Mutation score reported alongside coverage. Property tester finds at least 1 real invariant violation in first 10 real PRs. Engineers can query `/cortex/explain` for any skill.

---

### Phase 3 — Reliability Loop + Self-Improvement (3 weeks)
*Goal: PlayerZero SRE-equivalent + harness self-improvement*

**SDLC (primary)**:
- [ ] `dev/incident-detector` skill: triggered by monitoring alerts + growth anomalies
- [ ] `dev/root-cause-tracer` skill: anomaly → git log → suspect commit + file
- [ ] `dev/fix-proposer` skill: root cause → rollback PR or forward-fix PR
- [ ] Reliability loop connected end-to-end: alert fires → PR proposed in < 10 minutes
- [ ] `dev/flaky-test-repairer` skill: dynamic call graph traversal → selective context → fix (FlakyGuard, arXiv:2511.14002)
- [ ] Flaky test detection: re-run policy (3x on fail) → quarantine if inconsistent → trigger repairer
- [ ] `dev/regression-capturer` skill: auto-generate regression test from every merged bug fix, <3min (arXiv:2501.11086)
- [ ] `dev/fuzz-harness-generator` skill: 5-agent pipeline for API endpoint fuzzing (HarnessAgent, arXiv:2512.03420)
- [ ] `dev/concolic-explorer` skill: LLM-guided concolic execution for CRITICAL-tier financial code paths (arXiv:2601.12274)
- [ ] Transactional execution for finance/compliance skills (`[389]` pattern)
- [ ] Step-level trace rewards in MemRL (which step failed, not just whole execution)

**Multi-domain (secondary)**:
- [ ] Reflexion → SKILL.md patch generation (Evolution Agent)
- [ ] Regression test gate (fixture-based, blocks regressing patches)
- [ ] GitHub PR creation from maintenance CronJob
- [ ] PlugMem [417] propositional/prescriptive fact separation
- [ ] TALM [191] consolidation step in MemRL maintenance

**Done when**: One production alert (from growth heartbeat or Datadog) triggers the reliability loop and produces a fix PR in < 10 minutes with root cause identified.

---

### Phase 4 — Discover + Behavioral Simulation + Research (ongoing)
*Goal: Knowledge graph + PlayerZero Tier B simulation + R1–R8 experiments*

**SDLC (primary)**:
- [ ] Discover v1: search over episodic memory (cross-skill, cross-domain)
- [ ] Discover v2: index Slack, Notion, GitHub, execution summaries
- [ ] Behavioral simulation model (fine-tuned on execution traces): Sim-1 analogue
- [ ] Proactive context injection pre-execution from Discover
- [ ] Instrument all metrics for R1–R8 research questions
- [ ] Controlled experiments: v1 vs v2 on same skills, v1 harness vs blueprint harness

**Multi-domain (secondary)**:
- [ ] Cross-domain knowledge transfer (finance → dev for shared vendor context)
- [ ] Skill marketplace with usage metrics
- [ ] Workflow topology optimization (SEW [312] pattern)

**Done when**: Discover query answers "has any skill hit this failure pattern?" in < 2s. Behavioral simulation predicts skill failures with measurable precision (target: > 65%).

---

### Roadmap Summary

| Phase | Duration | Primary Deliverable | SDLC Loop |
|-------|----------|--------------------|-----------|
| 0 | 2w | Tool governance pipeline + HandoffArtifact + dry-run + prompt cache | Foundation |
| 1 | 3w | Build Loop: blueprint coding with hard gates + evaluator agent | Loop 1 |
| 2 | 3w | Quality Loop: imagined execution + risk-tiered testing + repo readiness | Loop 2 + 3 |
| 3 | 3w | Reliability Loop: alert → fix PR + regression capturer + self-improvement | Loop 4 |
| 4 | ongoing | Discover + behavioral simulation + research | All loops |

---

## 10. What This Is Not

To keep scope honest:

- **Not an LLM training project.** We are not fine-tuning models. All improvements are harness-level: better context, better contracts, better feedback loops.
- **Not a general-purpose agent framework.** This is Agentura-specific. The primitives (SKILL.md, SOUL.md, HEARTBEAT.md) are preserved. We are adding typed contracts on top, not replacing the execution model.
- **Not replacing human judgment.** Self-improvement proposes patches. Humans merge them. The human is never removed from safety-critical decisions. Finance and compliance skills always have human-in-the-loop on outbound actions.
- **Not starting from scratch.** Every v2 capability is additive. v1 skills continue to work without harness.py. The readiness score just tells you which ones to upgrade first.

---

## 11. Shopify Production Patterns — What's New vs. Already Covered

Shopify's 23,000-engineer AI playbook (Bessemer, 2026) adds three things to the v2 plan that were not there. Everything else they describe either maps to something Agentura already does or is addressed in Pillars 1–3.

### Already Covered

| Shopify Pattern | Agentura Equivalent |
|----------------|-------------------|
| Parallel agents in separate terminals | Pipeline parallel dispatch (PTC + Claude Code pods) |
| MCP servers for internal systems | 15+ MCP servers in production |
| CLAUDE.md as team infrastructure | SOUL.md + DOMAIN.md committed to git |
| Agents can read/write/test/commit, cannot push/deploy | environment.yaml tool permissions (advisory) |

### Genuinely New — Three Additions

#### 11.1 LLM Gateway Layer (Platform-Level)

Shopify's most important infrastructure decision: a centralized LLM proxy that sits between all engineering tools and all AI providers. Every Claude Code, Copilot, and Cursor request routes through one gateway.

**What it provides:**
- Cost control: per-team/per-skill token budgets enforced at the gateway, not in the skill
- Usage analytics: which skills cost the most, which models perform best per dollar, daily/weekly burn rate
- Model routing: swap Claude Sonnet → Haiku for a skill class without touching SKILL.md
- Data residency enforcement: route sensitive domains to models with zero-retention guarantees

**Agentura v2 implementation:**
```yaml
# gateway/config/model-routing.yaml
routes:
  - match:
      domain: finance
      skill_role: specialist
    target: claude-haiku-4-5          # cheap for structured extraction
    zero_retention: true               # no training data use

  - match:
      domain: growth
      skill_role: agent
    target: claude-sonnet-4-6
    budget_per_execution_usd: 0.50    # enforced at gateway level

  - match:
      trigger: heartbeat
    target: claude-haiku-4-5          # all scheduled work on cheapest model

  - match:
      skill_role: manager             # classifiers
    target: claude-haiku-4-5
    budget_per_execution_usd: 0.02
```

**New endpoint:**
```
GET /api/v1/platform/cost-report?period=7d
→ {
    "total_usd": 47.23,
    "by_domain": { "growth": 18.40, "pm": 12.10, "finance": 9.80, ... },
    "by_model": { "sonnet-4-6": 38.10, "haiku-4-5": 9.13 },
    "by_skill": [ { "skill": "growth/weekly-review", "usd": 11.20, "executions": 28 }, ... ],
    "p95_cost_per_execution": 0.42
  }
```

This belongs in Phase 0 — it is infrastructure, not a feature. Without it, you cannot make evidence-based model selection decisions for R1–R5 experiments.

#### 11.2 Bash-Level Execution Guardrails

Shopify's permissions config is operational, not advisory. It enforces at the shell level what commands a Claude Code agent can run. This is stronger than `environment.yaml` (which declares intent) — it is a wall, not a suggestion.

**V2: `permissions.json` per executor pod, enforced by the harness SDK:**

```json
{
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "LS", "Edit", "Write",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(dev test *)",
      "Bash(dev style *)",
      "Bash(mvn test *)",
      "Bash(./gradlew test *)",
      "Bash(kubectl get *)",
      "Bash(kubectl describe *)",
      "Bash(kubectl logs *)"
    ],
    "deny": [
      "Read(**/.env*)",
      "Read(**/secrets*)",
      "Bash(git push *)",
      "Bash(git force-push *)",
      "Bash(kubectl delete *)",
      "Bash(kubectl apply *)",
      "Bash(rm -rf *)",
      "Bash(dev deploy *)",
      "Bash(**/db:drop*)",
      "Bash(curl * | bash *)"
    ],
    "defaultMode": "acceptEdits"
  }
}
```

**Domain-specific overrides:** Finance skills get `Read(**/.env*)` denied AND gmail write denied. Incubator builder skills get `Bash(git push origin feat/* )` allowed (they must push feature branches). K8s-access skill gets `Bash(kubectl apply *)` allowed with explicit namespace scope.

**The distinction from environment.yaml:**
- `environment.yaml` → tells the LLM what it should do (advisory)
- `permissions.json` → tells the harness what it can do (enforced, pre-execution check)

Both are needed. The LLM reads environment.yaml for context. The harness SDK enforces permissions.json before any tool call executes.

#### 11.3 Critique Loop as a Harness Mechanism

Shopify's extended critique loop pattern — where the agent proposes, critiques, revises, critiques again, then delivers — produces dramatically better outputs for architectural and complex reasoning tasks. This is not in Pillar 1.

**V2: `CritiqueLoop` harness type** (a new skill role alongside Manager/Specialist/Agent):

```python
# skills/product/trend-researcher/harness.py
from agentura.harness import CritiqueLoopHarness

class TrendResearcherHarness(CritiqueLoopHarness):
    critique_rounds = 2          # propose → critique → revise → critique → final
    confidence_threshold = 0.75  # only deliver if agent's self-assessed confidence ≥ this

    critique_prompt = """
    You just produced the above output. Now critique it:
    1. What assumptions did you make that might be wrong?
    2. What counter-evidence exists against your main thesis?
    3. Where is your confidence lowest, and why?
    After critiquing, revise your output to address these weaknesses.
    Rate your final confidence (0.0–1.0) and explain.
    """
```

**When to use CritiqueLoop vs. Agent:**
- Agent: execution tasks (run SQL, post to Slack, create PR) — speed matters, verification handles quality
- CritiqueLoop: reasoning tasks (architecture decisions, market analysis, risk assessment) — quality matters more than speed

**Research angle R6 (new):** Does CritiqueLoop with 2 rounds outperform single-shot Agent on reasoning tasks? Measured by: human rating of output quality, self-assessed confidence calibration (does confidence 0.8 actually mean 80% correct?).

---

## 12. Summary Table

### SDLC Gaps (Primary — Pillar 0)

| Problem | Competitive Reference | V2 Solution | Phase |
|---------|----------------------|-------------|-------|
| No deterministic gates — LLM skips lint/tests | Minions (Stripe) | DeterministicNode in harness.py | 1 |
| No general Build Loop (ticket → PR) | Devin, OpenHands, Minions | dev/code-builder blueprint + dev/spec-analyzer generalized | 1 |
| No codebase intelligence | Augment Code, Sourcegraph | AST-graph pre-execution indexing + LoadRepoMemory | 1 |
| Max 2 CI round discipline | Minions (hard cap) | max_pipeline_retries=2 in harness | 1 |
| No behavioral simulation / imagined execution | PlayerZero Sim-1, QualityFlow | dev/impact-predictor (imagined execution) | 2 |
| No risk scoring before merge | PlayerZero | dev/risk-scorer → quality gate | 2 |
| Consensus missing for BLOCKER findings | CANDOR [342] | 2-reviewer consensus required for BLOCKER | 2 |
| No test generation from diffs | Slash Agentic Quality Lifecycle | dev/test-generator skill | 2 |
| No repository readiness scoring | Slash "Agent Ready" | Repo readiness score (context/testing/cicd) | 2 |
| No SRE/incident loop | PlayerZero Autopilot SRE | dev/incident-detector + root-cause-tracer + fix-proposer | 3 |
| Memory is invisible / uncorrectable | PlayerZero living model | GET /cortex/explain + POST /cortex/correct | 2 |
| No behavioral simulation model | PlayerZero Sim-1 (full) | Fine-tuned simulation model on episode traces | 4 |

### Harness Infrastructure Gaps (Pillar 1)

| Problem | Source | V2 Solution | Phase |
|---------|--------|-------------|-------|
| Implicit I/O contracts | — | harness.py typed schema | 0 |
| No output verification | — | harness.verify() hook | 0 |
| Advisory-only tool permissions | — | permissions.json (enforced) | 0 |
| No tool-call governance pipeline | AutoHarness | 6-step: parse→classify→check→execute→sanitize→audit | 0 |
| Tool responses unsanitized | AutoHarness | Output sanitize step: strip secrets, compact logs, redact PII | 0 |
| Raw JSON between pipeline stages | Anthropic 3-agent | HandoffArtifact: task_spec + progress + constraints + criteria | 0 |
| No independent evaluator agent | Anthropic 3-agent | evaluator-agent role: executes output, never produces it | 1 |
| No dry-run mode | OpenHarness | `agentura dry-run <skill>`: resolves context/tools/permissions without executing | 0 |
| Prompt caching not used | Claude API | `cache_control: ephemeral` on SKILL.md + DOMAIN_FACTS.yaml (90% cost reduction) | 0 |
| No cost/usage visibility | Shopify | LiteLLM gateway + ClickHouse wide events (replaces Langfuse) | 0 |
| Build agents have no isolated env | Stripe Minions devbox | Devstack integration: DeterministicNode tests hit real devstack services | 1 |
| Loop 4 uses metric inference not events | Canonical logging  | signoz-mcp connected to incident-detector: stack trace + blast radius SQL | 0 |
| Harness telemetry not in ClickHouse | canonical logging wide events | Skill execution events → Vector → ClickHouse alongside app logs | 0 |
| Unstructured pipeline state | L2MAC | HandoffArtifact + targeted context views per agent | 0 |
| Planning mode undeclared | Paper §3.1 | planning_mode in config | 0 |
| Execution env not classified | Paper §2.3 | execution_environment in config | 0 |
| No mid-loop verification | VeriGuard [226] | mid-loop verify hook | 1 |
| No early exit | QualityFlow [253] | convergence oracle | 2 |
| Belief divergence in multi-agent | SyncMind [347] | state_hash check on HandoffArtifact | 2 |
| Transactional execution (finance) | [389] | rollback on failure | 3 |

### Memory Gaps (Pillar 2)

| Problem | V2 Solution | Phase |
|---------|-------------|-------|
| No episodic memory | Episode traces + quality gate (MemGovern) | 1 |
| No declarative facts | DOMAIN_FACTS.yaml (propositional/prescriptive split) | 1 |
| Reactive-only MemRL | Strategy synthesis from successes (ExpeL) + step-level traces | 1 |
| Binary MemRL scoring | Step-level trace rewards | 3 |
| Episodic retrieval by recency | Abstract state scoring (Synapse [414]) | 2 |
| MemRL deduplication | Consolidation step (TALM [191]) | 3 |
| Skills can't self-improve | Reflexion → SKILL.md PR (Evolution Agent) | 3 |
| Context window explosion | Budgeted slots (CodeMem [45]) + L2MAC scheduling | 1 |

### Scale Gaps (Pillar 3)

| Problem | V2 Solution | Phase |
|---------|-------------|-------|
| No skill quality measurement | Readiness Score (3 axes) | 2 |
| Hard to contribute skills | Scaffold generator + CI gate | 2 |
| No cross-skill knowledge | Discover v1 (episodes) → v2 (cross-system) | 2–4 |
| Research not instrumented | R1–R8 experiments + telemetry | 4 |
