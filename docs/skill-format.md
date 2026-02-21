# SKILL.md Format Specification

Skills are defined as markdown files with YAML frontmatter. The LLM executes the skill based on this prompt.

## Two Supported Formats

### Format 1: Standard Frontmatter (Recommended)

```markdown
---
name: my-skill
role: specialist
domain: my-domain
trigger: manual
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.10"
---

# My Skill

## Task
...

## Output Format
...
```

Used by: `packages/skills/safety/*.skill.md`

### Format 2: Code Fence Metadata

```markdown
# My Skill

## Skill Metadata
\```yaml
skill:
  name: my-skill
  role: specialist
  domain: my-domain
\```

## Task
...
```

Used by: `examples/auto-rca/*.md`

## Required Frontmatter Fields

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `name` | string | yes | — |
| `role` | enum | yes | specialist |
| `domain` | string | yes | — |
| `trigger` | string | no | manual |
| `model` | string | no | anthropic/claude-sonnet-4.5 |
| `cost_budget_per_execution` | string | no | $0.10 |
| `timeout` | string | no | 60s |
| `routes_to` | list | no | [] |

## Recommended Sections

1. **Task** — What the skill does (imperative instructions)
2. **Context You'll Receive** — Expected input structure
3. **Available Tools (MCP)** — Tools the skill can call
4. **Output Format** — JSON schema for output
5. **Example Execution** — Input/output pairs
6. **Guardrails** — Hard rules (NEVER/ALWAYS)

## Relationship to aspora.config.yaml

`SKILL.md` defines **what** a single skill does. `aspora.config.yaml` defines **how** skills are orchestrated at the domain level (routing, guardrails, observability, feedback).
