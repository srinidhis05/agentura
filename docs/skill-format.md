# SKILL.md Format Specification

> **Purpose**: Reference for the SKILL.md file format — frontmatter fields, recommended sections, and the 4-layer prompt hierarchy.

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

## 4-Layer Prompt Hierarchy

When a skill executes, its system prompt is assembled from up to 4 layers, separated by `\n\n---\n\n`:

```
Layer 0: WORKSPACE.md  — Organization-wide context (policies, conventions, shared rules)
Layer 1: DOMAIN.md     — Domain identity & voice (dev, finance, hr, productivity)
Layer 2: Reflexions    — Learned rules from past corrections (auto-generated)
Layer 3: SKILL.md      — Task-specific prompt
```

| Layer | File | Owner | Scope |
|-------|------|-------|-------|
| 0 | `skills/WORKSPACE.md` | Platform admin | All skills, all domains |
| 1 | `skills/{domain}/DOMAIN.md` | Domain lead | All skills in one domain |
| 2 | `reflexion_entries.json` / mem0 | Auto-generated | Per-skill |
| 3 | `skills/{domain}/{skill}/SKILL.md` | Skill author | One task |

Each layer is optional except Layer 3 (SKILL.md). Missing layers are silently skipped.

### File discovery

- **WORKSPACE.md**: Walks up from the skill directory (max 5 levels) looking for `WORKSPACE.md`. Typically at `skills/WORKSPACE.md`.
- **DOMAIN.md**: Walks up from the skill directory (max 3 levels) looking for `DOMAIN.md`. Typically at `skills/{domain}/DOMAIN.md`.
- **Reflexions**: Loaded from mem0 semantic memory or `.agentura/reflexion_entries.json`.

## Relationship to agentura.config.yaml

`SKILL.md` defines **what** a single skill does. `agentura.config.yaml` defines **how** skills are orchestrated at the domain level (routing, guardrails, observability, feedback).
