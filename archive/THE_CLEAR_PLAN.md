# THE CLEAR PLAN: Problem Statement → Skills → Orchestration → Execution → Feedback

**Goal:** Abstract problem statements → generate skills → orchestrate execution → observe → learn from feedback

**Approach:** Skills-first (deliverable is `skill.md`), Manager → Specialist pattern, config-driven orchestration

---

## PART 1: THE UNIVERSAL PATTERN

Every one of your 20+ problems follows this structure:

```
┌─────────────────┐
│ Manager Skill   │  ← Receives bulk data (500 orders, 100 alerts)
│ (Triage/Detect) │  ← Groups, analyzes, detects high-signal patterns
└────────┬────────┘  ← Routes to specialist with context
         │
         │ Context Handoff (focused problem + metadata)
         ▼
┌─────────────────┐
│ Specialist Skill│  ← Receives focused problem + context
│ (Deep Dive/RCA) │  ← Queries logs, checks runbooks, root cause analysis
└────────┬────────┘  ← Returns actionable recommendation
         │
         │ User Correction (if agent wrong)
         ▼
┌─────────────────┐
│ Feedback Skill  │  ← Captures correction → generates test
│ (Learn/Improve) │  ← Updates episodic memory for future learning
└─────────────────┘
```

### Concrete Example: ECM Stuck Orders

**Manager Skill** (`triage-and-assign.md`):
```yaml
Input: 500 stuck orders from Redshift
Logic:
  1. GROUP BY stuck_at stage
  2. COUNT critical priority orders
  3. DETECT trend (UP/DOWN/STABLE)
Output: "90 orders stuck_at_lulu, 68 critical, UP +4 trend"
Routes to: Field Agent (with context: lulu, 90 orders, critical, UP)
```

**Specialist Skill** (`diagnose-and-resolve.md`):
```yaml
Input: Context from Manager (lulu stuck, 90 orders, critical, UP trend)
Logic:
  1. Query application logs for lulu errors
  2. Check runbooks/25-lulu-api-issues.md
  3. Identify root cause
Output: "Lulu API timeout since 10:15 AM, see runbook #12, ETA 2h"
Returns to: Manager (who notifies user)
```

**Feedback Skill** (`capture-correction.md`):
```yaml
Input: User correction "Actually it was rate limit, not timeout"
Logic:
  1. Generate regression test (if agent says timeout, correct answer is rate limit)
  2. Store in episodic memory (pgvector)
  3. Update Manager/Specialist with reflection
Output: Test saved to tests/generated/test_lulu_rate_limit.yaml
```

---

## PART 2: SKILL GENERATION PROCESS

### Input: Problem Statement

Example from your 20+ problems:

**Problem #11: Auto-RCA for Production Incidents**
```
Current: When deployment causes metric spike, engineers manually trace root cause (2-4h)
Goal: Auto-detect spike → trace deployment → identify config change → suggest fix
```

### Output: Generated Skills

I created the example in `/Users/apple/code/experimentation/wealth-copilot/examples/auto-rca/`:

1. **Manager Skill:** `manager-detect-anomaly.md`
   - Receives Prometheus alert
   - Detects anomaly type (metric spike, error rate, latency)
   - Checks recent deployments (last 2 hours)
   - Routes to Specialist if deployment found

2. **Specialist Skill:** `specialist-trace-deployment.md`
   - Gets deployment diff (config changes, code changes)
   - Queries logs around spike time
   - Searches runbooks for known issues
   - Identifies root cause + suggests fix

3. **Config:** `aspora.config.yaml`
   - Routing rules (when manager outputs `recent_deployment: true`, route to specialist)
   - Guardrails (budget caps, human-in-loop for rollbacks)
   - Observability (metrics, logs, traces)
   - Feedback loop (corrections → tests)

### Generation Formula

For ANY problem statement, generate:

```
Manager Skill:
  name: {domain}-{action}-manager
  task: Analyze bulk data → Detect pattern → Route to specialist
  model: anthropic/claude-haiku-4.5  # Cheaper for triage
  triggers: alert | cron | message
  outputs: Pattern + context for specialist

Specialist Skill:
  name: {domain}-{action}-specialist
  task: Deep dive → Root cause → Recommendation
  model: anthropic/claude-sonnet-4.5  # Deeper reasoning
  triggers: routed (from manager)
  inputs: Context from manager
  outputs: Actionable recommendation

Config (aspora.config.yaml):
  routing:
    - when: manager.output matches condition
      then: route_to specialist
  guardrails:
    - budget_caps
    - human_in_loop_for_risky_actions
  observability:
    - metrics (Prometheus)
    - logs (Langfuse)
    - traces (Opik)
  feedback:
    - capture_corrections: true
    - auto_generate_tests: true
```

---

## PART 3: ORCHESTRATOR DESIGN

### Config-Driven Routing (NOT Code)

```yaml
# aspora.config.yaml
routing:
  # Rule 1: If manager detects deployment spike, route to deployment specialist
  - when:
      skill: auto-rca-detect-anomaly
      output_match:
        anomaly_type: metric_spike
        recent_deployment: true
    then:
      route_to: auto-rca-trace-deployment
      pass_context: [metric, spike_time, deployment_id, service]

  # Rule 2: If manager detects spike but no deployment, route to general investigator
  - when:
      skill: auto-rca-detect-anomaly
      output_match:
        anomaly_type: metric_spike
        recent_deployment: false
    then:
      route_to: auto-rca-general-investigation
      pass_context: [metric, spike_time, service]

  # Rule 3: If specialist needs more data, route to data-fetcher
  - when:
      skill: auto-rca-trace-deployment
      output_match:
        confidence: low
        needs_more_data: true
    then:
      route_to: auto-rca-fetch-additional-logs
      pass_context: [service, time_window]
```

### Handoff Protocol (Manager → Specialist)

```json
// Manager outputs this JSON
{
  "route_to": "auto-rca-trace-deployment",
  "context": {
    "metric": "api_latency_p95",
    "baseline": 200,
    "current": 2500,
    "spike_time": "2026-02-17T10:15:00Z",
    "deployment_time": "2026-02-17T10:10:00Z",
    "deployment_id": "payment-api-v2.3.4",
    "service": "payment-api",
    "correlation": "high",
    "severity": "p1"
  }
}

// Specialist receives this as input + has access to same MCP tools
```

### NOT Knowledge Graph Traversal

**What we're NOT doing:**
```
❌ Agent queries Neo4j: MATCH (alert)-[:CAUSED_BY]->(deployment)-[:CHANGED]->(config)
❌ Graph stores causal relationships for cross-domain learning
❌ Agents discover patterns by traversing graph
```

**What we ARE doing:**
```
✅ Manager analyzes data → outputs JSON with route_to field
✅ Orchestrator reads routing rules from YAML config
✅ Specialist receives context via function call (Pydantic AI tools)
✅ Simple, deterministic, config-driven routing
```

---

## PART 4: EXECUTION PLATFORM

### Platform Components

```
┌───────────────────────────────────────────────────────────────┐
│                    ASPORA PLATFORM                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Skill Executor  │  │ Skill Registry  │  │ Orchestrator │ │
│  │ (Pydantic AI)   │  │ (PostgreSQL)    │  │ (Routing)    │ │
│  │                 │  │                 │  │              │ │
│  │ - Load skill.md │  │ - Metadata      │  │ - Read YAML  │ │
│  │ - Call LLM      │  │ - Versions      │  │ - Match rule │ │
│  │ - Use MCP tools │  │ - Permissions   │  │ - Route call │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Observability   │  │ Guardrails      │  │ Feedback     │ │
│  │                 │  │                 │  │              │ │
│  │ - Prometheus    │  │ - Budget caps   │  │ - Capture    │ │
│  │ - Langfuse      │  │ - HITL approvals│  │ - Gen tests  │ │
│  │ - Opik          │  │ - Rate limits   │  │ - Episodic   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
         ▲                      ▲                      ▲
         │                      │                      │
    ┌────┴─────┐          ┌────┴─────┐          ┌────┴─────┐
    │ Triggers │          │ Channels │          │   MCP    │
    │          │          │          │          │  Servers │
    │ - Alerts │          │ - Slack  │          │          │
    │ - Cron   │          │ - WhatsApp│         │ - Redshift│
    │ - Messages│         │ - API    │          │ - Postgres│
    └──────────┘          └──────────┘          │ - Logs   │
                                                 └──────────┘
```

### Skill Executor (Pydantic AI)

```python
# This is the ONLY Python you need (100 lines total)
# Everything else is skill.md files + aspora.config.yaml

from pydantic_ai import Agent
from pydantic import BaseModel

class SkillExecutor:
    def execute(self, skill_path: str, input_data: dict) -> dict:
        # 1. Load skill.md
        skill_md = load_skill(skill_path)

        # 2. Create Pydantic AI agent
        agent = Agent(
            model=skill_md.metadata['model'],
            system_prompt=skill_md.task,
            tools=load_mcp_tools(skill_md.metadata['mcp_tools'])
        )

        # 3. Execute
        result = agent.run_sync(input_data)

        # 4. Log to observability
        log_to_langfuse(skill_path, input_data, result)

        # 5. Check routing
        if 'route_to' in result:
            return orchestrator.route(result['route_to'], result['context'])

        return result
```

### MCP Tools Integration

Skills declare which tools they need:

```yaml
# In skill.md frontmatter
mcp_tools:
  - server: redshift-mcp
    tools: [query_stuck_orders, query_order_details]

  - server: runbooks-mcp
    tools: [search_runbooks, get_runbook_content]
```

Platform loads these at runtime (Pydantic AI native MCP support).

---

## PART 5: OBSERVABILITY

### Three-Tier Metrics (Prometheus)

```yaml
# Platform Level (for leadership)
aspora_executions_total{domain, outcome}
aspora_cost_total_dollars{domain}
aspora_success_rate{domain}

# Domain Level (ECM, Fraud, Wealth)
aspora_domain_executions_total{domain, skill_role}  # manager vs specialist
aspora_domain_latency_seconds{domain, skill_role}
aspora_domain_cost_dollars{domain, skill_role}

# Skill Level (debugging)
aspora_skill_executions_total{skill_name, outcome}
aspora_skill_latency_seconds{skill_name}
aspora_skill_cost_dollars{skill_name, model}
aspora_skill_user_satisfaction{skill_name}  # From feedback
```

### Logging (Langfuse)

Every execution logs:
- Skill input
- Skill output
- LLM reasoning trace (for ReAct debugging)
- Tool calls (which MCP tools used)
- User corrections (if any)

### Tracing (Opik)

Traces manager → specialist handoffs:
```
Trace ID: auto-rca-2026-02-17-12345
  ├─ Span: auto-rca-detect-anomaly (Haiku, 1.2s, $0.003)
  │   ├─ Tool: query_prometheus (0.4s)
  │   ├─ Tool: query_deployments (0.3s)
  │   └─ Output: route_to=auto-rca-trace-deployment
  │
  └─ Span: auto-rca-trace-deployment (Sonnet, 8.7s, $0.12)
      ├─ Tool: get_deployment_diff (1.2s)
      ├─ Tool: query_logs (2.3s)
      ├─ Tool: search_runbooks (0.8s)
      └─ Output: root_cause="DB pool exhausted", confidence=high
```

---

## PART 6: FEEDBACK LOOP

### User Correction → Auto-Generated Test

**Scenario:** Agent gets RCA wrong

```yaml
# Agent's output
root_cause: "Lulu API timeout"
recommended_fix: "Increase timeout from 30s to 60s"

# User correction
actual_root_cause: "Lulu API rate limit (429 errors)"
actual_fix: "Reduce request rate or implement exponential backoff"
```

**Feedback Skill captures this:**

```python
# Auto-generated test (DeepEval)
@pytest.mark.deepeval
def test_lulu_api_rate_limit_vs_timeout():
    """
    Generated from user correction on 2026-02-17
    Ensure agent distinguishes rate limit (429) from timeout (504)
    """
    input_data = {
        "service": "payment-api",
        "symptom": "Lulu API errors",
        "logs": [
            "2026-02-17T10:15:23 ERROR: HTTP 429 Too Many Requests",
            "2026-02-17T10:15:24 ERROR: HTTP 429 Too Many Requests"
        ]
    }

    result = skill_executor.execute("diagnose-and-resolve.md", input_data)

    assert "rate limit" in result["root_cause"].lower()
    assert "429" in result["evidence"]
    assert "timeout" not in result["root_cause"].lower()
```

**Reflexion update (episodic memory):**

```json
{
  "execution_id": "exec-12345",
  "skill": "diagnose-and-resolve",
  "mistake": "Confused HTTP 429 (rate limit) with timeout",
  "correction": "429 errors indicate rate limiting, not timeouts. Check for 'Too Many Requests' in logs.",
  "revised_approach": "When diagnosing Lulu API issues, check HTTP status codes: 429=rate limit, 504=timeout. Different fixes needed.",
  "embedding": [0.123, 0.456, ...],  # Stored in pgvector
  "created_at": "2026-02-17T12:30:00Z"
}
```

**Future executions:** Vector search retrieves this correction when similar context appears.

---

## PART 7: THE 2-HOUR PRIMITIVE

Following Engineering Brain rhythm: **Question → Primitive (< 2 hours) → Demo → Sharpen**

### Primitive Goal

Prove the pattern end-to-end with ONE problem:
- Problem: ECM stuck orders
- Manager skill: Triage and detect pattern
- Specialist skill: Diagnose root cause
- Execute with real data
- Capture feedback

### Build Timeline (2 Hours)

**Hour 1: Skills + Config**

```bash
# 0:00 - 0:20: Manager skill
cat > examples/ecm/manager-triage.md <<EOF
# ECM Manager: Triage Stuck Orders
[Task: Query Redshift for stuck orders, group by stuck_at, detect trends]
[Output: JSON with stuck_at, count, critical_count, trend, route_to]
EOF

# 0:20 - 0:40: Specialist skill
cat > examples/ecm/specialist-diagnose.md <<EOF
# ECM Field: Diagnose Root Cause
[Task: Query logs for stuck_at stage, check runbooks, identify RCA]
[Output: JSON with root_cause, evidence, recommended_fix]
EOF

# 0:40 - 1:00: Config
cat > examples/ecm/aspora.config.yaml <<EOF
domain: ecm
skills:
  - name: ecm-triage
    path: ./manager-triage.md
    model: anthropic/claude-haiku-4.5
    triggers:
      - type: cron
        schedule: "0 */8 * * *"  # 3x daily

  - name: ecm-diagnose
    path: ./specialist-diagnose.md
    model: anthropic/claude-sonnet-4.5
    triggers:
      - type: routed
        from: ecm-triage

routing:
  - when:
      skill: ecm-triage
      output_match:
        critical_count: {$gte: 10}  # If 10+ critical orders stuck
    then:
      route_to: ecm-diagnose
      pass_context: [stuck_at, count, critical_count, trend]

mcp_tools:
  - server: redshift-mcp
    tools: [query_stuck_orders, query_order_details]
  - server: runbooks-mcp
    tools: [search_runbooks, get_runbook_content]

observability:
  logs:
    destination: langfuse
  metrics:
    destination: prometheus
EOF
```

**Hour 2: Execution + Demo**

```bash
# 1:00 - 1:20: Minimal executor (100 lines Python)
# (Use Pydantic AI to load skill.md + call OpenRouter + route)

# 1:20 - 1:40: Execute with real data
python executor.py execute examples/ecm/manager-triage.md \
  --trigger cron \
  --input '{}'

# Output:
# {
#   "stuck_at": "lulu",
#   "count": 90,
#   "critical_count": 68,
#   "trend": "UP",
#   "route_to": "ecm-diagnose",
#   "context": {...}
# }

# Auto-routed to specialist:
# {
#   "root_cause": "Lulu API rate limit (429 errors)",
#   "evidence": ["Logs show 429 errors", "Runbook #25 matches"],
#   "recommended_fix": "Implement exponential backoff"
# }

# 1:40 - 2:00: Demo feedback loop
# User corrects: "Actually it was timeout, not rate limit"
# System generates test + stores in episodic memory
```

### Demo Output

```
✅ Manager skill executed (1.2s, $0.003)
✅ Detected pattern: 68 critical orders stuck at lulu (UP trend)
✅ Routed to specialist: ecm-diagnose

✅ Specialist skill executed (8.7s, $0.12)
✅ Root cause: Lulu API rate limit (429 errors)
✅ Evidence: 3 sources (logs, runbooks, similar incidents)
✅ Recommended fix: Implement exponential backoff

✅ Logged to Langfuse
✅ Metrics sent to Prometheus
✅ Trace available in Opik

💬 User feedback captured (corrected RCA)
✅ Test generated: tests/generated/test_lulu_timeout_vs_rate_limit.yaml
✅ Episodic memory updated (reflexion)
```

---

## PART 8: SCALING TO 20+ PROBLEMS

Once primitive works, scale by:

1. **Generate skills for each problem** (use the formula from Part 2)
2. **Create domain configs** (aspora.config.yaml per domain)
3. **Deploy platform** (Firecracker VMs for skill isolation, DEC-009)
4. **Add MCP servers** (one per data source: Redshift, Postgres, logs, metrics)

### 20+ Problems → 40+ Skills (Manager + Specialist per problem)

| Problem | Manager Skill | Specialist Skill | Trigger |
|---------|--------------|------------------|---------|
| ECM stuck orders | triage-and-assign | diagnose-and-resolve | cron (3x daily) |
| FinCrime alerts | hypothesis-generator | diagnostic-questions | alert (when anomaly detected) |
| Fraud rule simulation | simulate-rule-impact | generate-edge-cases | message (Slack command) |
| Auto-RCA | detect-anomaly | trace-deployment | alert (Prometheus) |
| Churn prediction | analyze-user-signals | personalize-outreach | cron (daily) |
| Support CX | classify-complaint | resolve-with-context | message (Slack/WhatsApp) |
| ... | ... | ... | ... |

### Platform Scales to 6+ Domains

```
aspora-platform/
├── domains/
│   ├── ecm/
│   │   ├── aspora.config.yaml
│   │   ├── manager-triage.md
│   │   ├── specialist-diagnose.md
│   │   └── runbooks/
│   ├── fincrime/
│   │   ├── aspora.config.yaml
│   │   ├── manager-hypothesis.md
│   │   ├── specialist-diagnostic.md
│   │   └── models/
│   ├── fraud-guardian/
│   │   ├── aspora.config.yaml
│   │   ├── manager-simulate.md
│   │   ├── specialist-edge-cases.md
│   │   └── rules/
│   ├── auto-rca/
│   ├── churn/
│   └── support/
└── platform/
    ├── executor/
    ├── orchestrator/
    ├── observability/
    └── feedback/
```

---

## SUMMARY: THE CLEAR PLAN

### What You Build

1. **Skills** (markdown files with YAML frontmatter)
   - Manager skills (triage, detect, route)
   - Specialist skills (deep dive, RCA, recommend)
   - Feedback skills (capture corrections, generate tests)

2. **Configs** (aspora.config.yaml per domain)
   - Routing rules (when X, route to Y)
   - Guardrails (budget, HITL, rate limits)
   - Observability (metrics, logs, traces)
   - MCP tools (data sources)

3. **Platform** (~1000 lines Python total)
   - Skill executor (Pydantic AI)
   - Orchestrator (YAML-driven routing)
   - Observability (Prometheus, Langfuse, Opik)
   - Feedback loop (DeepEval, Reflexion, pgvector)

### What You DON'T Build

❌ Multi-agent knowledge graphs (Neo4j)
❌ Complex Python orchestration code
❌ Custom LLM wrappers (use Pydantic AI)
❌ Manual test suites (auto-generated from feedback)

### Engineering Brain Rhythm

```
Question: How to abstract 20+ problems into skills?
  ↓
Primitive (< 2h): Build ECM Manager + Specialist + execute with real data
  ↓
Demo: Show manager → specialist handoff + feedback loop
  ↓
Sharpen: Add observability, guardrails, test generation
  ↓
Scale: Generate skills for remaining 19 problems
  ↓
Skill-ify: Package as platform (API, CLI, Slack integration)
```

### Next Steps (Immediate)

1. **Hour 1-2:** Build the 2-hour primitive (ECM example)
2. **Hour 3-4:** Add observability (Langfuse, Prometheus)
3. **Hour 5-6:** Add feedback loop (capture corrections, generate tests)
4. **Day 2:** Generate skills for 5 more problems (Auto-RCA, Churn, Fraud, Support, FinCrime)
5. **Week 1:** Full platform deployment (all 20+ problems)

---

## FILES CREATED

You now have:

1. **/Users/apple/code/experimentation/wealth-copilot/THE_CLEAR_PLAN.md** (this file)
2. **/Users/apple/code/experimentation/wealth-copilot/examples/auto-rca/manager-detect-anomaly.md**
3. **/Users/apple/code/experimentation/wealth-copilot/examples/auto-rca/specialist-trace-deployment.md**
4. **/Users/apple/code/experimentation/wealth-copilot/examples/auto-rca/aspora.config.yaml**

These show the **complete pattern** for generating skills from problem statements.

To build the 2-hour primitive, start with ECM (your most production-ready domain).
