# Decision Record Room

## DEC-037: Agent role uses sandbox + multi-provider LLM loop (not Claude Code)
**Chose**: Docker/K8s sandbox + provider-abstracted tool_use loop (OpenRouter primary, Anthropic fallback)
**Over**: Claude Code in Docker, direct Docker exec, no sandbox, E2B cloud sandbox
**Why**: Better observability (each tool call is a discrete event), lower cost (no Claude Code overhead), container isolation, zero cloud dependency, clean integration with existing SkillContext→SkillResult pipeline
**Constraint**: Agent skills MUST define sandbox config in agentura.config.yaml; max_iterations is mandatory

## DEC-038: Service knowledge graph stored as markdown files
**Chose**: .agentura/services/{name}/*.md loaded into LLM context at execution time
**Over**: Neo4j, in-memory Python objects, vector embeddings
**Why**: Human-readable, git-versionable, directly usable as LLM context, matches SKILL.md pattern
**Constraint**: SERVICE.md < 5KB; external skills truncated at 30K chars

## DEC-040: PR pipeline uses sequential skill execution with async gateway dispatch
**Chose**: Go gateway responds 200 immediately, dispatches async; Python orchestrator runs skills sequentially
**Over**: Parallel skill execution, queue-based pipeline, GitHub Actions integration
**Why**: Sequential allows each skill to use prior skill output (test-writer → test-runner); async avoids GitHub 10s timeout; simpler than queue for POC
**Constraint**: Gateway MUST respond within 10s; pipeline failure in one skill MUST NOT block others

## DEC-041: SDLC stages defined as YAML config, not hardcoded in SDK
**Chose**: `sdlc.yaml` with stage → skill mappings, read by skill_mapper
**Over**: Hardcoded Python dict in skill_mapper, per-skill SDLC tags in frontmatter
**Why**: Config-driven, single source of truth, human-reviewable, git-versionable; decouples SDK code from skill inventory changes
**Constraint**: SKILL_LIBRARY_DIR must be set for expertise injection; pipeline degrades gracefully without it

## DEC-042: Isolated skill execution via ExecutionDispatcher pattern
**Chose**: Gateway dispatches executions via interface (proxy/docker/k8s), K8s operator creates Jobs with configurable runtimeClass (gVisor/Kata)
**Over**: Running all skills in single Python process, sidecar-based isolation, Firecracker-only
**Why**: Config-driven mode switching, backward-compatible proxy default, K8s-native with CRDs for production, Docker fallback for local dev
**Constraint**: execution.mode MUST be proxy|docker|kubernetes; K8s mode requires operator + CRDs installed; Docker mode requires Docker socket mounted

## DEC-039: Agent SKILL.md uses phased execution with context gates
**Chose**: 6-phase protocol (Pre-flight → Understand → Plan → Implement → Test → Verify → Deliver)
**Over**: Flat single-prompt agent, multi-agent orchestrator spawning sub-agents
**Why**: Phases prevent context bloat, lazy skill loading, fail-fast; simpler than multi-agent for POC
**Constraint**: Each phase MUST have a context gate (3-sentence summary)

## DEC-044: Multi-skill workflow via artifact extraction + context_for_next chaining
**Chose**: Extract sandbox files to /artifacts hostPath volume; chain skills via SkillResult.context_for_next injected into next skill's input_data; SSE pipeline streaming endpoint
**Over**: GitHub as handoff, shared PVC between sandbox pods, S3 artifact store
**Why**: Zero external deps, uses existing context_for_next field, consistent with sequential pipeline pattern; /artifacts volume is simple hostPath for POC
**Constraint**: Pipeline steps MUST be sequential; artifact extraction runs before sandbox.close(); deployer is an agent skill that runs kubectl in its sandbox

## DEC-043: K8s/Docker sandbox via factory pattern
**Chose**: Factory in `sandbox/__init__.py` selects backend (docker|k8s) via `SANDBOX_BACKEND` env var; sandbox-runtime FastAPI container serves tool endpoints
**Over**: E2B cloud sandbox, direct pod exec via kubectl, WebSocket-based sandbox protocol
**Why**: Zero cloud dependency, same interface for all backends, config-driven, local dev via Docker fallback
**Constraint**: SANDBOX_BACKEND must be docker|k8s; K8s mode requires executor ServiceAccount with pod CRUD RBAC; sandbox-runtime image must be pre-built

## DEC-045: Deployer specialist generates K8s manifests, executor applies via kubectl
**Chose**: Deployer remains specialist (generates k8s_manifest YAML), executor post-processor writes manifest to file and runs `kubectl apply`; SandboxConfig extended with `image`, `service_account`, `mount_artifacts` for future agent-role skills
**Over**: Custom deployer sandbox image with kubectl baked in, agent-role deployer running kubectl inside sandbox
**Why**: Onboarding a new flow = add a skill + let the LLM generate output; no custom Docker images per skill; executor already has SA with RBAC; specialist is simpler and cheaper than agent for deterministic template generation
**Constraint**: Executor pod must have kubectl binary and SA with apps/deployments + core/services RBAC; deployer output must include `k8s_manifest` key

## DEC-046: MCP servers as pluggable tool providers for agent skills
**Chose**: Dedicated MCP server per infrastructure domain (k8s-mcp for kubectl), agent executor dynamically discovers tools via HTTP GET /tools, dispatches via POST /tools/call; deployer upgraded from specialist to agent with MCP tool bindings
**Over**: Baking kubectl into executor pod (DEC-045), embedding infrastructure logic in Python post-processors, hardcoded tool sets per skill
**Why**: MCP servers are plugins — K8s MCP today, GitHub Actions / ECS / Terraform MCP tomorrow; same agent executor code, zero code changes to onboard new flows; deployer as agent can verify its own deployment via kubectl_get
**Constraint**: MCP servers MUST expose /health, /tools, /tools/call endpoints; tool bindings configured in agentura.config.yaml mcp_tools section; server URLs resolved via MCP_{SERVER}_URL env vars

## DEC-047: Pipeline registry as YAML config (new pipeline = new YAML file)
**Chose**: `pipelines/` directory at repo root with one YAML per pipeline; generic engine.py loads config and iterates steps; generic endpoints at `/api/v1/pipelines/{name}/execute[-stream]`
**Over**: Hardcoded pipeline functions per workflow, per-pipeline Go handlers and TS functions
**Why**: Config-driven — adding a new pipeline requires zero code changes across Python/Go/TS; existing build-deploy pipeline is backward-compatible thin wrapper
**Constraint**: Pipeline YAML MUST have name + steps[].skill; input_mapping is optional; steps execute sequentially with context_for_next chaining

## DEC-048: Domain-level agent picker (not individual skills)
**Chose**: Chat picker shows domains and pipelines as entry points; triage internally routes to specialist skills within the selected domain
**Over**: Showing individual specialist skills directly in the picker
**Why**: Users think in workflows ("I need dev help"), not in skill names; keeps specialist routing as an internal concern; reduces cognitive load
**Constraint**: Picker MUST show domains + pipelines only; platform domain and manager-role skills are hidden; scoped conversations skip classifier but still use domain triage

## DEC-049: API endpoints read from store first, JSON file fallback
**Chose**: Memory/execution API endpoints read from CompositeStore (PostgreSQL) first, fall back to JSON files only if store returns empty
**Over**: Hardcoded JSON file reads, store-only with no fallback
**Why**: Production data lives in PostgreSQL via CompositeStore; JSON files are stale snapshots from early dev; fallback preserves backward compat for fresh installs without DB
**Constraint**: Any new API endpoint that reads execution/correction/reflexion data MUST use store.get_*() methods first

## DEC-051: Slack notifications as post-execution hooks in config
**Chose**: Notification dispatch in agentura.config.yaml (channel, config, on triggers) with SlackNotifier posting via chat.postMessage API
**Over**: Baking Slack posting into skill prompts, separate notification microservice, webhook-based notifications
**Why**: Config-driven; skill prompts stay focused on domain logic; notification config is per-skill; threading supported for structured output
**Constraint**: SLACK_BOT_TOKEN env var required; notifications are fire-and-forget (failure does not block execution result)

## DEC-054: Agent-role skills use Claude Agent SDK for execution
**Chose**: Claude Agent SDK (`claude-agent-sdk`) wrapping Claude Code CLI as subprocess for agent-role skills
**Over**: Custom sandbox pods with OpenRouter/Anthropic tool-use loop (DEC-037 approach)
**Why**: Eliminates sandbox pod lifecycle, HTTP tool dispatch, write-loop bugs (read_file 4000-char truncation → rewrite loops), and content truncation; native file tools, built-in streaming, MCP support, cost tracking, turn limits — all battle-tested; specialist/manager roles keep OpenRouter (single-turn, cheaper)
**Constraint**: Requires ANTHROPIC_API_KEY (direct Anthropic, not OpenRouter); legacy agent_executor.py retained as fallback when SDK unavailable; Node.js 20 required in executor image for CLI

## DEC-053: File-based IPC uses exec model for phase 1
**Chose**: Executor creates sandbox pod, uses K8s exec API to write/read files to /ipc/ directory inside sandbox pod
**Over**: Shared PVC between pods, sidecar model, WebSocket-based protocol
**Why**: Avoids shared volumes across pods (complex lifecycle); K8s exec is available via existing SA RBAC; file IPC protocol is simple JSON request/response; backward compatible (SANDBOX_IPC_MODE=http is default)
**Constraint**: SANDBOX_IPC_MODE must be http|file; file mode requires kubernetes Python SDK with exec support

## DEC-055: Worker pod pattern for Claude Code execution
**Chose**: Isolated worker pods (claude-code-worker image) per agent execution, HTTP SSE streaming back to executor
**Over**: In-process Claude Code SDK inside executor pod (DEC-054 phase 1)
**Why**: Container isolation per agent execution; executor stays lightweight (no Node.js, no OOM from concurrent agents); artifacts extracted via SSE result event (no kubectl exec); matches sandbox factory pattern; concurrent requests get separate pods
**Constraint**: Requires SANDBOX_BACKEND=k8s; CLAUDE_CODE_WORKER_IMAGE env var configurable; executor SA needs pod create/delete RBAC

## DEC-056: SSE streaming client uses zero-timeout HTTP client
**Chose**: Separate `streamingClient` in Go gateway with `Timeout: 0` for SSE proxy
**Over**: Single HTTP client with global timeout for all requests
**Why**: Go `http.Client.Timeout` covers entire request lifecycle including body reads; SSE streams run for minutes during agent execution, causing premature termination and "network error" fallback in UI
**Constraint**: Context cancellation from client disconnect provides the safety bound

## DEC-057: PTC executor uses lightweight worker pods for MCP-only agent skills
**Chose**: Isolated PTC worker pods (Python-only, ~200MB image) per execution, same SSE protocol as claude-code-worker; Anthropic Messages API with tool_use dispatching to MCP servers
**Over**: In-process PTC in executor pod (fast but no isolation), full sandbox pods (heavyweight for MCP-only skills)
**Why**: Isolation at scale — concurrent PTC executions in shared executor pod exhaust threads/memory; per-pod resource limits (512Mi/1CPU vs 2Gi/2CPU for claude-code-worker); no Node.js, no sandbox filesystem; consistent with DEC-055 worker pod pattern
**Constraint**: Requires SANDBOX_BACKEND=k8s + ANTHROPIC_API_KEY; executor: ptc in agentura.config.yaml; PTC_WORKER_IMAGE env var configurable

## DEC-058: Two-executor model — light (PTC) + full (Claude Code)
**Chose**: Two domain-agnostic worker images: ptc-worker (MCP-only, Python, 200MB/512Mi) and claude-code-worker (file I/O + code + MCP, Python+Node, 800MB/2Gi); legacy sandbox retained as fallback when SANDBOX_BACKEND != k8s
**Over**: Per-domain custom images, single heavyweight executor for all skills, in-process execution
**Why**: Skills pick executor via config (`executor: ptc|claude-code`), not custom images; onboarding new domains (ECM, HR, finance) requires zero Docker builds; PTC handles 80% of agent skills (MCP-only); claude-code handles the rest (code generation, file manipulation)
**Constraint**: New agent skills MUST set `executor: ptc` or `executor: claude-code` in agentura.config.yaml; legacy sandbox (no executor field) works but is deprecated for new skills

## DEC-059: max_tokens=16384 default for PTC workers (over 4096)
**Chose**: 16384 as default max_tokens for PTC worker agent loop
**Over**: 4096 (original hardcoded value), 8192
**Why**: Deployer skill embeds full HTML artifacts inside K8s ConfigMap YAML in tool_use calls, easily exceeding 4096 tokens. Truncated tool calls caused `stop_reason=max_tokens` instead of `tool_use`, silently failing deployment for 5+ runs with `iterations_count: 0` despite $0.07+ spend per run.
**Constraint**: Never set max_tokens below 8192 for skills that generate structured output containing embedded file contents

## DEC-060: max_tokens configurable via SandboxConfig (over hardcoded)
**Chose**: `max_tokens` field on SandboxConfig, threaded from agentura.config.yaml → ptc_executor.py → PTC worker pod
**Over**: Hardcoded in ptc-worker/main.py, per-skill env var override
**Why**: Different skills need different token budgets — deployer needs 16K+ for embedded HTML, while simple MCP-only skills work fine with 4K. Config-driven aligns with DEC-047 (YAML config pattern).
**Constraint**: SandboxConfig.max_tokens defaults to 16384; skills can override in agentura.config.yaml sandbox section

## DEC-061: Parallel pipeline uses `phases` array in YAML (over DAG syntax)
**Chose**: Flat `phases:` array with `type: parallel|sequential` + `fan_in_from`/`fan_out_from`
**Over**: Full DAG syntax with edges, Airflow-style operator dependencies
**Why**: Simpler to read/write for the 80% case (fan-out parallel, fan-in sequential). DAG syntax adds complexity without benefit for PR review pipelines. Backward-compatible with flat `steps:`.
**Constraint**: Flat `steps:` auto-wraps in single sequential phase; `phases:` takes precedence when present

## DEC-062: Fleet sessions tracked in PostgreSQL (over Redis/in-memory)
**Chose**: `fleet_sessions` + `fleet_agents` tables in existing PostgreSQL DB
**Over**: Redis for session state, in-memory with file persistence
**Why**: Same DB as executions/corrections/reflexions — minimal ops. PostgreSQL handles the query patterns (list by status, join agents). No new infrastructure dependency.
**Constraint**: Requires DATABASE_URL; fleet endpoints return empty/503 without it

## DEC-063: GitHub Checks API for per-agent status (over single comment)
**Chose**: One GitHub check run per parallel agent (Testing, SLT, Docs) + summary comment
**Over**: Single comment with all results, only PR review comments
**Why**: Each agent appears as a separate status check in the PR — developers see at-a-glance which checks passed/failed without reading comments. Summary comment provides detail.
**Constraint**: Requires GitHub App token with `checks:write` permission

## DEC-064: Presigned URLs for artifact transfer (future — inspired by Browser Use)
**Chose**: Sandbox/worker pods request presigned S3 URLs from executor for file upload/download; pods never hold cloud credentials
**Over**: Current approach (artifacts embedded in SSE payload or extracted via kubectl cp)
**Why**: Decouples artifact size from SSE payload limits; eliminates kubectl exec dependency; pods never see AWS credentials; scales to large artifacts (build outputs, test reports)
**Constraint**: Requires S3 bucket + executor IAM role for generating presigned URLs; worker pods need outbound HTTPS to S3; scoped per-session (no cross-session access)
**Status**: Future — not yet implemented

## DEC-065: Environment stripping in worker pod entrypoints (future — inspired by Browser Use)
**Chose**: Worker entrypoints read secrets (ANTHROPIC_API_KEY, etc.) into Python variables at startup, then delete them from os.environ before agent loop begins
**Over**: Current approach (secrets remain in os.environ for pod lifetime, visible via kubectl describe)
**Why**: Defense in depth — if agent code inspects os.environ or runs `env`, secrets are gone; combined with K8s Secrets (secretKeyRef) instead of plain env vars, reduces exposure surface
**Constraint**: Must read all needed secrets before stripping; secrets still visible in K8s pod spec (address with K8s Secrets + RBAC on pod/describe); does not protect against /proc/self/environ reads (requires bytecode-only or seccomp)
**Status**: Future — not yet implemented

## DEC-066: MemRL uses Bayesian smoothing for utility scoring
**Chose**: `(times_helped + 2) / (times_injected + 4)` Bayesian smoothing formula
**Over**: Raw ratio `helped/injected`, exponential moving average, neural scoring
**Why**: Cold-start safe (default 0.5), converges with evidence, no training data needed, single SQL expression
**Constraint**: Minimum 4 injections before utility diverges meaningfully from default; `min_score=0.3` threshold for injection

## DEC-067: Incident-to-eval uses fire-and-forget daemon threads
**Chose**: Daemon thread for failure test generation, never blocks execution response
**Over**: Synchronous post-processing, async task queue, background worker pod
**Why**: Zero latency impact on execution path; test generation is best-effort, not critical path; daemon thread dies with process (no orphans)
**Constraint**: Test generation failures are silently logged, never surfaced to user; requires `feedback.capture_failure_cases: true` in config

## DEC-068: Memory synthesis uses cheap LLM with compact summaries
**Chose**: Haiku via OpenRouter/Anthropic with max 20 entries per skill, 200-char error truncation
**Over**: Full execution log context with expensive model, embedding-based clustering
**Why**: Pattern extraction doesn't need deep reasoning; compact summaries keep token cost <$0.01 per synthesis run; deduplication against existing rules prevents bloat
**Constraint**: `source: "synthesis"` with `confidence: 0.5`; requires manual promotion for high-confidence rules

## DEC-069: Self-critique reuses same agent context (appended message)
**Chose**: Append verification prompt to existing message history, same agent verifies its own output
**Over**: Separate LLM call with fresh context, dedicated verifier agent
**Why**: Maintains conversation coherence; agent can reference its own reasoning; saves cost (no context reconstruction); self-correction uses existing tool access
**Constraint**: Verification uses `VERIFIED:` / `ISSUES:` protocol; max 1 retry by default; read-only tools in worker verification

## DEC-070: Workflow evals use in-process mock MCP server
**Chose**: In-process FastAPI server on random port with canned tool responses
**Over**: Separate mock pod in K8s, record/replay proxy, stub functions
**Why**: Enables CI without K8s cluster; zero infrastructure dependency; tracks tool calls for assertion checking; follows existing `/tools` + `/tools/call` MCP contract
**Constraint**: Evals run with `executor=""` (legacy path, no worker pods); mock server dies with test process; judge assertions require LLM API key

## DEC-076: Skill naming convention — every domain MUST have a "triage" skill
**Chose**: Rename `triage-and-assign` → `triage` to match Web UI convention
**Over**: Updating chat-router.ts to be dynamic
**Why**: `chat-router.ts` hardcodes `executeSkill(domain, "triage", ...)` — every domain must have a skill literally named `triage`
**Constraint**: Skill name in `agentura.config.yaml` must be `triage`, not a variant

## DEC-077: Multi-worker uvicorn (4 workers) for executor stability
**Chose**: `uvicorn.run("...app:app", workers=4)` with `asyncio.to_thread()` for blocking K8s calls
**Over**: Single-worker with health check bypass, sidecar health pod
**Why**: Single-worker uvicorn freezes health checks during long agent executions (blocking `_wait_for_ready` in K8s watch). 4 workers ensure at least one can respond to probes.
**Constraint**: `UVICORN_WORKERS` env var; multi-worker requires app as import string, not object

## DEC-078: Gateway HTTP transport with connection recycling for K8s pod IP changes
**Chose**: Custom `http.Transport` with `IdleConnTimeout: 30s`, `KeepAlive: 15s`
**Over**: Default transport (indefinite connection caching)
**Why**: When executor pod restarts, Go HTTP client caches stale TCP connections to old pod IP → `connection refused`. Short idle timeout forces reconnection.
**Constraint**: After executor pod restart, gateway/web pods MUST also be restarted (GR-017)

## DEC-079: Domain-scoped Slack bots auto-route unmatched messages to triage skill
**Chose**: `dispatchAuto` routes to `{domain}/triage` with user text as input
**Over**: Showing help text for unmatched messages
**Why**: Users expect conversational behavior. When a bot produces output with context, follow-up messages should be handled, not rejected with "I didn't recognize that command"
**Constraint**: Only for domain-scoped bots (`DomainScope != ""`); non-scoped bots still show help

## DEC-080: Per-server MCP endpoints over single aggregated endpoint (2026-03-08)
**Chose**: Individual `/mcp-connect/{server-id}` endpoints per MCP tool (Granola, Notion, Gmail, ClickUp)
**Over**: Single aggregated Obot MCP gateway endpoint
**Why**: Obot deploys each MCP server as a separate nanobot pod; no aggregation endpoint exists. Each server has its own session state.
**Constraint**: Each MCP server MUST have its own `MCP_{NAME}_URL` env var and separate initialize→session flow

## DEC-081: MCP Streamable HTTP session protocol for Obot (2026-03-08)
**Chose**: POST initialize (no session header) → read `Mcp-Session-Id` from response header → use in all subsequent requests
**Over**: Client-generated session IDs, X-Session-Id header, stateless requests
**Why**: Obot's MCP connect proxy requires server-issued session IDs; client-generated IDs return 405
**Constraint**: ALWAYS call `initialize` before `tools/list`; ALWAYS pass `Mcp-Session-Id` from response in subsequent calls

## DEC-082: PTC worker pods use hostNetwork + Default DNS for VPN-routed MCP access (2026-03-08)
**Chose**: `hostNetwork: true` + `dnsPolicy: Default` on PTC worker pods
**Over**: Cluster networking with CoreDNS, VPN sidecar, in-cluster proxy
**Why**: MCP servers (Obot) are on a remote K8s cluster reachable via VPN on the host. Cluster DNS resolves to wrong IP (internal cluster IP, not VPN-routable). Host DNS + host network = VPN routes work.
**Constraint**: Only one PTC worker per node at a time (port 8080 conflict with hostNetwork); future fix: random port assignment

## DEC-083: Client-side Granola meeting privacy filtering via SKILL.md prompt (2026-03-10)
**Chose**: Prompt-level privacy filter in SKILL.md (attendee count check + title keyword exclusion) executed by PTC worker at runtime
**Over**: Server-side Granola MCP filtering, code-level filter in executor, custom MCP proxy
**Why**: Granola MCP exposes only 4 tools (query_granola_meetings, list_meetings, get_meetings, get_meeting_transcript) with natural language queries — no server-side filtering by attendee count or meeting type exists. PTC workers are prompt-driven, so SKILL.md instructions are the enforcement mechanism.
**Constraint**: Filter MUST run BEFORE presenting meetings to user or counting totals; filtered meeting titles MUST NOT appear in any output; config overrides via `exclude_meeting_keywords` and `min_attendees` in project config

## DEC-084: RBAC via triggered_by column + _triggered_by in input_data (2026-03-10)
**Chose**: `triggered_by VARCHAR(200)` column on executions table; user ID passed via `_triggered_by` key in input_data dict; admin bypass via `ADMIN_USER_IDS` env var
**Over**: SkillContext schema change, JWT-based auth middleware, separate auth service
**Why**: Lightweight — no schema changes to SkillContext, no new auth infrastructure. `_triggered_by` underscore prefix avoids collision with skill inputs. Gateway already has `UserID` in `ExecuteRequest`. Admin bypass is a simple env var check.
**Constraint**: Non-admin users ALWAYS see only their own executions; `X-User-ID` header forwarded by gateway; admin IDs comma-separated in env var

## DEC-085: Slack interactive approvals as Block Kit buttons after skill result (2026-03-10)
**Chose**: Parse skill result JSON for `pending_approvals` array, post separate Block Kit message with Approve/Reject buttons; handle clicks via both HTTP webhook and Socket Mode paths
**Over**: Inline approval in skill result message, dashboard-only approval, separate approval service
**Why**: Users (Neha, Ashutosh) explicitly requested "approve in Slack only". Block Kit buttons are native Slack UX. Separate message avoids reformatting the skill result. Both HTTP and Socket Mode paths ensure it works regardless of Slack app configuration.
**Constraint**: Interactive payload handler registered outside auth middleware (same as other webhooks); `response_url` used for message updates; signature verification reuses existing `verifySlackSignature()`

## DEC-086: Thread continuity via gateway-only in-memory registry (2026-03-11)
**Chose**: sync.Map thread registry in gateway keyed by `{app}:{channel}:{threadTS}`, with 30-min TTL and 5-min sweep; thread replies skip triage and route directly to previously matched skill with previous output as context
**Over**: Executor/Python-side thread tracking, Redis/DB-backed thread state, full conversation history replay
**Why**: Zero executor changes — PTC worker receives thread context naturally via `input_data.thread_context`; in-memory is sufficient for demo (no persistence needed across restarts); gateway already owns the Slack dispatch path
**Constraint**: Thread entries expire after 30 min idle; only `auto` (triage-routed) commands register threads; explicit `run`/`pipeline`/`help` bypass thread lookup; `postSlackMessage`/`postSlackThreadReply` now return posted `ts` for registration

## DEC-087: Internal ALB for VPN-accessible web UI + API (2026-03-11)
**Chose**: Internal ALB ingress (`scheme: internal`) routing `/api` → gateway:3001, `/` → web:3000; HTTP:80 only
**Over**: kubectl port-forward, public ALB with auth, CloudFront + WAF
**Why**: VPN-only access is sufficient for internal team use; no TLS overhead needed for private network; single ALB serves both web UI and gateway API
**Constraint**: Requires VPN connectivity to VPC; ALB controller IRSA must be configured (role: `vance-core-infra-mumbai-01-aws-loadbalancer-controller`); private subnets tagged `kubernetes.io/role/internal-elb=1`

## DEC-088: Git-sync init container for org skills from private GitHub repo (2026-03-11)
**Chose**: Init container (`alpine/git`) clones `Vance-Club/agentura-skills` private repo on every pod start; SSH deploy key stored as K8s secret
**Over**: kubectl cp (manual), S3 sync, baking skills into executor image, PVC
**Why**: Org skills stay in org's private repo — never leak into platform repo; auto-syncs on restart; deploy key is read-only; new skills = git push + rollout restart; makes agentura extensible per-org without forking
**Constraint**: `agentura-skills-repo` secret has repo URL + branch; `agentura-skills-repo-key` secret has SSH deploy key; repo must have `skills/`, `pipelines/`, `agency/` at root (paths configurable)

## DEC-089: PDBs + do-not-disrupt annotations to prevent Karpenter consolidation eviction (2026-03-11)
**Chose**: PodDisruptionBudget (`minAvailable: 1`) + `karpenter.sh/do-not-disrupt: "true"` annotation on all core pods (executor, gateway, web, postgres)
**Over**: No disruption protection (default), higher replica counts
**Why**: Karpenter consolidates "underutilized" nodes after PTC/CC worker pods complete, evicting all core pods and wiping emptyDir data. PDBs block voluntary eviction; annotation tells Karpenter to never consider these pods for consolidation.
**Constraint**: With replicas=1 and minAvailable=1, Karpenter cannot voluntarily evict these pods at all; scaling to 2+ replicas would allow rolling disruption

## DEC-090: Comprehensive Slack interaction primitives via config-driven routing (2026-03-14)
**Chose**: Config-driven `interaction_handlers` in SlackAppConfig mapping callback_id → skill/pipeline; unified handler for modals, selects, shortcuts, block actions, overflow menus; works in both HTTP webhook and Socket Mode
**Over**: Hardcoded interaction routing in gateway code, per-interaction handler functions, MCP-based interaction handling
**Why**: Slack interactions (modals, selects, shortcuts) are essential for rich UX but were completely missing — only approval buttons existed. Config-driven routing matches existing pattern (commands, events). Single dispatch mechanism handles all 7 interaction types. Skills receive structured input (form_values, message_text, etc.) and can return outputs, modals, or validation errors.
**Constraint**: InteractionHandler requires callback_id (matches Slack callback_id or action_id); type field is optional (allows wildcard matching); exactly one of skill or pipeline must be specified; form value extraction uses "block_id.action_id" format; executor integration uses direct HTTP calls (not via executor adapter)

## DEC-091: Configurable POD_READY_TIMEOUT to handle cluster resource pressure (2026-03-14)
**Chose**: POD_READY_TIMEOUT env var (default 120s, set to 300s in production) for K8s sandbox and worker pod readiness checks
**Over**: Hardcoded 120s timeout, reducing worker resource requests, aggressive auto-scaling
**Why**: EKS cluster resource pressure during peak hours causes PTC/CC worker pods to exceed 120s startup (image pull + init container + readiness probe). "Peer closed connection" errors blocked all skill executions. Configurable timeout allows cluster-specific tuning without code changes. 300s handles Karpenter node spin-up + image pull on fresh nodes.
**Constraint**: Timeout applies to all K8s sandbox pods and PTC/CC worker pods; set via POD_READY_TIMEOUT env var in executor deployment; must be ≥120s (lower values cause false timeouts on cold starts)
