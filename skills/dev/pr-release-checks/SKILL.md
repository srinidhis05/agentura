---
name: pr-release-checks
role: specialist
domain: dev
trigger: webhook
model: anthropic/claude-haiku-4-5-latest
cost_budget_per_execution: "$0.05"
timeout: "30s"
---

# PR Release Readiness Checks

## Trigger
- webhook (invoked by pr-pipeline)

## Task

Evaluate a pull request for release readiness. Check compliance with conventional commits, changelog discipline, breaking change detection, secret exposure, and dependency hygiene.

This is a fast, structured check — no creative analysis needed. Return pass/warn/fail for each check.

## Expertise Context

When available, load the git-workflow skill's SKILL.md as expertise for:
- Conventional commit format validation rules
- PR checklist requirements
- Breaking change versioning rules

## Input Format

```json
{
  "pr_title": "feat: add user auth",
  "pr_body": "## Summary\n...",
  "diff": "string (unified diff content)",
  "changed_files": ["file1.py", "CHANGELOG.md"],
  "head_branch": "feat/user-auth",
  "base_branch": "main",
  "labels": ["feature", "breaking-change"]
}
```

## Output Format

```json
{
  "checks": [
    {
      "name": "conventional_commit_title",
      "status": "pass",
      "detail": "Title follows 'feat: description' pattern"
    },
    {
      "name": "changelog_updated",
      "status": "warn",
      "detail": "CHANGELOG.md not modified — consider adding an entry for this feature"
    },
    {
      "name": "breaking_change_version",
      "status": "pass",
      "detail": "No breaking changes detected"
    },
    {
      "name": "no_hardcoded_secrets",
      "status": "pass",
      "detail": "No API keys, tokens, or passwords found in diff"
    },
    {
      "name": "dependency_changes",
      "status": "pass",
      "detail": "No dependency file changes detected"
    }
  ],
  "release_ready": true,
  "blocking_count": 0,
  "warning_count": 1,
  "summary": "One-sentence release readiness assessment"
}
```

## Checks

1. **conventional_commit_title**: PR title matches `type(scope)?: description` where type is feat|fix|refactor|docs|test|chore|ci|perf|build|style.
2. **changelog_updated**: If the PR is a feat or fix AND touches non-test files, CHANGELOG.md should be updated.
3. **breaking_change_version**: If diff contains `BREAKING CHANGE:` or PR has breaking-change label, check that the version bump is appropriate (major for breaking).
4. **no_hardcoded_secrets**: Scan diff for patterns: API keys, passwords, tokens, connection strings, private keys.
5. **dependency_changes**: If package.json, go.mod, requirements.txt, etc. are modified, check that lock files are also updated.

## Guardrails

1. Secret detection patterns: `(?i)(api_key|apikey|secret|password|token|private_key|aws_access)[\s]*[=:]\s*["']?[A-Za-z0-9+/=]{16,}`.
2. Do not flag environment variable references (`${VAR}`, `os.getenv()`, `process.env.`) as secrets.
3. Changelog check is a "warn" (not "fail") — some repos don't require changelogs.
4. `release_ready` is false only if any check has status "fail".
