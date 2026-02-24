# Getting Started with Agentura SDK

## Prerequisites

- Python 3.11+
- pip

## Install

```bash
cd agentura
pip install -e "sdk[test]"
```

Verify:
```bash
agentura --version
```

## Create Your First Skill

```bash
agentura create skill demo/hello --lang python --role specialist
```

This creates:
```
skills/demo/hello/
├── SKILL.md              # Edit this — your skill's brain
├── agentura.config.yaml    # Routing, guardrails, observability
├── DECISIONS.md          # Track decisions
├── GUARDRAILS.md         # Track anti-patterns
├── code/handler.py       # Optional custom logic
├── tests/                # DeepEval + Promptfoo tests
└── fixtures/             # Test input data
```

## Edit Your Skill

Open `skills/demo/hello/SKILL.md`. This is the skill definition — a markdown prompt the LLM follows.

Key sections:
- **Frontmatter**: Skill metadata (name, role, model, budget)
- **Task**: What the skill does
- **Available Tools**: MCP tools the skill can call
- **Output Format**: Expected JSON structure
- **Example Execution**: Input/output pairs
- **Guardrails**: Hard rules the skill must follow

## Validate

```bash
agentura validate demo/hello
```

Checks: required files exist, config is valid, SKILL.md has frontmatter.

## Run

```bash
# Dry run (no API key needed)
agentura run demo/hello --dry-run

# With model (requires OPENROUTER_API_KEY)
export OPENROUTER_API_KEY=your-key
agentura run demo/hello
```

## Test

```bash
agentura test demo/hello
```

Runs DeepEval (quality metrics) and Promptfoo (regression tests).

## SDLC Phases

See [sdlc.md](sdlc.md) for the full skill development lifecycle.

## Next Steps

1. Study the `examples/auto-rca/` domain for a production-grade skill setup
2. Read `DECISIONS.md` in the project root for architecture context
3. Add MCP tools to your skill for real capabilities
