# Aspora SDK

Developer tooling for the Aspora skill platform. Create, run, and test skills locally.

## Quick Start

```bash
# Install
cd wealth-copilot
pip install -e "sdk[test]"

# Create your first skill
aspora create skill wealth/suggest-allocation --lang python --role specialist

# Edit the skill definition
# skills/wealth/suggest-allocation/SKILL.md    — task, tools, output format
# skills/wealth/suggest-allocation/aspora.config.yaml — routing, guardrails, observability

# Validate
aspora validate wealth/suggest-allocation

# Run (dry-run, no API key needed)
aspora run wealth/suggest-allocation --dry-run

# Run with model (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your-key
aspora run wealth/suggest-allocation --input skills/wealth/suggest-allocation/fixtures/sample_input.json

# Test
aspora test wealth/suggest-allocation

# List all skills
aspora list
```

## Skill Structure

```
skills/{domain}/{skill-name}/
├── SKILL.md              # Skill definition (prompt + metadata)
├── aspora.config.yaml    # Domain config (routing, guardrails, observability)
├── DECISIONS.md          # Decision record for this skill
├── GUARDRAILS.md         # Anti-patterns to avoid
├── code/
│   └── handler.py        # Optional custom logic (most skills are prompt-only)
├── tests/
│   ├── test_deepeval.py  # DeepEval quality tests
│   └── test_promptfoo.yaml  # Promptfoo regression tests
└── fixtures/
    └── sample_input.json # Test input data
```

## Skill Format

Skills are **config + markdown, not code**. The primary definition is `SKILL.md` — a markdown file with YAML frontmatter describing the task, available tools, output format, and examples. The LLM executes the skill based on this prompt.

Add a `handler.py` only when you need custom pre/post-processing logic beyond what the LLM can do from the prompt alone.

## Commands

| Command | Description |
|---------|-------------|
| `aspora create skill <domain>/<name>` | Scaffold a new skill |
| `aspora run <domain>/<name>` | Execute skill locally |
| `aspora test <domain>/<name>` | Run DeepEval + Promptfoo tests |
| `aspora validate <domain>/<name>` | Validate structure + config |
| `aspora list` | List all skills in workspace |
| `aspora get skills` | List skills from gateway |
| `aspora get domains` | List domains (namespaces) |
| `aspora get executions` | List execution history |
| `aspora get events` | List platform events |
| `aspora get threads` | Group executions by session/thread |
| `aspora memory status` | Memory store status |
| `aspora memory search "query"` | Search shared memory |
| `aspora memory prompt <domain>/<name>` | Assembled prompt |
| `aspora replay <execution-id>` | Re-run a past execution |

## Architecture Decisions

This SDK embeds the Engineering Brain principles into templates:

- **DEC-004**: Skills live in `skills/{domain}/{name}/` (marketplace model)
- **DEC-005**: `--lang` flag supports Python/TypeScript/Go handlers
- **DEC-006**: Feedback config enabled by default (corrections → tests)
- **DEC-008**: Observability section in every config
- **DEC-011**: `--role` sets manager/specialist/field isolation

See `DECISIONS.md` in the project root for full decision record.
