# Spec Analyzer — Heartbeat

## Schedule

| Cadence       | Action                                                    |
|---------------|-----------------------------------------------------------|
| On-demand     | Analyze incoming product ideas into structured specs      |
| Daily 17:00   | Review any specs pending clarification — ping requestor   |

## Protocol

1. **Idea received** — Parse the raw input, identify ambiguities, produce structured spec with acceptance criteria. If the idea is too vague, return a list of clarification questions instead of a partial spec.
2. **Clarification received** — Update the spec with new information, re-validate completeness, deliver to incubator-lead.
3. **End-of-day review** — Check for specs that have been waiting for clarification for 24h+. Send a reminder to the requestor via the incubator-lead.

## On Failure

- **Input completely uninterpretable**: Return structured feedback explaining what's missing. Never produce a spec from insufficient input.
- **Budget threshold hit**: Queue incoming requests. Complete any in-progress analysis. Notify incubator-lead.
