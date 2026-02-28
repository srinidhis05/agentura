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

## GR-006: Sync skills/ to K8s pod after editing — hostPath is not your local filesystem
**Mistake**: Edited `skills/dev/app-builder/agentura.config.yaml` and `SKILL.md` locally, rebuilt the Docker image 3 times and redeployed, but the pod kept using the old config. Skills are volume-mounted via hostPath (`/skills` on the K8s node), not baked into the Docker image.
**Impact**: Three failed deploy cycles. New `executor: claude-code` config never reached the pod. App-builder kept using legacy sandbox executor with the write-loop bug it was supposed to fix.
**Rule**: After editing any file under `skills/`, ALWAYS sync to the pod via `kubectl cp`. The Docker image only packages Python code (`sdk/agentura_sdk/`), not skills. Verify with `kubectl exec -- cat /skills/<path>`.
**Detection**: Any `skills/` file edit followed by `docker build` + `kubectl rollout restart` without a corresponding `kubectl cp` or hostPath sync.

## GR-004: Check actual runtime environment before giving instructions — never assume Docker Compose
**Mistake**: Told user to run `docker compose up` three separate times despite the full Agentura stack (executor, gateway, web, postgres, k8s-mcp) already running as K8s pods in the `agentura` namespace. Also missed deployed todo-list apps from prior pipeline runs.
**Impact**: Wasted user time, eroded trust. User had to correct the same mistake three times.
**Rule**: Before giving "how to run" instructions, ALWAYS run `kubectl get pods -n agentura` (and `kubectl get svc -n agentura` if URLs are needed) to check what's actually running. The production runtime is Kubernetes, not Docker Compose. Docker Compose exists for legacy/local-only use.
**Detection**: Any response containing `docker compose up` or `docker-compose up` without first checking `kubectl get pods`.

## GR-007: Use todo lists for complex multi-step tasks to prevent context loss
**Mistake**: During long multi-file implementation sessions, progress tracking relied on mental state rather than explicit task lists. Context compaction dropped intermediate progress, leading to repeated work and missed steps.
**Impact**: Tasks got partially completed or forgotten after context refresh. User had to remind Claude of remaining work.
**Rule**: For tasks with 3+ steps or multi-file changes, ALWAYS create a TaskCreate todo list at the start. Mark tasks in_progress when starting, completed when done. This survives context compaction and keeps both Claude and the user aligned on what's done vs. pending.
**Detection**: Any multi-file implementation plan without corresponding TaskCreate calls.

## GR-008: Never hardcode max_tokens below 8192 for agent skills with structured output
**Mistake**: ptc-worker/main.py had `max_tokens=4096` hardcoded. The deployer skill generates K8s ConfigMap YAML containing full HTML file contents inside `kubectl_apply` tool calls — easily 6000+ tokens. When hit, `stop_reason` became `"max_tokens"` not `"tool_use"`, and the code discarded the partial tool call silently.
**Impact**: 5+ deployer pipeline runs appeared to succeed (`iterations_count: 0`, cost $0.07+) but created zero K8s resources. The model was generating correct tool calls that got truncated and silently dropped.
**Rule**: Never hardcode `max_tokens` below 8192 for any agent skill that generates structured output (YAML, JSON, code) containing embedded file contents. Use SandboxConfig.max_tokens (default 16384) and always handle `stop_reason="max_tokens"` with continuation logic.
**Detection**: Any hardcoded `max_tokens` value below 8192 in executor or worker code, or any agent loop that doesn't handle `stop_reason="max_tokens"`.

## GR-009: ExecuteRequest requires input_data wrapper — raw top-level fields silently ignored
**Mistake**: Sent `{"description": "build a counter app"}` directly to `/v1/skills/deployer/execute` but `ExecuteRequest` model expects `{"input_data": {"description": "..."}}`. The `input_data` field defaults to `{}` when the key is missing, so the skill received empty input with no error.
**Impact**: Agent executed with empty prompt context, wasting tokens and producing generic responses instead of actual work.
**Rule**: All direct API calls to execute endpoints MUST wrap payload in `{"input_data": {...}}`. When debugging "agent did nothing useful", always check whether `input_data` is actually populated.
**Detection**: Any curl/httpx call to `/execute` or `/execute-stream` where the JSON body lacks an `input_data` key.
