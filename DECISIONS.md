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
**Constraint**: SERVICE.md < 5KB; ai-velocity skills truncated at 30K chars

## DEC-040: PR pipeline uses sequential skill execution with async gateway dispatch
**Chose**: Go gateway responds 200 immediately, dispatches async; Python orchestrator runs skills sequentially
**Over**: Parallel skill execution, queue-based pipeline, GitHub Actions integration
**Why**: Sequential allows each skill to use prior skill output (test-writer → test-runner); async avoids GitHub 10s timeout; simpler than queue for POC
**Constraint**: Gateway MUST respond within 10s; pipeline failure in one skill MUST NOT block others

## DEC-041: SDLC stages defined as YAML config in ai-velocity, not hardcoded in SDK
**Chose**: `sdlc.yaml` in ai-velocity root with stage → skill mappings, read by skill_mapper
**Over**: Hardcoded Python dict in skill_mapper, per-skill SDLC tags in frontmatter
**Why**: Config-driven (CLAUDE.md principle), single source of truth, human-reviewable, git-versionable; decouples SDK code from skill inventory changes
**Constraint**: AI_VELOCITY_DIR must be set for expertise injection; pipeline degrades gracefully without it

## DEC-042: Isolated skill execution via ExecutionDispatcher pattern
**Chose**: Gateway dispatches executions via interface (proxy/docker/k8s), K8s operator creates Jobs with configurable runtimeClass (gVisor/Kata)
**Over**: Running all skills in single Python process, sidecar-based isolation, Firecracker-only
**Why**: Config-driven mode switching (CLAUDE.md principle), backward-compatible proxy default, K8s-native with CRDs for production, Docker fallback for local dev
**Constraint**: execution.mode MUST be proxy|docker|kubernetes; K8s mode requires operator + CRDs installed; Docker mode requires Docker socket mounted

## DEC-039: Agent SKILL.md uses phased execution with context gates
**Chose**: 6-phase protocol (Pre-flight → Understand → Plan → Implement → Test → Verify → Deliver)
**Over**: Flat single-prompt agent, multi-agent orchestrator spawning sub-agents
**Why**: Phases prevent context bloat (LC4), lazy skill loading (LC1), fail-fast (LC9); simpler than multi-agent for POC
**Constraint**: Each phase MUST have a context gate (3-sentence summary); ai-velocity skills loaded only at the phase that needs them

## DEC-044: Multi-skill workflow via artifact extraction + context_for_next chaining
**Chose**: Extract sandbox files to /artifacts hostPath volume; chain skills via SkillResult.context_for_next injected into next skill's input_data; SSE pipeline streaming endpoint
**Over**: GitHub as handoff, shared PVC between sandbox pods, S3 artifact store
**Why**: Zero external deps, uses existing context_for_next field (types.py:142), consistent with sequential pipeline pattern from github_pr.py; /artifacts volume is simple hostPath for POC
**Constraint**: Pipeline steps MUST be sequential; artifact extraction runs before sandbox.close(); deployer is an agent skill that runs kubectl in its sandbox

## DEC-043: K8s/Docker sandbox via factory pattern
**Chose**: Factory in `sandbox/__init__.py` selects backend (docker|k8s) via `SANDBOX_BACKEND` env var; sandbox-runtime FastAPI container serves tool endpoints
**Over**: E2B cloud sandbox, direct pod exec via kubectl, WebSocket-based sandbox protocol
**Why**: Zero cloud dependency, same interface for all backends, config-driven (CLAUDE.md principle), local dev via Docker fallback
**Constraint**: SANDBOX_BACKEND must be docker|k8s; K8s mode requires executor ServiceAccount with pod CRUD RBAC; sandbox-runtime image must be pre-built

## DEC-045: Deployer specialist generates K8s manifests, executor applies via kubectl
**Chose**: Deployer remains specialist (generates k8s_manifest YAML), executor post-processor writes manifest to file and runs `kubectl apply`; SandboxConfig extended with `image`, `service_account`, `mount_artifacts` for future agent-role skills
**Over**: Custom deployer sandbox image with kubectl baked in, agent-role deployer running kubectl inside sandbox
**Why**: Onboarding a new flow = add a skill + let the LLM generate output; no custom Docker images per skill (DEC-043 constraint); executor already has SA with RBAC; specialist is simpler and cheaper than agent for deterministic template generation
**Constraint**: Executor pod must have kubectl binary and SA with apps/deployments + core/services RBAC; deployer output must include `k8s_manifest` key

## DEC-046: MCP servers as pluggable tool providers for agent skills
**Chose**: Dedicated MCP server per infrastructure domain (k8s-mcp for kubectl), agent executor dynamically discovers tools via HTTP GET /tools, dispatches via POST /tools/call; deployer upgraded from specialist to agent with MCP tool bindings
**Over**: Baking kubectl into executor pod (DEC-045), embedding infrastructure logic in Python post-processors, hardcoded tool sets per skill
**Why**: MCP servers are plugins — K8s MCP today, GitHub Actions / ECS / Terraform MCP tomorrow; same agent executor code, zero code changes to onboard new flows; deployer as agent can verify its own deployment via kubectl_get
**Constraint**: MCP servers MUST expose /health, /tools, /tools/call endpoints; tool bindings configured in agentura.config.yaml mcp_tools section; server URLs resolved via MCP_{SERVER}_URL env vars

## DEC-047: Pipeline registry as YAML config (new pipeline = new YAML file)
**Chose**: `pipelines/` directory at repo root with one YAML per pipeline; generic engine.py loads config and iterates steps; generic endpoints at `/api/v1/pipelines/{name}/execute[-stream]`
**Over**: Hardcoded pipeline functions per workflow (run_build_deploy, run_github_pr), per-pipeline Go handlers and TS functions
**Why**: Config-driven (CLAUDE.md principle) — adding a new pipeline requires zero code changes across Python/Go/TS; existing build-deploy pipeline is backward-compatible thin wrapper
**Constraint**: Pipeline YAML MUST have name + steps[].skill; input_mapping is optional; steps execute sequentially with context_for_next chaining

## DEC-048: Domain-level agent picker (not individual skills)
**Chose**: Chat picker shows domains (Dev, HR, Finance) and pipelines as entry points; triage internally routes to specialist skills within the selected domain
**Over**: Showing individual specialist skills (App Builder, TestGen, Deployer) directly in the picker
**Why**: Users think in workflows ("I need dev help"), not in skill names; matches ChatGPT GPTs / Coze pattern; keeps specialist routing as an internal concern; reduces cognitive load
**Constraint**: Picker MUST show domains + pipelines only; platform domain and manager-role skills are hidden; scoped conversations skip classifier but still use domain triage

## DEC-049: API endpoints read from store first, JSON file fallback
**Chose**: Memory/execution API endpoints read from CompositeStore (PostgreSQL) first, fall back to JSON files only if store returns empty
**Over**: Hardcoded JSON file reads, store-only with no fallback
**Why**: Production data lives in PostgreSQL via CompositeStore; JSON files are stale snapshots from early dev; fallback preserves backward compat for fresh installs without DB
**Constraint**: Any new API endpoint that reads execution/correction/reflexion data MUST use store.get_*() methods first

## DEC-050: ECM skills use agent role with MCP tool bindings in agentura.config.yaml
**Chose**: ECM manager skills converted to agent role with MCP bindings (ecm-gateway for Redshift + Sheets) configured in agentura.config.yaml
**Over**: Claude Code --print execution, specialist role with post-processors, direct API calls
**Why**: Agent role provides sandbox isolation + observable tool_use loop; MCP bindings are config-driven (DEC-046 pattern); ecm-gateway already exists as production MCP server
**Constraint**: ECM skills MUST use ecm-gateway MCP server only; MCP_ECM_GATEWAY_URL env var required on executor pod

## DEC-051: Slack notifications as post-execution hooks in config
**Chose**: Notification dispatch in agentura.config.yaml (channel, config, on triggers) with SlackNotifier posting via chat.postMessage API
**Over**: Baking Slack posting into skill prompts, separate notification microservice, webhook-based notifications
**Why**: Config-driven (CLAUDE.md principle); skill prompts stay focused on domain logic; notification config is per-skill; threading supported for structured output
**Constraint**: SLACK_BOT_TOKEN env var required; notifications are fire-and-forget (failure does not block execution result)

## DEC-052: ECM daily flow uses staggered cron entries 10min apart
**Chose**: Individual cron triggers per skill (1:30, 1:40, 1:50 UTC) instead of pipeline-based sequential scheduling
**Over**: Single pipeline cron that runs all 3 phases sequentially, parallel execution with dependencies
**Why**: Staggered cron allows each skill to run independently; failure in one does not block others; pipeline endpoint exists for on-demand full flow; simpler scheduler logic
**Constraint**: Gateway scheduler timeout MUST be >= 10min for ECM skills (600s timeout)

## DEC-053: File-based IPC uses exec model for phase 1
**Chose**: Executor creates sandbox pod, uses K8s exec API to write/read files to /ipc/ directory inside sandbox pod
**Over**: Shared PVC between pods, sidecar model, WebSocket-based protocol
**Why**: Avoids shared volumes across pods (complex lifecycle); K8s exec is available via existing SA RBAC; file IPC protocol is simple JSON request/response; backward compatible (SANDBOX_IPC_MODE=http is default)
**Constraint**: SANDBOX_IPC_MODE must be http|file; file mode requires kubernetes Python SDK with exec support

## DEC-054: ECM skills live in ai-velocity repo, mounted into executor
**Chose**: ECM skills in ai-velocity/work-plugins/ecm-operations/agentura-skills/, mounted as /skills/ecm via hostPath volume
**Over**: Duplicating ECM skills in public agentura repo, gitignore with symlinks, separate private repo
**Why**: ECM contains company-specific business logic (SQL queries, runbooks, stuck-reasons); agentura repo stays public; single source of truth in ai-velocity; zero duplication
**Constraint**: Executor deployment MUST mount ecm-skills volume at /skills/ecm; K8s node must have ai-velocity repo at /ecm-skills hostPath
