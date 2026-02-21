# Iteration 3: Compose

> **Docker parallel:** `docker-compose.yaml` → `docker-compose up`
> **Aspora parallel:** `aspora.config.yaml` → `aspora up wealth`

## What This Proves

Multiple skills can be orchestrated declaratively. No code. Just config.

## The Compose File

`aspora.config.yaml` is to skills what `docker-compose.yaml` is to containers:

```yaml
# docker-compose.yaml          # aspora.config.yaml
services:                       domain: wealth
  web:                          skills:
    image: nginx                  - name: risk-assess
    ports: ["80:80"]                role: specialist
  api:                            - name: suggest-allocation
    image: myapi                    role: specialist
    depends_on: [db]
  db:                           routing:
    image: postgres               - from: risk-assess
                                    to: suggest-allocation
                                    condition: output_match("risk_profile != null")
```

## What Happens

```
User asks: "Assess my risk and suggest investments"

┌──────────────┐     routing      ┌─────────────────────┐
│ risk-assess  │────────────────▶│ suggest-allocation  │
│ (specialist) │  passes context  │ (specialist)        │
│              │  risk_profile,   │                     │
│ Output:      │  horizon,        │ Output:             │
│ risk=moderate│  surplus         │ Buy NIFTY 50 SIP    │
└──────────────┘                  └─────────────────────┘
```

## Run It

```bash
# Run the full domain (executes skill chain)
aspora up wealth --input showcase/iterations/03-compose/wealth/fixtures/input.json

# Or run skills individually
aspora run wealth/risk-assess --input fixtures/nri_profile.json
# Output feeds into next skill automatically via routing rules
```

## Files

```
03-compose/wealth/
├── aspora.config.yaml          # Domain orchestration (THE compose file)
├── risk-assess/
│   ├── SKILL.md
│   └── fixtures/nri_profile.json
├── suggest-allocation/
│   ├── SKILL.md
│   └── fixtures/request.json
└── fixtures/
    └── input.json              # End-to-end test input
```

## The Guardrails Layer (no Docker equivalent — this is new)

```yaml
guardrails:
  max_cost_per_session: "$1.00"       # Budget enforcement
  require_human_approval:
    - action: "place_order"
      threshold: "$5000"              # HITL gate
  blocked_actions:
    - "withdraw_funds"                # Hard block
```

Docker doesn't care what your container does. Aspora does — because these are financial agents.

## Next: [Iteration 4 — Test →](../04-test/)
