---
name: pr-pipeline
role: manager
domain: dev
trigger: webhook
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$3.00"
timeout: "600s"
---

# PR Pipeline Manager

## Trigger
- webhook: GitHub `pull_request` events (opened, synchronize, review_requested)
- webhook: GitHub `issue_comment` events (developer feedback on bot comments)

## Task

Orchestrate a pipeline of specialist skills when a GitHub PR is opened or updated. The pipeline runs sequentially so each step can use prior step output:

1. **Code Review** (`dev/github-pr-reviewer`) — Security, bugs, performance analysis
2. **Documentation** (`dev/pr-doc-generator`) — Missing docstrings, README gaps, API docs
3. **Test Generation** (`dev/e2e-test-generator`) — Test cases from the diff
4. **Test Execution** (`dev/service-agent`) — Run generated tests in E2B sandbox
5. **Release Checks** (`dev/pr-release-checks`) — Conventional commits, secrets, changelog

After all steps complete, post results to GitHub as:
- Inline PR review comments (from code review + doc suggestions)
- Summary comment with collapsible sections per skill

Each bot comment embeds an execution ID marker (`<!-- agentura:exec:EXEC-xxx:domain/skill -->`) enabling the developer feedback loop: replies trigger corrections, reactions are polled for sentiment.

## Pipeline Behavior

- If any sub-skill fails, the pipeline continues with remaining skills.
- Failures are reported in the summary comment.
- Diff is truncated at 50K chars (largest files by change count included first).
- Cost budget is the sum of all sub-skill budgets.

## Input Format

```json
{
  "delivery_id": "github-delivery-uuid",
  "action": "opened | synchronize | review_requested",
  "pr_number": 42,
  "pr_url": "https://github.com/owner/repo/pull/42",
  "pr_title": "feat: add feature",
  "pr_body": "Description...",
  "diff_url": "https://github.com/owner/repo/pull/42.diff",
  "head_branch": "feat/my-feature",
  "base_branch": "main",
  "head_sha": "abc123",
  "repo": "owner/repo",
  "sender": "username"
}
```

## Output Format

```json
{
  "pipeline_id": "PIPE-timestamp",
  "pr_number": 42,
  "repo": "owner/repo",
  "steps": [
    {
      "skill": "dev/github-pr-reviewer",
      "status": "success | error",
      "execution_id": "EXEC-xxx",
      "latency_ms": 2500,
      "cost_usd": 0.05
    }
  ],
  "github_review_posted": true,
  "github_comment_posted": true,
  "total_cost_usd": 0.25,
  "total_latency_ms": 15000
}
```

## Guardrails

1. Never expose API tokens or secrets in GitHub comments.
2. Pipeline MUST respond to the webhook within 10 seconds (async dispatch).
3. Individual skill failures must not block the pipeline.
4. Diff truncation must note which files were skipped.
