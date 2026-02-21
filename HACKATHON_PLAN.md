# Aspora AI Platform — Hackathon Plan (FINAL)

> **Status**: LOCKED. No more ideation. Build this.
> **Date**: 2026-02-18
> **Team**: 3 people
> **Time**: Friday build day + weekend polish
> **Category**: Open (All BAU Problems)

---

## The Idea (One Sentence)

**An enterprise AI platform where business teams define skills in Markdown, the platform routes and executes them across domains, and every correction makes the system measurably better.**

---

## Why This Solves ALL 14 BAU Problems (Not Just One)

Every BAU problem at Aspora has the same three layers:

```
1. KNOWLEDGE     → What do you need to KNOW?     → That's a Skill (SKILL.md)
2. CONNECTIONS   → What data do you ACCESS?       → That's a Plugin (MCP)
3. DECISIONS     → What judgment calls are MADE?   → That's an Agent (DOMAIN.md + Skills)
```

The platform doesn't solve "ECM" or "Fraud." It solves the PATTERN.
Add a DOMAIN.md + SKILL.md + MCP config → new problem solved. Same platform.

### All 14 Problems Mapped

```
┌──────────────────┬──────────────────────┬──────────────────┬──────────────────┬───────────┐
│ BAU PROBLEM      │ SKILL.md             │ MCP (Data)       │ DOMAIN.md Voice  │ HACKATHON │
│                  │ (Knowledge)          │ (Connections)    │ (Decisions)      │ STATUS    │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 1. Operations    │ escalation-triage    │ Redshift         │ Terse,           │ LIVE DEMO │
│    (ECM)         │ order-details        │ Google Sheets    │ operational      │ (6 skills │
│                  │ resolve-ticket       │                  │                  │  running) │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 2. Fraud & Risk  │ fraud-triage         │ Redshift         │ Investigative,   │ LIVE DEMO │
│    (FRM)         │ rule-simulation      │                  │ audit-trail      │ (5 skills │
│                  │ kyc-optimizer        │                  │                  │  running) │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 3. Growth        │ suggest-allocation   │ Market APIs      │ Advisory,        │ LIVE DEMO │
│    (Wealth)      │ risk-assess          │ Portfolio DB     │ cautious         │ (3 skills)│
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 4. Product Speed │ spec-to-plan         │ Jira, GitHub     │ Engineering,     │ SCAFFOLD  │
│                  │ plan-to-code         │                  │ precise          │ (Act 2    │
│                  │ code-to-ship         │                  │                  │  demo)    │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 5. CX Quality    │ support-agent        │ Zendesk/CRM      │ Empathetic,      │ SLIDE     │
│                  │ tone: Aspora voice   │ Knowledge base   │ brand-aligned    │           │
│                  │ escalation rules     │                  │                  │           │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 6. Data Sanity   │ data-quality-check   │ Redshift         │ Analytical,      │ SLIDE     │
│                  │ anomaly-detector     │ Metabase         │ precise          │           │
│                  │ funnel-validator     │                  │                  │           │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 7. Engagement    │ engagement-hooks     │ User activity DB │ Friendly,        │ SLIDE     │
│                  │ rate-alerts          │ Notification svc │ timely           │           │
│                  │ goal-updates         │                  │                  │           │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 8. Legal &       │ compliance-checker   │ Regulation DB    │ Regulatory,      │ SLIDE     │
│    Compliance    │ geo-specific rules   │ Policy docs      │ formal           │           │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 9. Context &     │ THIS IS THE PLATFORM │ All of the above │ All of the above │ LIVE DEMO │
│    Knowledge     │ Every skill IS       │                  │                  │ (this is  │
│                  │ encoded knowledge    │                  │                  │  Act 2)   │
├──────────────────┼──────────────────────┼──────────────────┼──────────────────┼───────────┤
│ 10-14. Others    │ Same pattern:        │ Same pattern:    │ Same pattern:    │ SLIDE     │
│ (Retention,      │ Write SKILL.md       │ Add MCP config   │ Write DOMAIN.md  │ "same     │
│  Acquisition,    │ with domain rules    │ for data source  │ with voice/      │  platform,│
│  Document Review,│                      │                  │ principles       │  new       │
│  RFI, etc.)      │                      │                  │                  │  domain"  │
└──────────────────┴──────────────────────┴──────────────────┴──────────────────┴───────────┘
```

### The Pitch Reframe

**Don't say**: "We built an AI platform that runs skills."
**Say**: "We have 14 BAU problems. They all decompose the same way:
knowledge + data + judgment. We built ONE platform that handles
all of them. Let me show you 3 running today, 1 onboarded live,
and the map to the other 10."

### Hackathon Strategy: 3 Live + 1 Onboarded + 10 Mapped

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   LIVE DEMO (built, running, real data):                    │
│   ● Operations (ECM) — 6 skills, Redshift MCP              │
│   ● Fraud & Risk (FRM) — 5 skills, Redshift MCP            │
│   ● Growth (Wealth) — 3 skills, Market APIs                 │
│                                                             │
│   ONBOARDED LIVE (Act 2, 5 minutes on stage):               │
│   ◐ Product Speed OR CX Quality — scaffold + run            │
│                                                             │
│   MAPPED (slide with the table above):                      │
│   ○ CX Quality                                              │
│   ○ Data Sanity                                             │
│   ○ Engagement                                              │
│   ○ Legal & Compliance                                      │
│   ○ Retention, Acquisition, Doc Review, RFI, etc.           │
│                                                             │
│   "Same DOMAIN.md + SKILL.md + MCP. Different problem."     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why This Wins the Hackathon (Open Category)

The Open Category wants breadth + depth. Most teams will:
- Pick 1 problem, build 1 solution, demo 1 thing

We show:
- 14 problems, 1 architecture, 3 running live, 1 onboarded on stage, 10 mapped
- The platform IS the solution to "Context & Knowledge" (problem #9)
- Learning loop means it gets better at ALL 14 problems simultaneously

### Updated Slide 2 (The Pain) — Now 14 Problems

```
SLIDE 2 — THE PAIN
─────────────────────────────────────────────
  "Aspora has 14 BAU problems.
   Today, each gets its own tool, its own team, its own silo."

   ┌─────────────────────────────────────────┐
   │  Operations: manual triage (2-3h/order) │
   │  Fraud: high false positives (60%+)     │
   │  Growth: generic advice (no per-market) │
   │  CX: L1 handled by humans ($$$)        │
   │  Data: weekly manual quality checks     │
   │  Legal: geo-compliance is spreadsheets  │
   │  ... 8 more problems, 8 more silos      │
   └─────────────────────────────────────────┘

   "Every one of these has the same 3 layers:
    Knowledge. Data. Judgment.
    We built one platform for all of them."
```

### Updated Slide 10 (Close)

```
SLIDE 10 — CLOSE
─────────────────────────────────────────────
  "14 BAU problems. 1 platform. 3 running today.

   Every team writes Markdown, not code.
   Every correction makes it better.
   Every domain's knowledge stays when people leave.

   The AI that learns from your team."
```

---

## The Architecture (Final)

```
                           TRIGGER SURFACES
                    (how work enters the platform)
            ┌──────────┬──────────┬──────────┬──────────┐
            │  Slack   │   Cron   │ Webhook  │   CLI    │
            │  (prod)  │ (batch)  │ (alerts) │  (demo)  │
            └────┬─────┴────┬─────┴────┬─────┴────┬─────┘
                 │          │          │          │
                 └──────────┴────┬─────┴──────────┘
                                 │
                        normalized message
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PLATFORM CLASSIFIER                            │
│                  (a SKILL, not code)                             │
│                                                                 │
│  DOMAIN.md: "Classify into ecm | frm | wealth | hr | ..."      │
│  plugin.yaml: trigger patterns per domain                       │
│  Executed by: Pydantic AI + Haiku (fast, cheap)                 │
│  Returns: { domain: "ecm", confidence: 0.95 }                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┼────────────┬────────────┐
            │            │            │            │
            ▼            ▼            ▼            ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  ECM DOMAIN   │ │ FRM DOMAIN   │ │WEALTH DOMAIN │ │  HR DOMAIN   │
│               │ │              │ │              │ │  (onboarded  │
│ DOMAIN.md     │ │ DOMAIN.md    │ │ DOMAIN.md    │ │   via SDK)   │
│ ┌───────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │ │              │
│ │  MANAGER  │ │ │ │ MANAGER  │ │ │ │ MANAGER  │ │ │ DOMAIN.md    │
│ │ SKILL.md  │ │ │ │ SKILL.md │ │ │ │ SKILL.md │ │ │ ┌──────────┐ │
│ └─────┬─────┘ │ │ └────┬─────┘ │ │ └────┬─────┘ │ │ │ MANAGER  │ │
│       │       │ │      │       │ │      │       │ │ │ SKILL.md │ │
│  ┌────┼────┐  │ │ ┌────┼────┐  │ │ ┌────┼────┐  │ │ └────┬─────┘ │
│  ▼    ▼    ▼  │ │ ▼    ▼    ▼  │ │ ▼    ▼    ▼  │ │      ▼       │
│ order my  run │ │rule  rule qa │ │risk sug- port│ │  leave-      │
│ det.  tix ECM │ │sim   comp    │ │ass  gest folio│ │  policy      │
│               │ │              │ │              │ │              │
│ MCP:Redshift  │ │ MCP:Redshift │ │ MCP:APIs     │ │ MCP:HRIS     │
│ MCP:Sheets    │ │              │ │              │ │              │
│ Config:YAML   │ │ Config:YAML  │ │ Config:YAML  │ │ Config:YAML  │
└───────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │                │                │                │
        └────────────────┴────────┬───────┴────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL EXECUTOR                                │
│                    (the ONLY Python code)                        │
│                                                                 │
│  1. Load DOMAIN.md (identity, voice, principles)                │
│  2. Load SKILL.md (task, domain model, guardrails)              │
│  3. Compose system prompt = DOMAIN.md + SKILL.md                │
│  4. Connect MCP tools (Redshift, Sheets, APIs)                  │
│  5. Call LLM via Pydantic AI + OpenRouter                       │
│  6. Return SkillResult with reasoning_trace                     │
│  7. Log to Langfuse/Opik for observability                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LEARNING LOOP                                 │
│                    (the moat nobody else has)                    │
│                                                                 │
│  User corrects output                                           │
│       │                                                         │
│       ▼                                                         │
│  Correction logged to skill_executions.user_correction          │
│       │                                                         │
│       ├──▶ DeepEval test auto-generated (regression)            │
│       ├──▶ GUARDRAILS.md updated (anti-pattern recorded)        │
│       └──▶ Reflexion entry created (mistake → correction →      │
│            revised_approach)                                     │
│       │                                                         │
│       ▼                                                         │
│  Skill re-runs → measurably better (test passes)                │
│                                                                 │
│  After 6 months: 10,000+ auto-generated tests                  │
│  Competitors: 0                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Makes This Different From Swarms / OpenClaw / CrewAI

```
┌─────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│                 │ SWARMS               │ OPENCLAW             │ OUR PLATFORM         │
│                 │ (kyegomez)           │ (steinberger)        │ (aspora)             │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ WHAT IT IS      │ Python framework     │ Personal AI          │ Enterprise AI        │
│                 │ for developers       │ assistant            │ platform for teams   │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ AGENT DEFINED   │ Python code          │ SKILL.md             │ SKILL.md + DOMAIN.md │
│ HOW?            │ (60+ params)         │ (flat, personal)     │ + plugin.yaml        │
│                 │                      │                      │ (hierarchical,       │
│                 │                      │                      │  config-driven)      │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ WHO CREATES     │ Python developers    │ Power users          │ Business teams       │
│ AGENTS?         │                      │                      │ (Markdown + YAML)    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ ROUTING         │ SwarmRouter          │ LLM reasons over     │ Classifier skill     │
│                 │ (16 patterns,        │ injected skills      │ (Haiku) + plugin.yaml│
│                 │  code-selected)      │ (implicit)           │ triggers (explicit)  │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ DOMAIN          │ None — generic       │ SOUL.md (1 per       │ DOMAIN.md per domain │
│ KNOWLEDGE       │ prompt + tools       │ agent, personality)  │ + config YAMLs       │
│                 │                      │                      │ (diagnosis-mapping,  │
│                 │                      │                      │  stuck-reasons)      │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ HIERARCHY       │ Flat (all agents     │ Flat (skills at      │ Domain → Manager →   │
│                 │ at one level)        │ one level)           │ Specialist + RBAC    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ DATA ACCESS     │ Python callables     │ Shell, browser,      │ MCP (Redshift SQL,   │
│                 │ (shell, browser)     │ file system          │ Databricks, Sheets)  │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ LEARNING        │ None — same mistake  │ Memory (remembers    │ Corrections → auto   │
│                 │ forever              │ conversations)       │ tests → GUARDRAILS → │
│                 │                      │                      │ measurably better    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ TESTING         │ None built-in        │ None built-in        │ DeepEval + Promptfoo │
│                 │                      │                      │ + Opik + Langfuse    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ ISOLATION       │ Shared Conversation  │ Per-agent workspace  │ Domain RBAC +        │
│                 │ object (no RBAC)     │                      │ blocked_resources    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ MARKETPLACE     │ swarms.world +       │ ClawHub (3000+       │ Internal skill       │
│                 │ Solana crypto token  │ community skills)    │ registry (enterprise)│
└─────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

**Our position**: We took the skill primitive that OpenClaw proved (SKILL.md) and the orchestration
vocabulary that Swarms popularized (named patterns, routing), then built what neither has:
**domain knowledge architecture + hierarchical isolation + learning from corrections**.

---

## What EXISTS Today (Already Built)

| Asset | Location | Status |
|-------|----------|--------|
| ECM Operations plugin | `aspora-ai-ops/plugins/ecm-operations/` | Production (12 triggers, 6 skills, Redshift MCP) |
| FRM Platform plugin | `trm-platform/` | Production (5 skills, Redshift MCP) |
| SDK CLI + templates | `wealth-copilot/sdk/` | Built (create, run, test, validate commands) |
| Config loader | `sdk/aspora_sdk/runner/config_loader.py` | Built (handles both YAML formats) |
| Skill loader | `sdk/aspora_sdk/runner/skill_loader.py` | Built (frontmatter + DOMAIN.md composition) |
| Local runner | `sdk/aspora_sdk/runner/local_runner.py` | Built (Pydantic AI + OpenRouter) |
| SKILL.md template | `sdk/aspora_sdk/templates/skill.md.j2` | Built (Three Cognitive Layers + SAGE) |
| DOMAIN.md template | `sdk/aspora_sdk/templates/domain.md.j2` | Built (identity, voice, principles, audience) |
| 11 Jinja2 templates | `sdk/aspora_sdk/templates/` | Built |
| Types (SkillContext→SkillResult) | `sdk/aspora_sdk/types.py` | Built |
| Engineering Brain | `engineering-brain/` | Reference docs (ENGINEERING_BRAIN, AGENTIC_SKILLS, SKILL_DESIGN_PRINCIPLES) |
| 22 Architecture Decisions | `DECISIONS.md` | Recorded (DEC-001 through DEC-022) |
| 6 Guardrails | `GUARDRAILS.md` | Recorded (GRD-001 through GRD-006) |

---

## What to BUILD for Hackathon

### Build Block 1: Skill Executor (DONE — polish only)
**Owner**: You | **Time**: 1h | **Confidence**: HIGH

`local_runner.py` already works. Polish:
- Ensure DOMAIN.md + SKILL.md composition works end-to-end
- Add `--verbose` flag to show composed prompt in dry-run
- Test with real ECM SKILL.md + Redshift MCP

### Build Block 2: Platform Classifier Skill
**Owner**: You | **Time**: 1h | **Confidence**: HIGH

A SKILL.md (not Python) that classifies inputs to domains:
```
skills/platform/
├── DOMAIN.md              # "You are the platform router..."
└── classifier/
    └── SKILL.md           # "Given input, return {domain, confidence, reasoning}"
```

Uses Haiku for speed. Deterministic fallback via plugin.yaml trigger patterns.

### Build Block 3: Wire ECM + FRM as Domains
**Owner**: You | **Time**: 2h | **Confidence**: MEDIUM

Point the executor at existing production skills:
- ECM: `aspora-ai-ops/plugins/ecm-operations/SKILL.md` + MCP config
- FRM: `trm-platform/.claude/skills/rule-simulation.md` + MCP config
- Create thin `DOMAIN.md` for each

Show: same executor, different domains, different voice.

### Build Block 4: SDK Scaffold Demo (Act 2)
**Owner**: Person 2 | **Time**: 2h | **Confidence**: HIGH

Live demo of `aspora create skill hr/leave-policy --lang python --role specialist`:
- Generates: DOMAIN.md, SKILL.md, plugin.yaml, DECISIONS.md, GUARDRAILS.md, tests, fixtures
- Show the Three Cognitive Layers in SKILL.md template
- Edit SKILL.md with HR-specific content (2 minutes)
- `aspora run hr/leave-policy --input sample.json` → works

### Build Block 5: Correction → Test Loop (Act 3)
**Owner**: Person 3 | **Time**: 3h | **Confidence**: MEDIUM

The moat demo:
1. Skill runs → gets answer wrong
2. User corrects → `aspora correct ecm/order-details --execution-id X --correction "should be Y"`
3. DeepEval test auto-generated from correction
4. GUARDRAILS.md updated with anti-pattern
5. Skill re-runs → passes the new test
6. Show test count: 0 → 1 → 5 → projected 10,000 at 6 months

### Build Block 6: Slides (Breadth, Not Built)
**Owner**: Person 3 | **Time**: 2h | **Confidence**: HIGH

What's a slide (not built):
- Communication Gateway (Slack/WhatsApp architecture)
- Canary deployments / shadow mode
- Neo4j GraphRAG knowledge layer
- Three-tier observability (Grafana mockups)
- Firecracker sandboxing
- Orchestration patterns catalog (sequential, concurrent, hierarchical, mixture)

---

## Hackathon Demo Script (8 Minutes)

### Act 1: "We Run 3 Domains on One Platform" (3 min)

**Setup**: Terminal with `aspora` CLI ready.

```
"Our platform already runs production AI operations across multiple
 business domains. Let me show you."
```

**Demo 1a — ECM (terse, operational voice)**
```bash
aspora run ecm/order-details --input fixtures/stuck_order.json
```
→ Output: Structured diagnosis with resolution steps, terse, data-first.
→ Point out: "Notice the voice — terse, operational. Field agents handling
  50 tickets don't want paragraphs. That's DOMAIN.md."

**Demo 1b — FRM (investigative, precise voice)**
```bash
aspora run frm/rule-simulation --input fixtures/fraud_rule.json
```
→ Output: Rule impact analysis with confidence scores, audit trail.
→ Point out: "Different domain, different voice, different data source.
  Same platform, same executor. Zero routing code."

**Demo 1c — Show the classifier**
```bash
aspora run platform/classifier --input '{"message": "order UK131K456 is stuck"}'
```
→ Output: `{ domain: "ecm", confidence: 0.97 }`
→ "The router is a skill too. Everything is a skill."

**Key message**: Multiple business domains. ONE platform. ZERO Python routing code.

### Act 2: "Any Team Can Onboard in 5 Minutes" (2 min)

```
"What if HR wants AI for leave policy? They don't write Python.
 They write Markdown."
```

**Demo 2a — Scaffold**
```bash
aspora create skill hr/leave-policy --lang python --role specialist
```
→ Show generated files. Open SKILL.md — Three Cognitive Layers template.
→ Open DOMAIN.md — "Notice: identity, voice, principles, audience."

**Demo 2b — Edit and run**
→ Fill in SKILL.md with leave policy content (30 seconds, pre-prepared).
```bash
aspora run hr/leave-policy --input fixtures/leave_request.json
```
→ Works. New domain, new skill, 5 minutes.

**Key message**: Engineering Brain principles BUILT INTO the scaffold.
Not documentation — architecture.

### Act 3: "It Learns From Every Mistake" (3 min)

```
"Here's what nobody else does. When this agent gets it wrong,
 it gets better."
```

**Demo 3a — Skill gets it wrong**
```bash
aspora run ecm/order-details --input fixtures/edge_case.json
```
→ Output: Wrong diagnosis (missing corridor-specific rule).

**Demo 3b — User corrects**
```bash
aspora correct ecm/order-details \
  --correction "UAE corridor orders stuck in CNR_RESERVED need LULU escalation, not standard path"
```
→ Show: DeepEval test generated. GUARDRAILS.md updated.

**Demo 3c — Skill improves**
```bash
aspora run ecm/order-details --input fixtures/edge_case.json
```
→ Output: Correct diagnosis. Test passes.

```
"That's ONE correction. After 6 months of production use,
 that's 10,000 auto-generated regression tests.

 Swarms has 16 orchestration patterns and zero learning.
 OpenClaw has 3,000 community skills and zero testing.
 We have corrections that compound into a moat."
```

**Key message**: The AI that learns from your team.

---

## Decision Tree (Locked — GRD-005)

```
"Should I write Python for this?"
     │
     ├─ EXECUTING a skill? (load SKILL.md, call LLM, return result)
     │   └─ YES → Python (Pydantic AI executor)
     │
     ├─ ROUTING or CLASSIFYING?
     │   └─ NO → Make it a SKILL.md
     │
     ├─ FETCHING DATA from a database?
     │   └─ NO → Configure MCP in plugin.yaml
     │
     └─ STORING KNOWLEDGE? (rules, mappings, diagnosis)
         └─ NO → Put it in config YAML
```

**Rule**: Python is glue. Skills are intelligence. Config is knowledge.

---

## File Structure (What the Demo Shows)

```
skills/
├── platform/                          # Platform-level skills
│   └── classifier/
│       └── SKILL.md                   # Routes to domains
│
├── ecm/                               # ECM Domain
│   ├── DOMAIN.md                      # Terse, operational, data-first
│   ├── GUARDRAILS.md
│   ├── DECISIONS.md
│   ├── config/
│   │   ├── diagnosis-mapping.yaml     # 47 sub-states → diagnoses
│   │   └── stuck-reasons.yaml         # SLAs, team deps, runbooks
│   └── order-details/
│       ├── SKILL.md                   # Full diagnosis + resolution
│       ├── plugin.yaml                # Triggers: "order {id}", "lookup"
│       └── fixtures/
│
├── frm/                               # FRM Domain
│   ├── DOMAIN.md                      # Investigative, precise, audit-trail
│   ├── GUARDRAILS.md
│   └── rule-simulation/
│       ├── SKILL.md                   # Rule impact analysis
│       ├── plugin.yaml                # Triggers: "simulate rule"
│       └── fixtures/
│
├── wealth/                            # Wealth Domain
│   ├── DOMAIN.md                      # Advisory, cautious, jurisdiction-aware
│   └── risk-assess/
│       ├── SKILL.md
│       └── fixtures/
│
└── hr/                                # NEW (created live in Act 2)
    ├── DOMAIN.md                      # Empathetic, policy-grounded
    └── leave-policy/
        ├── SKILL.md
        └── fixtures/
```

---

## Team Split

| Person | Owns | Builds | Deliverable |
|--------|------|--------|-------------|
| **You** | Architecture + Demo | Blocks 1-3 | Working executor running ECM + FRM + classifier |
| **Person 2** | SDK + Act 2 | Block 4 | `aspora create` produces working scaffold, live edit + run |
| **Person 3** | Learning Loop + Slides | Blocks 5-6 | Correction→test demo + presentation deck |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| MCP connection fails live | Pre-cache query results in fixtures. Fall back to `--input fixtures/` |
| Model API slow/down | Use OpenRouter auto-fallback (DEC-003). Pre-record backup video |
| Correction loop not ready | Show the test generation step manually. The concept is the moat, not the CLI polish |
| Judge asks "how is this different from Swarms?" | "Swarms is a Python framework — 60 params to create one agent. We're config-driven — business teams write Markdown. And we have learning: 10K auto-tests after 6 months. They have zero." |
| Judge asks "how is this different from OpenClaw?" | "OpenClaw is a personal assistant — one person, one agent, flat skills. We're enterprise — multiple domains, role isolation, compliance-grade data access via MCP." |

---

## What's NOT Built (Slides Only)

| Feature | Why It's a Slide |
|---------|-----------------|
| Slack/WhatsApp gateway | Needs Slack Bolt integration (Week 2 work) |
| Canary deployments | Needs production infra |
| Neo4j GraphRAG | Needs 100+ executions to seed |
| Three-tier observability | Needs Prometheus + Grafana setup |
| Firecracker sandboxing | Needs cloud infra |
| Orchestration pattern catalog | Named patterns (hierarchical, sequential, concurrent, mixture) shown as architecture diagram |
| Marketplace / skill registry | Month 6+ feature |

---

## Success Criteria

The demo wins if judges leave thinking:

1. **"This already works"** — 3 domains running, real data, structured output
2. **"My team could use this tomorrow"** — 5-minute onboarding, no Python needed
3. **"This gets better over time"** — correction → test → improvement loop demonstrated
4. **"This is genuinely different"** — not another Swarms/OpenClaw/CrewAI clone

---

## Moats (Defensible Advantages That Compound Over Time)

### Moat 1: Learning Loop (Strongest — Gets Wider Every Day)

```
Day 1:     0 tests,   0 guardrails,  0 corrections
Month 1:   500 tests, 30 guardrails, 500 corrections
Month 6:   10,000 tests, 200 guardrails, 10,000 corrections
Month 12:  50,000 tests — a competitor starting today starts at ZERO
```

Every user correction becomes a regression test. Every mistake becomes a guardrail.
A competitor can copy our code in a week. They cannot copy 12 months of accumulated
corrections. This is the primary moat — it's why DEC-006 exists.

**Why competitors can't replicate this:**
- Swarms: No correction capture, no test generation, no learning loop. Zero.
- OpenClaw: Has conversational memory (remembers what you said). Does NOT improve
  skill quality from corrections.
- CrewAI: Static agent definitions. No feedback mechanism.

### Moat 2: Domain Knowledge Encoded as Config

```
skills/ecm/config/diagnosis-mapping.yaml    # 47 sub-states → diagnoses
skills/ecm/config/stuck-reasons.yaml        # SLAs, team deps, runbooks
skills/ecm/GUARDRAILS.md                    # 6+ anti-patterns from production
skills/ecm/DECISIONS.md                     # 10+ decisions from real operations
skills/ecm/DOMAIN.md                        # Voice, principles, audience
```

This is **institutional knowledge as code**. When an employee leaves, their
expertise stays. When a new team member joins, they inherit 6 months of
encoded decisions. No other platform captures domain knowledge this way.

### Moat 3: Config-Driven Onboarding (Network Effect)

```
Write SKILL.md (5 min) → aspora run → works
vs
Swarms: Write 60+ params Python Agent class → debug → deploy → works (hours)
```

Lower barrier = more teams onboard = more skills = more corrections = better platform.
This is a **network effect**: each new domain makes the platform more valuable
for every other domain (shared patterns, cross-domain guardrails).

### Moat 4: Enterprise Data via MCP (Can't Replicate Without Access)

Our skills connect to Redshift, Databricks, Google Sheets — behind VPNs and RBAC.
A competitor would need:
- Access to the same databases
- The same MCP server configurations
- The same query patterns (honed over months)
- The same compliance approvals

The MCP connections are non-transferable. The data access IS the moat.

### Moat 5: Testing Infrastructure as Trust Signal

| Tool | License | Purpose |
|------|---------|---------|
| DeepEval | Apache 2.0 | LLM unit testing, 60+ metrics |
| Promptfoo | MIT | A/B testing, red teaming |
| Opik | Apache 2.0 | Production tracing, auto test gen |
| Langfuse | AGPL | Self-hosted, compliance audit trail |

For regulated industries (finance, healthcare), the testing stack IS the
compliance story. "We test every skill with 4 frameworks" is a sales argument
that no competitor in the multi-agent space can match.

---

## Business Outcomes (Numbers That Matter)

### For the Hackathon Judges (Business Language)

| Metric | Before (Manual/No AI) | After (Our Platform) |
|--------|----------------------|---------------------|
| **Time to resolve stuck order** | 2-3 hours (manual lookup, diagnosis, escalation) | 30 seconds (skill queries Redshift, diagnoses, recommends action) |
| **New AI use case onboarding** | 2-4 weeks (hire ML team, build pipeline, test) | 5 minutes (`aspora create`, edit SKILL.md, run) |
| **Error rate over time** | Flat (same mistakes repeated) | Declining (each correction → test → guardrail) |
| **Knowledge retention when employee leaves** | Lost (in their head) | Preserved (DECISIONS.md, GUARDRAILS.md, config YAMLs) |
| **Cost per AI operation** | $50K+ setup + $X/query (custom pipeline) | $0.10/execution (OpenRouter, Haiku for routing, Sonnet for skills) |
| **Cross-domain coverage** | Separate tool per domain | ONE platform: ECM + FRM + Wealth + HR + any new domain |

### The Compound Effect (Project Forward)

```
Month 1:  3 domains, 15 skills, 500 corrections
Month 3:  5 domains, 40 skills, 3,000 corrections, 3,000 auto-tests
Month 6:  8 domains, 100 skills, 10,000 corrections, 10,000 auto-tests
Month 12: 12 domains, 250 skills, 50,000 corrections, 50,000 auto-tests
          ↑ THIS is what a competitor cannot replicate by copying code
```

### ROI Calculation (For One Domain: ECM)

```
Current: 3 ops agents × 8 hours/day × 22 days × $30/hour = $15,840/month
         handling ~200 stuck orders/day manually

With platform: 200 orders × 30 seconds × $0.10/execution = $600/month
               + 1 ops agent reviewing AI outputs (4 hours) = $2,640/month

Savings: $12,600/month per domain = $151,200/year
Scale to 6 domains: ~$900K/year operational savings
```

---

## Presentation Deck Structure

> **Format**: 10 slides. One idea per slide. Large text. White background.
> **Time**: 8 minutes (5 min presentation + 3 min demo).
> **Style**: YC Demo Day clarity + Razorpay DevStack problem-journey-impact pattern.

### Reference Decks Studied

1. **Razorpay DevStack** (Srinidhi VV, 2021) — 33 slides
   - Pattern: Problem → Iterative Q&A journey (Q1→Q2→Q3→Q4→Q5→Q6) → Demo → Impact metrics
   - Strength: Each problem introduced as a question, solution shown immediately
   - Impact slide: "10-15x reduction in time to take feature live. 2 min vs 20-40 min."
   - What to take: Problem→Solution pairing, concrete before/after metrics

2. **Accelerating Engineering Efficiency with AI** (TFInfinity) — 11 slides
   - Pattern: Problem (with numbers) → Idea (one sentence) → How It Works → Demo → Impact
   - Strength: Led with pain ("7-8 days to provision", "2-3 days per feature")
   - Impact: "40+ man-days saved per quarter", "30-40% reduction in DBA effort"
   - What to take: Lead with pain numbers, show compound savings

3. **YC Demo Day Format** — 5-7 slides, 2.5 minutes
   - Vertebrae Framework: What are we building? Why hasn't this been done? Why is it hard? Why unmissable?
   - One idea per slide. Under 7 words per text block.
   - Goal: "Intrigue investors enough that they will want to meet you and learn more"
   - What to take: Ruthless simplicity, memorability, 3-4 key points max

### Our Deck: 10 Slides

```
SLIDE 1 — TITLE
─────────────────────────────────────────────
  Aspora AI Platform
  "The AI that learns from your team"

  [Company logo. One line. Nothing else.]


SLIDE 2 — THE PAIN (with numbers)
─────────────────────────────────────────────
  "AI agents in enterprise today:"

  ┌─────────────────────────────────────────┐
  │ 2-4 weeks to onboard one AI use case   │
  │ Same mistakes repeated forever          │
  │ Knowledge walks out the door            │
  │ Separate tool per business function     │
  └─────────────────────────────────────────┘

  [4 bullet points. Large font. Red/orange accent.
   Audience should feel the pain before you offer the cure.]


SLIDE 3 — THE INSIGHT (why now, why us)
─────────────────────────────────────────────
  "LLMs don't need code to be smart.
   They need the right context."

  Swarms: 60-param Python class per agent
  OpenClaw: Personal assistant for individuals
  Everyone else: Code-driven, no learning, no domain knowledge

  We asked: What if business teams wrote Markdown,
  not Python — and the AI got better every day?

  [This is the non-obvious insight. The "why hasn't
   this been done before" slide.]


SLIDE 4 — THE SOLUTION (one sentence + diagram)
─────────────────────────────────────────────
  "Skills as Markdown. Knowledge as Config.
   Learning from every correction."

  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ SKILL.md │ + │DOMAIN.md │ + │plugin.yml│ = Working AI Agent
  │ (what to │   │(voice &  │   │(triggers │   No Python required.
  │  do)     │   │ rules)   │   │ & data)  │
  └──────────┘   └──────────┘   └──────────┘

  [Keep it simple. Three files = one agent.
   The audience must get this in 3 seconds.]


SLIDE 5 — DEMO: "3 Domains, 1 Platform" (LIVE)
─────────────────────────────────────────────
  [Switch to terminal. Run Act 1.]

  Show: ECM (terse voice) → FRM (investigative voice)
        → Classifier routing → "zero code, same executor"

  Back to slides with:
  "3 domains. 14 skills. 0 lines of routing code."


SLIDE 6 — DEMO: "5 Minutes to Onboard" (LIVE)
─────────────────────────────────────────────
  [Switch to terminal. Run Act 2.]

  Show: aspora create → edit SKILL.md → aspora run → works

  Back to slides with:
  "HR just got AI. No ML team. No pipeline. 5 minutes."


SLIDE 7 — DEMO: "It Learns" (LIVE)
─────────────────────────────────────────────
  [Switch to terminal. Run Act 3.]

  Show: Wrong answer → Correct → Test generated → Right answer

  Back to slides with:
  "Every correction = a regression test.
   After 6 months: 10,000 tests. Competitors: 0."


SLIDE 8 — THE MOAT (why this compounds)
─────────────────────────────────────────────

  ┌─────────────────────────────────────────┐
  │         THE COMPOUND EFFECT             │
  │                                         │
  │  Month 1:    500 corrections,    500 tests  │
  │  Month 6:  10,000 corrections, 10,000 tests │
  │  Month 12: 50,000 corrections, 50,000 tests │
  │                                         │
  │  A competitor starting today: 0         │
  └─────────────────────────────────────────┘

  5 moats that widen daily:
  1. Learning loop (corrections → tests → better)
  2. Domain knowledge as config (stays when people leave)
  3. Config-driven onboarding (network effect)
  4. Enterprise data via MCP (non-transferable access)
  5. Testing infrastructure (compliance trust signal)


SLIDE 9 — IMPACT & BUSINESS OUTCOMES
─────────────────────────────────────────────
  ┌─────────────────────────────────────────┐
  │                                         │
  │  2-3 hours → 30 seconds                 │
  │  (stuck order resolution)               │
  │                                         │
  │  2-4 weeks → 5 minutes                  │
  │  (new AI use case onboarding)           │
  │                                         │
  │  $15,840/mo → $3,240/mo per domain      │
  │  (operational cost)                     │
  │                                         │
  │  ~$900K/year savings at 6 domains       │
  │                                         │
  └─────────────────────────────────────────┘

  [Big numbers. Before/after. No clutter.
   Razorpay pattern: "10-15x reduction"
   Ours: "2-4 weeks → 5 minutes"]


SLIDE 10 — CLOSE (memorable, forward-looking)
─────────────────────────────────────────────
  "Swarms gives you a framework.
   OpenClaw gives you an assistant.
   We give you a platform that learns."

  Already running: ECM (6 skills), FRM (5 skills), Wealth (3 skills)
  Next: 6 more domains in 3 months

  The AI that learns from your team.

  [End on the tagline. Repeat it. Make it stick.]
```

### Presentation Principles (From YC + Reference Decks)

| Principle | Source | How We Apply |
|-----------|--------|-------------|
| One idea per slide | YC Demo Day guide | 10 slides, 10 ideas |
| Lead with pain, not solution | Razorpay DevStack | Slide 2: numbers that hurt |
| Before/after metrics | Both reference decks | Slide 9: "2-3 hours → 30 seconds" |
| Demo in the middle, not the end | Razorpay DevStack | Slides 5-7 are live demo |
| Compound effect as moat | YC Seed Deck guide | Slide 8: month-by-month projection |
| Under 7 words per text block | YC design guide | All text large, scannable |
| End memorably | YC Demo Day guide | Slide 10: tagline repeated |
| Speak slowly, pause for emphasis | YC delivery guide | Practice: 8 min = slow, deliberate |
| No jargon in slides | YC anti-patterns | "Skills as Markdown" not "config-driven SKILL.md with SAGE" |
| Show the journey | Razorpay DevStack | Problem → 3 demos → impact → moat |

### What NOT to Do (Anti-Patterns From YC)

- Do NOT say "enterprise-grade" (Swarms says it, means nothing)
- Do NOT show architecture diagrams to judges (save for Q&A)
- Do NOT explain how LLMs work or what MCP is
- Do NOT use the words "orchestration", "SAGE", "Three Cognitive Layers" in slides
- Do NOT show code. Show the SKILL.md file — it's Markdown, judges can read it
- Do NOT read slides. Tell the story. The slides are visual anchors.
- Do NOT rush. 8 minutes is long. Use pauses after big numbers.

### The 3 Things Judges Must Remember (Vertebrae Framework)

When judges walk away, they should remember exactly 3 things:

1. **"Business teams write Markdown, not code"** — the onboarding story
2. **"It gets better from every correction"** — the learning loop
3. **"10,000 tests after 6 months, competitors have zero"** — the moat

---

## Deployment Architecture (Kubernetes)

### What EXISTS Already

```
wealth-copilot-go/
├── Dockerfile              # Multi-stage Go build (1.23-alpine), port 8080
├── docker-compose.yml      # Go server + PostgreSQL 16
├── Makefile                # build, test, lint, docker-up/down
├── cmd/server/             # Go HTTP/gRPC server
├── config/                 # YAML config files
└── proto/agent/v1/         # gRPC proto for agent communication
```

The Go service is the API gateway. The Python SDK is the skill executor.
These are TWO containers that talk via gRPC.

### K8s Architecture (Target)

```
┌─────────────────────────────────────────────────────────────────┐
│ KUBERNETES CLUSTER                                              │
│                                                                 │
│  ┌─────────────────────┐    ┌──────────────────────────────┐   │
│  │ INGRESS (Traefik)   │    │ SKILLS VOLUME (PVC or Git)   │   │
│  │ api.aspora.internal │    │                              │   │
│  └──────────┬──────────┘    │ /skills/                     │   │
│             │               │ ├── platform/classifier/     │   │
│             ▼               │ ├── ecm/                     │   │
│  ┌──────────────────────┐   │ │   ├── DOMAIN.md            │   │
│  │ API GATEWAY          │   │ │   ├── GUARDRAILS.md        │   │
│  │ (Go service)         │   │ │   ├── config/              │   │
│  │                      │   │ │   └── order-details/       │   │
│  │ - REST/gRPC API      │   │ ├── frm/                     │   │
│  │ - Auth/RBAC          │   │ ├── wealth/                  │   │
│  │ - Request routing    │   │ └── hr/                      │   │
│  │ - Execution logging  │   │                              │   │
│  │ - Cost tracking      │   └──────────┬───────────────────┘   │
│  └──────────┬──────────┘               │                       │
│             │ gRPC                     │ mounted volume         │
│             ▼                          ▼                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ SKILL EXECUTOR (Python, Pydantic AI)                     │  │
│  │ Deployment: 2-5 replicas (HPA on CPU/request count)      │  │
│  │                                                          │  │
│  │ 1. Receive (domain, skill_name, input) from gateway      │  │
│  │ 2. Load /skills/{domain}/DOMAIN.md                       │  │
│  │ 3. Load /skills/{domain}/{skill}/SKILL.md                │  │
│  │ 4. Compose system prompt                                 │  │
│  │ 5. Call LLM via OpenRouter                               │  │
│  │ 6. Return SkillResult                                    │  │
│  │                                                          │  │
│  │ Env: OPENROUTER_API_KEY, LANGFUSE_URL, OPIK_URL          │  │
│  └──────────────────────────────────────────────────────────┘  │
│             │                                                   │
│             │ MCP connections (per domain)                      │
│             ▼                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ MCP: Redshift   │  │ MCP: Sheets    │  │ MCP: HRIS      │   │
│  │ (ECM, FRM)      │  │ (ECM)          │  │ (HR)           │   │
│  │ Sidecar or      │  │ Sidecar or     │  │ Sidecar or     │   │
│  │ ClusterIP svc   │  │ ClusterIP svc  │  │ ClusterIP svc  │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DATA LAYER                                               │  │
│  │                                                          │  │
│  │ PostgreSQL (StatefulSet)                                 │  │
│  │ - Skill registry (metadata, versions)                    │  │
│  │ - Execution logs (input, output, cost, latency)          │  │
│  │ - Corrections (user_correction, test_generated)          │  │
│  │                                                          │  │
│  │ Redis (Deployment) — optional                            │  │
│  │ - Hot skill cache (LRU, DEC-007)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ OBSERVABILITY                                            │  │
│  │ Langfuse (self-hosted) + Prometheus + Grafana            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Where to Keep Skills

Three options, from simplest to most production-ready:

**Option A: Git repo + Init Container (Hackathon — use this)**
```yaml
# K8s Deployment
initContainers:
  - name: clone-skills
    image: alpine/git
    command: ['git', 'clone', 'https://github.com/aspora/skills.git', '/skills']
    volumeMounts:
      - name: skills-volume
        mountPath: /skills
containers:
  - name: executor
    image: aspora/skill-executor:latest
    volumeMounts:
      - name: skills-volume
        mountPath: /skills
        readOnly: true
```
- Skills in a Git repo. Init container clones at pod startup.
- To update: restart pod or add a git-sync sidecar.
- Good for hackathon. Simple. Version-controlled.

**Option B: Git-Sync Sidecar (Month 1 — auto-updates)**
```yaml
containers:
  - name: git-sync
    image: registry.k8s.io/git-sync/git-sync:v4
    args: ['--repo=https://github.com/aspora/skills', '--period=60s']
    volumeMounts:
      - name: skills-volume
        mountPath: /skills
  - name: executor
    volumeMounts:
      - name: skills-volume
        mountPath: /skills
        readOnly: true
```
- Skills update every 60 seconds from Git. No pod restart needed.
- Enables: push SKILL.md to Git → live in production in 60s.
- This is the Razorpay DevStack pattern (they used Devspace file sync).

**Option C: OCI Registry (Month 3+ — versioned skill packages)**
```bash
# Package skills as OCI artifacts (like Helm charts)
oras push ghcr.io/aspora/skills/ecm:v1.2.0 ./skills/ecm/
# Pull in K8s via init container
oras pull ghcr.io/aspora/skills/ecm:v1.2.0
```
- Skills versioned like container images. Rollback = previous tag.
- Enables canary: 90% traffic → v1.1.0, 10% → v1.2.0 (DEC-010).
- Production-grade. Overkill for hackathon.

**Recommendation for hackathon**: Option A (Git clone init container).
**Recommendation for Month 1**: Option B (Git-sync sidecar).

### K8s Manifests Needed (Hackathon — Minimal)

```
k8s/
├── namespace.yaml              # aspora namespace
├── executor-deployment.yaml    # Python skill executor (2 replicas)
├── executor-service.yaml       # ClusterIP for gRPC
├── gateway-deployment.yaml     # Go API gateway
├── gateway-service.yaml        # ClusterIP
├── gateway-ingress.yaml        # Traefik/Nginx ingress
├── postgres-statefulset.yaml   # PostgreSQL (reuse existing docker-compose config)
├── configmap-env.yaml          # OPENROUTER_API_KEY, model configs
└── secrets.yaml                # API keys, DB credentials
```

That's 8 files. With the existing Dockerfile and Go service, this is ~2 hours of work.

---

## UI: What's Realistic

### Honest Assessment

| UI Type | Time | Hackathon Feasible? |
|---------|------|-------------------|
| Cosmos.video-style spatial visualization (agents as avatars in rooms) | 2-3 weeks | No |
| Swarms.ai-style marketing site with agent cards | 1 week | No |
| Full React dashboard with real-time execution | 3-5 days | No |
| **Streamlit dashboard showing domains/skills/executions** | **3-4 hours** | **Yes (stretch)** |
| **Static HTML page generated from skill configs** | **1-2 hours** | **Yes** |
| Terminal demo (current approach) | Already done | Yes |

### Recommended: Streamlit Dashboard (3-4 hours, Person 3)

Streamlit is Python, uses our existing SDK, and can be built fast:

```python
# ui/app.py — ~150 lines total
import streamlit as st
from pathlib import Path
from aspora_sdk.runner.skill_loader import load_skill_md, load_domain_md
from aspora_sdk.runner.config_loader import load_config
import json, asyncio

st.set_page_config(page_title="Aspora AI Platform", layout="wide")
st.title("Aspora AI Platform")

# --- Sidebar: Domain selector ---
skills_root = Path("skills")
domains = [d.name for d in skills_root.iterdir() if d.is_dir()]
selected_domain = st.sidebar.selectbox("Domain", domains)

# --- Domain info ---
domain_md = load_domain_md(skills_root / selected_domain / "any")
if domain_md:
    st.markdown(domain_md)

# --- Skills in this domain ---
domain_path = skills_root / selected_domain
skill_dirs = [s for s in domain_path.iterdir()
              if s.is_dir() and (s / "SKILL.md").exists()]

cols = st.columns(min(len(skill_dirs), 3))
for i, skill_dir in enumerate(skill_dirs):
    skill = load_skill_md(skill_dir / "SKILL.md")
    with cols[i % 3]:
        st.metric(skill.metadata.name, skill.metadata.role)
        st.caption(f"Model: {skill.metadata.model}")
        st.caption(f"Budget: {skill.metadata.cost_budget_per_execution}")
        if st.button(f"Run {skill.metadata.name}", key=skill_dir.name):
            st.session_state.selected_skill = skill_dir

# --- Execution panel ---
if "selected_skill" in st.session_state:
    skill_dir = st.session_state.selected_skill
    skill = load_skill_md(skill_dir / "SKILL.md")

    # Input
    fixture = skill_dir / "fixtures" / "sample_input.json"
    default_input = fixture.read_text() if fixture.exists() else "{}"
    user_input = st.text_area("Input JSON", default_input, height=200)

    if st.button("Execute Skill"):
        from aspora_sdk.runner.local_runner import execute_skill
        from aspora_sdk.types import SkillContext

        ctx = SkillContext(
            skill_name=skill.metadata.name,
            domain=skill.metadata.domain,
            role=skill.metadata.role,
            model=skill.metadata.model,
            system_prompt=skill.system_prompt,
            input_data=json.loads(user_input),
        )
        result = asyncio.run(execute_skill(ctx))

        if result.success:
            st.success("Execution successful")
            st.json(result.output)
        else:
            st.error("Execution failed")
            st.json(result.output)

        st.metric("Latency", f"{result.latency_ms:.0f}ms")
        st.metric("Cost", f"${result.cost_usd:.4f}")
```

### What the Dashboard Shows

```
┌─────────────────────────────────────────────────────────────┐
│ ASPORA AI PLATFORM                              [domain: ▼] │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ Domains  │  ECM Operations                                  │
│ ────────  │  ──────────────                                  │
│ ● ECM    │  Identity: Terse, operational, data-first        │
│ ○ FRM    │  Audience: Field ops agents                      │
│ ○ Wealth │  Skills: 6  │  Corrections: 47  │  Tests: 312   │
│ ○ HR     │                                                  │
│          │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│ Skills   │  │ order-   │ │ my-      │ │ run-ecm  │         │
│ ────────  │  │ details  │ │ tickets  │ │          │         │
│ 14 total │  │ speclist │ │ speclist │ │ manager  │         │
│ 4 domains│  │ ▶ Run    │ │ ▶ Run    │ │ ▶ Run    │         │
│          │  └──────────┘ └──────────┘ └──────────┘         │
│ Tests    │                                                  │
│ ────────  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│ 312 pass │  │ resolve- │ │ escalate │ │ assign-  │         │
│ 3 fail   │  │ ticket   │ │ -ticket  │ │ tickets  │         │
│          │  │ speclist │ │ speclist │ │ speclist │         │
│ Budget   │  │ ▶ Run    │ │ ▶ Run    │ │ ▶ Run    │         │
│ ────────  │  └──────────┘ └──────────┘ └──────────┘         │
│ $12.40   │                                                  │
│ of $50   │  ┌───────────────────────────────────────────┐   │
│ this mo  │  │ EXECUTION PANEL                           │   │
│          │  │                                           │   │
│          │  │ Skill: order-details                      │   │
│          │  │ Input: {"order_id": "UK131K456"}          │   │
│          │  │                                           │   │
│          │  │ [Execute]                                 │   │
│          │  │                                           │   │
│          │  │ Output:                                   │   │
│          │  │ {                                         │   │
│          │  │   "diagnosis": "CNR_RESERVED_WAIT",       │   │
│          │  │   "confidence": 0.95,                     │   │
│          │  │   "resolution": ["Check LULU status",     │   │
│          │  │     "Verify beneficiary details"],        │   │
│          │  │   "reasoning_trace": "..."                │   │
│          │  │ }                                         │   │
│          │  │                                           │   │
│          │  │ Latency: 1,240ms  Cost: $0.08             │   │
│          │  │                                           │   │
│          │  │ [👍 Correct] [✏️ Correct This]             │   │
│          │  └───────────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────────┘
```

### Why Streamlit (Not React)

- Python — uses our existing SDK directly (import `load_skill_md`, `execute_skill`)
- 3-4 hours to build, not days
- `streamlit run ui/app.py` — one command, no build step
- Looks polished enough for hackathon demo
- Can deploy on K8s as another container alongside the executor

### Deploy Streamlit on K8s

```yaml
# k8s/ui-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aspora-ui
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: ui
          image: aspora/ui:latest
          command: ["streamlit", "run", "app.py", "--server.port=8501"]
          ports:
            - containerPort: 8501
          volumeMounts:
            - name: skills-volume
              mountPath: /skills
              readOnly: true
```

### Revised Team Split (With UI)

| Person | Owns | Builds | Time |
|--------|------|--------|------|
| **You** | Executor + K8s + Demo | Blocks 1-3 + K8s manifests | 4-5h |
| **Person 2** | SDK + Act 2 | Block 4 (scaffold demo) | 2-3h |
| **Person 3** | UI + Learning Loop + Slides | Streamlit dashboard + Block 5 + deck | 5-6h |

### UI Scope for Hackathon (Person 3)

**Must have** (3 hours):
- Domain selector sidebar
- Skill cards per domain (name, role, model, budget)
- Run button → execute skill → show output
- Show DOMAIN.md content for selected domain

**Nice to have** (1 more hour):
- Correction button → capture correction → show test generated
- Execution history (last 5 runs)
- Domain metrics (skill count, correction count, test count)

**NOT doing** (save for later):
- Cosmos-style spatial visualization (agents as avatars)
- Real-time execution streaming
- Drag-and-drop skill routing
- Agent communication visualization

---

## Testing, Feedback Loop & Knowledge Layer (Detailed)

### What EXISTS Today

| Component | File | Status |
|-----------|------|--------|
| DeepEval runner | `sdk/aspora_sdk/testing/deepeval_runner.py` | Built — runs pytest, generates test from correction |
| Test generator | `sdk/aspora_sdk/testing/test_generator.py` | Built — appends Promptfoo YAML test cases |
| CLI test command | `sdk/aspora_sdk/cli/test_cmd.py` | Built — `aspora test` runs DeepEval + Promptfoo |
| DeepEval template | `sdk/aspora_sdk/templates/test_deepeval.py.j2` | Built — scaffolded per skill |
| Promptfoo template | `sdk/aspora_sdk/templates/test_promptfoo.yaml.j2` | Built — scaffolded per skill |
| FeedbackConfig type | `sdk/aspora_sdk/types.py` | Built — capture_corrections, auto_generate_tests, learning_strategy |
| Correction lifecycle doc | `showcase/feedback-loop/correction_to_test.json` | Documented — 7-step pipeline |
| Corrections registry | `showcase/knowledge-layer/corrections.json` | Sample data — 2 corrections (CORR-001, CORR-002) |
| Reflexion entries | `showcase/knowledge-layer/reflexion_entries.json` | Sample data — 2 entries (REFL-001, REFL-002) |
| Episodic memory | `showcase/knowledge-layer/episodic_memory.json` | Sample data — 5 executions |
| Regression suite | `showcase/feedback-loop/regression.yaml` | Built — 3 Promptfoo tests from real corrections |
| Generated DeepEval test | `showcase/feedback-loop/generated_test.py` | Built — GEval with custom criteria |
| ECM diagnosis-mapping | `aspora-ai-ops/plugins/ecm-operations/config/diagnosis-mapping.yaml` | Production — 47 sub-states → diagnoses with confidence scores |
| ECM stuck-reasons | `aspora-ai-ops/plugins/ecm-operations/stuck-reasons.yaml` | Production — 31 stuck reasons, teams, SLAs, runbooks |
| ECM guardrails | `aspora-ai-ops/plugins/ecm-operations/skills/guardrails.md` | Production — 7 rules, must/must-not table |

### What Needs WIRING for Hackathon

The pieces exist but aren't connected end-to-end. Here's the gap:

```
WHAT EXISTS                          WHAT'S MISSING (the wire)
──────────                           ────────────────────────
deepeval_runner.py                   CLI `aspora correct` command
  → generates test from correction     that captures correction, calls
                                       test_generator, updates GUARDRAILS

test_generator.py                    Reflexion injection into
  → appends Promptfoo test case        skill_loader (load REFL entries
                                       into system prompt)

corrections.json (sample)            Storage backend
reflexion_entries.json (sample)        (JSON files for hackathon,
episodic_memory.json (sample)          PostgreSQL for production)

regression.yaml (real tests)         CLI `aspora test` integration
                                       with generated/ tests folder
```

### The Complete Pipeline (7 Steps)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: SKILL EXECUTES                                          │
│                                                                 │
│ aspora run ecm/order-details --input stuck_order.json           │
│                                                                 │
│ Executor loads:                                                 │
│   DOMAIN.md (voice, principles)                                 │
│ + SKILL.md (task, domain model)                                 │
│ + Active reflexion entries for this skill (REFL-001, REFL-002)  │
│ + Config YAMLs (diagnosis-mapping, stuck-reasons)               │
│ = Composed system prompt → LLM call → SkillResult               │
│                                                                 │
│ Output logged to: episodic_memory (execution_id, in, out, cost) │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: USER REVIEWS OUTPUT                                     │
│                                                                 │
│ In Streamlit UI or Slack:                                       │
│   [👍 Correct]  [✏️ Correct This]                                │
│                                                                 │
│ If correct: log outcome=accepted, move on                       │
│ If wrong: user provides correction text                         │
│   "UAE corridor orders stuck in CNR_RESERVED need LULU          │
│    escalation, not standard path"                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: CORRECTION CAPTURED                                     │
│                                                                 │
│ aspora correct ecm/order-details \                              │
│   --execution-id EXEC-001 \                                     │
│   --correction "UAE corridor CNR_RESERVED needs LULU escalation"│
│                                                                 │
│ Stored in: corrections.json (hackathon) / PostgreSQL (prod)     │
│ {                                                               │
│   "correction_id": "CORR-003",                                  │
│   "execution_id": "EXEC-001",                                   │
│   "skill": "ecm/order-details",                                 │
│   "original_output": { ... },                                   │
│   "user_correction": "UAE corridor CNR_RESERVED needs...",      │
│   "corrected_output": { ... }                                   │
│ }                                                               │
└──────────┬───────────────────────┬──────────────────────────────┘
           │                       │
           ▼                       ▼
┌────────────────────┐  ┌────────────────────────────────────────┐
│ STEP 4: REFLEXION  │  │ STEP 5: AUTO-GENERATE TESTS            │
│                    │  │                                        │
│ Agent self-assesses│  │ a) DeepEval test (deepeval_runner.py)  │
│ why it was wrong:  │  │    → tests/generated/test_corr_3.py   │
│                    │  │    → GEval metric with custom criteria │
│ {                  │  │    → threshold: 0.7                    │
│  "mistake": "...", │  │                                        │
│  "root_cause":"..,"│  │ b) Promptfoo test (test_generator.py)  │
│  "rule": "When UAE │  │    → tests/generated/corrections.yaml  │
│   corridor...",    │  │    → llm-rubric + contains assertions  │
│  "applies_when":   │  │                                        │
│   "CNR_RESERVED    │  │ Both tests encode the CORRECTED        │
│    + UAE corridor" │  │ behavior as the expected outcome.       │
│ }                  │  │                                        │
│                    │  │ Test count: 0 → 1 → 2 → ... → 10,000  │
│ Stored in:         │  │                                        │
│ reflexion_entries  │  │                                        │
│ .json              │  │                                        │
└────────┬───────────┘  └───────────────────┬────────────────────┘
         │                                  │
         ▼                                  ▼
┌────────────────────┐  ┌────────────────────────────────────────┐
│ STEP 6: GUARDRAILS │  │ STEP 7: NEXT EXECUTION IS BETTER       │
│ UPDATED            │  │                                        │
│                    │  │ System prompt now includes:             │
│ GUARDRAILS.md gets │  │                                        │
│ new entry:         │  │   DOMAIN.md                            │
│                    │  │ + SKILL.md                              │
│ "GR-003: UAE       │  │ + REFLEXION ENTRIES:                    │
│  corridor          │  │   "REFL-003: When UAE corridor order    │
│  CNR_RESERVED      │  │    is in CNR_RESERVED, ALWAYS check     │
│  orders need LULU  │  │    LULU escalation path first."         │
│  escalation, not   │  │ + Config YAMLs                          │
│  standard path"    │  │                                        │
│                    │  │ LLM now knows this specific edge case  │
│ Detection: If      │  │ and will handle it correctly.           │
│ CNR_RESERVED +     │  │                                        │
│ UAE → check LULU   │  │ aspora test ecm/order-details          │
│                    │  │ → 3/3 tests pass (including new one)   │
└────────────────────┘  └────────────────────────────────────────┘
```

### What to BUILD for Hackathon (Wiring the Pipeline)

#### Wire 1: `aspora correct` CLI Command (~2h)

```python
# sdk/aspora_sdk/cli/correct.py

@click.command()
@click.argument("skill_path")                    # ecm/order-details
@click.option("--execution-id", required=True)    # which execution to correct
@click.option("--correction", required=True)      # user's correction text
def correct(skill_path, execution_id, correction):
    """Capture a correction and auto-generate tests."""

    # 1. Load the original execution from episodic memory
    execution = load_execution(execution_id)

    # 2. Store correction
    store_correction(skill_path, execution_id, correction, execution.output)

    # 3. Generate reflexion entry (LLM call: "why was the original wrong?")
    reflexion = generate_reflexion(
        skill=skill_path,
        original_output=execution.output,
        correction=correction,
    )
    store_reflexion(reflexion)

    # 4. Auto-generate DeepEval test
    deepeval_file = generate_test_from_correction(
        skill_dir=skill_dir,
        input_data=execution.input,
        actual_output=execution.output,
        corrected_output={"correction": correction},
    )

    # 5. Auto-generate Promptfoo test
    promptfoo_file = generate_promptfoo_test(
        skill_dir=skill_dir,
        input_data=execution.input,
        expected_output={"correction": correction},
        description=f"Correction: {correction[:80]}",
    )

    # 6. Update GUARDRAILS.md
    append_guardrail(skill_dir, reflexion)

    console.print(f"[green]Correction captured:[/]")
    console.print(f"  Reflexion: {reflexion.rule}")
    console.print(f"  DeepEval test: {deepeval_file}")
    console.print(f"  Promptfoo test: {promptfoo_file}")
    console.print(f"  GUARDRAILS.md updated")
```

#### Wire 2: Reflexion Injection in Skill Loader (~1h)

```python
# In skill_loader.py — load reflexion entries and inject into prompt

def load_reflexion_entries(skill_path: Path) -> str:
    """Load reflexion entries for this skill from knowledge layer."""
    # Walk up to find knowledge-layer/reflexion_entries.json
    reflexion_file = find_knowledge_file(skill_path, "reflexion_entries.json")
    if not reflexion_file:
        return ""

    entries = json.loads(reflexion_file.read_text())
    skill_name = f"{skill_path.parent.name}/{skill_path.stem}"

    # Filter entries for this skill
    relevant = [e for e in entries.get("entries", [])
                if e["skill"] == skill_name]

    if not relevant:
        return ""

    # Format as system prompt section
    lines = ["## Learned Rules (from past corrections)"]
    for entry in relevant:
        lines.append(f"- **{entry['reflexion_id']}**: {entry['rule']}")
        lines.append(f"  Applies when: {entry['applies_when']}")
    return "\n".join(lines)
```

Then compose into system prompt:
```
DOMAIN.md + REFLEXION ENTRIES + SKILL.md + GUARDRAILS
```

#### Wire 3: Execution Logging (~1h)

```python
# In local_runner.py — log every execution to episodic memory

def log_execution(ctx: SkillContext, result: SkillResult) -> str:
    """Log execution to episodic memory. Returns execution_id."""
    execution_id = f"EXEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    entry = {
        "execution_id": execution_id,
        "skill": f"{ctx.domain}/{ctx.skill_name}",
        "timestamp": datetime.now().isoformat(),
        "input_summary": ctx.input_data,
        "output_summary": result.output,
        "outcome": "pending_review",  # until user confirms/corrects
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
    }
    # Append to episodic_memory.json (hackathon)
    # or INSERT into PostgreSQL (production)
    append_to_episodic_memory(entry)
    return execution_id
```

### Testing Architecture (4 Tools, 4 Purposes)

```
┌─────────────────────────────────────────────────────────────────┐
│                    TESTING STACK                                 │
│                                                                 │
│  ┌──────────────┐   DEVELOPMENT TIME                            │
│  │   DeepEval   │   "Does the skill produce good output?"       │
│  │  (Apache 2.0)│                                               │
│  │              │   - AnswerRelevancy: Is output relevant?       │
│  │  Unit tests  │   - Faithfulness: Does it match input data?   │
│  │  per skill   │   - GEval: Custom criteria from corrections   │
│  │              │   - Threshold: 0.7 (configurable per skill)   │
│  │              │                                               │
│  │  Run: aspora test ecm/order-details --framework deepeval     │
│  └──────────────┘                                               │
│                                                                 │
│  ┌──────────────┐   REGRESSION / A/B TESTING                    │
│  │  Promptfoo   │   "Does the skill handle known edge cases?"   │
│  │  (MIT)       │                                               │
│  │              │   - LLM rubrics: judge output quality          │
│  │  Regression  │   - contains/not-contains: hard assertions    │
│  │  suite from  │   - Correction tests: auto-generated          │
│  │  corrections │   - Model comparison: Sonnet vs Haiku         │
│  │              │                                               │
│  │  Run: aspora test ecm/order-details --framework promptfoo    │
│  └──────────────┘                                               │
│                                                                 │
│  ┌──────────────┐   PRODUCTION TRACING                          │
│  │    Opik      │   "What happened in this execution?"          │
│  │ (Apache 2.0) │                                               │
│  │              │   - Trace every LLM call (in/out/tokens)      │
│  │  Production  │   - Auto-generate test cases from traces      │
│  │  monitoring  │   - Link traces to corrections                │
│  │              │   - Cost tracking per execution                │
│  │              │                                               │
│  │  Hackathon: SLIDE (not integrated yet)                       │
│  └──────────────┘                                               │
│                                                                 │
│  ┌──────────────┐   COMPLIANCE AUDIT                            │
│  │  Langfuse    │   "Can we prove this is safe?"                │
│  │  (AGPL)      │                                               │
│  │              │   - Self-hosted (data stays on-prem)           │
│  │  Audit trail │   - Full execution history with reasoning     │
│  │  for         │   - User corrections linked to test results   │
│  │  compliance  │   - Export for regulatory review               │
│  │              │                                               │
│  │  Hackathon: SLIDE (not integrated yet)                       │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘

Hackathon: DeepEval (built) + Promptfoo (built) = LIVE DEMO
Month 1:   + Opik tracing
Month 2:   + Langfuse audit trail
```

### Knowledge Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER                               │
│        (3 tiers, all config-driven, no RAG needed)              │
│                                                                 │
│  TIER 1: STATIC DOMAIN KNOWLEDGE (loaded every execution)       │
│  ─────────────────────────────────────────────────────           │
│  │                                                             │
│  │  DOMAIN.md          — Identity, voice, principles, audience │
│  │  GUARDRAILS.md      — Anti-patterns (grows from corrections)│
│  │  DECISIONS.md       — Prior decisions (prevents re-deciding)│
│  │                                                             │
│  │  These are ALWAYS in the system prompt.                     │
│  │  Cost: ~500-1000 tokens. Always loaded.                     │
│  └─────────────────────────────────────────────────────────────┘
│                                                                 │
│  TIER 2: DOMAIN CONFIG (loaded per skill, from plugin.yaml)     │
│  ──────────────────────────────────────────────────────          │
│  │                                                             │
│  │  diagnosis-mapping.yaml  — 47 sub-states → diagnoses         │
│  │    Structure:                                               │
│  │    CNR_RESERVED_WAIT:                                       │
│  │      meaning: "Card payment succeeded, LULU hasn't confirmed"│
│  │      root_cause: "Webhook not received"                     │
│  │      confidence: 95                                         │
│  │      steps:                                                 │
│  │        - title: "Verify Checkout Payment"                   │
│  │          time: "1 min"                                      │
│  │          action: "Checkout Dashboard → Search: {quote_id}"  │
│  │                                                             │
│  │  stuck-reasons.yaml      — 31 reasons, teams, SLAs          │
│  │    Structure:                                               │
│  │    - id: status_sync_issue                                  │
│  │      team: Ops                                              │
│  │      runbook: runbooks/status-sync-issue.md                 │
│  │      sla_hours: 12                                          │
│  │      resolution_hint: "Check Falcon/Lulu status sync"       │
│  │                                                             │
│  │  These are loaded when the skill's SKILL.md references them.│
│  │  Lazy loading (LC-3): only when execution path needs them.  │
│  │  Cost: 1000-5000 tokens per config file.                    │
│  └─────────────────────────────────────────────────────────────┘
│                                                                 │
│  TIER 3: LEARNED KNOWLEDGE (grows from corrections)             │
│  ─────────────────────────────────────────────────               │
│  │                                                             │
│  │  corrections.json       — Every user correction captured     │
│  │    { correction_id, execution_id, skill, original_output,   │
│  │      user_correction, corrected_output, lesson_learned }    │
│  │                                                             │
│  │  reflexion_entries.json — Agent self-assessments             │
│  │    { reflexion_id, mistake, root_cause, rule,               │
│  │      applies_when, confidence, validated_by_test }          │
│  │                                                             │
│  │  episodic_memory.json   — Execution history                 │
│  │    { execution_id, skill, input, output, outcome,           │
│  │      user_feedback, cost, latency, reflexion_applied }      │
│  │                                                             │
│  │  These are injected selectively:                            │
│  │  - Reflexion entries matching current skill → system prompt  │
│  │  - Past corrections → test suite (never deleted)            │
│  │  - Episodic memory → pattern matching (future: pgvector)    │
│  │                                                             │
│  │  Storage evolution:                                         │
│  │  Hackathon: JSON files in skill directory                   │
│  │  Month 1:   PostgreSQL tables                               │
│  │  Month 3:   + pgvector for semantic similarity              │
│  │  Month 6:   + Neo4j for causal reasoning (DEC-016)          │
│  └─────────────────────────────────────────────────────────────┘
│                                                                 │
│  NOT IN KNOWLEDGE LAYER (handled separately):                   │
│  ─────────────────────────────────────────────                   │
│  │  Live data (Redshift, Databricks)  → MCP (DEC-022)          │
│  │  Unstructured docs (>context)      → RAG (future, only      │
│  │                                      when context exceeded)  │
│  └─────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

### How Knowledge Flows in One Execution

```
User: "order UK131K456 is stuck"
  │
  ▼
Classifier → domain: ecm
  │
  ▼
Load system prompt:
  ├── DOMAIN.md (Tier 1: "You are ECM agent. Terse. Data-first.")
  ├── GUARDRAILS.md (Tier 1: "Never invent diagnoses. Say I don't know.")
  ├── REFLEXION ENTRIES (Tier 3: "REFL-003: UAE CNR_RESERVED → LULU first")
  ├── SKILL.md (order-details task definition)
  ├── diagnosis-mapping.yaml (Tier 2: loaded because SKILL.md references it)
  └── stuck-reasons.yaml (Tier 2: loaded because SKILL.md references it)
  │
  ▼
Executor calls LLM with composed prompt
  │
  ▼
LLM queries Redshift via MCP:
  SELECT * FROM orders WHERE order_id = 'UK131K456'
  │
  ▼
LLM maps query result to diagnosis-mapping.yaml:
  sub_state = CNR_RESERVED_WAIT → confidence 95%
  │
  ▼
LLM checks reflexion entries:
  REFL-003 applies (UAE corridor + CNR_RESERVED) → use LULU escalation
  │
  ▼
Output: {
  "order_id": "UK131K456",
  "diagnosis": "CNR_RESERVED_WAIT",
  "confidence": 0.95,
  "resolution": ["Check LULU status (1 min)", "Escalate to LULU ops if >2h"],
  "reasoning_trace": "Applied REFL-003: UAE corridor CNR_RESERVED → LULU path"
}
  │
  ▼
Logged to episodic_memory. User reviews.
If wrong → STEP 2 (correction loop repeats, knowledge grows)
If right → outcome=accepted, REFL-003 confidence increases
```

### Hackathon Build Priority for These 3 Components

| Component | What to Build | Time | Priority |
|-----------|--------------|------|----------|
| `aspora correct` CLI | Capture correction → generate tests → update guardrails | 2h | **P0** (Act 3 demo) |
| Reflexion injection | Load reflexion entries → inject into system prompt | 1h | **P0** (makes Act 3 demo work) |
| Execution logging | Log every run to episodic_memory.json | 1h | **P1** (needed for correct command) |
| Promptfoo regression run | `aspora test` picks up generated/corrections.yaml | 30min | **P1** (shows test count growing) |
| Knowledge tier display in UI | Streamlit sidebar: corrections count, test count, reflexion count | 1h | **P2** (nice to have for demo) |
| Opik tracing | Wire Opik SDK into executor | — | **Slide** (Month 1) |
| Langfuse audit | Wire Langfuse SDK into executor | — | **Slide** (Month 2) |
| pgvector episodic memory | Migrate JSON → PostgreSQL + pgvector | — | **Slide** (Month 3) |
| Neo4j GraphRAG | Causal reasoning graph | — | **Slide** (Month 6) |
