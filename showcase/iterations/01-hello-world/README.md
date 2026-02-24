# Iteration 1: Hello World

> **Docker parallel:** `docker run hello-world`
> **Agentura parallel:** `agentura run showcase/hello --dry-run`

## What This Proves

A skill is a markdown file. You run it with one command. That's it.

## The Skill

```
hello/
├── SKILL.md                    # ← This IS the agent. No code.
└── fixtures/
    └── sample_input.json       # ← Test data
```

`SKILL.md` has:
- YAML frontmatter (metadata: name, role, model, budget)
- Markdown body (task, output format, guardrails)

That's the entire agent definition. Like a Dockerfile — declarative, readable, versionable.

## Run It

```bash
# Dry run (no API key needed — validates structure)
agentura run hello --dry-run --input showcase/iterations/01-hello-world/hello/fixtures/sample_input.json

# Real run (calls the model via OpenRouter)
export OPENROUTER_API_KEY=your-key
agentura run hello --input showcase/iterations/01-hello-world/hello/fixtures/sample_input.json
```

## What Happens

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ SKILL.md    │────▶│ agentura run   │────▶│ LLM Output  │
│ (markdown)  │     │ (SDK runner) │     │ (JSON)      │
└─────────────┘     └──────────────┘     └─────────────┘
```

1. SDK reads SKILL.md frontmatter → extracts model, budget, role
2. SDK reads SKILL.md body → becomes the system prompt
3. SDK loads input JSON → becomes the user message
4. SDK calls OpenRouter with (system_prompt + user_message)
5. LLM responds → SDK returns SkillResult

No framework code. No Python classes. No boilerplate. Markdown in, JSON out.

## Next: [Iteration 2 — Write Your Own →](../02-write-your-own/)
