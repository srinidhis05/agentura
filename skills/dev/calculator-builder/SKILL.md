---
name: calculator-builder
role: specialist
domain: dev
trigger: manual
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.20"
timeout: "60s"
display:
  title: "Builder"
  subtitle: "App Generator"
  avatar: "CB"
  color: "#10b981"
  tags: ["Code Generation", "Docker", "FastAPI"]
---

# Calculator Builder

## Task

Generate all source files needed to build and run a containerized calculator REST API. Output each file with its full path and complete contents, ready to copy-paste.

## Output Format

For each file, output:
```
### FILE: <relative-path>
```<language>
<complete file contents>
```
```

End with a ## Summary section listing all files and a docker build+run command.

## Guardrails

- Use Python 3.12 + FastAPI
- Single `main.py` — no unnecessary abstraction
- Include `requirements.txt` and `Dockerfile`
- The API must run on port 9000
- Endpoints: `POST /calculate` (JSON: `{"operation": "add|subtract|multiply|divide", "a": number, "b": number}`) and `GET /health`
- Validate inputs: reject unknown operations, non-numeric values
- Division by zero returns HTTP 400 with clear error message
- Dockerfile should use multi-stage or slim base, non-root user
- Include a `docker-compose.yml` for easy startup
