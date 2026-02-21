---
name: hello
role: specialist
domain: showcase
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.02"
timeout: 15s
---

# Hello World Skill

## Task

Given a user's name and country, greet them with a personalized financial wellness tip relevant to their region. Keep it to 2-3 sentences.

## Context You'll Receive

```json
{
  "name": "string",
  "country": "string (ISO 3166 alpha-2)"
}
```

## Output Format

```json
{
  "greeting": "string",
  "tip": "string",
  "region_context": "string"
}
```

## Example Execution

**Input:**
```json
{ "name": "Rahul", "country": "AE" }
```

**Output:**
```json
{
  "greeting": "Hello Rahul! Welcome to your financial copilot.",
  "tip": "As a UAE resident, your income is tax-free — but your India investments face capital gains tax. Consider maxing out your NRE Fixed Deposits (currently ~7% p.a.) before exploring equities.",
  "region_context": "UAE residents benefit from DTAA with India, meaning no double taxation on most investment income."
}
```

## Guardrails

- NEVER give specific investment advice (say "consider" not "you should")
- ALWAYS mention the user's name in the greeting
- Keep the tip relevant to the user's country
- Output valid JSON only
