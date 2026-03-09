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

## GR-010: Challenge inspiration-driven features — demand evidence before building
**Mistake**: User shared patterns from an external repo (awesome-agentic-patterns). Claude immediately designed a 31-file, 5-feature implementation plan and built it. No one asked: "Do we have enough execution data for MemRL scoring to matter? Are any skills running in production daily? What's the actual failure rate?" The features are well-engineered but solve problems that don't exist yet — zero skills had `capture_failure_cases` enabled, zero evals existed, and the system lacked the execution volume for synthesis or utility scoring to produce meaningful results.
**Impact**: 2,600+ lines of code that sits as potential energy. Development time spent on meta-learning infrastructure instead of getting real workloads running through the platform. Opportunity cost of not fixing the actual bottleneck (adoption and real usage).
**Rule**: When the user brings an external idea (X post, paper, repo pattern), Claude MUST ask three questions before designing or building:
1. **"What specific problem are you hitting today that this solves?"** — If the answer is "none yet" or "I think we might need it", the next step is observation/measurement, not implementation.
2. **"Do we have evidence this is the bottleneck?"** — Check actual execution counts, failure rates, and usage patterns. Run `kubectl get pods` and query the DB if needed.
3. **"What's the cheapest way to validate this matters?"** — A spreadsheet, a manual test, a 20-line script, or a config change beats a 31-file implementation plan every time.
Only proceed to implementation if at least question 1 has a concrete, evidence-backed answer. "It would be cool" is not evidence. "Our deployer fails 30% of the time and the failures repeat the same pattern" is evidence.
**Detection**: Any implementation plan with 10+ files that doesn't reference specific production metrics, failure rates, or user-reported problems. Any feature that requires execution volume to function (scoring, synthesis, pattern detection) built before that volume exists.

## GR-011: Agent skills with git/PR delivery MUST have mechanical completion enforcement
**Mistake**: Incubator builder SKILL.md files had git push + PR creation as a separate late phase (Phase 4-6). The claude-agent-sdk `query()` terminates on `end_turn` (text-only response). After completing code generation (~30 turns), the agent naturally summarized its work — triggering `end_turn` — and never reached the push/PR phase. Adding "CRITICAL: you MUST create a PR" directives to the prompt had zero effect because `end_turn` is a mechanical SDK behavior, not a prompt-interpretable instruction.
**Impact**: 5 failed builder executions. Each used ~$1.00 and ~35 turns correctly generating code, but produced zero PRs. Agent "succeeded" from the SDK's perspective (no error) but failed the actual goal.
**Rule**: For skills where the deliverable requires side effects (git push, PR creation, API calls), NEVER rely on prompt text to ensure delivery. Use mechanical enforcement: (1) the cc-worker continuation loop — if TASK_RESULT.json doesn't exist after the main query, automatically retry with a completion prompt, and (2) structure the SKILL.md so that push/PR commands are interleaved with code generation, not in a separate late phase.
**Detection**: Any SKILL.md where git push or PR creation appears as a separate phase after code generation, without the cc-worker continuation mechanism enabled.

## GR-017: After executor pod restart, MUST restart gateway AND web pods
**Mistake**: Restarted executor pod (new IP), but gateway cached old executor IP in Go HTTP client and web cached old gateway IP in Node.js HTTP client. Both got `connection refused` → 502/500 cascade.
**Impact**: All skill executions failed across both UI and Slack for 15+ minutes while debugging DNS caching.
**Rule**: After executor pod restarts (for any reason), ALWAYS restart gateway, then web pods. Order matters.
**Detection**: Any `kubectl rollout restart deployment/executor` not followed by gateway + web restarts.

## GR-018: mcp_tools config must use dict format, not string list
**Mistake**: `mcp_tools: [ecm-gateway]` in config.yaml. The executor at `app.py:546` calls `mcp_ref.get("server", "")` — expects dicts, not strings. String format silently fails.
**Impact**: Agent skill launched PTC worker but no MCP tools were bound — worker returned "No MCP tools discovered".
**Rule**: `mcp_tools` must be `[{server: "name", tools: [tool1, tool2]}]`, never `["name"]`.
**Detection**: Any `mcp_tools:` entry that's a plain string instead of a dict.

## GR-019: Skill output must never offer follow-up options (single-shot agents)
**Mistake**: LLM generated "Would you like me to: 1. Query deeper? 2. Update sheet?" in Slack output. User selected an option, bot couldn't continue — showed help text instead.
**Impact**: User confusion; broken UX expectation.
**Rule**: Add "NEVER offer follow-up options" guardrail to every SKILL.md. Skills are single-shot — they cannot respond to follow-ups.
**Detection**: Any SKILL.md missing the no-follow-up guardrail.

## GR-020: MCP tool defs from external servers must be sanitized before Anthropic API (2026-03-08)
**Mistake**: Passed raw MCP tool definitions (containing `annotations`, `title`, `outputSchema` fields) to Anthropic Messages API. API rejected with `Extra inputs are not permitted`.
**Impact**: PTC worker discovered all 64 tools successfully but every execution failed at the LLM call.
**Rule**: ALWAYS strip MCP tool defs to only `{name, description, input_schema}` before passing to Anthropic. Never forward extra MCP fields.
**Detection**: Any `tools=` parameter to Anthropic API containing fields other than `name`, `description`, `input_schema`.

## GR-021: Wildcard `"*"` in allowed_mcp_tools must be handled as "allow all" (2026-03-08)
**Mistake**: Config `tools: ["*"]` produced `allowed_mcp_tools = ["*"]`. Filter code checked `if name not in allowed_tools` — literal `"*"` matched nothing, so ALL tools were silently filtered out.
**Impact**: PTC worker discovered 64 tools but passed 0 to the agent. "No MCP tools discovered" despite successful MCP connectivity.
**Rule**: ALWAYS check `"*" not in allowed_tools` before applying the tool name filter. `"*"` means allow all.
**Detection**: Any tool filtering loop that doesn't handle `"*"` as a wildcard.

## GR-022: Never commit marketing, social media, or internal strategy content to a public repo
**Mistake**: Generated `docs/LINKEDIN_POST.md` containing product positioning, competitor comparisons, cost/latency metrics, and internal tool names (Granola, ClickUp, Slack workflows) — then committed and pushed it to the public repo.
**Impact**: Exposed internal tooling choices, pricing data, and go-to-market strategy to anyone browsing the repo. Social media drafts in a codebase signal immaturity and leak competitive intent.
**Rule**: NEVER commit marketing copy, social media drafts, investor pitches, internal strategy docs, or competitive analysis to a public repo. These belong in private docs (Notion, Google Docs, private repo). Before committing any `.md` file under `docs/`, verify it is technical documentation (architecture, onboarding, API reference), not business/marketing content.
**Detection**: Any file under `docs/` containing LinkedIn, Twitter/X, social media, investor, pitch, or marketing language. Any committed file with `#AIAgents #OpenSource` style hashtags.

## GR-012: "Done" means deployed, not compiled
**Mistake**: After writing UI changes and fixing a backend bug, verified only that `next build` succeeded. Did not build Docker images or restart K8s pods. Changes sat on disk for the rest of the session while the user assumed they were live.
**Impact**: User had to explicitly ask "are the changes deployed?" — wasted time, eroded trust.
**Rule**: In this K8s-based project, a task is not complete until the full loop runs: code → docker build → kubectl rollout restart → verify pods are Running. A passing `next build` or `pytest` is a mid-step, not the finish line.
**Detection**: Any session where file writes are followed by a build check but no `docker build` + `kubectl rollout restart` for the affected service.
