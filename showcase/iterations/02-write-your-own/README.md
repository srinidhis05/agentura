# Iteration 2: Write Your Own

> **Docker parallel:** Write a `Dockerfile`, then `docker build && docker run`
> **Agentura parallel:** Write a `SKILL.md`, then `agentura validate && agentura run`

## What This Proves

Anyone can create an AI agent in 5 minutes. No Python. No framework. Just markdown.

## Steps

```bash
# 1. Scaffold (like `docker init`)
agentura create skill demo/my-first --lang python --role specialist

# 2. Edit the skill definition (like editing a Dockerfile)
#    Open skills/demo/my-first/SKILL.md in your editor
#    Change the Task, Output Format, and Guardrails sections

# 3. Validate (like `docker build`)
agentura validate demo/my-first

# 4. Run (like `docker run`)
agentura run demo/my-first --dry-run
agentura run demo/my-first --input skills/demo/my-first/fixtures/sample_input.json
```

## What Gets Scaffolded

```
skills/demo/my-first/
├── SKILL.md              ← The agent (edit this)
├── agentura.config.yaml    ← Orchestration config
├── DECISIONS.md          ← Track decisions
├── GUARDRAILS.md         ← Track anti-patterns
├── code/handler.py       ← Optional custom logic (most skills don't need this)
├── tests/
│   ├── test_deepeval.py  ← Quality tests
│   └── test_promptfoo.yaml ← Regression tests
└── fixtures/
    └── sample_input.json ← Test data
```

## The Key Insight

Just like you don't write Go code to define a Docker container (you write a Dockerfile), you don't write Python code to define an AI agent (you write a SKILL.md).

Code is optional (`handler.py`) — only needed for custom pre/post-processing, just like multi-stage Dockerfiles are optional for simple apps.

## Next: [Iteration 3 — Compose →](../03-compose/)
