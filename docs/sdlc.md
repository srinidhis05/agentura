# Skill Development Lifecycle (SDLC)

> **Purpose**: Step-by-step guide for creating, testing, deploying, and improving skills.

## Two Paths to Create a Skill

### Path A: Guided (Recommended)

```
agentura cortex
    ↓
Interview → Generate → Refine → Done
 (Haiku)    (Sonnet)   (Sonnet)
```

A PM-style interactive session that asks you what problem you're solving, what inputs/outputs look like, and what guardrails matter. It generates the full skill scaffold automatically.

### Path B: Manual

```
IDEATE → DEFINE → BUILD → VALIDATE → LEARN
```

Create files by hand. Best when you know exactly what you want.

---

## Path A: `agentura cortex`

The fastest way to create a production-quality skill. Three phases, all conversational:

### Phase 1: Interview (Haiku)

The system acts as a product manager. It asks questions to understand:
- What domain does this skill belong to?
- What problem does it solve?
- What inputs does it need? What outputs should it produce?
- What guardrails should it follow?
- What role? (manager, specialist, field)

You have a natural conversation — no forms, no templates. The interviewer adapts its questions based on your answers and existing skills in the workspace.

```bash
agentura cortex
```

### Phase 2: Generation (Sonnet)

Once the interview produces a complete spec, a more capable model generates:
- `SKILL.md` — full prompt with Task, Input Format, Output Format, Guardrails
- `agentura.config.yaml` — model, cost budget, triggers, routing
- `fixtures/sample_input.json` — realistic test data
- `DECISIONS.md` and `GUARDRAILS.md` — scaffolded

### Phase 3: Refinement (Sonnet)

You review the generated skill. If something's off, describe the change and the model refines it. This loops up to 5 times until you approve.

```
Generated skill: hr/performance-review
Review the SKILL.md? [Y/n]: y
  → Shows rendered SKILL.md
Approve or describe changes: "Add a guardrail about not comparing employees to each other"
  → Regenerates with the guardrail added
Approve or describe changes: approve
  → Files written to skills/hr/performance-review/
```

### Quick Mode

Skip the interview for simple skills:

```bash
agentura cortex --quick
```

Prompts for domain, name, role, and description, then generates directly.

---

## Path B: Manual Creation

### Phase 1: IDEATE (5 min)

Decide what skill to build:
- What domain does it belong to?
- What role? (manager = triage/route, specialist = deep work, field = interactive)
- What trigger? (manual, alert, cron, routed)

```bash
agentura create skill {domain}/{name} --lang python --role specialist
```

### Phase 2: DEFINE (30 min)

Edit `SKILL.md`:
- Write a clear Task section
- Define input and output JSON formats
- Add 1-2 example executions
- Write guardrails (what the skill must NEVER do)

Edit `agentura.config.yaml`:
- Set model and cost budget
- Define triggers
- Add routing rules (if manager skill)

Add `fixtures/sample_input.json` with realistic test data.

### Phase 3: BUILD (1-4h)

Most skills are prompt-only (SKILL.md does everything). For custom logic:

```bash
# Edit code/handler.py
# Run to test
agentura run {domain}/{name} --input fixtures/sample_input.json
```

Iterate: edit → run → check output → edit again.

---

## Validate (Both Paths)

```bash
# Structure check
agentura validate {domain}/{name}

# Run all tests
agentura test {domain}/{name}

# Quality metrics (DeepEval)
agentura test {domain}/{name} --framework deepeval

# Regression tests (Promptfoo)
agentura test {domain}/{name} --framework promptfoo
```

## Learn

The feedback loop runs continuously after a skill is live:

1. User runs skill → output logged to `.agentura/episodic_memory.json`
2. User corrects a mistake → correction stored, reflexion rule generated, regression test auto-created
3. Next execution includes the learned rule → accept rate improves over time

See [memory-system.md](memory-system.md) for the full feedback loop documentation.
