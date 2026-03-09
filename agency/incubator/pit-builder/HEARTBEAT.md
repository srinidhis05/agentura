# Pit Builder — Heartbeat

## Schedule

| Cadence       | Action                                                    |
|---------------|-----------------------------------------------------------|
| On-demand     | Build web application prototypes from structured specs    |
| Every 2h      | Check for stale builds — any in-progress for 2h+ without a commit |

## Protocol

1. **Spec assigned** — Clone repo, create feature branch, build according to spec, push commits, open PR. Interleave git operations with code generation (GR-011).
2. **Quality gate feedback** — Address specific remediation items. Push fixes to the same PR branch. Request re-review.
3. **Stale build check** — If a build has been in-progress for 2h+ without a new commit, log a diagnostic and report status to incubator-lead.

## On Failure

- **Build fails to compile**: Include error output in PR description. Attempt one fix. If still broken, report to incubator-lead with root cause analysis.
- **Spec ambiguity discovered mid-build**: Build what's unambiguous, flag gaps in PR description, notify incubator-lead.
- **Budget threshold hit**: Complete current build (in-flight work), then pause. Notify incubator-lead.
