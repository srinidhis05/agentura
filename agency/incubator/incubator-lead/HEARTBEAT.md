# Incubator Lead — Heartbeat

## Schedule

| Cadence       | Action                                                        |
|---------------|---------------------------------------------------------------|
| On-demand     | Orchestrate incubation pipeline for new product ideas         |
| Every 4h      | Check pipeline status — any stuck builds or stale quality gates|
| Daily 09:00   | Review overnight builder completions, trigger quality gates   |
| Weekly Mon    | Publish weekly incubation metrics — ideas submitted, prototypes shipped, quality pass rate |

## Protocol

1. **New idea submitted** — Dispatch to spec-analyzer for structured spec. Wait for spec output before assigning to a builder.
2. **Spec complete** — Evaluate scope and assign to pit-builder (web) or mobile-builder (mobile) based on platform target in the spec.
3. **Build complete** — Trigger quality-gate review. Block delivery until quality gate passes.
4. **Quality gate passed** — Trigger reporter for stakeholder summary. Mark incubation as shipped.
5. **Quality gate failed** — Route failure report back to builder with specific remediation items. Allow one retry before escalating.

## On Failure

- **Builder unresponsive**: Reassign to alternate builder if available. Log for capacity review.
- **Quality gate stuck**: If no verdict within 2 hours, ping quality-gate agent. If still stuck after 4 hours, escalate to human.
- **Budget threshold hit**: Pause non-critical incubations. Complete in-progress builds. Notify human for budget approval.
