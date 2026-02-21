# Aspora Platform — Architecture Diagram

**Question:** Separate managers per domain OR single manager? How to monitor all?

**Answer:** **One Manager per domain** (ECM Manager, Fraud Manager, Auto-RCA Manager), monitored by central observability stack.

---

## HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRIGGER LAYER (Inputs)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Prometheus   │  │ Cron Jobs    │  │ Slack/       │  │ Webhooks     │   │
│  │ Alerts       │  │ (3x daily)   │  │ WhatsApp     │  │ (API calls)  │   │
│  │              │  │              │  │ Messages     │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASPORA PLATFORM (Core)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CENTRAL ORCHESTRATOR                            │   │
│  │                                                                     │   │
│  │  • Receives trigger (alert/cron/message/webhook)                   │   │
│  │  • Routes to appropriate DOMAIN based on trigger metadata          │   │
│  │  • Enforces cross-domain guardrails (global rate limits, budget)   │   │
│  │  • Aggregates metrics from all domains                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────┬──────────────────┬──────────────────┬─────────────┐  │
│  │                  │                  │                  │             │  │
│  ▼                  ▼                  ▼                  ▼             ▼  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────┐ │
│  │ ECM DOMAIN │  │ FRAUD      │  │ AUTO-RCA   │  │ FINCRIME   │  │ ... │ │
│  │            │  │ DOMAIN     │  │ DOMAIN     │  │ DOMAIN     │  │     │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  └─────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DOMAIN ARCHITECTURE (Each Domain Has Same Structure)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ECM DOMAIN                                        │
│                    (Other domains follow same pattern)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    MANAGER SKILL (ecm-triage)                         │ │
│  │                                                                       │ │
│  │  Role: Analyze bulk data → Detect patterns → Route to specialists    │ │
│  │  Model: claude-haiku-4.5 (cheap, fast for triage)                    │ │
│  │  Trigger: Cron (3x daily at 00:00, 08:00, 16:00 UTC)                 │ │
│  │                                                                       │ │
│  │  Logic:                                                               │ │
│  │    1. Query Redshift: 500 stuck orders                               │ │
│  │    2. GROUP BY stuck_at stage                                         │ │
│  │    3. COUNT critical priority                                         │ │
│  │    4. DETECT trend (UP/DOWN/STABLE)                                   │ │
│  │    5. IF critical_count >= 10 → Route to specialist                  │ │
│  │                                                                       │ │
│  │  Output:                                                              │ │
│  │    {                                                                  │ │
│  │      "stuck_at": "lulu",                                              │ │
│  │      "count": 90,                                                     │ │
│  │      "critical_count": 68,                                            │ │
│  │      "trend": "UP",                                                   │ │
│  │      "route_to": "ecm-diagnose",  ◄─── Routing decision              │ │
│  │      "context": {...}                                                 │ │
│  │    }                                                                  │ │
│  └───────────────────────────┬───────────────────────────────────────────┘ │
│                              │                                             │
│                              │ Context Handoff                             │
│                              ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │             SPECIALIST SKILL #1 (ecm-diagnose)                        │ │
│  │                                                                       │ │
│  │  Role: Deep dive on specific stuck_at → Root cause → Fix             │ │
│  │  Model: claude-sonnet-4.5 (smarter for RCA)                          │ │
│  │  Trigger: Routed from manager                                        │ │
│  │                                                                       │ │
│  │  Logic:                                                               │ │
│  │    1. Receive context (lulu stuck, 90 orders, critical, UP)          │ │
│  │    2. Query application logs for lulu errors                         │ │
│  │    3. Search runbooks/25-lulu-api-issues.md                          │ │
│  │    4. Check episodic memory (similar past incidents)                 │ │
│  │    5. Identify root cause                                            │ │
│  │                                                                       │ │
│  │  Output:                                                              │ │
│  │    {                                                                  │ │
│  │      "root_cause": "Lulu API rate limit (429 errors)",               │ │
│  │      "evidence": ["Logs", "Runbook #25", "Past incident #123"],      │ │
│  │      "recommended_fix": "Implement exponential backoff",             │ │
│  │      "confidence": "high"                                            │ │
│  │    }                                                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │         SPECIALIST SKILL #2 (ecm-resolve) [If needed]                │ │
│  │                                                                       │ │
│  │  Role: Execute fix (e.g., trigger API retry, update config)          │ │
│  │  Model: claude-haiku-4.5                                             │ │
│  │  Trigger: Routed from ecm-diagnose if confidence=high AND auto_fix   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                   DOMAIN CONFIG (aspora.config.yaml)                  │ │
│  │                                                                       │ │
│  │  skills:                                                              │ │
│  │    - ecm-triage (manager)                                            │ │
│  │    - ecm-diagnose (specialist)                                       │ │
│  │    - ecm-resolve (specialist)                                        │ │
│  │                                                                       │ │
│  │  routing:                                                             │ │
│  │    - when: manager.critical_count >= 10 → route to ecm-diagnose      │ │
│  │    - when: diagnose.confidence == high → route to ecm-resolve        │ │
│  │                                                                       │ │
│  │  guardrails:                                                          │ │
│  │    - budget: $5/day max                                              │ │
│  │    - human_in_loop: required for ecm-resolve (approval before fix)   │ │
│  │                                                                       │ │
│  │  mcp_tools:                                                           │ │
│  │    - redshift-mcp (query_stuck_orders)                               │ │
│  │    - runbooks-mcp (search_runbooks)                                  │ │
│  │    - logs-mcp (query_application_logs)                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MULTI-DOMAIN VIEW (How Multiple Managers Work Together)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CENTRAL ORCHESTRATOR                                    │
│                                                                             │
│  Trigger Router:                                                            │
│    • Prometheus alert "HighAPILatency" → AUTO-RCA Domain                   │
│    • Cron "0 */8 * * *" → ECM Domain                                       │
│    • Slack message "@fraud-agent" → FRAUD Domain                           │
│    • Webhook /api/fincrime/analyze → FINCRIME Domain                       │
└────────┬──────────────┬──────────────┬──────────────┬────────────────┬──────┘
         │              │              │              │                │
         ▼              ▼              ▼              ▼                ▼
    ┌────────┐    ┌─────────┐    ┌──────────┐   ┌──────────┐    ┌──────────┐
    │  ECM   │    │  FRAUD  │    │ AUTO-RCA │   │ FINCRIME │    │  CHURN   │
    │ DOMAIN │    │ DOMAIN  │    │  DOMAIN  │   │  DOMAIN  │    │  DOMAIN  │
    └────────┘    └─────────┘    └──────────┘   └──────────┘    └──────────┘
         │              │              │              │                │
    ┌────▼────┐    ┌────▼────┐   ┌────▼─────┐  ┌────▼─────┐   ┌────▼─────┐
    │ Manager │    │ Manager │   │ Manager  │  │ Manager  │   │ Manager  │
    │ ecm-    │    │ fraud-  │   │ rca-     │  │ fincrime-│   │ churn-   │
    │ triage  │    │ simulate│   │ detect-  │  │ hypothe- │   │ analyze- │
    │         │    │ -rule   │   │ anomaly  │  │ sis      │   │ signals  │
    └────┬────┘    └────┬────┘   └────┬─────┘  └────┬─────┘   └────┬─────┘
         │              │              │              │                │
    Routes to:     Routes to:     Routes to:     Routes to:       Routes to:
         │              │              │              │                │
    ┌────▼────┐    ┌────▼────┐   ┌────▼─────┐  ┌────▼─────┐   ┌────▼─────┐
    │Specialist│   │Specialist│  │Specialist│  │Specialist│   │Specialist│
    │ ecm-    │    │ fraud-  │   │ rca-     │  │ fincrime-│   │ churn-   │
    │ diagnose│    │ edge-   │   │ trace-   │  │ diagnose │   │ personal-│
    │         │    │ cases   │   │ deploy   │  │          │   │ ize      │
    └─────────┘    └─────────┘   └──────────┘  └──────────┘   └──────────┘

EACH DOMAIN IS INDEPENDENT:
  • Has its own Manager skill (triage/detect/classify)
  • Has its own Specialist skills (deep dive/RCA/recommend)
  • Has its own routing rules (config-driven)
  • Has its own MCP tools (data sources)
  • Has its own guardrails (budget, rate limits)

DOMAINS DO NOT TALK TO EACH OTHER:
  • ECM Manager does NOT route to Fraud Specialist
  • Each domain is isolated (vertical slice)
  • Central orchestrator enforces cross-domain guardrails only
```

---

## MONITORING ARCHITECTURE (How You Monitor All Managers + Agents)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY STACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PROMETHEUS (Metrics)                             │   │
│  │                                                                     │   │
│  │  Platform-Level Metrics (Leadership Dashboard):                    │   │
│  │    • aspora_executions_total{domain}                               │   │
│  │    • aspora_cost_total_dollars{domain}                             │   │
│  │    • aspora_success_rate{domain}                                   │   │
│  │    • aspora_feedback_corrections_total{domain}                     │   │
│  │                                                                     │   │
│  │  Domain-Level Metrics (Domain Owner Dashboard):                    │   │
│  │    • aspora_domain_executions_total{domain, skill_role}            │   │
│  │        → skill_role = "manager" | "specialist"                     │   │
│  │    • aspora_domain_latency_seconds{domain, skill_role}             │   │
│  │    • aspora_domain_cost_dollars{domain, skill_role, model}         │   │
│  │                                                                     │   │
│  │  Skill-Level Metrics (Debugging Dashboard):                        │   │
│  │    • aspora_skill_executions_total{skill_name, outcome}            │   │
│  │    • aspora_skill_latency_seconds{skill_name}                      │   │
│  │    • aspora_skill_cost_dollars{skill_name, model}                  │   │
│  │    • aspora_skill_user_satisfaction{skill_name}  (from feedback)   │   │
│  │    • aspora_skill_routing_decisions{from_skill, to_skill}          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LANGFUSE (Logging)                               │   │
│  │                                                                     │   │
│  │  Every skill execution logs:                                       │   │
│  │    • Skill name + domain                                           │   │
│  │    • Input data (what manager received)                            │   │
│  │    • Output data (what manager/specialist returned)                │   │
│  │    • LLM reasoning trace (for ReAct debugging)                     │   │
│  │    • Tool calls (which MCP tools were used)                        │   │
│  │    • User corrections (if any)                                     │   │
│  │    • Cost breakdown (prompt tokens, completion tokens, $)          │   │
│  │                                                                     │   │
│  │  Searchable by:                                                     │   │
│  │    • Domain (ecm, fraud, auto-rca)                                 │   │
│  │    • Skill name (ecm-triage, ecm-diagnose)                         │   │
│  │    • Outcome (success, error, user_corrected)                      │   │
│  │    • Time range                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OPIK (Tracing)                                   │   │
│  │                                                                     │   │
│  │  Traces manager → specialist handoffs:                             │   │
│  │                                                                     │   │
│  │  Trace ID: ecm-2026-02-17-08:00:23                                 │   │
│  │    ├─ Span: ecm-triage (manager)                                   │   │
│  │    │   ├─ Tool: query_stuck_orders (Redshift MCP, 0.4s)            │   │
│  │    │   ├─ LLM: claude-haiku-4.5 (1.2s, $0.003)                     │   │
│  │    │   └─ Output: route_to=ecm-diagnose                            │   │
│  │    │                                                                │   │
│  │    └─ Span: ecm-diagnose (specialist)                              │   │
│  │        ├─ Tool: query_application_logs (Logs MCP, 2.3s)            │   │
│  │        ├─ Tool: search_runbooks (Runbooks MCP, 0.8s)               │   │
│  │        ├─ Tool: get_similar_incidents (Memory MCP, 0.5s)           │   │
│  │        ├─ LLM: claude-sonnet-4.5 (8.7s, $0.12)                     │   │
│  │        └─ Output: root_cause="Rate limit", confidence=high         │   │
│  │                                                                     │   │
│  │  Latency breakdown:                                                 │   │
│  │    • Total: 13.9s                                                   │   │
│  │    • Manager: 1.6s (12%)                                            │   │
│  │    • Specialist: 12.3s (88%)                                        │   │
│  │       └─ Tools: 3.6s (29%)                                          │   │
│  │       └─ LLM: 8.7s (71%)                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    GRAFANA DASHBOARDS                               │   │
│  │                                                                     │   │
│  │  Dashboard 1: Platform Overview (for Leadership)                   │   │
│  │    • Total executions today: 1,427                                 │   │
│  │    • Total cost today: $142.50                                     │   │
│  │    • Success rate: 94.3%                                            │   │
│  │    • Active domains: 6                                              │   │
│  │    • Top domain by volume: ECM (1,250 executions)                  │   │
│  │    • Top domain by cost: Auto-RCA ($45.20)                         │   │
│  │                                                                     │   │
│  │  Dashboard 2: Domain Deep Dive (for Domain Owners)                 │   │
│  │    • ECM Domain: 1,250 executions today                            │   │
│  │      ├─ Manager (ecm-triage): 3 executions (cron 3x daily)         │   │
│  │      └─ Specialist (ecm-diagnose): 8 executions (routed from mgr)  │   │
│  │    • Cost breakdown:                                                │   │
│  │      ├─ Manager: $0.009 (Haiku 3x)                                 │   │
│  │      └─ Specialist: $0.96 (Sonnet 8x)                              │   │
│  │    • User satisfaction: 87% (7/8 no correction)                    │   │
│  │                                                                     │   │
│  │  Dashboard 3: Skill Performance (for Engineers)                    │   │
│  │    • ecm-diagnose skill:                                            │   │
│  │      ├─ Executions: 8 today, 245 last 30 days                      │   │
│  │      ├─ Success rate: 87.5% (1 user correction)                    │   │
│  │      ├─ Avg latency: 8.7s (p50), 12.3s (p95)                       │   │
│  │      ├─ Avg cost: $0.12 per execution                              │   │
│  │      ├─ Most used tool: search_runbooks (94% of executions)        │   │
│  │      └─ Common mistakes: Confusing timeout vs rate limit (3x)      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MONITORING HIERARCHY (Three Levels)

### Level 1: Platform (Leadership View)

**Who:** CEO, CTO, VP Engineering
**Frequency:** Daily/weekly review
**Metrics:**
```sql
-- Total platform health
SELECT
  COUNT(*) as total_executions,
  SUM(cost_dollars) as total_cost,
  AVG(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as success_rate,
  COUNT(DISTINCT domain) as active_domains
FROM skill_executions
WHERE timestamp > NOW() - INTERVAL '24 hours'

-- Top domains by volume
SELECT domain, COUNT(*) as executions
FROM skill_executions
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY domain
ORDER BY executions DESC
LIMIT 5

-- Cost per domain
SELECT domain, SUM(cost_dollars) as cost
FROM skill_executions
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY domain
ORDER BY cost DESC
```

**Grafana Panel:**
```
┌─────────────────────────────────────────────┐
│ ASPORA PLATFORM OVERVIEW                    │
├─────────────────────────────────────────────┤
│ Executions Today:  1,427    ▲ +12% vs. avg │
│ Cost Today:        $142.50  ▼ -5% vs. avg  │
│ Success Rate:      94.3%    ▼ -2.1% (⚠️)   │
│ Active Domains:    6                        │
│                                             │
│ Top Domains (by volume):                    │
│   1. ECM:         1,250 exec, $3.75         │
│   2. Auto-RCA:    89 exec, $45.20           │
│   3. Fraud:       52 exec, $18.30           │
│   4. FinCrime:    24 exec, $52.10           │
│   5. Churn:       12 exec, $23.15           │
└─────────────────────────────────────────────┘
```

---

### Level 2: Domain (Domain Owner View)

**Who:** ECM team lead, Fraud team lead, etc.
**Frequency:** Daily standup
**Metrics:**
```sql
-- Domain health (ECM example)
SELECT
  skill_role,
  COUNT(*) as executions,
  AVG(latency_seconds) as avg_latency,
  SUM(cost_dollars) as cost,
  AVG(CASE WHEN user_correction IS NOT NULL THEN 0 ELSE 1 END) as satisfaction
FROM skill_executions
WHERE domain = 'ecm'
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY skill_role

-- Manager → Specialist routing patterns
SELECT
  manager_skill,
  specialist_skill,
  COUNT(*) as routing_count
FROM skill_executions
WHERE domain = 'ecm'
  AND specialist_skill IS NOT NULL
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY manager_skill, specialist_skill
```

**Grafana Panel:**
```
┌─────────────────────────────────────────────┐
│ ECM DOMAIN DASHBOARD                        │
├─────────────────────────────────────────────┤
│ Manager (ecm-triage):                       │
│   Executions: 3 (cron 3x daily)             │
│   Avg latency: 1.6s                         │
│   Cost: $0.009                              │
│   Routing: 8/3 = 2.67 avg specialists/run   │
│                                             │
│ Specialists:                                │
│   ecm-diagnose:  8 exec, 8.7s avg, $0.96   │
│   ecm-resolve:   2 exec, 3.2s avg, $0.06   │
│                                             │
│ User Satisfaction: 87% (7/8 no correction)  │
│                                             │
│ Routing Flow (last 7 days):                 │
│   ecm-triage → ecm-diagnose:    21 times    │
│   ecm-triage → [no routing]:     0 times    │
│   ecm-diagnose → ecm-resolve:    6 times    │
└─────────────────────────────────────────────┘
```

---

### Level 3: Skill (Engineer Debugging View)

**Who:** Individual engineers debugging specific skill
**Frequency:** When debugging issue or after user correction
**Metrics:**
```sql
-- Skill performance deep dive (ecm-diagnose example)
SELECT
  execution_id,
  input_data,
  output_data,
  reasoning_trace,
  tool_calls,
  latency_seconds,
  cost_dollars,
  user_correction
FROM skill_executions
WHERE skill_name = 'ecm-diagnose'
  AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 50

-- Common failure patterns
SELECT
  JSON_EXTRACT(user_correction, '$.actual_root_cause') as correction,
  COUNT(*) as frequency
FROM skill_executions
WHERE skill_name = 'ecm-diagnose'
  AND user_correction IS NOT NULL
  AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY correction
ORDER BY frequency DESC
```

**Langfuse Detail Page:**
```
┌─────────────────────────────────────────────┐
│ EXECUTION: ecm-diagnose-2026-02-17-08:05:32 │
├─────────────────────────────────────────────┤
│ Input (from ecm-triage):                    │
│   stuck_at: lulu                            │
│   count: 90                                 │
│   critical_count: 68                        │
│   trend: UP                                 │
│                                             │
│ Tool Calls:                                 │
│   1. query_application_logs(service=lulu)   │
│      → 127 errors found                     │
│   2. search_runbooks(query="lulu stuck")    │
│      → Found runbook #25                    │
│   3. get_similar_incidents(embedding=...)   │
│      → Found incident #123 (80% similar)    │
│                                             │
│ Reasoning Trace:                            │
│   "Logs show HTTP 429 errors starting..."  │
│   "Runbook #25 mentions rate limiting..."  │
│   "Similar incident #123 had same symptom" │
│   "Confidence: HIGH (3 corroborating...)"  │
│                                             │
│ Output:                                     │
│   root_cause: "Lulu API rate limit"        │
│   evidence: [3 sources]                     │
│   confidence: high                          │
│                                             │
│ User Correction: NONE ✅                    │
│                                             │
│ Cost: $0.12                                 │
│ Latency: 8.7s                               │
│   ├─ Tools: 3.6s (41%)                      │
│   └─ LLM: 5.1s (59%)                        │
└─────────────────────────────────────────────┘
```

---

## MANAGER COORDINATION PATTERNS

### Pattern 1: Independent Managers (RECOMMENDED)

```yaml
# ECM Manager only cares about ECM domain
ecm-triage:
  receives: Redshift data (500 stuck orders)
  routes_to: ecm-diagnose OR ecm-resolve
  does_NOT_route_to: fraud-specialist, rca-specialist

# Fraud Manager only cares about Fraud domain
fraud-simulate-rule:
  receives: Proposed rule change
  routes_to: fraud-edge-cases OR fraud-qa
  does_NOT_route_to: ecm-diagnose, rca-specialist
```

**Why:**
- ✅ Simple (each domain is isolated vertical slice)
- ✅ Scalable (add new domain without touching others)
- ✅ Debuggable (clear ownership)

---

### Pattern 2: Meta-Manager (Future, if needed)

```
Central Meta-Manager
  │
  ├─ Detects cross-domain pattern
  │   (e.g., "ECM stuck orders correlated with Fraud blocks")
  │
  └─ Routes to multiple domain managers
      ├─ ECM Manager: Diagnose stuck orders
      └─ Fraud Manager: Check if same users blocked
```

**When to use:** Only if you discover cross-domain patterns (Month 3-6).
**For now:** Stick to Pattern 1 (independent managers).

---

## ALERTING (How You Get Notified of Issues)

```yaml
# Alert 1: Platform-level success rate drop
- alert: PlatformSuccessRateLow
  expr: |
    (
      sum(rate(aspora_executions_total{outcome="success"}[5m]))
      /
      sum(rate(aspora_executions_total[5m]))
    ) < 0.90
  for: 10m
  annotations:
    summary: "Platform success rate below 90% for 10+ minutes"
    runbook: "Check Langfuse for common failures"

# Alert 2: Domain cost exceeding budget
- alert: DomainBudgetExceeded
  expr: |
    sum(aspora_cost_dollars{domain="ecm"}) > 5.0
  for: 1h
  annotations:
    summary: "ECM domain exceeded $5 daily budget"
    action: "Review routing rules, check if manager over-routing"

# Alert 3: Manager not routing to specialist (stuck)
- alert: ManagerNotRouting
  expr: |
    (
      rate(aspora_skill_executions_total{skill_role="manager"}[1h])
      /
      rate(aspora_skill_routing_decisions[1h])
    ) < 0.1
  for: 30m
  annotations:
    summary: "Manager skill executing but not routing to specialists"
    action: "Check routing rules in aspora.config.yaml"

# Alert 4: Skill latency spike
- alert: SkillLatencyHigh
  expr: |
    histogram_quantile(0.95,
      rate(aspora_skill_latency_seconds_bucket[5m])
    ) > 30
  for: 10m
  annotations:
    summary: "Skill p95 latency > 30s for 10+ minutes"
    action: "Check Opik trace for bottleneck (tools vs LLM)"
```

---

## SUMMARY: ARCHITECTURE DECISIONS

### Q: Separate managers or single manager?

**A: One manager per domain** (ECM Manager, Fraud Manager, Auto-RCA Manager)

**Why:**
- Each domain has different data sources (Redshift, Prometheus, Slack)
- Each domain has different routing logic (ECM: stuck_at patterns, Fraud: rule simulation, RCA: deployment correlation)
- Isolation = easier to debug, scale, own

---

### Q: How do managers coordinate?

**A: They DON'T** (at least not in v1)

Each domain is a vertical slice:
```
ECM Domain: Redshift → Manager → Specialist → User
Fraud Domain: API → Manager → Specialist → User
RCA Domain: Prometheus → Manager → Specialist → User
```

If you need cross-domain coordination (e.g., ECM learns from Fraud), add in Month 3-6 with Meta-Manager pattern.

---

### Q: How do you monitor all managers?

**A: Three-tier observability**

1. **Platform Level** (Prometheus + Grafana): Total executions, cost, success rate across ALL domains
2. **Domain Level** (Prometheus + Grafana): Per-domain metrics (ECM vs Fraud vs RCA)
3. **Skill Level** (Langfuse + Opik): Individual execution debugging (reasoning trace, tool calls, user corrections)

**One dashboard for leadership,
One dashboard per domain owner,
One detail page per skill execution.**

---

## NEXT STEP

Build the 2-hour primitive for ECM domain:
1. Create `ecm-triage` manager skill
2. Create `ecm-diagnose` specialist skill
3. Execute with real Redshift data
4. Add monitoring (Prometheus metrics + Langfuse logs)
5. Verify manager → specialist routing works

Once ECM works, copy the pattern to other domains (Fraud, RCA, FinCrime, etc.).
