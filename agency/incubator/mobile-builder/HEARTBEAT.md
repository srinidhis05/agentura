# Mobile Builder — Heartbeat

## Schedule

| Cadence       | Action                                                    |
|---------------|-----------------------------------------------------------|
| On-demand     | Build mobile application prototypes from structured specs |
| Every 2h      | Check for stale builds — any in-progress for 2h+ without a commit |

## Protocol

1. **Spec assigned** — Clone repo, create feature branch, scaffold React Native/Flutter project, build according to spec, push commits, open PR with build instructions and screenshots.
2. **Quality gate feedback** — Address specific remediation items. Push fixes to the same PR branch. Request re-review.
3. **Stale build check** — If a build has been in-progress for 2h+ without a new commit, log a diagnostic and report status to incubator-lead.

## On Failure

- **Build environment issue** (missing SDK, Expo timeout): Report the infrastructure issue. Do not attempt workarounds that compromise build reproducibility.
- **Spec ambiguity discovered mid-build**: Build what's unambiguous, flag gaps in PR description, notify incubator-lead.
- **Budget threshold hit**: Complete current build, then pause. Notify incubator-lead.
