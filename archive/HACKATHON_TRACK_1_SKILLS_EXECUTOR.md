# Track 1: Skills Executor Platform (OpenClaw-style)

**Tagline**: "Multi-Domain Agent Platform for Operations Teams"

**What You're Building**: Production-grade skills executor that runs ECM, FinCrime, and Fraud Guardian domains for internal operations teams via Slack/WhatsApp.

**Demo Pitch**: "One platform. Three domains. Ten skills. Field agents resolve shipments, analysts investigate alerts, risk teams simulate rules — all through Slack. Multi-agent orchestration with auto-learning from user corrections."

---

## Strategic Positioning

### The Problem You're Solving
Operations teams use 10+ disconnected tools:
- ECM: Salesforce for tickets, Excel for tracking, Email for escalations
- FinCrime: Core banking system, sanctions screening, manual investigations
- Fraud: Rule engines scattered across systems, no simulation environment

**Pain**: Context switching kills productivity. Knowledge locked in expert heads.

### The Solution
Unified agent platform where ANY operation is a Slack message:
- "show my tickets" → ECM agent lists pending work
- "investigate alert 5678" → FinCrime agent pulls transaction history
- "simulate rule change" → Fraud agent predicts impact

**Moat**: Auto-learning from user corrections. Platform improves itself.

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Agent Framework** | Pydantic AI | Type-safe, structured outputs, tool calling |
| **LLM Router** | OpenRouter | Cost optimization (Haiku for lookups, Sonnet for analysis) |
| **Communication** | Slack Bolt SDK, Meta WhatsApp Business | Official SDKs (not OpenClaw wrappers) |
| **Registry** | PostgreSQL + YAML configs | Skill metadata, execution logs |
| **Orchestration** | Pydantic AI multi-agent | Manager → Field → Analyst handoffs |
| **Observability** | OpenTelemetry → Prometheus | Per-skill cost, latency, error rate |
| **Testing** | DeepEval (unit), Promptfoo (A/B) | LLM-specific testing frameworks |
| **Deployment** | Docker Compose (demo), K8s (production) | Multi-container orchestration |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  COMMUNICATION LAYER (Slack Bolt, WhatsApp Webhook)             │
│  - Event listeners (message, command, button click)             │
│  - User identity mapping (Slack ID → Aspora user_id)            │
│  - Channel adapters (format responses for Slack/WhatsApp)       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  PLATFORM CORE (SkillExecutor + DomainRegistry)                 │
│  - Route message to appropriate domain                          │
│  - Inject context (user_id, team_id, role)                      │
│  - Validate required context fields                             │
│  - Execute skill with Pydantic AI agent                         │
│  - Log execution (cost, latency, user, output)                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  DOMAINS (ECM, FinCrime, Fraud Guardian)                        │
│                                                                 │
│  ecm/                                                           │
│  ├── aspora.config.yaml (scope: team, model routing)           │
│  └── skills/                                                    │
│      ├── field/my-tickets.md (Haiku, < 1s)                     │
│      ├── field/shipment-status.md (Haiku)                      │
│      ├── manager/approve-refund.md (Sonnet, complex logic)     │
│      └── manager/analytics-summary.md (Sonnet)                 │
│                                                                 │
│  fincrime/                                                      │
│  ├── aspora.config.yaml (scope: team, audit logging)           │
│  └── skills/                                                    │
│      ├── investigate-alert.md (Sonnet, multi-step)             │
│      ├── sanctions-check.md (Haiku)                            │
│      └── disposition-recommend.md (Sonnet)                     │
│                                                                 │
│  fraud-guardian/                                                │
│  ├── aspora.config.yaml (scope: analyst, simulation)           │
│  └── skills/                                                    │
│      ├── simulate-rule-change.md (Sonnet, statistical)         │
│      ├── explain-false-positive.md (Sonnet)                    │
│      └── backtest-rule.md (Sonnet, heavy compute)              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  DATA LAYER (PostgreSQL + CSV/Parquet for demo)                │
│  - users (id, team_id, role, preferences)                      │
│  - user_identities (slack_id → user_id mapping)                │
│  - skill_executions (audit log: who, when, what, cost)         │
│  - ecm_tickets (demo data)                                     │
│  - fincrime_alerts (demo data)                                 │
│  - fraud_rules (demo data)                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 36-Hour Timeline (5 People)

### Team Roles
- **Person A (Platform Lead)**: SkillExecutor, DomainRegistry, context validation
- **Person B (Domain Lead)**: ECM, FinCrime, Fraud config files + demo data
- **Person C (Channel Lead)**: Slack bot, WhatsApp webhook, user identity
- **Person D (Observability Lead)**: OpenTelemetry, cost tracking, dashboard
- **Person E (Testing Lead)**: DeepEval tests, Promptfoo A/B, correction tracking

---

### Hour 0-4: Foundation Setup

**Person A (Platform)**:
```bash
# Create project structure
mkdir -p aspora-platform/{packages,domains,channels,tests,workflows}

# Setup packages/executor
cd packages/executor
# Install Pydantic AI, OpenRouter client
pip install pydantic-ai openai python-dotenv

# Create skill_executor.py
```

```python
# packages/executor/skill_executor.py
from pydantic_ai import Agent
from openai import OpenAI
import yaml

class SkillExecutor:
    def __init__(self, registry_path: str, openrouter_key: str):
        self.registry = self._load_registry(registry_path)
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )

    async def execute(self, skill_id: str, context: dict) -> dict:
        """Execute a skill with context validation"""
        skill = self.registry.get_skill(skill_id)
        domain = self.registry.get_domain(skill['domain'])

        # Validate required context
        required = skill.get('requires_context', [])
        missing = [r for r in required if r not in context]
        if missing:
            raise ValueError(f"Missing context: {missing}")

        # Build prompt with context injection
        skill_content = self._load_skill_file(skill['path'])
        prompt = self._inject_context(skill_content, context)

        # Execute with appropriate model
        model = skill.get('model', 'anthropic/claude-haiku-4.5')
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "https://aspora.ai",
                "X-Title": "Aspora Platform"
            }
        )

        # Log execution
        await self._log_execution(skill_id, context, response)

        return {
            "skill": skill_id,
            "output": response.choices[0].message.content,
            "cost": self._calculate_cost(response),
            "latency": response.elapsed
        }
```

**Person B (Domains)**:
```bash
# Create domain directories
mkdir -p domains/{ecm,fincrime,fraud-guardian}/skills

# Create aspora.config.yaml for each domain
```

```yaml
# domains/ecm/aspora.config.yaml
domain:
  name: ecm
  description: ECM Operations for field and manager teams
  scope: team
  data_isolation: team_id
  owner: operations-team

skills:
  - name: my-tickets
    path: skills/field/my-tickets.md
    description: Show tickets assigned to user
    requires_context: [user_id, team_id]
    model: anthropic/claude-haiku-4.5
    avg_latency_ms: 800
    avg_cost_usd: 0.01

  - name: shipment-status
    path: skills/field/shipment-status.md
    description: Check shipment tracking status
    requires_context: [user_id, shipment_id]
    model: anthropic/claude-haiku-4.5
    avg_latency_ms: 600

  - name: approve-refund
    path: skills/manager/approve-refund.md
    description: Approve refund request with policy check
    requires_context: [user_id, team_id, ticket_id]
    model: anthropic/claude-sonnet-4.5
    avg_latency_ms: 2000
    avg_cost_usd: 0.05
```

**Person C (Channels)**:
```bash
# Setup Slack bot
cd channels/slack
npm init -y
npm install @slack/bolt dotenv
```

```typescript
// channels/slack/bot.ts
import { App } from '@slack/bolt';
import { SkillExecutor } from '../../packages/executor';

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET
});

const executor = new SkillExecutor(
  './domains',
  process.env.OPENROUTER_API_KEY
);

// User identity lookup
async function getAsporaUser(slackUserId: string) {
  // Query PostgreSQL user_identities table
  const result = await db.query(`
    SELECT u.* FROM users u
    JOIN user_identities ui ON u.id = ui.user_id
    WHERE ui.channel = 'slack' AND ui.channel_user_id = $1
  `, [slackUserId]);

  if (!result.rows[0]) {
    throw new Error('User not registered in Aspora');
  }

  return result.rows[0];
}

// Route messages to skills
app.message(/show my tickets|my tickets/, async ({ message, say }) => {
  const user = await getAsporaUser(message.user);

  const result = await executor.execute('ecm/field/my-tickets', {
    user_id: user.id,
    team_id: user.team_id,
    requesting_user_id: user.id
  });

  await say({
    text: result.output,
    blocks: [
      { type: 'section', text: { type: 'mrkdwn', text: result.output } },
      {
        type: 'context',
        elements: [
          { type: 'mrkdwn', text: `💰 $${result.cost.toFixed(4)} | ⚡ ${result.latency.toFixed(2)}s` }
        ]
      }
    ]
  });
});
```

**Person D (Observability)**:
```python
# packages/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace

# Metrics
skill_executions = Counter(
    'aspora_skill_executions_total',
    'Total skill executions',
    ['domain', 'skill', 'status']
)

skill_latency = Histogram(
    'aspora_skill_latency_seconds',
    'Skill execution latency',
    ['domain', 'skill']
)

skill_cost = Histogram(
    'aspora_skill_cost_usd',
    'Skill execution cost in USD',
    ['domain', 'skill', 'model']
)

active_users = Gauge(
    'aspora_active_users',
    'Currently active users',
    ['domain']
)
```

**Person E (Testing)**:
```python
# tests/skills/test_ecm_my_tickets.py
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

def test_my_tickets_skill():
    """Test ECM my-tickets skill returns relevant ticket list"""

    # Execute skill
    result = await executor.execute('ecm/field/my-tickets', {
        'user_id': 'sarah@aspora.com',
        'team_id': 'operations'
    })

    # Test case
    test_case = LLMTestCase(
        input="Show my pending tickets",
        actual_output=result['output'],
        expected_output="List of tickets assigned to Sarah with status, priority, description"
    )

    # Metrics
    relevancy = AnswerRelevancyMetric(threshold=0.7)

    assert_test(test_case, [relevancy])
    assert result['cost'] < 0.02  # Cost constraint (Haiku)
    assert result['latency'] < 2.0  # Latency constraint
```

---

### Hour 4-8: Domain Skills (ECM Focus)

**Person B (All 4 ECM Skills)**:

```markdown
# domains/ecm/skills/field/my-tickets.md
---
name: my-tickets
description: Show tickets assigned to user
triggers:
  - "show my tickets"
  - "my pending tickets"
  - "what do I need to work on"
---

# My Tickets Skill

> You show the user their assigned ECM tickets with priorities and deadlines.

## Input Context
- `user_id`: The requesting user's email
- `team_id`: User's team identifier

## Data Source
Query the `ecm_tickets` table:
```sql
SELECT ticket_id, title, status, priority, created_at, due_date
FROM ecm_tickets
WHERE assigned_to = {user_id} AND team_id = {team_id}
AND status IN ('pending', 'in_progress')
ORDER BY priority DESC, due_date ASC
LIMIT 10
```

## Output Format
```
📋 Your Tickets ({count} pending)

HIGH PRIORITY:
- #{ticket_id} {title}
  Status: {status} | Due: {due_date}
  {short_description}

NORMAL PRIORITY:
- #{ticket_id} {title}
  ...
```

## Guardrails
- ONLY show tickets assigned to requesting user
- NEVER show tickets from other teams (validate team_id)
- If > 10 tickets, show count and suggest filtering
- Always sort by priority, then due date
```

```markdown
# domains/ecm/skills/field/shipment-status.md
---
name: shipment-status
description: Check real-time shipment tracking
triggers:
  - "track shipment {id}"
  - "where is shipment {id}"
  - "shipment status {id}"
---

# Shipment Status Skill

> You provide real-time shipment tracking information.

## Input Context
- `user_id`: Requesting user
- `shipment_id`: Shipment tracking number

## Data Source
Query `ecm_shipments` table:
```sql
SELECT s.*, l.location, l.timestamp, l.status
FROM ecm_shipments s
JOIN shipment_locations l ON s.shipment_id = l.shipment_id
WHERE s.shipment_id = {shipment_id}
ORDER BY l.timestamp DESC
```

## Output Format
```
📦 Shipment #{shipment_id}

Route: {origin} → {destination}
Current Location: {current_location}
Status: {status}

Timeline:
✅ {timestamp1} - {location1} ({status1})
✅ {timestamp2} - {location2} ({status2})
🔄 {timestamp3} - {location3} (In Transit)

Estimated Delivery: {eta}
```

## Guardrails
- Verify user has access to shipment (same team)
- If stuck > 48 hours, suggest escalation
- Show delays prominently
```

```markdown
# domains/ecm/skills/manager/approve-refund.md
---
name: approve-refund
description: Approve refund with policy validation
triggers:
  - "approve refund {ticket_id}"
  - "refund request {ticket_id}"
---

# Approve Refund Skill

> You help managers approve refund requests with policy checks.

## Input Context
- `user_id`: Manager approving refund
- `team_id`: Manager's team
- `ticket_id`: Ticket requesting refund

## Logic
1. Fetch ticket details and refund amount
2. Check refund policy:
   - Amount <= $500: Auto-approve
   - Amount > $500, <= $2000: Manager approval (this skill)
   - Amount > $2000: Requires VP approval
3. Validate manager has authority (role = 'manager' or 'vp')
4. Check refund reason against policy (fraud, damaged goods, delay)

## Output Format
```
✅ Refund Approved: Ticket #{ticket_id}

Amount: ${amount}
Reason: {reason}
Customer: {customer_name}
Order Date: {order_date}

Policy Check: ✅ PASS
- Amount within manager authority (< $2000)
- Valid reason: {reason}

Next Steps:
1. Refund processed to original payment method
2. Customer notified via email
3. Accounting updated

⚠️ Note: Refund will appear in 3-5 business days
```

## Guardrails
- VERIFY user has 'manager' or 'vp' role
- NEVER approve if amount > $2000 (escalate to VP)
- LOG approval for audit trail
```

```markdown
# domains/ecm/skills/manager/analytics-summary.md
---
name: analytics-summary
description: Team performance analytics
triggers:
  - "team analytics"
  - "performance summary"
  - "team stats"
---

# Analytics Summary Skill

> You provide team performance metrics for managers.

## Input Context
- `user_id`: Manager requesting analytics
- `team_id`: Team to analyze
- `period`: Optional, defaults to 'last_7_days'

## Data Source
Aggregate queries on `ecm_tickets`:
```sql
SELECT
  COUNT(*) as total_tickets,
  COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
  AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) as avg_hours_to_resolve,
  COUNT(*) FILTER (WHERE priority = 'high') as high_priority
FROM ecm_tickets
WHERE team_id = {team_id}
AND created_at >= NOW() - INTERVAL '7 days'
```

## Output Format
```
📊 Team Analytics ({period})

Ticket Volume:
- Total: {total_tickets}
- Resolved: {resolved} ({resolution_rate}%)
- Pending: {pending}

Performance:
- Avg Resolution Time: {avg_hours}h
- High Priority: {high_priority} tickets

Top Performers:
1. {agent1} - {count1} resolved
2. {agent2} - {count2} resolved
3. {agent3} - {count3} resolved

⚠️ Blockers:
- {blocker_count} tickets stuck > 48h
```

## Guardrails
- ONLY show data for manager's team (validate team_id)
- Anonymize if < 5 agents (privacy)
```

**Person A (Platform)**:
- Implement domain registry loader
- Add skill file parser (markdown → prompt)
- Test context injection

**Person C (Channels)**:
- Add message routing for all 4 ECM skills
- Implement user identity caching
- Add error handling (user not found, skill failed)

**Person D (Observability)**:
- Instrument SkillExecutor with metrics
- Setup Prometheus scraping
- Create basic Grafana dashboard

**Person E (Testing)**:
- Write DeepEval tests for all 4 skills
- Add cost/latency assertions
- Test multi-user scenarios (team scoping)

---

### Hour 8-12: Multi-Agent Workflow (ECM)

**Goal**: Field agent asks question → escalates to manager → manager approves

**Person A (Orchestration)**:

```python
# packages/executor/multi_agent.py
from pydantic_ai import Agent, RunContext

class MultiAgentOrchestrator:
    def __init__(self, executor: SkillExecutor):
        self.executor = executor

    async def execute_workflow(self, workflow_id: str, context: dict):
        """Execute multi-agent workflow"""
        workflow = self._load_workflow(workflow_id)

        results = []
        current_context = context.copy()

        for step in workflow['steps']:
            # Execute skill
            result = await self.executor.execute(
                step['skill'],
                current_context
            )

            results.append(result)

            # Check transition condition
            if self._should_transition(step, result):
                # Inject previous result into next step's context
                current_context[f"{step['name']}_output"] = result['output']
                continue
            else:
                # Workflow complete or blocked
                break

        return {
            "workflow": workflow_id,
            "steps_completed": len(results),
            "results": results
        }
```

```yaml
# workflows/ecm-refund-approval.yaml
workflow:
  name: ecm-refund-approval
  description: Field agent requests refund → Manager approves
  trigger: "approve refund for ticket {ticket_id}"

steps:
  - name: validate_ticket
    skill: ecm/field/ticket-details
    context: [user_id, ticket_id]
    outputs: [refund_amount, customer_name, reason]

  - name: manager_review
    skill: ecm/manager/approve-refund
    context: [manager_id, ticket_id, refund_amount, reason]
    transition_if: refund_amount <= 2000

  - name: vp_escalation
    skill: ecm/vp/approve-large-refund
    context: [vp_id, ticket_id, refund_amount, manager_review_output]
    transition_if: refund_amount > 2000
```

**Person B (Workflow Skills)**:
```markdown
# domains/ecm/skills/field/ticket-details.md
# Returns ticket information for workflow handoff
```

**Person C (Channels - Workflow Trigger)**:
```typescript
// Slack command: /refund-approval {ticket_id}
app.command('/refund-approval', async ({ command, ack, say }) => {
  await ack();

  const user = await getAsporaUser(command.user_id);
  const ticketId = command.text;

  // Execute multi-agent workflow
  const result = await orchestrator.execute_workflow(
    'ecm-refund-approval',
    { user_id: user.id, ticket_id: ticketId }
  );

  // Show workflow progress
  await say({
    text: `Refund workflow initiated for ticket ${ticketId}`,
    blocks: result.results.map(step => ({
      type: 'section',
      text: { type: 'mrkdwn', text: `✅ ${step.skill}\n${step.output}` }
    }))
  });
});
```

**Person E (Workflow Testing)**:
```python
# Test multi-step workflow execution
def test_refund_workflow_manager_approval():
    """Test refund <= $2000 goes to manager only"""
    result = await orchestrator.execute_workflow(
        'ecm-refund-approval',
        {
            'user_id': 'sarah@aspora.com',
            'ticket_id': 'T1234',
            'manager_id': 'john@aspora.com'
        }
    )

    assert result['steps_completed'] == 2  # validate + manager review
    assert 'vp_escalation' not in [r['skill'] for r in result['results']]
```

---

### Hour 12-18: Domain 2 & 3 (FinCrime + Fraud Guardian)

**Person B (All FinCrime Skills)**:

```yaml
# domains/fincrime/aspora.config.yaml
domain:
  name: fincrime
  description: FinCrime Alert Investigation
  scope: team
  data_isolation: team_id
  audit_required: true

skills:
  - name: investigate-alert
    path: skills/investigate-alert.md
    requires_context: [user_id, team_id, alert_id]
    model: anthropic/claude-sonnet-4.5  # Complex analysis
    avg_cost_usd: 0.08
```

```markdown
# domains/fincrime/skills/investigate-alert.md
---
name: investigate-alert
description: Investigate FinCrime alert with transaction analysis
---

# Investigate Alert Skill

> You help analysts investigate FinCrime alerts by analyzing transaction patterns.

## Input Context
- `user_id`: Analyst investigating
- `team_id`: FinCrime team
- `alert_id`: Alert identifier

## Data Source
```sql
SELECT a.*, t.amount, t.currency, t.sender, t.receiver, t.timestamp
FROM fincrime_alerts a
JOIN transactions t ON a.transaction_id = t.id
WHERE a.alert_id = {alert_id} AND a.team_id = {team_id}
```

## Analysis Steps
1. Fetch alert details (type, risk score, trigger reason)
2. Analyze transaction pattern:
   - Multiple same-amount transactions (structuring)
   - Cross-border velocity spike
   - Sanctioned entity match
3. Fetch customer history (past 90 days)
4. Recommend disposition (APPROVE, REJECT, ESCALATE)

## Output Format
```
🚨 Alert #{alert_id} Investigation

Transaction:
- Amount: {amount} {currency}
- Sender: {sender}
- Receiver: {receiver}
- Timestamp: {timestamp}

Risk Indicators:
⚠️ {indicator1}: {description}
⚠️ {indicator2}: {description}

Customer History (90 days):
- Total txns: {count}
- Avg amount: {avg}
- Sanctions hits: {sanctions_count}

💡 Recommendation: {APPROVE/REJECT/ESCALATE}
Rationale: {rationale}

Next Steps:
[ ] Verify sender identity
[ ] Check sanctions list manually
[ ] Document decision in core system
```

## Guardrails
- LOG every investigation for audit
- VERIFY analyst has fincrime team access
- NEVER auto-approve > $10K transactions
```

**Person B (Fraud Guardian Skills)**:

```yaml
# domains/fraud-guardian/aspora.config.yaml
domain:
  name: fraud-guardian
  description: Fraud Rule Simulation and Analysis
  scope: analyst
  data_isolation: analyst_id

skills:
  - name: simulate-rule-change
    path: skills/simulate-rule-change.md
    requires_context: [user_id, rule_id, change_params]
    model: anthropic/claude-sonnet-4.5
    avg_cost_usd: 0.12  # Heavy compute
```

```markdown
# domains/fraud-guardian/skills/simulate-rule-change.md
---
name: simulate-rule-change
description: Simulate fraud rule change impact
---

# Simulate Rule Change Skill

> You help risk analysts simulate fraud rule changes and predict impact.

## Input Context
- `user_id`: Analyst running simulation
- `rule_id`: Rule to modify
- `change_params`: JSON of parameter changes

## Logic
1. Load current rule configuration
2. Apply proposed changes (threshold, velocity window, scoring)
3. Run simulation on historical data (last 30 days)
4. Calculate:
   - False positive rate change
   - False negative rate change
   - Transaction decline impact
   - Fraud catch rate

## Output Format
```
🧪 Rule Simulation: {rule_name}

Current Configuration:
- Threshold: {current_threshold}
- Velocity Window: {current_window}

Proposed Changes:
- Threshold: {current} → {proposed}

Simulation Results (30-day backtest):

Impact Summary:
- Declined Txns: {current_declines} → {new_declines} ({change}%)
- False Positives: {current_fp} → {new_fp} ({fp_rate}%)
- Fraud Caught: {current_fraud} → {new_fraud} ({catch_rate}%)

Risk Assessment:
{SAFE/CAUTION/HIGH_RISK}

💡 Recommendation:
{approve_change / reject_change / test_in_shadow_mode}

Rationale: {reasoning}
```

## Guardrails
- ALWAYS run on at least 10K transactions
- WARN if false positive rate > 5%
- REQUIRE shadow mode if high risk
```

**Person C (Channels - Add FinCrime/Fraud Routes)**:
```typescript
// FinCrime routing
app.message(/investigate alert (\d+)/, async ({ message, context, say }) => {
  const user = await getAsporaUser(message.user);
  const alertId = context.matches[1];

  // Verify user in fincrime team
  if (user.team_id !== 'fincrime') {
    await say('⛔ FinCrime access restricted to compliance team');
    return;
  }

  const result = await executor.execute('fincrime/investigate-alert', {
    user_id: user.id,
    team_id: user.team_id,
    alert_id: alertId
  });

  await say(result.output);
});

// Fraud Guardian routing
app.message(/simulate rule (.+)/, async ({ message, context, say }) => {
  // Parse rule change params from message
  // Execute simulation skill
});
```

**Person E (Testing - FinCrime/Fraud)**:
```python
# Test FinCrime investigation accuracy
def test_fincrime_alert_investigation():
    test_case = LLMTestCase(
        input="Investigate alert with multiple same-amount transactions",
        actual_output=result['output'],
        context=["Alert #5678: 5 transactions of $9,999 to same receiver"]
    )

    # Should identify structuring pattern
    faithfulness = FaithfulnessMetric(threshold=0.8)
    assert_test(test_case, [faithfulness])

# Test Fraud simulation accuracy
def test_fraud_rule_simulation():
    # Verify math is correct (false positive rate calculation)
    assert result['output'] contains "False Positives: 120 → 85 (29% reduction)"
```

---

### Hour 18-24: Auto-Learning & Correction Tracking

**The Moat**: When users correct agent responses, system auto-generates test cases.

**Person A (Correction Tracking)**:

```python
# packages/executor/learning.py
class LearningEngine:
    async def track_correction(self, execution_id: str, correction: dict):
        """User corrected agent output → generate test case"""

        # Fetch original execution
        execution = await self.db.get_execution(execution_id)

        # Store correction
        await self.db.insert_correction({
            'execution_id': execution_id,
            'skill_id': execution['skill_id'],
            'original_output': execution['output'],
            'corrected_output': correction['user_correction'],
            'correction_type': correction['type'],  # 'factual_error', 'format_issue', 'missing_data'
            'timestamp': datetime.now()
        })

        # Generate DeepEval test case
        test_case = self._generate_test_case(execution, correction)

        # Auto-commit to tests/
        await self._write_test_file(
            f"tests/corrections/test_{execution['skill_id'].replace('/', '_')}_{execution_id}.py",
            test_case
        )

        return {
            'correction_id': correction_id,
            'test_case_generated': True,
            'test_file': test_file_path
        }

    def _generate_test_case(self, execution, correction):
        """Generate DeepEval test from correction"""
        return f"""
# Auto-generated from correction on {datetime.now()}
# Original execution: {execution['execution_id']}

from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

def test_correction_{execution['execution_id']}():
    '''
    User corrected: {correction['correction_type']}
    Original: {execution['output'][:100]}...
    Expected: {correction['user_correction'][:100]}...
    '''

    test_case = LLMTestCase(
        input=\"\"\"{execution['input']}\"\"\",
        actual_output=\"\"\"{execution['output']}\"\"\",
        expected_output=\"\"\"{correction['user_correction']}\"\"\"
    )

    # Metric based on correction type
    metric = AnswerRelevancyMetric(threshold=0.8)

    assert_test(test_case, [metric])
"""
```

**Person C (Slack Correction UI)**:
```typescript
// Add "Report Issue" button to all skill responses
app.action('report_issue', async ({ ack, body, client }) => {
  await ack();

  // Show modal for correction
  await client.views.open({
    trigger_id: body.trigger_id,
    view: {
      type: 'modal',
      title: { type: 'plain_text', text: 'Report Issue' },
      blocks: [
        {
          type: 'input',
          block_id: 'correction',
          label: { type: 'plain_text', text: 'What was wrong?' },
          element: { type: 'plain_text_input', multiline: true }
        },
        {
          type: 'input',
          block_id: 'correction_type',
          label: { type: 'plain_text', text: 'Issue type' },
          element: {
            type: 'static_select',
            options: [
              { text: { type: 'plain_text', text: 'Wrong data' }, value: 'factual_error' },
              { text: { type: 'plain_text', text: 'Bad format' }, value: 'format_issue' },
              { text: { type: 'plain_text', text: 'Missing info' }, value: 'missing_data' }
            ]
          }
        }
      ],
      submit: { type: 'plain_text', text: 'Submit' }
    }
  });
});

// Handle correction submission
app.view('correction_modal', async ({ ack, body, view }) => {
  await ack();

  const executionId = body.view.private_metadata;
  const correction = view.state.values.correction.value;
  const correctionType = view.state.values.correction_type.selected_option.value;

  // Track correction
  await learningEngine.track_correction(executionId, {
    user_correction: correction,
    type: correctionType
  });

  // Notify user
  await say('✅ Thank you! Test case generated to prevent this in the future.');
});
```

**Person E (Testing - Correction Flow)**:
```python
# Test correction tracking
def test_correction_generates_test_case():
    """When user corrects output, test case is auto-generated"""

    # Simulate execution
    execution_id = 'exec_123'

    # User corrects
    result = await learning_engine.track_correction(execution_id, {
        'user_correction': 'Ticket #1234 is HIGH priority, not NORMAL',
        'type': 'factual_error'
    })

    # Verify test case created
    assert result['test_case_generated'] == True
    assert os.path.exists(result['test_file'])

    # Verify test case content
    test_content = open(result['test_file']).read()
    assert 'HIGH priority' in test_content
```

---

### Hour 24-30: Dashboard + Cost Tracking

**Person D (Observability Dashboard)**:

```python
# packages/observability/dashboard.py
from fastapi import FastAPI
from prometheus_client import generate_latest

app = FastAPI()

@app.get('/metrics')
async def metrics():
    """Prometheus scrape endpoint"""
    return Response(generate_latest(), media_type='text/plain')

@app.get('/dashboard')
async def dashboard():
    """Real-time cost/latency dashboard"""

    # Query metrics from Prometheus
    skills = await db.query("""
        SELECT
            skill_id,
            COUNT(*) as executions,
            AVG(cost_usd) as avg_cost,
            AVG(latency_ms) as avg_latency,
            SUM(cost_usd) as total_cost
        FROM skill_executions
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        GROUP BY skill_id
        ORDER BY total_cost DESC
    """)

    return {
        'skills': skills,
        'total_cost_1h': sum(s['total_cost'] for s in skills),
        'total_executions_1h': sum(s['executions'] for s in skills)
    }
```

```html
<!-- Simple dashboard UI -->
<!DOCTYPE html>
<html>
<head><title>Aspora Platform Dashboard</title></head>
<body>
  <h1>Skills Executor Dashboard</h1>

  <div id="cost-summary">
    <h2>Cost (Last 1 Hour)</h2>
    <p>Total: $<span id="total-cost">0.00</span></p>
    <p>Executions: <span id="total-executions">0</span></p>
  </div>

  <table id="skills-table">
    <thead>
      <tr>
        <th>Skill</th>
        <th>Executions</th>
        <th>Avg Cost</th>
        <th>Avg Latency</th>
        <th>Total Cost</th>
      </tr>
    </thead>
    <tbody id="skills-body"></tbody>
  </table>

  <script>
    setInterval(async () => {
      const data = await fetch('/dashboard').then(r => r.json());
      document.getElementById('total-cost').textContent = data.total_cost_1h.toFixed(4);
      document.getElementById('total-executions').textContent = data.total_executions_1h;

      const tbody = document.getElementById('skills-body');
      tbody.innerHTML = data.skills.map(s => `
        <tr>
          <td>${s.skill_id}</td>
          <td>${s.executions}</td>
          <td>$${s.avg_cost.toFixed(4)}</td>
          <td>${s.avg_latency.toFixed(1)}ms</td>
          <td>$${s.total_cost.toFixed(4)}</td>
        </tr>
      `).join('');
    }, 5000);  // Refresh every 5s
  </script>
</body>
</html>
```

**Person D (Cost Comparison)**:

```python
# Show cost comparison: Aspora vs manual operations
def calculate_cost_comparison():
    """
    Manual operations: $50/hour analyst wage × 100 tickets/day = $6.25/ticket
    Aspora: $0.08 average per skill execution

    Savings: 98.7% cost reduction
    """

    manual_cost_per_ticket = 50 / 8  # $50/hour wage, 8 tickets/hour
    aspora_cost_per_ticket = 0.08  # Average skill cost

    savings_pct = (manual_cost_per_ticket - aspora_cost_per_ticket) / manual_cost_per_ticket * 100

    return {
        'manual_cost': manual_cost_per_ticket,
        'aspora_cost': aspora_cost_per_ticket,
        'savings_pct': savings_pct
    }
```

---

### Hour 30-33: Demo Data & Polish

**Person B (Demo Data Creation)**:

```python
# scripts/seed_demo_data.py
import pandas as pd
import random
from datetime import datetime, timedelta

# Generate realistic ECM tickets
def generate_ecm_tickets():
    tickets = []
    for i in range(50):
        tickets.append({
            'ticket_id': f'T{1000 + i}',
            'title': random.choice([
                'Stuck shipment in customs',
                'Payment failure - beneficiary mismatch',
                'Package damaged in transit',
                'Delivery delay > 48 hours',
                'Customer refund request'
            ]),
            'status': random.choice(['pending', 'in_progress', 'pending']),
            'priority': random.choice(['high', 'normal', 'normal', 'normal']),
            'assigned_to': random.choice(['sarah@aspora.com', 'john@aspora.com']),
            'team_id': 'operations',
            'created_at': datetime.now() - timedelta(days=random.randint(0, 30)),
            'due_date': datetime.now() + timedelta(days=random.randint(1, 7))
        })

    df = pd.DataFrame(tickets)
    df.to_csv('data/ecm_tickets.csv', index=False)

# Generate FinCrime alerts
def generate_fincrime_alerts():
    alerts = []
    for i in range(30):
        alerts.append({
            'alert_id': f'A{5000 + i}',
            'alert_type': random.choice([
                'Multiple same-amount transactions',
                'Cross-border velocity spike',
                'Sanctioned entity match',
                'Unusual transaction pattern'
            ]),
            'risk_score': random.randint(60, 95),
            'transaction_id': f'TXN{random.randint(10000, 99999)}',
            'amount': random.choice([9999, 9998, 9997, 15000, 25000]),
            'currency': 'USD',
            'status': 'pending',
            'team_id': 'fincrime',
            'created_at': datetime.now() - timedelta(hours=random.randint(1, 72))
        })

    df = pd.DataFrame(alerts)
    df.to_csv('data/fincrime_alerts.csv', index=False)

# Generate fraud rules
def generate_fraud_rules():
    rules = [
        {
            'rule_id': 'R001',
            'rule_name': 'Velocity Check - Same Card',
            'threshold': 5,
            'velocity_window_minutes': 60,
            'current_fp_rate': 0.12,
            'fraud_catch_rate': 0.78
        },
        {
            'rule_id': 'R002',
            'rule_name': 'Geographic Mismatch',
            'threshold': 500,  # miles
            'velocity_window_minutes': 30,
            'current_fp_rate': 0.08,
            'fraud_catch_rate': 0.65
        }
    ]

    df = pd.DataFrame(rules)
    df.to_csv('data/fraud_rules.csv', index=False)

if __name__ == '__main__':
    generate_ecm_tickets()
    generate_fincrime_alerts()
    generate_fraud_rules()
```

**Person C (Slack Bot Polish)**:
- Add welcome message when bot joins channel
- Add help command (list available skills)
- Add typing indicator while executing skill
- Error handling with user-friendly messages

**Person E (Final Testing)**:
- Run full DeepEval test suite
- Verify all corrections generate test cases
- Load test (10 concurrent users)
- Measure end-to-end latency

---

### Hour 33-36: Rehearsal & Video

**Everyone: Demo Rehearsal (3 rounds)**

**Demo Script (3 minutes)**:

```
Act 1 (45s): "The Problem"
  [Show current workflow: Excel, Salesforce, Email tabs open]
  "ECM field agents juggle 10 tools. FinCrime analysts spend hours on manual investigations.
   Knowledge locked in expert heads. New hires take months to ramp."

Act 2 (90s): "The Solution - Multi-Domain Agent Platform"

  [Slack: Sarah (ECM field agent)]
  Sarah: "show my tickets"
  Bot: 📋 Your Tickets (5 pending)
       #1234 Stuck shipment (Dubai → Mumbai)
       #1235 Payment failure...

  Sarah: "approve refund for ticket 1235"
  Bot: ✅ Refund Approved: $450
       [Shows policy check, next steps]
       Cost: $0.05 | 1.2s

  [Switch to Raj (FinCrime analyst)]
  Raj: "investigate alert 5678"
  Bot: 🚨 Alert #5678 Investigation
       Transaction: $9,999 USD
       Risk: Multiple same-amount txns (structuring)
       💡 Recommendation: ESCALATE
       Rationale: Pattern matches layering behavior
       Cost: $0.08 | 2.1s

  [Switch to Risk Team]
  Analyst: "simulate rule R001 threshold 3"
  Bot: 🧪 Rule Simulation
       Declined Txns: 1,200 → 1,850 (+54%)
       False Positives: 120 → 85 (-29%)
       Fraud Caught: 780 → 920 (+18%)
       💡 Recommendation: APPROVE CHANGE
       Cost: $0.12 | 3.4s

  "Three domains. One platform. Context injection handles multi-tenancy."

Act 3 (45s): "The Moat - Auto-Learning"

  [Show correction flow]
  Sarah: "show my tickets"
  Bot: [shows output]
  Sarah: [clicks "Report Issue" button]
       "Ticket #1234 is HIGH priority, not NORMAL"
  Bot: ✅ Thank you! Test case generated.

  [Show generated test file]
  tests/corrections/test_ecm_field_my_tickets_exec123.py

  "User correction → Auto-generates test case → Platform improves itself.
   Feedback loop is the moat."

Act 4 (30s): "The Economics"

  [Show dashboard]
  Last 1 Hour:
  - 47 skill executions
  - Total cost: $2.34
  - Avg latency: 1.8s

  Manual Operations:
  - 47 tickets × $6.25/ticket = $293.75
  - Aspora: $2.34
  - Savings: 99.2%

  "From $50/hour analyst to $0.05/query.
   Production-grade. Multi-domain. Self-improving."

[End: Show repo, invite judges to test in Slack]
```

**Person A**: Record video (screencast)
**Person B**: Prep backup demo (if Slack breaks, show CLI)
**Person C**: Write pitch deck (problem, solution, moat, economics)
**Person D**: Prep cost analysis spreadsheet
**Person E**: Document test coverage metrics

---

## Success Metrics

### Minimum Viable Demo (Must Have)
- ✅ 3 domains onboarded (ECM, FinCrime, Fraud)
- ✅ 10+ skills working (4 ECM, 3 FinCrime, 3 Fraud)
- ✅ Slack bot with context injection
- ✅ Multi-agent workflow (field → manager)
- ✅ Cost tracking dashboard

### Stretch Goals (Nice to Have)
- 🎯 Auto-learning (correction → test case)
- 🎯 WhatsApp channel (in addition to Slack)
- 🎯 Wealth domain (4th domain, portfolio check)
- 🎯 Real-time dashboard UI

### Gold Standard (Wow Factor)
- 🏆 Live demo with judges using platform
- 🏆 Correction flow working (judge reports issue, test generated)
- 🏆 Cost comparison resonates (99% savings)
- 🏆 Someone says "When can I use this?"

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Slack API failures during demo | MEDIUM | HIGH | Pre-record video, have CLI backup |
| OpenRouter rate limits | LOW | MEDIUM | Pre-load $50 credits, test limits |
| Context injection bugs (wrong user data) | MEDIUM | CRITICAL | Unit test all multi-tenancy paths |
| Multi-agent workflow doesn't complete | MEDIUM | HIGH | Test workflows extensively, fallback to single-agent |
| Auto-learning too complex | HIGH | LOW | Make it stretch goal, not MVP |
| Team exhaustion | HIGH | MEDIUM | Schedule sleep hours 18-24, 30-33 |

---

## Why You'll Win

### Technical Excellence
- ✅ Production-grade architecture (not hacky prototype)
- ✅ Real observability (OpenTelemetry, Prometheus)
- ✅ LLM-specific testing (DeepEval, Promptfoo)
- ✅ Multi-tenancy done right (context injection, RBAC)

### Business Impact
- ✅ 99% cost reduction (compelling economics)
- ✅ Multi-domain (shows platform versatility)
- ✅ Real use cases (ECM, FinCrime relatable to judges)

### Differentiator
- ✅ Auto-learning moat (correction → test case)
- ✅ Feedback loop (platform improves itself)
- ✅ Not just another chatbot (structured workflows, team collaboration)

### Demo Polish
- ✅ 3-minute demo (fits attention span)
- ✅ Live interaction (judges can try it)
- ✅ Economic proof (dashboard with real numbers)

---

## Files to Create

```
aspora-platform/
├── packages/
│   ├── executor/
│   │   ├── skill_executor.py (200 lines)
│   │   ├── domain_registry.py (150 lines)
│   │   ├── multi_agent.py (180 lines)
│   │   └── learning.py (220 lines)
│   └── observability/
│       ├── metrics.py (100 lines)
│       └── dashboard.py (150 lines)
├── domains/
│   ├── ecm/
│   │   ├── aspora.config.yaml (50 lines)
│   │   └── skills/ (4 files × 80 lines = 320 lines)
│   ├── fincrime/
│   │   ├── aspora.config.yaml (40 lines)
│   │   └── skills/ (3 files × 100 lines = 300 lines)
│   └── fraud-guardian/
│       ├── aspora.config.yaml (40 lines)
│       └── skills/ (3 files × 120 lines = 360 lines)
├── channels/
│   ├── slack/
│   │   └── bot.ts (400 lines)
│   └── whatsapp/
│       └── webhook.py (200 lines, STRETCH)
├── workflows/
│   └── ecm-refund-approval.yaml (30 lines)
├── tests/
│   ├── skills/ (10 tests × 30 lines = 300 lines)
│   └── corrections/ (auto-generated)
├── scripts/
│   └── seed_demo_data.py (150 lines)
├── data/
│   ├── ecm_tickets.csv
│   ├── fincrime_alerts.csv
│   └── fraud_rules.csv
└── docker-compose.yml (database, bot, dashboard)

Total: ~3,000 lines of code
```

---

## Resources Needed

- **OpenRouter API key** ($50 credits)
- **Slack workspace** (free tier, create demo workspace)
- **PostgreSQL** (Docker container)
- **Prometheus + Grafana** (Docker containers, optional)
- **DeepEval license** (open source, free)
- **GitHub repo** (for demo + judges to clone)

---

## Post-Hackathon Path

If you win or want to continue:

### Week 1-2: Production Hardening
- Add authentication (API keys per domain)
- Rate limiting per user
- Database connection pooling
- Error recovery (retry logic)

### Week 3-4: Scale Testing
- Load test with 100 concurrent users
- Optimize slow skills (caching)
- Add Redis for session state

### Month 2: Compliance
- Audit logging for FinCrime (regulatory requirement)
- Encryption at rest (PII in tickets)
- RBAC with fine-grained permissions

### Month 3: Monetization
- Usage-based pricing ($0.10/skill execution)
- Enterprise tier (custom domains, SSO)
- Partner with ECM/FinCrime vendors

---

## Final Checklist

**Before You Start**:
- [ ] OpenRouter API key funded ($50)
- [ ] Slack workspace created
- [ ] GitHub repo initialized
- [ ] Team roles assigned
- [ ] Development environments ready (Python 3.11, Node 18, Docker)

**Hour 18 Checkpoint**:
- [ ] SkillExecutor executes at least 1 skill
- [ ] Slack bot responds to 1 command
- [ ] ECM domain with 2 skills working
- [ ] Metrics collecting (cost, latency)

**Hour 30 Checkpoint**:
- [ ] All 3 domains working (ECM, FinCrime, Fraud)
- [ ] 10+ skills executable
- [ ] Multi-agent workflow tested
- [ ] Demo data loaded
- [ ] Dashboard showing costs

**Hour 36 - Go Time**:
- [ ] Video recorded (backup)
- [ ] Live demo rehearsed 3x
- [ ] Judges can access Slack workspace
- [ ] Pitch deck ready
- [ ] Team rested and confident

---

**TL;DR**: Build a production-grade multi-domain agent platform in 36 hours. Three domains (ECM, FinCrime, Fraud Guardian), 10+ skills, Slack bot, multi-agent workflows, auto-learning from corrections, real-time cost tracking. Win with technical excellence + compelling economics (99% cost reduction) + unique moat (feedback loop).
