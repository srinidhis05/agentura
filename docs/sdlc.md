# Skill Development Lifecycle (SDLC)

```
IDEATE (5 min)  →  DEFINE (30 min)  →  BUILD (1-4h)  →  VALIDATE (30 min)
     ↓                   ↓                  ↓                   ↓
aspora create      Edit SKILL.md       Write handler      aspora validate
                   Edit config         aspora run          aspora test
                   Add fixtures        Write tests         Peer review
                                                               ↓
                                                   STAGE → PRODUCTION → LEARN
                                                   (Phase 2: requires platform)
```

## Phase 1: IDEATE (5 min)

Decide what skill to build. Answer:
- What domain does it belong to?
- What role? (manager = triage/route, specialist = deep work, field = interactive)
- What trigger? (manual, alert, cron, routed)

```bash
aspora create skill {domain}/{name} --lang python --role specialist
```

## Phase 2: DEFINE (30 min)

Edit `SKILL.md`:
- Write a clear Task section
- List MCP tools the skill needs
- Define the output JSON format
- Add 1-2 example executions
- Write guardrails (what the skill must NEVER do)

Edit `aspora.config.yaml`:
- Set model and cost budget
- Define triggers
- Add routing rules (if manager skill)
- Configure observability

Add `fixtures/sample_input.json` with realistic test data.

## Phase 3: BUILD (1-4h)

Most skills are prompt-only (SKILL.md does everything). For custom logic:

```bash
# Edit code/handler.py
# Run to test
aspora run {domain}/{name} --input fixtures/sample_input.json
```

Iterate: edit → run → check output → edit again.

## Phase 4: VALIDATE (30 min)

```bash
# Structure check
aspora validate {domain}/{name}

# Run tests
aspora test {domain}/{name}

# Quality metrics (DeepEval)
aspora test {domain}/{name} --framework deepeval

# Regression tests (Promptfoo)
aspora test {domain}/{name} --framework promptfoo
```

Record decisions in `DECISIONS.md`. Record anti-patterns in `GUARDRAILS.md`.

## Phase 5: STAGE (Phase 2)

Platform deployment via skill registry. Requires:
- All tests passing
- DECISIONS.md populated
- Peer review

## Phase 6: PRODUCTION (Phase 2)

Canary deployment (DEC-010):
- 10% traffic → monitor success rate
- Auto-rollback if < 95% of previous version
- Shadow mode for batch/cron skills (DEC-012)

## Phase 7: LEARN

Feedback loop (DEC-006):
1. User corrects skill output
2. Correction captured in `skill_executions.user_correction`
3. DeepEval regression test auto-generated
4. Reflexion entry stored in episodic memory (DEC-013)
5. Skill improves from corrections over time
