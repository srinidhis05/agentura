# Incubation Reporter — Heartbeat

## Schedule

| Cadence       | Action                                                    |
|---------------|-----------------------------------------------------------|
| On-demand     | Generate stakeholder reports for completed incubations    |
| Weekly Fri    | Compile weekly incubation summary for all active projects |

## Protocol

1. **Incubation shipped** — Aggregate outputs from spec-analyzer, builder, and quality-gate. Produce formatted report with status, metrics, highlights, and next steps.
2. **Weekly summary** — Pull all incubation activity from the week. Report: ideas submitted, specs completed, builds attempted, quality gate pass/fail rates, shipped prototypes.

## On Failure

- **Missing data from upstream agents**: Report with available data. Mark missing sections as "DATA UNAVAILABLE — [agent] output not found."
- **Budget threshold hit**: Queue reporting. Notify incubator-lead.
