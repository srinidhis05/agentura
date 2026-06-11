# Agentura Harness v2 — Engineering Plan

**Date**: 2026-06
**Status**: Work in progress — research-backed design document

> GitHub: [github.com/Vance-Club/agentura](https://github.com/Vance-Club/agentura) | Site: [agenturaai.tech](https://agenturaai.tech)

---

## The Problem

Every major engineering organisation is discovering the same thing: the bottleneck in AI-assisted software development has shifted.

Generation is no longer the hard part. Verification is.

When coding agents work in parallel, autonomously, across a team — the constraint isn't producing code. It's knowing whether the code is right. An agent that generates without a verification layer is a defect accelerator.

This document describes the harness architecture that makes autonomous software development trustworthy.

---

## The Three Stages of Agentic Development

Most teams are moving through three stages:

```
Stage 1              Stage 2              Stage 3
──────────────       ──────────────       ──────────────────────
Structured           Factory model        Harness engineering
skills

GStack-style         Parallel agents,     Deterministic gates,
CLAUDE.md +          autonomous loops,    typed state, independent
sprint workflow      multi-domain         verification layer

One developer        Agentic teams        Production at scale
moves faster         generate faster      systems stay trustworthy
```

Stage 1 is well understood — tools like GStack (github.com/garrytan/gstack) show what structured skills look like for one developer. Stage 2 is where most teams are building today. Stage 3 is what this document describes.

---

## What "Harness" Means

An agent harness is the infrastructure layer that surrounds a language model and governs its execution: memory, tools, permissions, feedback loops, verification, and state management.

From arXiv:2605.18747 (UIUC/Meta/Stanford, 2026):
> *"The bottleneck of autonomy is not only the reasoning ability of the base model, but also the reliability of the system that connects model outputs to long-horizon actions and persistent states."*

The harness is that system. `Agent = Model + Harness`.

---

## The Four SDLC Loops

Agentura v2 owns four interconnected loops across the software development lifecycle:

```
LOOP 1 — BUILD
Ticket → Spec → Code → [Deterministic gates] → PR
The linter always fires. Tests always run.
Not prompted — hardcoded in the pipeline executor.

LOOP 2 — QUALITY
PR diff → Behavioral simulation → Risk classification → Test depth
The harness decides what verification depth is required.

LOOP 3 — REVIEW
PR → Parallel specialist agents → Consensus → Merge decision
Creator ≠ verifier. No agent reviews its own output.

LOOP 4 — RELIABILITY
Monitor → Anomaly → SQL root cause → Fix PR
Every production incident closes a feedback loop.
```

Each loop feeds the next. Every failure in Loop 4 strengthens Loop 1.

---

## Core Mechanisms

### DeterministicNode

Hardcoded pipeline steps that always execute regardless of LLM judgment:

```python
pipeline = [
    AgenticNode("implement_code"),

    DeterministicNode("lint",
        command="./gradlew detekt",
        always_runs=True),      # Cannot be skipped

    AgenticNode("fix_lint_errors", condition="lint_failed"),

    DeterministicNode("unit_tests",
        command="./gradlew test",
        always_runs=True),      # Cannot be skipped

    DeterministicNode("commit",
        always_runs=True),

    DeterministicNode("open_pr",
        always_runs=True),
]
max_pipeline_retries = 2        # Hard cap — escalate after 2 failures
```

Under context pressure, agents skip steps. A `DeterministicNode` cannot be skipped. This is the single most impactful change for production reliability — the insight from Stripe Minions (1,300 merged PRs/week).

---

### HandoffArtifact

In a multi-stage pipeline, each stage passes its output to the next as a JSON blob. By stage 4, the original intent has been paraphrased and compressed — the agent guesses what stage 1 intended.

A `HandoffArtifact` carries the original task specification unchanged through every stage:

```python
@dataclass
class HandoffArtifact:
    task_spec: TaskSpec          # original intent — NEVER compressed
    stage: str                   # which stage produced this
    outputs: dict                # typed outputs
    constraints: list[str]       # invariants next agent must honour
    open_questions: list[str]    # things next agent must resolve
    verification_criteria: list[str]  # how evaluator judges completion
    cost_usd: float
```

Stage 4 reads the same task spec as stage 1. Intent persists. Context resets between stages.

*Reference: Anthropic three-agent harness (InfoQ, April 2026) — sessions up to 4 hours without degradation.*

---

### Evaluator Agent

The same agent that produced the output will rationalise its correctness when reviewing it. An independent evaluator agent uses a separate model invocation with independent context — it only judges, never produces:

```
Builder agent   →  produces code, tests, documentation
Evaluator agent →  executes output, judges against verification criteria
                   structurally incapable of rationalising its own mistakes
```

*Reference: arXiv:2605.18747 §4.1 — "separating creator from verifier is the single strongest reliability lever."*

---

### Tool Governance Pipeline

Every MCP tool call currently: invoke → result. No risk classification. No output sanitization. Tool responses enter LLM context verbatim — including credentials, large logs, and internal URLs.

V2 enforces a 6-step governance pipeline on every tool call:

```
1. Parse & Validate    ← reject malformed inputs
2. Risk Classify       ← dangerous shell ops, secret exposure, prompt injection
3. Permission Check    ← allow/deny list, risk-tier gates
4. Execute
5. Output Sanitize     ← strip credentials, compact logs, redact PII
6. Audit Log           ← JSONL provenance (args_hash, not raw args)
```

*Reference: AutoHarness (github.com/aiming-lab/AutoHarness) — MIT licensed.*

---

### 4-Layer Memory Architecture

MemRL (v1 learning loop) operates on one layer: reflexion rules from failures. V2 adds three additional layers:

```
Layer 4: REFLEXION     "Don't query the DB on Tuesdays 14-16 UTC"
         (MemRL)        Failure-derived, Bayesian scored, auto-decaying

Layer 3: PROCEDURAL    "Weekly review runs queries A→B→C in this order"
                        Learned from successful execution traces

Layer 2: DECLARATIVE   "Vendor Stripe uses JP Morgan bank"
                        Stable facts, version-controlled, human-correctable

Layer 1: EPISODIC      "Last run: took 4m, cost $0.11, flagged 1 anomaly"
                        Compressed execution traces, retrieved by similarity
```

Key references: MemGovern [48], ExpeL [189], Synapse [414], PlugMem [417] — from arXiv:2605.18747.

---

### Testing Depth Hierarchy

Coverage is the wrong convergence signal. 100% coverage at 4% mutation score is a false positive.

V2 routes code changes to the appropriate verification depth based on risk classification:

| Depth | What it catches | When |
|-------|----------------|------|
| **Coverage** | Obvious crashes | Always |
| **Mutation score** | Behavioral equivalence failures | Medium+ risk |
| **Property-based** | Invariant violations across input ranges | High+ risk |
| **Oracle synthesis** | Semantic misalignment between intent and code | Money/auth/state |
| **Fuzzing** | Crashes, security vulnerabilities | API endpoints |

The harness decides the depth. The LLM does not.

Key references: MUTGEN [arXiv:2506.02954], Agentic PBT [arXiv:2510.09907], Nexus [arXiv:2510.26423], FlakyGuard [arXiv:2511.14002].

---

## Skills at Scale

Skills are the unit of capability — a `SKILL.md` prompt plus an `agentura.config.yaml` configuration:
- Version-controlled in git
- Triggered by events (GitHub webhooks, Slack mentions, schedules)
- Domain-isolated (finance skills cannot read growth data)
- Self-improving via MemRL (failures synthesize rules, rules improve future runs)

V2 extensions:
- **Typed contracts**: `harness.py` with `InputSchema`, `OutputSchema`, `verify()` hook
- **Skill readiness scoring**: Context + Execution + Feedback axes (75+ = "Agent Ready")
- **Scaffold generator**: `agentura create skill` + CI validation gate
- **Discover**: cross-skill knowledge graph queryable across all domains

---

## Research Foundation

Full reading of arXiv:2605.18747 "Code as Agent Harness" (UIUC, Meta, Stanford, 102 pages, May 2026).

The open problems the paper identifies — and which v2 directly addresses:

| Open Problem | Agentura v2 Answer |
|-------------|-------------------|
| Evaluation beyond task completion | Eval-as-code + mutation score as convergence criterion |
| Self-evolving harnesses without regression | Evolution Agent + regression test gate before skill patches |
| Transactional shared program state | HandoffArtifact + belief divergence detection |
| Human-in-the-loop safety | permissions.json enforcement + HITL gates for critical tier |

---

## Implementation Roadmap

| Phase | Duration | Primary Deliverable |
|-------|----------|-------------------|
| **0** | 2 weeks | LiteLLM gateway + tool governance pipeline + HandoffArtifact + dry-run mode |
| **1** | 3 weeks | DeterministicNode + Build Loop + evaluator agent + isolated execution |
| **2** | 3 weeks | Risk-tiered testing + imagined execution + adversarial test generation |
| **3** | 3 weeks | Reliability loop + self-improving skills + regression capture |
| **4** | Ongoing | Cross-skill knowledge graph + behavioral simulation + research experiments |

---

## Further Reading

- arXiv:2605.18747 — [Code as Agent Harness](https://arxiv.org/abs/2605.18747)
- Stripe Engineering — [Minions: one-shot coding agents](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents)
- Addy Osmani — [Loop Engineering](https://addyosmani.com/blog/loop-engineering/) · [The Factory Model](https://addyosmani.com/blog/factory-model/)
- GStack — [github.com/garrytan/gstack](https://github.com/garrytan/gstack)
- AutoHarness — [github.com/aiming-lab/AutoHarness](https://github.com/aiming-lab/AutoHarness)
- Anthropic — [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Martin Fowler — [Harness Engineering for Coding Agents](https://martinfowler.com/articles/harness-engineering.html)
