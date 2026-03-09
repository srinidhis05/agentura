# DX Roadmap: From Fragile to Production-Grade

Fixing the 6 pain points in the skill onboarding SDLC — organized as 3 parallel workstreams.

> **Harness Engineering insight**: "The secret isn't the model — it's the harness." OpenAI shipped 1M+ lines of production code with zero human-written source by investing in constraints, feedback loops, and deterministic linters. Our harness (SKILL.md + config + pipeline YAML) is already the right shape. This roadmap makes it reliable.

---

## The 6 Pain Points

| # | Pain Point | Root Cause | $ Cost Per Occurrence |
|---|-----------|------------|----------------------|
| 1 | No local testing for agent skills | Agent loop requires K8s worker pods | $0.50-2.00 per iteration |
| 2 | Silent failures (GR-009/018/020/021) | Validation happens at LLM call, not config load | $0.50+ wasted per silent fail |
| 3 | Deploy is manual and fragile (GR-006) | No `agentura deploy` command | 15-30 min debugging stale configs |
| 4 | Metadata split (SKILL.md vs config.yaml) | Two files define overlapping fields | Confusion, precedence bugs |
| 5 | No skill versioning | mtime-based, no semver/rollback | Risk of regression with no undo |
| 6 | Validation is opt-in | Server discovers broken skills at first request | Broken skill burns LLM budget |

---

## 3 Parallel Workstreams

```
Workstream 1: DX & Testing     Workstream 2: Fail-Fast        Workstream 3: Architecture
(Harness: Observability)        (Harness: Constraints)          (Harness: Entropy Mgmt)
─────────────────────           ─────────────────────           ─────────────────────
Week 1-2:                       Week 1-2:                       Week 1-2:
  agentura deploy                 Startup validation              Metadata consolidation
  agentura test                   input_data validation           plan

Week 3-4:                       Week 3-4:                       Week 3-4:
  Local mock executor             MCP binding validation          Single source of truth
  (basic)                         Error budget alerts              migration

Week 5-6:                       Week 5-6:                       Week 5-6:
  Local mock executor             CI linter (GitHub Action)       Skill versioning
  (MCP mock)                      Pre-deploy validation hook      Rollback support
```

All three workstreams run in parallel. Zero dependencies between them.

---

## Workstream 1: Developer Experience & Testing

**Harness Engineering parallel**: OpenAI's "Observability Integration" — agents use telemetry (logs, metrics, spans) to reproduce bugs in isolated environments. We need the same for skill development.

### 1.1 `agentura deploy` (Week 1 — Small)

**Problem**: GR-006 — editing skills locally, forgetting `kubectl cp`, debugging stale configs for 30 minutes.

**Solution**: Single command that syncs and restarts.

```bash
agentura deploy [domain/skill-name]     # Deploy specific skill
agentura deploy --all                    # Deploy all skills
agentura deploy --pipeline pr-parallel   # Deploy pipeline + its skills
```

**Implementation**:
```python
# sdk/agentura_sdk/cli/deploy.py (new file, ~80 lines)

def deploy(skill_path: str, namespace: str = "agentura"):
    """Sync skill to executor pod, restart gateway if config.yaml changed."""

    # 1. Find executor pod
    pod = _get_pod(namespace, label="app=executor")

    # 2. Validate before deploying
    errors = validate(skill_path)
    if errors:
        print(f"Validation failed — not deploying. Fix {len(errors)} errors first.")
        return

    # 3. kubectl cp skills/{domain}/{name} → pod:/skills/{domain}/{name}
    _kubectl_cp(skill_path, pod, f"/skills/{skill_path}")

    # 4. If gateway config changed, restart gateway + web (GR-017)
    if _gateway_config_changed():
        _restart_deployment(namespace, "gateway")
        _restart_deployment(namespace, "web")

    # 5. Verify
    _kubectl_exec(pod, f"cat /skills/{skill_path}/agentura.config.yaml")
    print(f"Deployed {skill_path} to {pod}")
```

**Files**: 1 new (`cli/deploy.py`), 1 edit (`cli/__init__.py` to register command)
**Effort**: 2-3 hours

### 1.2 `agentura test` (Week 1-2 — Medium)

**Problem**: No way to run fixtures through a skill and assert the output schema matches expectations.

**Solution**: Fixture-driven test runner.

```bash
agentura test support/ticket-responder                    # Run all fixtures
agentura test support/ticket-responder --fixture edge.json # Run specific fixture
agentura test --domain support                             # Run all skills in domain
```

**Implementation**:
```python
# sdk/agentura_sdk/cli/test_runner.py (new file, ~120 lines)

def test_skill(skill_path: str, fixture: str = None):
    """Run fixture through skill, assert output schema."""

    # 1. Load skill + config
    skill = load_skill_md(skill_path)
    config = load_config(skill_path)

    # 2. Load fixtures (all .json in fixtures/ or specific one)
    fixtures = _load_fixtures(skill_path, fixture)

    # 3. For each fixture:
    for fix in fixtures:
        # a. Execute skill (specialist: in-process, agent: --dry-run)
        result = execute_skill(skill, fix.input_data, dry_run=(skill.role == "agent"))

        # b. Assert output matches expected schema from SKILL.md
        schema_errors = _validate_output_schema(result.output, skill.output_schema)

        # c. Assert verify criteria if configured
        if config.verify.enabled:
            verify_errors = _check_verify_criteria(result, config.verify.criteria)

        # d. Report pass/fail
        _report(fix.name, schema_errors, verify_errors)
```

**Files**: 1 new (`cli/test_runner.py`), 1 edit (`cli/__init__.py`)
**Effort**: 4-6 hours

### 1.3 Local Mock Executor (Week 3-6 — Large)

**Problem**: Agent skills can't test without K8s. Every iteration costs $0.50+ and requires `kubectl cp`.

**Solution**: In-process mock executor with canned MCP responses.

```bash
agentura run support/ticket-responder --mock-mcp     # Use mock MCP server
agentura run support/ticket-responder --record-mcp    # Record real MCP responses for replay
agentura run support/ticket-responder --replay-mcp    # Replay recorded responses
```

**Phase 1 (Week 3-4)**: Basic mock — hardcoded tool responses from fixture files.

```python
# sdk/agentura_sdk/testing/mock_mcp.py (new file, ~150 lines)

class MockMCPServer:
    """In-process FastAPI server with canned tool responses."""

    def __init__(self, responses_dir: str):
        self.app = FastAPI()
        self.responses = _load_canned_responses(responses_dir)
        self.tool_calls = []  # Track for assertion

        @self.app.get("/tools")
        def list_tools():
            return [{"name": name, "description": r["description"],
                     "input_schema": r["input_schema"]}
                    for name, r in self.responses.items()]

        @self.app.post("/tools/call")
        def call_tool(request: ToolCallRequest):
            self.tool_calls.append(request)
            return self.responses[request.name]["response"]

    def start(self) -> str:
        """Start on random port, return URL."""
        ...
```

**Phase 2 (Week 5-6)**: Record/replay — record real MCP responses, replay for testing.

```
fixtures/
  mcp_recordings/
    granola/
      search_meetings.json      # Recorded response
      get_transcript.json
    clickup/
      get_tasks.json
```

**Files**: 2-3 new files, 2-3 edits to executor/runner
**Effort**: 15-20 hours total (across 4 weeks)

**Harness Engineering parallel**: This is exactly OpenAI's "isolated development environments" pattern — agents reproduce bugs and iterate in isolation, without touching production infrastructure.

---

## Workstream 2: Fail-Fast Validation

**Harness Engineering parallel**: OpenAI's "Architectural Constraints" — "deterministic linters and LLM-based agents enforcing structural rules." LangChain jumped from 52.8% to 66.5% accuracy by improving their harness, not their model. Our equivalent: catch bad configs before they eat LLM budget.

### 2.1 Startup Validation (Week 1 — Small)

**Problem**: Server discovers broken skills at first request. A typo in config.yaml burns $0.50 before anyone notices.

**Solution**: Scan and validate all skills when the executor starts.

```python
# sdk/agentura_sdk/server/app.py — add to startup event (~30 lines)

@app.on_event("startup")
async def validate_all_skills():
    """Fail-fast: validate every skill at startup."""
    skills_dir = os.environ.get("SKILLS_DIR", "/skills")
    errors = []

    for domain_dir in Path(skills_dir).iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
            continue
        for skill_dir in domain_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_errors = validate_skill(f"{domain_dir.name}/{skill_dir.name}")
            if skill_errors:
                errors.extend(skill_errors)

    if errors:
        logger.error(f"Skill validation failed at startup: {len(errors)} errors")
        for err in errors:
            logger.error(f"  {err}")
        # Log but don't crash — graceful degradation
```

**Files**: 1 edit (`server/app.py`)
**Effort**: 1-2 hours

### 2.2 Strict `input_data` Validation (Week 1 — Small)

**Problem**: GR-009 — `POST /execute` without `input_data` wrapper silently sends `{}` to the skill.

**Solution**: Reject requests with empty `input_data` when the skill's SKILL.md defines an Input section.

```python
# sdk/agentura_sdk/server/app.py — add to execute endpoint (~15 lines)

def _validate_input(request: ExecuteRequest, skill: LoadedSkill):
    """Reject empty input_data when skill expects input fields."""
    if not request.input_data and skill.has_input_section:
        raise HTTPException(
            status_code=422,
            detail=f"Skill '{skill.name}' expects input_data but received empty. "
                   f"Wrap your payload in {{\"input_data\": {{...}}}}. See GR-009."
        )
```

**Files**: 1 edit (`server/app.py`)
**Effort**: 1 hour

### 2.3 MCP Binding Validation (Week 3-4 — Medium)

**Problem**: GR-018/020/021 — MCP tool format errors, raw defs forwarded to Anthropic, wildcard not handled. All discovered at LLM call time.

**Solution**: Validate MCP bindings at config load time, not execution time.

```python
# sdk/agentura_sdk/runner/config_loader.py — add to load_config() (~40 lines)

def _validate_mcp_tools(mcp_tools: list, skill_name: str) -> list[str]:
    """Catch GR-018/020/021 at config load, not at LLM call."""
    errors = []
    for i, tool in enumerate(mcp_tools):
        # GR-018: Must be dict, not string
        if isinstance(tool, str):
            errors.append(
                f"mcp_tools[{i}]: '{tool}' is a string. "
                f"Must be {{server: '{tool}', tools: ['*']}}. See GR-018."
            )
            continue

        # Must have 'server' key
        if "server" not in tool:
            errors.append(f"mcp_tools[{i}]: missing 'server' key.")

        # Must have 'tools' key
        if "tools" not in tool:
            errors.append(f"mcp_tools[{i}]: missing 'tools' key.")

    return errors
```

**Files**: 1-2 edits (`config_loader.py`, `validate.py`)
**Effort**: 3-4 hours

### 2.4 CI Linter — GitHub Action (Week 5-6 — Medium)

**Problem**: Validation is opt-in. Skills can be committed and deployed without validation.

**Solution**: GitHub Action that runs `agentura validate` on every PR touching `skills/`.

```yaml
# .github/workflows/validate-skills.yaml
name: Validate Skills
on:
  pull_request:
    paths: ['skills/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e sdk/
      - run: |
          # Validate only changed skills
          CHANGED=$(git diff --name-only origin/main...HEAD -- 'skills/' | \
            grep -oP 'skills/\K[^/]+/[^/]+' | sort -u)
          for skill in $CHANGED; do
            echo "Validating $skill..."
            agentura validate "$skill"
          done
```

**Harness Engineering parallel**: This is OpenAI's "mechanical rules and structural tests prevent violations of modular layering" — identical pattern, different domain.

**Files**: 1 new (`.github/workflows/validate-skills.yaml`)
**Effort**: 2-3 hours

---

## Workstream 3: Architecture Cleanup

**Harness Engineering parallel**: OpenAI's "Entropy Management" — periodic cleanup agents that "find inconsistencies, documentation drift, and constraint violations." Our entropy: metadata split, no versioning, no rollback.

### 3.1 Metadata Consolidation Plan (Week 1-2 — Analysis)

**Problem**: `name`, `role`, `model`, `cost_budget`, `timeout` exist in both SKILL.md frontmatter AND agentura.config.yaml. Precedence is unclear.

**Decision to make**: Which file is the single source of truth?

| Option | Pros | Cons |
|--------|------|------|
| **A: SKILL.md is truth** | Prompt + config in one file, simpler for authors | config.yaml becomes anemic (just runtime settings) |
| **B: config.yaml is truth** | Clean separation (prompt vs runtime), matches K8s patterns | SKILL.md frontmatter becomes redundant |
| **C: config.yaml is truth, SKILL.md frontmatter is optional display-only** | Backward compatible, clear precedence rule | Still two files, but with defined precedence |

**Recommendation**: Option C — config.yaml is authoritative for all runtime settings. SKILL.md frontmatter is display metadata only (shown in dashboard, not used for execution). Add a single log line when they disagree:

```
WARN: Skill 'support/ticket-responder' has cost_budget=$0.50 in SKILL.md
      but $0.30 in config.yaml. Using config.yaml value.
```

**Effort**: 2-3 hours (analysis + decision doc), 4-6 hours (migration)

### 3.2 Single Source of Truth Migration (Week 3-4 — Medium)

**Implementation**: Update `skill_loader.py` to use config.yaml as authoritative, SKILL.md frontmatter as fallback.

```python
# sdk/agentura_sdk/runner/skill_loader.py — modify load_skill_md()

def _resolve_metadata(skill_md_meta: SkillMetadata, config: SkillConfig) -> SkillMetadata:
    """Config.yaml is authoritative. SKILL.md frontmatter is fallback."""
    resolved = SkillMetadata(
        name=config.skills[0].name or skill_md_meta.name,
        role=config.skills[0].role or skill_md_meta.role,
        model=config.skills[0].model or skill_md_meta.model,
        cost_budget=config.guardrails.budget.max_per_execution or skill_md_meta.cost_budget,
        timeout=config.agent.timeout if config.agent else skill_md_meta.timeout,
    )

    # Warn on disagreement
    if skill_md_meta.cost_budget and config_budget and skill_md_meta.cost_budget != config_budget:
        logger.warning(f"Skill '{resolved.name}': cost_budget differs between "
                       f"SKILL.md ({skill_md_meta.cost_budget}) and config.yaml ({config_budget}). "
                       f"Using config.yaml.")

    return resolved
```

**Files**: 1-2 edits (`skill_loader.py`, `types.py`)
**Effort**: 4-6 hours

### 3.3 Skill Versioning (Week 5-6 — Medium)

**Problem**: `last_deployed` is file mtime. No rollback. Regression = `git revert`.

**Solution**: Git-based versioning with config-level version tag.

```yaml
# agentura.config.yaml
version: "1.2.0"        # Semver, bumped manually or by CI
```

```python
# sdk/agentura_sdk/runner/skill_loader.py — add version tracking

def _get_skill_version(skill_dir: Path) -> str:
    """Version from config.yaml, fallback to git short hash."""
    config = load_config(skill_dir)
    if hasattr(config, 'version') and config.version:
        return config.version

    # Fallback: git short hash of last commit touching this skill
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", str(skill_dir)],
            capture_output=True, text=True
        )
        return result.stdout.strip() or "unknown"
    except:
        return "unknown"
```

**Rollback support**: Version is logged with every execution. To rollback:

```bash
# See which version was running when things worked
agentura history support/ticket-responder --last 10

# Rollback to a specific version (git-based)
git checkout abc123 -- skills/support/ticket-responder/
agentura deploy support/ticket-responder
```

**Files**: 2-3 edits (`skill_loader.py`, `types.py`, `server/app.py`)
**Effort**: 4-6 hours

---

## Mapping to Product Vision & Harness Engineering

| Agentura Pain Point | Harness Engineering Pattern | Product Vision Phase | Fix |
|---------------------|---------------------------|---------------------|-----|
| No local agent testing | "Isolated development environments" | Phase 1.1 (Make Existing Reliable) | Mock MCP executor |
| Silent failures | "Deterministic linters enforcing structural rules" | Phase 1.1 | Startup + input validation |
| Manual deploy | "Mechanical rules prevent violations" | Phase 1.1 | `agentura deploy` |
| Metadata split | "Single source of truth for agents" (docs as infra) | Phase 1.1 | Config.yaml authoritative |
| No versioning | "Full versioning" (OpenAI Agent Builder) | Phase 5.4 (Audit & Compliance) | Semver + git hash |
| Opt-in validation | "Linters and CI validation" (OpenAI) | Phase 1.1 | CI Action + startup scan |

### How This Enables the Vision

The product vision says:
> **Tenet 4**: "Prove at every layer before building the next."

These 6 fixes are the foundation layer. Without them:
- Phase 2 (Event-Driven Triggers) breaks because skills deployed via webhook have stale configs
- Phase 3 (CEO/PM Agents) breaks because agent skills can't be iterated without burning $2/cycle
- Phase 4 (Hierarchical Orchestration) breaks because delegation to a broken skill silently fails

With them:
- Every skill is validated before it reaches production (CI + startup)
- Agent skills can be iterated locally ($0 per cycle)
- Deploy is one command, not a 3-step dance
- Regressions can be rolled back in seconds

### Stripe/OpenAI Comparison

| What They Did | What We're Doing | Same Pattern? |
|--------------|-----------------|---------------|
| Stripe: Slack task → agent writes code → passes CI → opens PR → human review | Agentura: Webhook → pipeline → parallel agents → fan-in → GitHub Check | Yes — event-driven, CI-gated |
| OpenAI: Deterministic linters enforce architectural boundaries | Agentura: `agentura validate` + CI Action + startup scan | Yes — mechanical constraints |
| OpenAI: "Rippable harnesses" designed to simplify as models improve | Agentura: SKILL.md is the harness — can be simplified as models need less guidance | Yes — evolvable constraints |
| OpenAI: 3.5 PRs per engineer per day with Codex agents | Agentura: 4-agent parallel fleet per PR, target >10 PRs/hour throughput | Yes — fleet parallelism |
| LangChain: Record/replay middleware for agent testing | Agentura: Mock MCP with record/replay (Workstream 1.3) | Yes — deterministic testing |

---

## Execution Timeline

```
Week 1-2 (Quick Wins — 3 parallel tracks)
├── WS1: agentura deploy + agentura test          [~8 hrs]
├── WS2: Startup validation + input_data check     [~3 hrs]
└── WS3: Metadata consolidation analysis            [~3 hrs]
    Total: ~14 hrs across 3 engineers or 1 engineer over 2 weeks

Week 3-4 (Medium Lifts)
├── WS1: Local mock executor (Phase 1 — basic)     [~10 hrs]
├── WS2: MCP binding validation                     [~4 hrs]
└── WS3: Single source of truth migration            [~5 hrs]
    Total: ~19 hrs

Week 5-6 (Polish)
├── WS1: Local mock executor (Phase 2 — record/replay) [~10 hrs]
├── WS2: CI linter GitHub Action                     [~3 hrs]
└── WS3: Skill versioning + rollback                  [~5 hrs]
    Total: ~18 hrs

Grand Total: ~51 hrs of implementation
```

### Priority Order (If Sequencing Required)

If only one engineer, do this order — maximum impact per hour:

1. **Startup validation** (1-2 hrs) — catches broken skills for free
2. **`agentura deploy`** (2-3 hrs) — eliminates GR-006 forever
3. **Strict `input_data` validation** (1 hr) — catches GR-009 for free
4. **MCP binding validation** (3-4 hrs) — catches GR-018/020/021 at config load
5. **`agentura test`** (4-6 hrs) — fixture-driven testing
6. **CI linter** (2-3 hrs) — blocks broken skills from merging
7. **Metadata consolidation** (4-6 hrs) — architectural cleanup
8. **Skill versioning** (4-6 hrs) — rollback support
9. **Local mock executor** (15-20 hrs) — the big one, do last

Items 1-4 are ~8 hours total and eliminate the 4 most common pain points. That's the 80/20.

---

## Success Criteria

| Metric | Before | After |
|--------|--------|-------|
| Time to deploy a skill change | 5-15 min (manual kubectl cp + debug) | 10 seconds (`agentura deploy`) |
| Cost of iterating an agent skill | $0.50-2.00 per cycle (remote execution) | $0 for fixture tests, $0.50 for live test |
| Silent config failures per month | 3-5 (GR-009/018/020/021) | 0 (caught at validation) |
| Time to rollback a broken skill | 10-30 min (find commit, git revert, deploy) | 30 seconds (`git checkout + agentura deploy`) |
| Skill author confusion about metadata | Every new contributor asks | Zero — config.yaml is truth, documented |
| Broken skills reaching production | Regularly (opt-in validation) | Never (CI + startup validation) |
