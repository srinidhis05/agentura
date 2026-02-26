# Decision Record Room

## DEC-037: Agent role uses E2B + Claude API (not Claude Code)
**Chose**: E2B sandbox + Anthropic SDK direct tool_use loop
**Over**: Claude Code in Docker, direct Docker exec, no sandbox
**Why**: Better observability (each tool call is a discrete event), lower cost (no Claude Code overhead), Firecracker microVM isolation, clean integration with existing SkillContext→SkillResult pipeline
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
