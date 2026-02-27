# Guardrails — Anti-Patterns and Rules

## GR-001: No custom Docker images per skill
**Mistake**: Created Dockerfile.deployer to bake kubectl into a sandbox image for the deployer skill, plus SandboxConfig image override, RBAC, and service account plumbing.
**Impact**: 7 files changed for what should have been a 2-file change. Violated YAGNI, DEC-043 (one sandbox-runtime image), and the project's core pattern: new flow = new skill + LLM prompt.
**Rule**: Onboarding a new flow MUST NOT require a new Docker image, new RBAC, or new infrastructure. If it does, the design is wrong. Skills generate output; the executor/pipeline handles infrastructure actions.
**Detection**: Any PR that adds a `Dockerfile.*` for a skill or modifies sandbox infrastructure to support a single skill.
