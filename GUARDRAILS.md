# Guardrails — Anti-Patterns and Rules

## GR-001: No custom Docker images per skill
**Mistake**: Created Dockerfile.deployer to bake kubectl into a sandbox image for the deployer skill, plus SandboxConfig image override, RBAC, and service account plumbing.
**Impact**: 7 files changed for what should have been a 2-file change. Violated YAGNI, DEC-043 (one sandbox-runtime image), and the project's core pattern: new flow = new skill + LLM prompt.
**Rule**: Onboarding a new flow MUST NOT require a new Docker image, new RBAC, or new infrastructure. If it does, the design is wrong. Skills generate output; the executor/pipeline handles infrastructure actions.
**Detection**: Any PR that adds a `Dockerfile.*` for a skill or modifies sandbox infrastructure to support a single skill.

## GR-002: API endpoints must read from configured store, not hardcoded JSON files
**Mistake**: Memory status, search, and execution list endpoints hardcoded reads from `episodic_memory.json` while actual data lived in PostgreSQL via CompositeStore. Dashboard showed 0 skills tracked despite 41 executions in the DB.
**Impact**: Memory dashboard completely broken — search returned nothing, stats showed zeros, users couldn't see their execution history.
**Rule**: Any endpoint that reads execution/correction/reflexion data MUST use the configured store (CompositeStore) first. JSON file reads are only acceptable as a fallback when the store returns empty results.
**Detection**: Any `open()` or `json.load()` call on `episodic_memory.json`, `corrections.json`, or `reflexions.json` without a preceding store query.

## GR-003: Always handle JSON parse errors from LLM API responses
**Mistake**: `openrouter.py` called `json.loads(raw_args)` on tool call arguments from OpenRouter API with no error handling. LLMs occasionally produce malformed JSON (unclosed strings, trailing commas).
**Impact**: Agent skills crashed with "Expecting ',' delimiter" JSON parse error, blocking both direct skill execution and pipeline runs.
**Rule**: Every `json.loads()` call on LLM-generated content MUST be wrapped in try/except with a repair attempt (close unclosed strings/braces/brackets) before falling back to `{"raw_input": raw_args}`.
**Detection**: Any `json.loads()` on a variable named `*args*`, `*response*`, or `*content*` from an LLM API without a try/except block.

## GR-005: Push to srinidhis05 remote only
**Rule**: This repo's remote is `git@github-personal:srinidhis05/agentura.git`. NEVER push to `vance-srinidhi` or any other GitHub account. Always verify with `git remote -v` before pushing.
**Detection**: Any `git push` to a URL containing a username other than `srinidhis05`.

## GR-004: Check actual runtime environment before giving instructions — never assume Docker Compose
**Mistake**: Told user to run `docker compose up` three separate times despite the full Agentura stack (executor, gateway, web, postgres, k8s-mcp) already running as K8s pods in the `agentura` namespace. Also missed deployed todo-list apps from prior pipeline runs.
**Impact**: Wasted user time, eroded trust. User had to correct the same mistake three times.
**Rule**: Before giving "how to run" instructions, ALWAYS run `kubectl get pods -n agentura` (and `kubectl get svc -n agentura` if URLs are needed) to check what's actually running. The production runtime is Kubernetes, not Docker Compose. Docker Compose exists for legacy/local-only use.
**Detection**: Any response containing `docker compose up` or `docker-compose up` without first checking `kubectl get pods`.
