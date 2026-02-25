# Memory System & Feedback Loop

> **Purpose**: How skills learn from corrections — the feedback loop, data schemas, memory store backends, and CLI commands.

Agentura skills improve over time through a correction-driven feedback loop. When a user corrects a skill's output, the system generates a reflexion rule, auto-creates regression tests, and injects the learned rule into future executions — no code changes needed.

```
Execute skill  →  User corrects output  →  Reflexion rule generated
     ↑                                            ↓
     └──── Rule injected into next execution ←────┘
```

## Table of Contents

1. [How It Works](#how-it-works)
2. [The 4-Layer Prompt Hierarchy](#the-4-layer-prompt-hierarchy)
3. [Data Schemas](#data-schemas)
4. [CLI Reference](#cli-reference)
5. [Memory Store Backends](#memory-store-backends)
6. [Domain Isolation](#domain-isolation)
7. [FAQ](#faq)

---

## How It Works

### Step 1: Execute a skill

```bash
agentura run hr/resume-screen --input fixtures/sample_input.json
```

The execution is logged to `.agentura/episodic_memory.json` with the full input, output, cost, latency, and model used. Each execution gets an ID like `EXEC-20260220124341`.

### Step 2: Correct the output

```bash
agentura correct hr/resume-screen \
  --execution-id EXEC-20260220124341 \
  --correction "When screening for senior backend roles, system design experience should be weighted separately from coding skills. A candidate with 5 years Python but no distributed systems should score below 60."
```

This triggers a pipeline:

| Stage | What happens | Output |
|-------|-------------|--------|
| **Store correction** | Saves the user's feedback linked to the execution | `CORR-003` in `corrections.json` |
| **Generate reflexion** | Extracts a reusable rule from the correction | `REFL-003` in `reflexion_entries.json` |
| **Generate test** | Creates a DeepEval regression test | `tests/generated/test_correction_3.py` |
| **Update guardrails** | Appends anti-pattern to `GUARDRAILS.md` | New bullet in skill's guardrails |

### Step 3: Next execution is improved

When the skill runs again, `load_reflexion_entries()` injects all relevant reflexion rules into the system prompt as Layer 2 of the 4-layer hierarchy:

```
## Learned Rules (from past corrections)

- **REFL-003** (confidence: 96%): When screening resumes for engineering roles,
  ALWAYS check for system design experience separately from coding skills.
  A candidate with 5 years of Python but no distributed systems experience
  should score below 60 for senior roles.
  _Applies when_: resume_text and job_description are provided, role is Senior Backend Engineer.
```

The LLM sees this rule as part of its system prompt and adjusts its behavior accordingly.

---

## The 4-Layer Prompt Hierarchy

When a skill executes, its system prompt is assembled from up to 4 layers:

```
Layer 0: WORKSPACE.md    — Organization-wide policies (e.g., "never log PII")
Layer 1: DOMAIN.md       — Domain identity & voice (e.g., HR domain guidelines)
Layer 2: Reflexions      — Learned rules from past corrections (auto-generated)
Layer 3: SKILL.md        — Task-specific prompt (what the skill does)
```

| Layer | Source | Owner | Scope |
|-------|--------|-------|-------|
| 0 | `skills/WORKSPACE.md` | Platform admin | All skills, all domains |
| 1 | `skills/{domain}/DOMAIN.md` | Domain lead | All skills in one domain |
| 2 | `.agentura/reflexion_entries.json` or mem0 | Auto-generated | Per-skill |
| 3 | `skills/{domain}/{skill}/SKILL.md` | Skill author | One skill |

Each layer is optional except Layer 3. Missing layers are silently skipped.

**File discovery**: WORKSPACE.md and DOMAIN.md are found by walking up from the skill directory. Reflexions are loaded from mem0 (semantic search) or JSON (exact skill match).

---

## Data Schemas

All data is stored in `.agentura/` at the project root. Three files form the memory system:

### episodic_memory.json — Execution Records

Every skill execution is logged here. This is the source of truth for the activity feed and execution history.

```json
{
  "entries": [
    {
      "execution_id": "EXEC-20260220124341",
      "skill": "hr/resume-screen",
      "timestamp": "2026-02-20T12:43:41.681444+00:00",
      "input_summary": {
        "candidate": "Jane Smith",
        "role": "Data Engineer"
      },
      "output_summary": {
        "overall_score": 72,
        "recommendation": "proceed_to_interview"
      },
      "outcome": "accepted",
      "cost_usd": 0.0093,
      "latency_ms": 1062,
      "model_used": "anthropic/claude-haiku-4-5-20251001"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `execution_id` | string | Auto-generated: `EXEC-{YYYYMMDDHHMMSS}` |
| `skill` | string | Format: `domain/skill-name` |
| `timestamp` | string | ISO 8601 UTC |
| `input_summary` | object | Raw input passed to the skill |
| `output_summary` | object | Structured output or raw LLM response |
| `outcome` | string | `accepted` \| `rejected` \| `pending_review` |
| `cost_usd` | float | Total API cost for this execution |
| `latency_ms` | float | Wall-clock time in milliseconds |
| `model_used` | string | Model identifier (e.g., `anthropic/claude-sonnet-4.5`) |

### corrections.json — User Feedback

Stores corrections linked to specific executions.

```json
{
  "corrections": [
    {
      "correction_id": "CORR-003",
      "execution_id": "EXEC-20260220124341",
      "skill": "hr/resume-screen",
      "timestamp": "2026-02-20T18:28:32.091440+00:00",
      "original_output": {
        "overall_score": 72,
        "recommendation": "proceed_to_interview"
      },
      "user_correction": "System design experience should be weighted separately from coding skills..."
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `correction_id` | string | Auto-generated: `CORR-{NNN}` (1-indexed) |
| `execution_id` | string | References the execution being corrected |
| `skill` | string | Format: `domain/skill-name` |
| `timestamp` | string | ISO 8601 UTC |
| `original_output` | object | Snapshot of the execution's output |
| `user_correction` | string | Freeform text describing what was wrong and what should change |

### reflexion_entries.json — Learned Rules

The core of the learning system. Each entry is a rule extracted from a correction that gets injected into future skill executions.

```json
{
  "entries": [
    {
      "reflexion_id": "REFL-003",
      "skill": "hr/resume-screen",
      "created_at": "2026-02-20T18:28:36.503554+00:00",
      "correction_id": "CORR-003",
      "mistake": "Original output scored candidate too high; missed lack of system design experience.",
      "root_cause": "Model treated all engineering experience as equivalent.",
      "rule": "When screening resumes for engineering roles, ALWAYS check for system design experience separately from coding skills. A candidate with 5 years of Python but no distributed systems experience should score below 60 for senior roles.",
      "applies_when": "When executing hr/resume-screen for senior engineering roles.",
      "confidence": 0.96,
      "validated_by_test": false,
      "generated_test_ids": []
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reflexion_id` | string | Auto-generated: `REFL-{NNN}` (1-indexed) |
| `skill` | string | Format: `domain/skill-name` |
| `created_at` | string | ISO 8601 UTC |
| `correction_id` | string | References the source correction |
| `mistake` | string | Human-readable description of what went wrong |
| `root_cause` | string | Category: why the model got it wrong |
| `rule` | string | The learned guidance — injected into system prompt |
| `applies_when` | string | Conditions when this rule is relevant |
| `confidence` | float | 0.0–1.0, how certain the rule is correct |
| `validated_by_test` | boolean | `true` if a generated test passes with this rule |
| `generated_test_ids` | list | Test IDs that validate this rule |

**Relationships:**

```
Execution (EXEC-001)
    ↓ user corrects
Correction (CORR-001)  →  references execution_id
    ↓ system extracts rule
Reflexion (REFL-001)   →  references correction_id
    ↓ injected into
Next Execution          →  system prompt includes rule
```

---

## CLI Reference

### Run a skill

```bash
agentura run hr/resume-screen --input fixtures/sample_input.json
```

Executes locally via Pydantic AI. Logs to `episodic_memory.json`.

### Correct an execution

```bash
agentura correct hr/resume-screen \
  --execution-id EXEC-20260220124341 \
  --correction "The score should be lower because..."
```

Full pipeline: correction → reflexion → test → guardrail update.

### View memory status

```bash
agentura memory status
```

Shows store type and counts:
```
Store: JSONStore
Executions: 15  |  Corrections: 3  |  Reflexions: 3  |  Tests: 5
```

### Search memory

```bash
agentura memory search "compliance check" -n 5
```

Semantic search across reflexions and executions (requires mem0 backend for semantic matching; JSON backend returns all entries for the skill).

### View assembled prompt

```bash
agentura memory prompt hr/resume-screen
```

Shows the full 4-layer system prompt that would be sent to the LLM, including any injected reflexion rules.

### Watch executions live

```bash
agentura watch                       # all skills
agentura watch --skill hr/triage     # filtered
```

Real-time table of executions with outcome, cost, and latency.

---

## Memory Store Backends

The system supports multiple storage backends, selected automatically based on available credentials:

| Priority | Backend | When selected | Capabilities |
|----------|---------|---------------|-------------|
| 1 | **CompositeStore** (PostgreSQL + mem0) | `DATABASE_URL` + LLM API key | Full: SQL queries + semantic search |
| 2 | **PgStore** (PostgreSQL only) | `DATABASE_URL` set | SQL queries, no semantic search |
| 3 | **Mem0Store** (mem0 only) | LLM API key set (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`) | Semantic search, vector storage |
| 4 | **JSONStore** (local files) | Fallback — always works | File-based, exact matching only |

All backends implement the same `MemoryStore` protocol:

```python
class MemoryStore(Protocol):
    def log_execution(self, skill_path: str, data: dict) -> str
    def add_correction(self, skill_path: str, data: dict) -> str
    def add_reflexion(self, skill_path: str, data: dict) -> str
    def get_reflexions(self, skill_path: str) -> list[dict]
    def search_similar(self, skill_path: str, query: str, limit: int = 5) -> list[dict]
    def get_executions(self, skill_path: str | None = None) -> list[dict]
    def get_corrections(self, skill_path: str | None = None) -> list[dict]
    def get_all_reflexions(self) -> list[dict]
    def update_reflexion(self, reflexion_id: str, updates: dict) -> None
```

### Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AGENTURA_KNOWLEDGE_DIR` | Path to `.agentura/` directory | `{project_root}/.agentura` |
| `DATABASE_URL` | PostgreSQL connection for PgStore | — |
| `OPENROUTER_API_KEY` | LLM key for mem0 semantic search | — |
| `ANTHROPIC_API_KEY` | Alternative LLM key for mem0 | — |
| `OPENAI_API_KEY` | Alternative LLM key for mem0 | — |

For local development, JSONStore works out of the box with no configuration.

---

## Domain Isolation

The `DomainScopedStore` wrapper enforces cross-domain memory isolation. An HR skill can only read HR memories.

```python
from agentura_sdk.memory.store import get_scoped_store

# HR agent only sees HR memories
store = get_scoped_store(allowed_domains={"hr"})
store.get_executions()         # only hr/* executions
store.get_all_reflexions()     # only hr/* reflexions

# Unrestricted access
store = get_scoped_store(allowed_domains=None)  # or {"*"}
```

**Write access** is enforced: calling `store.add_reflexion("finance/expense-analyzer", ...)` from an HR-scoped store raises `PermissionError`.

**Read operations** silently filter: `get_executions()` only returns entries where the skill's domain is in `allowed_domains`.

This is used by the gateway's JWT middleware, which extracts `domain_scope` from the token and creates a scoped store per request.

---

## FAQ

**Q: Do I need to set up anything for the feedback loop to work?**
No. JSONStore works immediately with no configuration. Run a skill, correct it, run it again — the reflexion is automatically injected.

**Q: How are reflexion rules injected into the prompt?**
`skill_loader.py` calls `load_reflexion_entries()` which searches for reflexions matching the current skill. Matching rules are formatted as a markdown section and prepended to the skill's system prompt as Layer 2 of the 4-layer hierarchy.

**Q: What happens if a reflexion rule is wrong?**
Edit `.agentura/reflexion_entries.json` directly — remove or modify the entry. There's no CLI command for this yet.

**Q: Can reflexion rules conflict?**
Yes. Multiple corrections can generate contradictory rules. The confidence score helps — higher-confidence rules should take precedence. The LLM resolves conflicts at execution time using its judgment.

**Q: How does semantic search work in mem0?**
When using Mem0Store, `search_similar()` embeds the query and searches a vector store (Qdrant) for reflexions with similar embeddings. This means "check compliance" will match a rule about "regulatory requirements" even if the exact words differ. JSONStore falls back to returning all reflexions for the skill (no semantic matching).

**Q: What tests are auto-generated?**
Two types:
1. **DeepEval test** (`test_correction_N.py`) — Asserts the corrected behavior using DeepEval's LLM-based evaluation
2. **Promptfoo test** (`test_promptfoo.yaml`) — YAML-based test case for the Promptfoo evaluation framework

Run them with `agentura test hr/resume-screen`.

**Q: Where does the confidence score come from?**
The `_generate_reflexion()` function assigns confidence based on how specific and actionable the correction is. A detailed correction with clear rules gets 0.8–1.0. A vague correction like "this is wrong" gets 0.5–0.6.

**Q: Can I manually create reflexion entries?**
Yes. Add entries to `.agentura/reflexion_entries.json` following the schema above. Set `validated_by_test: false` and a reasonable `confidence` score.
