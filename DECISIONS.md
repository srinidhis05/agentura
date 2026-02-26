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

## DEC-039: Agent SKILL.md uses phased execution with context gates
**Chose**: 6-phase protocol (Pre-flight → Understand → Plan → Implement → Test → Verify → Deliver)
**Over**: Flat single-prompt agent, multi-agent orchestrator spawning sub-agents
**Why**: Phases prevent context bloat (LC4), lazy skill loading (LC1), fail-fast (LC9); simpler than multi-agent for POC
**Constraint**: Each phase MUST have a context gate (3-sentence summary); ai-velocity skills loaded only at the phase that needs them
