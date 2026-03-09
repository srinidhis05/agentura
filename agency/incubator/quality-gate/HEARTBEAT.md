# Quality Gate — Heartbeat

## Schedule

| Cadence       | Action                                                    |
|---------------|-----------------------------------------------------------|
| On trigger    | Run quality review when builder agent completes a PR      |
| Every 4h      | Scan open PRs for stale quality reviews needing re-check  |
| Daily 09:00   | Publish daily quality metrics — pass rate, common failures|
| Weekly Fri    | Generate weekly quality trend report for incubator-lead   |

## Protocol

1. **PR submitted for review** — Pull the branch, run build verification, execute test suite, perform code quality analysis (linting, complexity, coverage). Produce a structured verdict: PASS, CONDITIONAL_PASS (minor issues), or FAIL (blocking issues).
2. **CONDITIONAL_PASS** — List specific issues with severity and suggested fixes. Allow the builder agent to address them without full re-review. Re-check only the flagged items on resubmission.
3. **FAIL** — Provide detailed failure report with root cause, affected files, and remediation guidance. Block merge. Notify incubator-lead if the same failure pattern recurs 3+ times.
4. **Stale review** — If a PR has been open for 24h+ since last quality review, re-run checks to catch drift from base branch changes.

## On Failure

- **Build environment unavailable**: Report the infrastructure issue to incubator-lead. Do not approve PRs without running the full gate.
- **Test suite timeout**: Retry once with extended timeout. If still failing, flag as infrastructure issue and report partial results with a clear warning.
- **Budget threshold hit**: Continue reviewing P1 (blocking) PRs. Queue P2/P3 reviews and notify incubator-lead for budget approval.
