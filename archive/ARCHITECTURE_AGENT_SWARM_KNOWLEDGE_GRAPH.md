# Aspora Agent Swarm — Knowledge Graph as Central Intelligence

**The Vision**: Build a platform where domain experts write skills (not code), specialized agents execute them, and a central knowledge graph enables holistic intelligence across all departments.

**The Problem**: 20+ agent use cases (Fraud, Churn, Support, RCA, VoC, etc.) all need to:
- Correlate data across domains (User complaint → Order ID → Beneficiary → Fraud pattern)
- Learn from each other's executions (Churn agent learns what Support agent discovered)
- Perform multi-hop reasoning (Payment delay → User frustration → Churn → Lost revenue)
- Access institutional memory ("We solved this before - apply same fix")

**Why Vector RAG Alone Fails**: Cannot traverse relationships, cannot connect cause-effect chains, cannot enable agent-to-agent learning.

**Why Knowledge Graph Wins**: Central substrate where ALL agents write/read, enabling emergent intelligence through graph accumulation.

---

## The Core Insight: Your Platform IS an Agent Swarm

### What is an Agent Swarm?

From OpenAI Swarm / Ant Swarm pattern:
- **Multiple specialized agents** (not one monolithic agent)
- **Each agent is expert** in one domain (Fraud, Support, Churn, etc.)
- **Agents hand off** to each other with context
- **Agents share knowledge** through central memory
- **Emergent behavior**: Complex problems solved by agent collaboration

### Your 20+ Use Cases = 20+ Specialized Agents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ASPORA AGENT SWARM PLATFORM                           │
│                                                                              │
│  DOMAIN AGENTS (Specialists):                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ FraudAgent   │  │ ChurnAgent   │  │ SupportAgent │  │ RCAAgent     │   │
│  │              │  │              │  │              │  │              │   │
│  │ Skills:      │  │ Skills:      │  │ Skills:      │  │ Skills:      │   │
│  │ • block-ben  │  │ • predict    │  │ • classify   │  │ • correlate  │   │
│  │ • blacklist  │  │ • intervene  │  │ • dedupe     │  │ • trace-code │   │
│  │ • investigate│  │ • analyze    │  │ • escalate   │  │ • rank       │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ VoCAgent     │  │ CommsAgent   │  │ InvoiceAgent │  │ WealthAgent  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  META-AGENTS (Orchestration):                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │ DataSanity   │  │ ContextMgr   │  │ Analytics    │                     │
│  │ Agent        │  │ Agent        │  │ Agent        │                     │
│  │              │  │              │  │              │                     │
│  │ Consolidates │  │ Organizes    │  │ Surfaces     │                     │
│  │ scattered    │  │ institutional│  │ insights     │                     │
│  │ data         │  │ knowledge    │  │ proactively  │                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
│                              ↓ ALL AGENTS READ/WRITE ↓                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                  CENTRAL KNOWLEDGE GRAPH (Neo4j)                     │   │
│  │                                                                      │   │
│  │  Entities: Users, Orders, Beneficiaries, Alerts, Bug Reports,       │   │
│  │            Deployments, Metrics, Interventions, Executions           │   │
│  │                                                                      │   │
│  │  Relationships: User complained → Order → Beneficiary → Fraud       │   │
│  │                 Deployment → Caused → MetricSpike → RootCause       │   │
│  │                 User → HasChurnRisk → Triggered → Intervention      │   │
│  │                 AgentA → HandedOffTo → AgentB                        │   │
│  │                 Execution → RevealedPattern → Solution               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How Knowledge Graph Solves Each Problem Holistically

### Problem Category 1: Cross-Domain Correlation

**Example**: Fraud Monitoring Agent + Support Agent + Churn Agent

#### Without Knowledge Graph (Current State):
```
[Email arrives: "User complains about unauthorized beneficiary"]

Support Agent:
1. Parse email → Extract order ID (manual or LLM)
2. Query PostgreSQL orders table → Find order
3. Extract beneficiary ID
4. ??? How to block across TRM platforms? (needs custom integration)
5. ??? How to check if this beneficiary appears in other fraud cases? (needs separate query)
6. ??? Should we proactively contact other users using same beneficiary? (no way to know)
```

**Problem**: Each agent operates in isolation. No shared context. Manual handoffs.

#### With Knowledge Graph (Swarm Intelligence):
```
[Email arrives: "User complains about unauthorized beneficiary"]

SupportAgent (Entry Point):
1. Parse email → Extract order ID
2. CREATE in graph:
   (user:User {id: "U123"})
   (complaint:Complaint {text: "unauthorized beneficiary", timestamp: now()})
   (user)-[:FILED]->(complaint)

3. Query graph to find order:
   MATCH (user)-[:PLACED]->(order:Order {id: "O456"})
   MATCH (order)-[:TO]->(ben:Beneficiary {id: "B789"})
   RETURN order, ben

4. CHECK if beneficiary is flagged:
   MATCH (ben)-[:FLAGGED_IN]->(alert:FraudAlert)
   RETURN alert
   // Result: Found 2 alerts from different users!

5. HAND OFF to FraudAgent with context:
   CREATE (complaint)-[:REQUIRES_ACTION_BY]->(fraudTask:Task)
   CREATE (fraudTask)-[:ASSIGNED_TO]->(fraudAgent:Agent {name: "FraudAgent"})
   CREATE (fraudTask)-[:CONTEXT {
     beneficiary_id: "B789",
     complaint_id: complaint.id,
     related_alerts: [alert1.id, alert2.id]
   })->(ben)

FraudAgent (Receives Handoff):
6. Reads graph context:
   MATCH (task:Task)-[:ASSIGNED_TO]->(me:Agent {name: "FraudAgent"})
   MATCH (task)-[:CONTEXT]->(ben:Beneficiary)
   MATCH (ben)-[:USED_IN]->(orders:Order)
   MATCH (orders)<-[:PLACED]-(users:User)
   RETURN ben, orders, users
   // Discovers: Beneficiary used in 12 orders by 8 different users!

7. Blocks beneficiary across platforms:
   CREATE (ben)-[:BLOCKED_AT {timestamp: now(), reason: "repeated_fraud"}]->(action:Action)
   CREATE (action)-[:EXECUTED_BY]->(me)

8. Proactive prevention:
   MATCH (ben)-[:USED_IN]->(orders:Order)
   WHERE NOT exists((orders)-[:COMPLETED])
   WITH orders, collect(users) as affected_users
   CREATE (action)-[:PREVENTED]->(orders)
   CREATE (notification:Notification {
     users: affected_users,
     message: "Beneficiary blocked - your pending order cancelled for security"
   })
   CREATE (action)-[:TRIGGERED]->(notification)

9. HAND OFF to ChurnAgent (prevent frustration):
   // Users who lost money might churn
   MATCH (users)-[:LOST_MONEY_IN]->(fraudOrder:Order)
   CREATE (task2:Task)-[:ASSIGNED_TO]->(churnAgent:Agent)
   CREATE (task2)-[:CONTEXT {action: "compensate", priority: "high"}]->(users)

ChurnAgent (Receives Handoff):
10. Proactive intervention:
    MATCH (task)-[:CONTEXT]->(users:User)
    MATCH (users)-[:HAS_CHURN_RISK]->(risk:ChurnRisk)
    // Fraud victims are HIGH churn risk
    SET risk.score = risk.score + 30
    CREATE (intervention:Intervention {
      type: "compensation_offer",
      amount: 50 GBP,
      message: "We're sorry - here's £50 credit for the inconvenience"
    })
    CREATE (users)-[:RECEIVES]->(intervention)
```

**Result**:
- ONE user complaint → 3 agents collaborated
- FraudAgent blocked ben across ALL platforms
- Prevented 12 pending orders automatically
- ChurnAgent compensated affected users proactively
- ALL of this is TRACED in the graph (audit trail)

**Query the graph later**:
```cypher
// "How many fraud cases did we prevent this month?"
MATCH (action:Action {type: 'block_beneficiary'})
WHERE action.timestamp > date('2026-02-01')
MATCH (action)-[:PREVENTED]->(orders:Order)
RETURN count(orders) AS prevented_fraud_orders

// "Which agent collaboration pattern is most effective?"
MATCH (agent1)-[:HANDED_OFF_TO]->(agent2)
      -[:COMPLETED]->(task)
WHERE task.user_feedback = 'approved'
RETURN agent1.name, agent2.name, count(task) AS successful_handoffs
ORDER BY successful_handoffs DESC
```

---

### Problem Category 2: Multi-Hop Causal Reasoning

**Example**: Auto-RCA Agent + CX Bug Resolver + DataSanity Agent

#### Without Knowledge Graph:
```
[Datadog alert: "Payment timeout spike - p99 latency 12s (was 2s)"]

Engineer manually investigates:
1. Check Datadog dashboard (which service?)
2. Check recent deployments (was anything deployed?)
3. Check logs (any errors?)
4. Check database (connection pool full?)
5. Ask in Slack: "Did anyone change payment config?"
6. 45 minutes later: "Oh, someone increased retry timeout from 5s → 15s"
```

**Problem**: Manual correlation. No causal chain. Tribal knowledge ("only Sarah knows payments pipeline").

#### With Knowledge Graph:
```
[Datadog alert: "Payment timeout spike"]

RCAAgent (Auto-triggered):
1. CREATE alert in graph:
   (alert:Alert {
     metric: "payment_p99_latency",
     value: 12000,
     threshold: 2000,
     timestamp: now()
   })

2. TRAVERSE dependency graph to find affected service:
   MATCH (alert)-[:DETECTED_IN]->(metric:Metric {name: "payment_p99_latency"})
   MATCH (metric)-[:BELONGS_TO]->(service:Service {name: "payment-service"})
   RETURN service

3. CHECK recent changes to this service:
   MATCH (service)<-[:CHANGED]-(event:ChangeEvent)
   WHERE event.timestamp > alert.timestamp - duration('PT24H')
   RETURN event
   ORDER BY event.timestamp DESC

   Results:
   - Deployment #1234 (2 hours ago) - code change to retry logic
   - Config change #567 (3 hours ago) - retry_timeout: 5000 → 15000
   - Feature flag flip #890 (4 hours ago) - enable_auto_retry: true

4. CORRELATE each change with metric timeline:
   MATCH (event)-[:RESULTED_IN]->(metric_change:MetricChange)
   WHERE metric_change.metric = "payment_p99_latency"
   RETURN event, metric_change
   ORDER BY metric_change.correlation_score DESC

   // Config change #567 has 0.94 correlation (happened right before spike)

5. TRAVERSE to find WHO made the change and WHY:
   MATCH (config:Config {retry_timeout: 15000})
   MATCH (config)<-[:UPDATED_BY]-(engineer:Engineer)
   MATCH (config)<-[:REQUESTED_IN]-(pr:PullRequest)
   MATCH (pr)-[:FIXES]->(issue:Issue)
   RETURN engineer, pr, issue

   // Engineer: "Alice", PR: "Increase retries to reduce false negatives"
   // Issue #456: "Too many payment failures due to transient errors"

6. FIND root cause vs symptom:
   // Config increased retry timeout to 15s
   // Under high load, this causes request queuing
   // Queue buildup → p99 latency spike

   CREATE (rc:RootCause {
     description: "Retry timeout increased to 15s causes request queuing under load",
     confidence: 0.94
   })
   CREATE (alert)-[:CAUSED_BY]->(rc)
   CREATE (config)-[:CONTRIBUTED_TO]->(rc)

7. SEARCH for similar past incidents:
   MATCH (rc_similar:RootCause)
   WHERE rc_similar.description CONTAINS "retry" AND rc_similar.description CONTAINS "queuing"
   MATCH (rc_similar)-[:SOLVED_BY]->(solution:Solution)
   RETURN solution
   ORDER BY solution.success_rate DESC

   // Found: "Reduce retry timeout OR increase worker pool size"
   // Past success rate: 0.89

8. AUTO-REMEDIATE (with approval):
   CREATE (action:RemediationAction {
     type: "config_rollback",
     target: "payment-service/retry_timeout",
     old_value: 15000,
     new_value: 5000,
     requires_approval: true
   })
   CREATE (rc)-[:SOLVED_BY]->(action)

   // Notify in Slack:
   // "@alice RCA complete: retry_timeout=15s causing queue buildup.
   //  Recommend rollback to 5s (89% success rate in past incidents).
   //  Approve? [Yes] [No] [Investigate More]"

9. HAND OFF to CXBugResolver (check user impact):
   MATCH (alert)-[:DURING_PERIOD]->(orders:Order)
   WHERE orders.status = 'failed' AND orders.error CONTAINS 'timeout'
   WITH count(orders) AS affected_count
   CREATE (task:Task {
     type: "customer_notification",
     affected_users: affected_count,
     message: "We experienced a payment processing delay. Your transfer is now complete."
   })
   CREATE (task)-[:ASSIGNED_TO]->(cxAgent:Agent {name: "CXBugResolver"})

CXBugResolver (Receives Handoff):
10. Check if this is a duplicate issue:
    MATCH (bug:BugReport)
    WHERE bug.symptom CONTAINS "payment timeout"
    AND bug.created_at > date() - duration('P7D')
    RETURN count(bug) AS similar_reports

    // Found 47 similar reports in past week!

11. DEDUPLICATE and create consolidated bug:
    MATCH (bug:BugReport)
    WHERE bug.symptom CONTAINS "payment timeout"
    WITH collect(bug) AS duplicates
    CREATE (consolidated:BugReport {
      title: "Payment timeout spike - retry config issue",
      frequency: size(duplicates),
      affected_users: sum([b in duplicates | b.affected_users]),
      root_cause_id: rc.id,
      status: "resolved"
    })
    FOREACH (bug in duplicates |
      CREATE (bug)-[:DUPLICATE_OF]->(consolidated)
    )

12. UPDATE DataSanity graph (for weekly report):
    MATCH (service:Service {name: "payment-service"})
    MATCH (consolidated:BugReport)
    CREATE (service)-[:HAD_INCIDENT {
      severity: "high",
      mttr_minutes: duration.between(alert.timestamp, action.resolved_at).minutes,
      user_impact: consolidated.affected_users
    }]->(consolidated)
```

**Result**:
- Alert → Root cause identified in 2 minutes (vs 45 minutes manual)
- Causal chain explicit: Config change → Queuing → Latency spike
- Similar past incident found (solution with 89% success rate)
- Auto-remediation proposed (with human approval)
- 47 duplicate bug reports auto-consolidated
- Full audit trail in graph

**Query for weekly sprint planning**:
```cypher
// "What bugs should we prioritize this week?"
MATCH (bug:BugReport)
WHERE bug.created_at > date() - duration('P7D')
AND bug.status = 'open'
MATCH (bug)-[:AFFECTS]->(service:Service)
MATCH (bug)<-[:DUPLICATE_OF]-(duplicates:BugReport)
RETURN
  bug.title,
  service.name,
  count(duplicates) AS frequency,
  sum(duplicates.affected_users) AS total_user_impact,
  bug.root_cause_id
ORDER BY frequency DESC, total_user_impact DESC
LIMIT 20
```

---

### Problem Category 3: Agent-to-Agent Learning (Swarm Intelligence)

**Example**: Churn Prediction + Comms Automation + VoC Engine

#### The Problem (Without Graph):
Each agent operates independently:
- ChurnAgent predicts risk, sends to MailChimp
- CommsAgent sends campaigns, tracks clicks
- VoCAgent analyzes feedback, stores in separate DB

**DISCONNECTED**: ChurnAgent doesn't know what CommsAgent tried. VoCAgent doesn't know if interventions worked.

#### With Knowledge Graph (Emergent Intelligence):

```
DAY 1: ChurnAgent predicts user at risk
────────────────────────────────────────────────────────────────────────────
ChurnAgent:
1. Calculate churn risk:
   MATCH (user:User {id: "U123"})
   MATCH (user)-[:PLACED]->(orders:Order)
   WITH user, count(orders) AS total_orders,
        max(orders.created_at) AS last_order_date,
        duration.between(last_order_date, date()).days AS days_since

   // Churn score = f(recency, frequency, engagement)
   WITH user, (days_since * 2) + (30 - total_orders) AS churn_score

   CREATE (risk:ChurnRisk {
     user_id: user.id,
     score: churn_score,
     predicted_at: date(),
     factors: {
       days_since_last_order: days_since,
       total_orders: total_orders,
       engagement_drop: true
     }
   })
   CREATE (user)-[:HAS_CHURN_RISK]->(risk)

2. HAND OFF to CommsAgent if score > 70:
   CREATE (task:Task {
     type: "churn_intervention",
     priority: "high"
   })
   CREATE (task)-[:ASSIGNED_TO]->(commsAgent:Agent {name: "CommsAgent"})
   CREATE (task)-[:CONTEXT]->(user)

DAY 1: CommsAgent sends intervention
────────────────────────────────────────────────────────────────────────────
CommsAgent:
3. Check what interventions worked for similar users:
   MATCH (similar_user:User)-[:HAS_CHURN_RISK]->(similar_risk:ChurnRisk)
   WHERE similar_risk.score > 70
   MATCH (similar_user)-[:RECEIVED]->(intervention:Intervention)
   MATCH (intervention)-[:RESULTED_IN]->(outcome:Outcome)
   WHERE outcome.did_reactivate = true
   RETURN intervention.type, count(outcome) AS success_count
   ORDER BY success_count DESC

   // Top interventions: "rate_alert" (87%), "bonus_offer" (82%), "human_outreach" (65%)

4. Send personalized intervention:
   MATCH (user)-[:LAST_USED_CORRIDOR]->(corridor:Corridor {name: "UK→India"})
   WITH user, corridor
   CREATE (intervention:Intervention {
     type: "rate_alert",
     message: "GBP/INR rate just hit ₹105 - best in 2 weeks!",
     sent_at: now()
   })
   CREATE (user)-[:RECEIVED]->(intervention)
   CREATE (intervention)-[:TARGETS_CORRIDOR]->(corridor)

5. TRACK outcome (graph edge will be updated):
   CREATE (intervention)-[:AWAITING_OUTCOME {check_after: now() + duration('PT36H')}]->(user)

DAY 3: User reactivates (or doesn't)
────────────────────────────────────────────────────────────────────────────
Event: User places order (or timeout after 36 hours)

CommsAgent (Auto-triggered):
6. Update outcome:
   MATCH (user)-[:PLACED]->(order:Order)
   WHERE order.created_at > date() - duration('P3D')
   MATCH (user)-[:RECEIVED]->(intervention:Intervention)
   WHERE intervention.sent_at > order.created_at - duration('PT48H')

   CREATE (outcome:Outcome {
     did_reactivate: true,
     time_to_reactivation_hours: duration.between(intervention.sent_at, order.created_at).hours,
     order_value: order.amount_gbp
   })
   CREATE (intervention)-[:RESULTED_IN]->(outcome)

   // Learning edge: This intervention type worked for this user profile
   MATCH (user)-[:HAS_PROFILE]->(profile:UserProfile)
   CREATE (profile)-[:RESPONDS_TO {effectiveness: 0.92}]->(intervention)

DAY 3: VoCAgent analyzes feedback
────────────────────────────────────────────────────────────────────────────
Event: User leaves app review or responds to NPS survey

VoCAgent:
7. Ingest feedback and link to intervention:
   MATCH (user:User {id: "U123"})
   CREATE (feedback:Feedback {
     text: "The rate alert was really helpful! Almost switched to competitor.",
     sentiment: 0.85,
     created_at: now()
   })
   CREATE (user)-[:PROVIDED]->(feedback)

8. CORRELATE with recent interventions:
   MATCH (user)-[:RECEIVED]->(intervention:Intervention)
   WHERE intervention.sent_at > feedback.created_at - duration('P7D')
   CREATE (feedback)-[:ABOUT]->(intervention)

9. EXTRACT insight and add to graph:
   // LLM extracts: "User almost churned to competitor, rate alert prevented"
   CREATE (insight:Insight {
     type: "near_miss_competitive_churn",
     description: "Rate alerts prevent competitive churn for price-sensitive UK→India users",
     evidence_count: 1
   })
   CREATE (feedback)-[:REVEALS]->(insight)
   CREATE (intervention)-[:VALIDATES]->(insight)

DAY 30: ChurnAgent learns from outcomes
────────────────────────────────────────────────────────────────────────────
ChurnAgent (Monthly learning cycle):
10. Query graph to improve churn model:
    MATCH (user:User)-[:HAS_CHURN_RISK]->(risk:ChurnRisk)
    MATCH (user)-[:RECEIVED]->(intervention:Intervention)
    MATCH (intervention)-[:RESULTED_IN]->(outcome:Outcome)

    RETURN
      risk.factors AS risk_factors,
      intervention.type AS intervention_type,
      outcome.did_reactivate AS success,
      user.corridor AS corridor

    // Train model: rate_alert works 87% for UK→India, 65% for UAE→India
    // Update churn model weights

11. REFINE intervention recommendations:
    MATCH (user:User)-[:HAS_CHURN_RISK]->(risk:ChurnRisk)
    WHERE risk.score > 70
    MATCH (user)-[:LAST_USED_CORRIDOR]->(corridor:Corridor)

    // Use graph to find best intervention for this corridor
    MATCH (corridor)<-[:TARGETS_CORRIDOR]-(past_interventions:Intervention)
          -[:RESULTED_IN]->(outcomes:Outcome {did_reactivate: true})

    WITH intervention_type, count(outcomes) AS success_count
    ORDER BY success_count DESC
    LIMIT 1

    RETURN intervention_type AS recommended_intervention

    // For UK→India: "rate_alert" (87% success)
    // For UAE→India: "bonus_offer" (82% success)

DAY 60: DataSanity Agent surfaces trend
────────────────────────────────────────────────────────────────────────────
DataSanityAgent (Weekly proactive insights):
12. Detect emerging pattern:
    MATCH (feedback:Feedback)-[:REVEALS]->(insight:Insight {type: "near_miss_competitive_churn"})
    WHERE feedback.created_at > date() - duration('P30D')

    WITH insight, count(feedback) AS evidence_count
    WHERE evidence_count > 50  // Threshold for "trend"

    CREATE (trend:Trend {
      pattern: "Competitive churn increasing for UK→India corridor",
      evidence_count: evidence_count,
      detected_at: date(),
      severity: "high"
    })
    CREATE (insight)-[:CONTRIBUTES_TO]->(trend)

13. HAND OFF to Product team (via Slack notification):
    // "@growth-team TREND ALERT: 50+ users cited 'almost switched to competitor'
    //  in past 30 days. Corridor: UK→India. Root cause: Rate sensitivity.
    //  Current mitigation: Rate alerts (87% effective).
    //  RECOMMENDATION: Consider rate-lock feature or competitive-rate-match guarantee."
```

**Result (Emergent Intelligence)**:
- ChurnAgent → CommsAgent → VoCAgent → DataSanityAgent collaboration
- Each agent learns from others' work (intervention effectiveness stored in graph)
- Patterns emerge: "Rate alerts work for UK→India, bonus offers for UAE→India"
- Proactive trend detection: "Competitive churn increasing"
- Product recommendations: "Build rate-lock feature"

**Query for Growth team review**:
```cypher
// "What's our churn intervention effectiveness by corridor?"
MATCH (corridor:Corridor)<-[:LAST_USED_CORRIDOR]-(user:User)
      -[:HAS_CHURN_RISK]->(risk:ChurnRisk)
MATCH (user)-[:RECEIVED]->(intervention:Intervention)
      -[:RESULTED_IN]->(outcome:Outcome)
RETURN
  corridor.name,
  intervention.type,
  count(outcome) AS total_sent,
  sum(CASE WHEN outcome.did_reactivate THEN 1 ELSE 0 END) AS reactivations,
  (sum(CASE WHEN outcome.did_reactivate THEN 1 ELSE 0 END) * 100.0 / count(outcome)) AS success_rate,
  avg(outcome.order_value) AS avg_order_value
ORDER BY corridor.name, success_rate DESC
```

---

## The Platform Architecture

### Layer 1: Skill Authoring (Humans Write Markdown)

Domain experts write skills in markdown:

```markdown
# fraud/block-beneficiary.md
---
name: block-beneficiary
description: Block a beneficiary across all TRM platforms when fraud detected
agent: FraudAgent
triggers:
  - manual: "block beneficiary {beneficiary_id}"
  - event: "fraud_alert_received"
requires_context: [beneficiary_id, reason, alert_id]
---

## Execution Steps

1. **Verify beneficiary exists**
   Query graph:
   ```cypher
   MATCH (ben:Beneficiary {id: $beneficiary_id})
   RETURN ben
   ```

2. **Check existing blocks**
   ```cypher
   MATCH (ben)-[:BLOCKED_AT]->(block:Block)
   WHERE block.status = 'active'
   RETURN block
   ```

   If already blocked → SKIP

3. **Create block action**
   ```cypher
   CREATE (block:Block {
     beneficiary_id: $beneficiary_id,
     reason: $reason,
     created_at: now(),
     created_by_alert: $alert_id,
     platforms: ['TRM_UK', 'TRM_US', 'TRM_UAE']
   })
   CREATE (ben)-[:BLOCKED_AT]->(block)
   CREATE (block)-[:EXECUTED_BY]->(agent:Agent {name: 'FraudAgent'})
   ```

4. **Find affected pending orders**
   ```cypher
   MATCH (ben)-[:USED_IN]->(orders:Order)
   WHERE orders.status IN ['pending', 'processing']
   WITH orders, collect(users) AS affected_users
   CREATE (block)-[:PREVENTED]->(orders)
   RETURN affected_users, count(orders) AS prevented_count
   ```

5. **Notify affected users**
   Hand off to Support Agent:
   ```cypher
   CREATE (task:Task {
     type: 'notify_fraud_prevention',
     users: affected_users,
     message: 'Your pending order was cancelled for security. We suspect fraud.'
   })
   CREATE (task)-[:ASSIGNED_TO]->(supportAgent:Agent {name: 'SupportAgent'})
   ```

6. **Hand off to Churn Agent**
   Prevent churn from affected users:
   ```cypher
   CREATE (task:Task {
     type: 'compensate_fraud_victims',
     users: affected_users,
     priority: 'high'
   })
   CREATE (task)-[:ASSIGNED_TO]->(churnAgent:Agent {name: 'ChurnAgent'})
   ```

## Success Criteria
- Beneficiary blocked across all platforms
- Pending orders cancelled
- Users notified
- Churn prevention triggered
```

**Key Point**: Domain expert writes WHAT to do. Platform handles HOW to execute, orchestrate, and learn.

---

### Layer 2: Agent Swarm Orchestration

```python
# packages/swarm/orchestrator.py
from pydantic_ai import Agent
from neo4j import GraphDatabase

class AgentSwarmOrchestrator:
    """
    Orchestrates multi-agent workflows using Knowledge Graph
    Pattern: OpenAI Swarm / Ant Colony
    """

    def __init__(self, neo4j_uri: str, agents_config: dict):
        self.graph = GraphDatabase.driver(neo4j_uri)
        self.agents = {}

        # Initialize specialized agents
        for agent_name, agent_config in agents_config.items():
            self.agents[agent_name] = self._create_agent(agent_name, agent_config)

    def _create_agent(self, name: str, config: dict) -> Agent:
        """Create specialized agent with graph access"""
        return Agent(
            config['model'],  # e.g., 'anthropic/claude-sonnet-4.5'
            system_prompt=f"""
You are {name}, a specialized agent in the Aspora platform.

Your role: {config['description']}
Your skills: {config['skills']}

You have access to a central Knowledge Graph (Neo4j) where ALL agents write/read.

CRITICAL:
1. ALWAYS query graph BEFORE acting (check what other agents discovered)
2. WRITE your findings to graph (so other agents learn)
3. HAND OFF to other agents when appropriate (create Task nodes)
4. CITE precedents from graph (use past successful patterns)

Your tools allow you to:
- Query graph (read what other agents learned)
- Write to graph (share your findings)
- Hand off tasks (trigger other agents)
- Search precedents (find similar past cases)
""",
            tools=self._get_agent_tools(name)
        )

    def _get_agent_tools(self, agent_name: str) -> list:
        """MCP tools for graph access"""
        return [
            self._tool_query_graph,
            self._tool_write_to_graph,
            self._tool_handoff_to_agent,
            self._tool_search_precedents,
            self._tool_find_related_entities
        ]

    async def execute_skill(self, skill_id: str, context: dict) -> dict:
        """
        Execute a skill, potentially triggering multi-agent workflow
        """
        # Load skill definition
        skill = await self._load_skill(skill_id)

        # Determine which agent owns this skill
        agent_name = skill['agent']
        agent = self.agents[agent_name]

        # Create execution node in graph
        with self.graph.session() as session:
            session.run("""
                CREATE (exec:Execution {
                    id: $exec_id,
                    skill_id: $skill_id,
                    agent: $agent_name,
                    context: $context,
                    started_at: datetime()
                })
            """, exec_id=uuid4(), skill_id=skill_id, agent_name=agent_name, context=context)

        # Execute with agent
        result = await agent.run(
            f"Execute skill: {skill['name']}\nContext: {json.dumps(context)}",
            deps={'graph': self.graph, 'context': context}
        )

        # Check if agent handed off to other agents
        handoffs = await self._check_handoffs(result)

        # Execute handoff tasks (recursive)
        for handoff in handoffs:
            await self.execute_skill(
                handoff['skill_id'],
                handoff['context']
            )

        return result

    async def _tool_handoff_to_agent(self, ctx, target_agent: str, task_type: str, task_context: dict):
        """Tool: Hand off task to another agent"""
        with self.graph.session() as session:
            session.run("""
                MATCH (source:Agent {name: $source_agent})
                CREATE (task:Task {
                    id: $task_id,
                    type: $task_type,
                    context: $task_context,
                    status: 'pending',
                    created_at: datetime()
                })
                CREATE (task)-[:ASSIGNED_TO]->(target:Agent {name: $target_agent})
                CREATE (source)-[:HANDED_OFF_TO {context: $task_context}]->(target)

                RETURN task.id
            """,
                source_agent=ctx.deps.get('agent_name'),
                target_agent=target_agent,
                task_id=str(uuid4()),
                task_type=task_type,
                task_context=task_context
            )

        return f"Task handed off to {target_agent}"
```

---

### Layer 3: Central Knowledge Graph Schema

```python
# knowledge-graph/schema.py

ENTITY_TYPES = {
    # Core Business Entities
    'User': ['id', 'email', 'corridor', 'country', 'churn_score', 'ltv'],
    'Order': ['id', 'amount_gbp', 'status', 'created_at', 'corridor'],
    'Beneficiary': ['id', 'account_number', 'bank', 'country'],
    'Transaction': ['id', 'amount', 'currency', 'timestamp', 'status'],

    # Agent Entities
    'Agent': ['name', 'type', 'skills', 'model'],
    'Execution': ['id', 'skill_id', 'agent', 'context', 'result', 'cost', 'embedding'],
    'Task': ['id', 'type', 'context', 'status', 'priority'],

    # Intelligence Entities
    'Pattern': ['name', 'description', 'frequency', 'confidence', 'embedding'],
    'RootCause': ['description', 'confidence', 'first_seen', 'last_seen', 'embedding'],
    'Solution': ['fix', 'description', 'success_rate', 'cost', 'embedding'],
    'Insight': ['type', 'description', 'evidence_count', 'severity'],
    'Trend': ['pattern', 'evidence_count', 'detected_at', 'severity'],

    # Fraud & Risk
    'FraudAlert': ['id', 'type', 'severity', 'timestamp', 'reason'],
    'Block': ['beneficiary_id', 'reason', 'platforms', 'created_at'],

    # Support & Operations
    'BugReport': ['title', 'symptom', 'frequency', 'affected_users', 'status', 'embedding'],
    'Deployment': ['id', 'service', 'version', 'timestamp', 'changes'],
    'Incident': ['id', 'severity', 'detected_at', 'resolved_at', 'mttr'],

    # Growth & Retention
    'ChurnRisk': ['user_id', 'score', 'factors', 'predicted_at'],
    'Intervention': ['type', 'message', 'sent_at', 'channel'],
    'Outcome': ['did_reactivate', 'time_to_reactivation_hours', 'order_value'],
    'Feedback': ['text', 'sentiment', 'created_at', 'source'],

    # Product & Context
    'Feature': ['name', 'description', 'launched_at', 'owner'],
    'Decision': ['title', 'context', 'chosen', 'reasoning', 'date'],
    'Document': ['type', 'title', 'content', 'updated_at', 'embedding'],
}

RELATIONSHIP_TYPES = {
    # Business Relationships
    'PLACED': {},  # User → Order
    'TO': {},  # Order → Beneficiary
    'CONTAINS': {},  # Order → Transaction
    'LAST_USED_CORRIDOR': {},  # User → Corridor

    # Agent Orchestration
    'EXECUTED_BY': {},  # Action → Agent
    'ASSIGNED_TO': {},  # Task → Agent
    'HANDED_OFF_TO': {'properties': ['context', 'timestamp']},  # Agent → Agent
    'TRIGGERED': {},  # Event → Task

    # Intelligence Relationships (CRITICAL FOR LEARNING)
    'EXHIBITS': {'properties': ['confidence']},  # Entity → Pattern
    'CAUSED_BY': {'properties': ['confidence', 'evidence']},  # Event → RootCause
    'SOLVED_BY': {'properties': ['success_rate', 'application_count']},  # RootCause → Solution
    'REVEALED': {},  # Execution → RootCause (agent learned something)
    'CORRECTED_BY': {},  # Execution → Correction (user fixed agent)
    'REFINED': {},  # Correction → Solution (learning applied)
    'SIMILAR_TO': {'properties': ['similarity']},  # Pattern → Pattern (vector edge)

    # Fraud & Risk
    'FLAGGED_IN': {},  # Beneficiary → FraudAlert
    'BLOCKED_AT': {},  # Beneficiary → Block
    'PREVENTED': {},  # Block → Order

    # Churn & Growth
    'HAS_CHURN_RISK': {},  # User → ChurnRisk
    'RECEIVED': {},  # User → Intervention
    'RESULTED_IN': {},  # Intervention → Outcome
    'PROVIDED': {},  # User → Feedback
    'REVEALS': {},  # Feedback → Insight
    'CONTRIBUTES_TO': {},  # Insight → Trend

    # Operations
    'REPORTED': {},  # User → BugReport
    'DUPLICATE_OF': {},  # BugReport → BugReport
    'TRACED_TO': {},  # BugReport → CodeFile
    'CHANGED_IN': {},  # CodeFile → Deployment
    'CAUSED': {},  # Deployment → Incident

    # Context & Knowledge
    'REFERENCES': {},  # Document → Document
    'DEPENDS_ON': {},  # Decision → Decision
    'IMPLEMENTED_BY': {},  # Feature → Deployment
}
```

---

## Solving Each Hackathon Problem with Graph

### 1. Rule-Based Simulation Platform
**Graph Pattern**: Simulation runs create nodes, rule violations create edges

```cypher
// Run simulation
CREATE (sim:Simulation {
  id: $sim_id,
  rule_set: 'remittances_v2',
  start_date: date('2025-01-01'),
  end_date: date('2025-12-31')
})

// For each transaction in historical data
MATCH (txn:Transaction)
WHERE txn.date BETWEEN sim.start_date AND sim.end_date

// Apply rules and create violations
FOREACH (rule in $rules |
  CASE WHEN evaluate_rule(txn, rule) = 'FAIL'
  CREATE (violation:RuleViolation {
    transaction_id: txn.id,
    rule: rule.name,
    severity: rule.severity
  })
  CREATE (txn)-[:VIOLATED]->(violation)
  CREATE (sim)-[:DETECTED]->(violation)
)

// Analyze patterns
MATCH (sim)-[:DETECTED]->(violations:RuleViolation)
WITH rule.name, count(violations) AS violation_count
ORDER BY violation_count DESC
RETURN rule.name, violation_count

// Find which user attributes predict violations
MATCH (user:User)-[:PLACED]->(order:Order)-[:CONTAINS]->(txn:Transaction)
      -[:VIOLATED]->(violation:RuleViolation)
WITH user.country, user.age_bucket, violation.rule, count(*) AS freq
RETURN user.country, user.age_bucket, violation.rule, freq
ORDER BY freq DESC
```

**Intelligence**: Graph reveals "UAE users aged 25-35 violate velocity rules 3x more" → Adjust risk model

---

### 2. Fraud Monitoring Agent
**Already covered above** — Multi-agent collaboration with handoffs

---

### 3. Vibecoding Companion
**Graph Pattern**: Project context graph + codebase relationship graph

```cypher
// Map codebase relationships
CREATE (file:CodeFile {path: 'src/payments/processor.ts'})
CREATE (func:Function {name: 'processPayment', file: file.path})
CREATE (func)-[:CALLS]->(dep:Function {name: 'validateBeneficiary'})
CREATE (func)-[:USES]->(service:Service {name: 'payment-service'})

// When developer asks: "How do I add retry logic to payment processing?"

// 1. Find relevant code
MATCH (func:Function {name: 'processPayment'})
MATCH (func)-[:CALLS]->(dependencies)
RETURN func, dependencies

// 2. Find similar past changes
MATCH (pr:PullRequest)-[:MODIFIED]->(file:CodeFile {path: 'src/payments/'})
WHERE pr.title CONTAINS 'retry'
MATCH (pr)-[:REVIEWED_BY]->(reviewer:Engineer)
WHERE reviewer.expertise CONTAINS 'payments'
RETURN pr, reviewer

// 3. Find guardrails
MATCH (decision:Decision)
WHERE decision.scope = 'payments' AND decision.topic = 'error_handling'
RETURN decision.constraint

// Agent response:
// "Found 2 similar changes (#PR1234, #PR5678)
//  Guardrail: Always use exponential backoff (DECISIONS.md #DEC-042)
//  Reviewer: @alice (payments expert)
//  Sample code: [link to PR1234]"
```

---

### 4. User Reachout Platform
**Graph Pattern**: Customer profile graph with interaction history

```cypher
// Create customer profile
CREATE (customer:Customer {
  id: $id,
  name: $name,
  segment: 'enterprise',
  status: 'prospect'
})

// After each reachout
CREATE (reachout:Reachout {
  timestamp: now(),
  channel: 'email',
  employee: 'sarah@aspora.com',
  message: 'Pitched benefits transfer service'
})
CREATE (customer)-[:CONTACTED_VIA]->(reachout)

// Employee adds response
CREATE (response:Response {
  text: "Interested but concerned about compliance in UAE",
  sentiment: 0.6,
  next_action: 'Send compliance documentation'
})
CREATE (reachout)-[:RECEIVED_RESPONSE]->(response)

// Extract insight
CREATE (objection:Objection {type: 'compliance_concern', region: 'UAE'})
CREATE (response)-[:RAISED]->(objection)

// Find patterns across reachouts
MATCH (customers:Customer)-[:CONTACTED_VIA]->(reachouts:Reachout)
      -[:RECEIVED_RESPONSE]->(responses:Response)
      -[:RAISED]->(objections:Objection)
WHERE objection.type = 'compliance_concern'
GROUP BY objection.region
RETURN objection.region, count(objections) AS frequency
ORDER BY frequency DESC

// Result: "UAE compliance concerns raised in 47% of enterprise reachouts"
// → Product action: Create UAE compliance one-pager
```

---

### 5. Comms Automation
**Already covered in Agent-to-Agent Learning section**

---

### 6. Invoice Processing
**Graph Pattern**: Invoice workflow with approval chain

```cypher
// Capture invoice
CREATE (invoice:Invoice {
  id: $id,
  vendor: 'AWS',
  amount_usd: 12500,
  due_date: date('2026-03-15'),
  received_at: datetime()
})

// Extract payment terms
CREATE (terms:PaymentTerms {
  net_days: 30,
  early_payment_discount: 0.02
})
CREATE (invoice)-[:HAS_TERMS]->(terms)

// Auto-route for approval
MATCH (invoice)
WHERE invoice.amount_usd > 10000
CREATE (approval:ApprovalRequest {
  status: 'pending',
  required_by: 'CFO'
})
CREATE (invoice)-[:REQUIRES_APPROVAL]->(approval)

// Schedule payment
MATCH (invoice)-[:HAS_TERMS]->(terms)
WITH invoice, date.add(invoice.received_at, duration({days: terms.net_days})) AS payment_date
CREATE (payment:ScheduledPayment {
  scheduled_for: payment_date,
  amount: invoice.amount_usd,
  status: 'pending_approval'
})
CREATE (invoice)-[:SCHEDULED_AS]->(payment)

// Weekly payment run
MATCH (payment:ScheduledPayment)
WHERE payment.scheduled_for BETWEEN date() AND date() + duration('P7D')
AND payment.status = 'approved'
RETURN payment
ORDER BY payment.scheduled_for
```

---

### 7. Churn Prediction & Intervention
**Already covered in Multi-Hop Reasoning section**

---

### 8. CX Bug Resolver
**Already covered in Auto-RCA section**

---

### 9. VoC Engine
**Graph Pattern**: Aggregate signals from all sources into insight graph

```cypher
// Ingest signals from multiple sources
CREATE (call:CallSummary {
  text: "Customer frustrated with slow KYC approval",
  sentiment: -0.7,
  source: 'zendesk_call_123'
})
CREATE (survey:SurveyResponse {
  nps: 4,
  comment: "KYC took 3 days, almost gave up",
  source: 'typeform_456'
})
CREATE (review:AppReview {
  rating: 2,
  text: "KYC verification is painfully slow",
  source: 'appstore_789'
})

// Extract common root cause (LLM-powered)
CREATE (root:RootCause {
  pattern: 'kyc_approval_delay',
  description: 'KYC manual review taking >48 hours',
  embedding: $embedding
})
CREATE (call)-[:REVEALS]->(root)
CREATE (survey)-[:REVEALS]->(root)
CREATE (review)-[:REVEALS]->(root)

// Quantify impact
MATCH (root)-[:REVEALED_BY]-(signals)
WITH root, count(signals) AS signal_count
WHERE signal_count > 20  // Threshold

// Calculate GMV at risk
MATCH (user:User)-[:LEFT_REVIEW|RESPONDED_TO_SURVEY|HAD_CALL]->(signal)
      -[:REVEALS]->(root)
MATCH (user)-[:WOULD_HAVE_PLACED]->(potential_order:PotentialOrder)
WITH root, sum(potential_order.estimated_value_gbp) AS gmv_at_risk

// Correlate with NPS
MATCH (survey:SurveyResponse)-[:REVEALS]->(root)
WITH root, avg(survey.nps) AS avg_nps

CREATE (brief:ProductBrief {
  title: 'KYC approval delays causing churn',
  evidence_count: signal_count,
  gmv_at_risk_gbp: gmv_at_risk,
  nps_impact: avg_nps - 7.2,  // vs company baseline
  priority: 'critical'
})
CREATE (root)-[:REQUIRES_ACTION {brief_id: brief.id}]->(brief)
```

**Result**: Auto-generated product brief:
- Evidence: 37 user signals (calls, surveys, reviews)
- GMV at risk: £450K/month
- NPS impact: -2.1 points
- Root cause: KYC manual review taking >48h
- Recommendation: Automate KYC for low-risk segments

---

## The Holistic Intelligence Layer

### How Graph Solves"Data Sanity" Problem

**Current State**: Data scattered across PostgreSQL, MongoDB, ClickHouse, S3, Metabase

**Graph Solution**: Unified entity resolution + relationship graph

```cypher
// Consolidate scattered user data
MATCH (pg_user:PostgresUser {email: 'john@example.com'})
MATCH (mongo_profile:MongoProfile {user_id: pg_user.id})
MATCH (analytics_user:ClickhouseUser {email: 'john@example.com'})

// Create canonical user node
MERGE (user:User {canonical_id: $canonical_id})
SET user += {
  email: pg_user.email,
  name: mongo_profile.name,
  country: pg_user.country,
  ltv: analytics_user.ltv,
  updated_at: datetime()
}

// Link source systems
CREATE (user)-[:SOURCED_FROM {system: 'postgres'}]->(pg_user)
CREATE (user)-[:SOURCED_FROM {system: 'mongo'}]->(mongo_profile)
CREATE (user)-[:SOURCED_FROM {system: 'clickhouse'}]->(analytics_user)

// Now ALL agents query canonical user graph, not scattered DBs
```

**Proactive Insight Detection**:
```cypher
// DataSanityAgent runs weekly
MATCH (user:User)-[:PLACED]->(orders:Order)
WITH user, count(orders) AS pg_order_count

MATCH (user)-[:SOURCED_FROM {system: 'clickhouse'}]->(ch_user)
WHERE abs(pg_order_count - ch_user.order_count) > 5

// Data mismatch detected
CREATE (alert:DataQualityAlert {
  type: 'order_count_mismatch',
  user_id: user.id,
  postgres_count: pg_order_count,
  clickhouse_count: ch_user.order_count,
  detected_at: datetime()
})

// Notify data team
CREATE (task:Task {type: 'investigate_data_mismatch'})
CREATE (task)-[:ASSIGNED_TO]->(dataTeam:Agent {name: 'DataSanityAgent'})
```

---

### How Graph Solves "Context & Knowledge Management"

**Current State**: Information in Notion, Slack, Google Docs, GitHub, scattered

**Graph Solution**: Unified knowledge graph with semantic links

```cypher
// Ingest all documents
CREATE (decision:Decision {
  title: "DEC-042: Use exponential backoff for payment retries",
  content: $content,
  date: date('2025-11-20'),
  source: 'DECISIONS.md',
  embedding: $embedding
})

CREATE (doc:Documentation {
  title: "Payment Processing Architecture",
  content: $content,
  source: 'docs/payments.md',
  embedding: $embedding
})

CREATE (slack:SlackThread {
  channel: '#engineering',
  topic: 'Payment retry strategy',
  messages: $messages,
  date: date('2025-11-18'),
  embedding: $embedding
})

// Create semantic links
MATCH (decision), (doc), (slack)
WHERE vector.similarity.cosine(decision.embedding, doc.embedding) > 0.80
CREATE (decision)-[:DOCUMENTED_IN]->(doc)

MATCH (decision), (slack)
WHERE vector.similarity.cosine(decision.embedding, slack.embedding) > 0.75
CREATE (decision)-[:DISCUSSED_IN]->(slack)

// When developer asks: "How should I implement payment retries?"
// ContextMgrAgent queries:
MATCH (decision:Decision)
WHERE decision.title CONTAINS 'retry'
MATCH (decision)-[:DOCUMENTED_IN]->(docs)
MATCH (decision)-[:DISCUSSED_IN]->(discussions)
RETURN decision, docs, discussions

// Response: "See DEC-042 (exponential backoff)
//           Documented in: docs/payments.md
//           Historical context: #engineering Slack thread from Nov 18"
```

**Institutional Memory Query**:
```cypher
// "Why did we choose Firecracker over Docker?"
MATCH (decision:Decision)
WHERE decision.title CONTAINS 'Firecracker' OR decision.title CONTAINS 'Docker'
MATCH (decision)-[:REFERENCED_BY]->(subsequent_decisions:Decision)
MATCH (decision)<-[:INFLUENCED]-(team_member:TeamMember)
RETURN
  decision.title,
  decision.reasoning,
  decision.constraints,
  collect(subsequent_decisions.title) AS impact,
  collect(team_member.name) AS decision_makers
```

---

## Implementation Timeline: 16-20 Hours (Hackathon)

### Phase 1 (0-6h): Core Graph + 3 Agents
- Deploy Neo4j AuraDB
- Define graph schema (entities + relationships from above)
- Build 3 core agents: FraudAgent, SupportAgent, RCAAgent
- Implement MCP server for graph queries
- Test 1-2 agent handoff scenarios

### Phase 2 (6-12h): Multi-Agent Orchestration
- Build AgentSwarmOrchestrator
- Implement handoff mechanism (Task creation)
- Add ChurnAgent + CommsAgent
- Test multi-agent workflow (3+ agents collaborating)
- Seed graph with 50-100 sample executions

### Phase 3 (12-16h): Intelligence Layer (GraphRAG)
- Add vector indexes to graph (embeddings on Execution, Solution, Pattern nodes)
- Implement hybrid query (vector entry → graph traversal)
- Build Reflexion learning loop (corrections update graph)
- Add DataSanityAgent + ContextMgrAgent (meta-agents)

### Phase 4 (16-20h): Demo Polish
- Create Neo4j Bloom visualization (show graph traversal live)
- Build demo script (show 3-4 problems solved holistically)
- Prep "Uber's pattern applied to agent swarm" pitch
- Documentation + README

---

## Demo Script: "The Aspora Brain"

### Act 1 (60s): "The Problem"
Show scattered systems:
- Fraud alerts in Metabase
- Support tickets in Slack
- Churn predictions in ClickHouse
- Bug reports in Linear
- User feedback in Zendesk

"Each system is a silo. Agents can't learn from each other. No institutional memory."

### Act 2 (90s): "The Graph Solution"
Show Neo4j visualization:
- User node in center
- Connected to: Orders, Fraud Alerts, Support Tickets, Churn Risk, Feedback
- Show relationships lighting up as agents traverse

Live demo:
1. User complains about beneficiary (SupportAgent creates node)
2. Graph traversal finds 5 other fraud cases with same beneficiary
3. FraudAgent blocks beneficiary automatically
4. ChurnAgent compensates affected users
5. VoCAgent aggregates feedback into trend
6. DataSanityAgent surfaces insight for product team

"ONE complaint → 5 agents collaborated → 12 prevented fraud orders → Competitive churn trend detected"

### Act 3 (60s): "The Learning Loop"
Show Reflexion in action:
1. Agent recommends solution A
2. User corrects: "Wrong, real issue is B"
3. Graph stores correction as (Execution)-[:CORRECTED_BY]->(Correction)-[:REFINED]->(Solution)
4. Next similar case: Agent loads correction FIRST
5. Correct answer immediately

"After 6 months: 10,000+ cases in graph. Competitor starting from zero can't catch up. This IS the moat."

### Act 4 (30s): "The Uber Precedent"
Show Uber quote:
> "Knowledge graph had biggest impact on accuracy, way more than prompt engineering"
> — Uber Senior Staff Engineer

"Uber built this for config validation with 2 engineers in 12 weeks.
 We're applying it to operational intelligence.
 Same pattern. Same timeline. 20x the use cases."

---

## Final Answer to Your Question

**Yes, Knowledge Graph + GraphRAG makes PERFECT sense for your platform because**:

1. **Cross-Domain Correlation**: Fraud + Support + Churn + VoC all need to traverse User → Order → Beneficiary → Pattern

2. **Multi-Hop Reasoning**: Payment delay → User frustration → Churn → Lost revenue (graph traversal, not vector similarity)

3. **Agent Swarm Substrate**: Each agent writes to graph, reads from graph, learns from other agents' work

4. **Institutional Memory**: Decisions, precedents, corrections all stored as graph nodes (solves Context & Knowledge Management)

5. **Data Sanity**: Canonical entity graph consolidates scattered data (solves "Data Sanity" problem inherently)

6. **Emergent Intelligence**: More agents execute → More patterns emerge → Better decisions (compound moat)

**The Platform You're Building**:
- **NOT** just an ECM/FinCrime skills executor
- **IS** Aspora's Central Intelligence Platform (like Jarvis for your company)
- **20+ agent use cases** all tapping into ONE knowledge graph
- **Humans write skills** (markdown), agents execute, graph learns

**Implementation**: 16-20 hours for hackathon MVP (3-5 agents, core graph, basic orchestration)

**The Pitch**: "We're building the Aspora Brain - where every department's agent learns from every other department's work. Uber validated this pattern. We're scaling it to 20+ use cases."

Want me to create a detailed implementation guide for the swarm orchestrator?
