# Multi-Tenancy Architecture: Mixed Domain Scopes

**Question**: How can wealth (personal finance) coexist with operations domains (ECM, FinCrime) on the same platform? Do we deploy one agent per user like OpenClaw?

**Answer**: Shared agent runtime with context-based data scoping. One platform executor, multiple domain scope types.

---

## The Problem

The Aspora platform has 4 domains with fundamentally different data scoping requirements:

| Domain | Scope | Example Request | Who Can Access |
|--------|-------|-----------------|----------------|
| **Wealth** | User-scoped | "check my portfolio" | Only the requesting user |
| **ECM Operations** | Team-scoped | "show pending tickets" | All users in operations team |
| **FinCrime Alerts** | Team-scoped | "investigate alert #1234" | All FinCrime analysts |
| **Fraud Guardian** | Analyst-scoped | "simulate this rule" | Analyst who ran simulation |

OpenClaw's model (one agent instance per user) works for personal use cases but breaks for team collaboration.

---

## Decision: Hybrid Scoping Model

### DEC-013: Context-Injected Multi-Tenancy Over Per-User Agent Instances

**Chose**: Shared agent runtime with domain-declared scope and context injection
**Over**: One agent instance per user (OpenClaw pattern)

**Why**:
- Operations domains (ECM, FinCrime) are team-shared — multiple users collaborate on same tickets/alerts
- Wealth domain is user-private — portfolio data isolated per individual
- Same platform executor can handle both by injecting different context
- Resource efficient (one runtime vs N user instances)

**Constraint**: Every skill execution MUST declare required context fields. Platform enforces context presence before execution.

---

## How It Works

### 1. Domain Scope Declaration

Each domain declares its scoping model in `aspora.config.yaml`:

```yaml
# domains/wealth/aspora.config.yaml
domain:
  name: wealth
  description: Personal wealth management
  scope: user  # Data is scoped per user
  data_isolation: strict  # Enforce user_id in all data access
  owner: wealth-team

skills:
  - name: portfolio-check
    path: skills/portfolio-check.md
    requires_context: [user_id]  # Platform validates user_id exists before execution
    model: anthropic/claude-haiku-4.5
```

```yaml
# domains/ecm/aspora.config.yaml
domain:
  name: ecm
  description: ECM Operations
  scope: team  # Data is shared across team members
  data_isolation: team_id  # Filter by team
  owner: operations-team

skills:
  - name: my-tickets
    path: skills/field/my-tickets.md
    requires_context: [user_id, team_id]  # Both user and team context
    model: anthropic/claude-haiku-4.5
```

```yaml
# domains/fincrime/aspora.config.yaml
domain:
  name: fincrime
  description: FinCrime Alert Investigation
  scope: team  # Shared queue
  data_isolation: team_id
  owner: compliance-team

skills:
  - name: investigate-alert
    path: skills/investigate-alert.md
    requires_context: [user_id, team_id, alert_id]  # User for audit, team for access control
    model: anthropic/claude-sonnet-4.5
```

### 2. Request Routing with Context Injection

Platform identifies user from channel (Slack, WhatsApp, etc.) and injects context:

```python
class SkillExecutor:
    def __init__(self, registry_path: str, openrouter_key: str):
        self.registry = self._load_registry(registry_path)
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )

    async def execute(self, skill_id: str, context: dict) -> dict:
        """
        Execute a skill with context injection and validation.

        Context contains:
        - user_id: Requesting user (for all skills)
        - team_id: User's team (for team-scoped skills)
        - Additional skill-specific params
        """
        skill = self.registry[skill_id]
        domain = self.registry.get_domain(skill['domain'])

        # VALIDATE REQUIRED CONTEXT
        required = skill.get('requires_context', [])
        missing = [r for r in required if r not in context]
        if missing:
            raise ValueError(f"Missing required context: {missing}")

        # ENFORCE DATA ISOLATION
        scope = domain.get('scope')
        if scope == 'user' and context.get('user_id') != context.get('requesting_user_id'):
            raise PermissionError("Cannot access another user's data in user-scoped domain")

        # INJECT CONTEXT INTO SKILL PROMPT
        skill_prompt = self._build_prompt(skill, context)

        # EXECUTE
        model = skill.get('model', 'anthropic/claude-haiku-4.5')
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": skill_prompt}],
            extra_headers={"HTTP-Referer": "https://aspora.ai", "X-Title": "Aspora Platform"}
        )

        # LOG FOR AUDIT (critical for FinCrime domain)
        await self._log_execution(
            skill_id=skill_id,
            user_id=context['user_id'],
            team_id=context.get('team_id'),
            timestamp=datetime.now(),
            cost=self._calculate_cost(response),
            output=response.choices[0].message.content
        )

        return {
            "skill": skill_id,
            "output": response.choices[0].message.content,
            "cost": self._calculate_cost(response),
            "latency": response.elapsed,
            "user_id": context['user_id']  # Return for traceability
        }
```

### 3. Slack Bot Integration Example

```python
# Slack adapter automatically injects user context
@app.message(/check portfolio|portfolio status/)
async def handle_wealth_request(message, say):
    # EXTRACT USER IDENTITY from Slack
    slack_user_id = message['user']
    user = await user_db.get_by_slack_id(slack_user_id)

    # EXECUTE WITH USER CONTEXT
    result = await executor.execute(
        skill_id="wealth/portfolio-check",
        context={
            "user_id": user.id,  # Maps Slack user to Aspora user
            "requesting_user_id": user.id,  # For permission check
            "currency_preference": user.preferences.get('currency', 'INR')
        }
    )

    await say({
        "text": result['output'],
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": result['output']}},
            {"type": "context", "elements": [
                {"type": "mrkdwn", "text": f"💰 Cost: ${result['cost']:.4f} | ⚡ {result['latency']:.2f}s"}
            ]}
        ]
    })

@app.message(/show pending tickets|my tickets/)
async def handle_ecm_request(message, say):
    slack_user_id = message['user']
    user = await user_db.get_by_slack_id(slack_user_id)

    # EXECUTE WITH USER + TEAM CONTEXT
    result = await executor.execute(
        skill_id="ecm/field/my-tickets",
        context={
            "user_id": user.id,
            "team_id": user.team_id,  # User's team determines data access
            "requesting_user_id": user.id
        }
    )

    await say(result['output'])

@app.message(/investigate alert (\d+)/)
async def handle_fincrime_request(message, context, say):
    slack_user_id = message['user']
    user = await user_db.get_by_slack_id(slack_user_id)
    alert_id = context['matches'][1]

    # VALIDATE: User is in FinCrime team
    if user.team_id != 'fincrime-team':
        await say("⛔ You don't have access to FinCrime alerts.")
        return

    # EXECUTE WITH TEAM CONTEXT
    result = await executor.execute(
        skill_id="fincrime/investigate-alert",
        context={
            "user_id": user.id,  # For audit trail
            "team_id": user.team_id,
            "requesting_user_id": user.id,
            "alert_id": alert_id
        }
    )

    await say(result['output'])
```

---

## Data Isolation Patterns

### User-Scoped (Wealth Domain)

```python
# skills/portfolio-check.md execution
# Context: {"user_id": "sarah@aspora.com", "currency": "INR"}

# Data access pattern
portfolio_data = pd.read_csv(f"data/portfolios/{user_id}.csv")
# OR in database
portfolio = db.query("SELECT * FROM portfolios WHERE user_id = ?", user_id)

# GUARDRAIL: Skill CANNOT access other users' data
# Platform enforces requesting_user_id == user_id for user-scoped domains
```

### Team-Scoped (ECM Domain)

```python
# skills/field/my-tickets.md execution
# Context: {"user_id": "sarah@aspora.com", "team_id": "operations"}

# Data access pattern
my_tickets = db.query("""
    SELECT * FROM ecm_tickets
    WHERE assigned_to = ?
    AND team_id = ?
    AND status != 'closed'
""", user_id, team_id)

# Team members can see shared queue
shared_queue = db.query("""
    SELECT * FROM ecm_tickets
    WHERE team_id = ?
    AND status = 'pending'
""", team_id)
```

### Team-Scoped with Audit (FinCrime Domain)

```python
# skills/investigate-alert.md execution
# Context: {"user_id": "analyst@aspora.com", "team_id": "fincrime", "alert_id": "12345"}

# Data access
alert = db.query("SELECT * FROM fincrime_master WHERE alert_id = ? AND team_id = ?", alert_id, team_id)

# CRITICAL: Log every access for regulatory compliance
audit_log.insert({
    "timestamp": datetime.now(),
    "user_id": user_id,
    "team_id": team_id,
    "action": "alert_view",
    "alert_id": alert_id,
    "ip_address": request.ip
})

# Investigation work
disposition = analyze_alert(alert)

# Log disposition decision
audit_log.insert({
    "timestamp": datetime.now(),
    "user_id": user_id,
    "action": "alert_disposition",
    "alert_id": alert_id,
    "disposition": disposition,
    "rationale": rationale
})
```

---

## User Database Schema

To map channel identities (Slack, WhatsApp) to Aspora users:

```sql
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,  -- sarah@aspora.com
    name VARCHAR(255),
    team_id VARCHAR(255),  -- operations, fincrime, analyst
    role VARCHAR(50),  -- manager, field, analyst
    created_at TIMESTAMP,
    preferences JSONB  -- {"currency": "INR", "timezone": "Asia/Kolkata"}
);

CREATE TABLE user_identities (
    user_id VARCHAR(255) REFERENCES users(id),
    channel VARCHAR(50),  -- slack, whatsapp, telegram
    channel_user_id VARCHAR(255),  -- Slack user ID, WhatsApp number
    PRIMARY KEY (channel, channel_user_id)
);

-- Example data
INSERT INTO users VALUES
    ('sarah@aspora.com', 'Sarah', 'operations', 'field', NOW(), '{"currency": "INR"}'),
    ('raj@aspora.com', 'Raj', 'fincrime', 'analyst', NOW(), '{"currency": "INR"}'),
    ('priya@aspora.com', 'Priya', NULL, 'retail_user', NOW(), '{"currency": "INR"}');

INSERT INTO user_identities VALUES
    ('sarah@aspora.com', 'slack', 'U12345ABC'),
    ('raj@aspora.com', 'slack', 'U67890DEF'),
    ('priya@aspora.com', 'whatsapp', '+919876543210');
```

---

## Demo Flow: Multi-Domain Platform

```
SLACK CHANNEL: #operations
Sarah: "show my pending tickets"
Bot: [Executes ecm/field/my-tickets with context={user_id: sarah@aspora.com, team_id: operations}]
📋 Your Tickets (5 pending)
- #1234 Stuck shipment (Dubai → Mumbai)
- #1235 Payment failure (beneficiary mismatch)
...

Sarah: "check my portfolio"
Bot: [Executes wealth/portfolio-check with context={user_id: sarah@aspora.com}]
📊 Your Portfolio (₹15,45,000)
- RELIANCE.NS (12.3%) — ₹1,89,950
- Bitcoin (8.5%) — $1,572
🎯 House in Mumbai: 45% (₹22L / ₹50L)
⚠️ Risk: Green

---

SLACK CHANNEL: #fincrime
Raj: "show alerts pending"
Bot: [Executes fincrime/show-alerts with context={user_id: raj@aspora.com, team_id: fincrime}]
🚨 FinCrime Queue (12 alerts)
- Alert #5678 (CRITICAL) - Multiple same-amount txns
- Alert #5679 (WARNING) - Cross-border velocity spike
...

Raj: "check my portfolio"
Bot: ⛔ You don't have access to Wealth domain. Contact admin to enable.

---

WHATSAPP: Priya (retail user, NOT part of any operations team)
Priya: "check my portfolio"
Bot: [Executes wealth/portfolio-check with context={user_id: priya@aspora.com}]
📊 Your Portfolio (₹8,50,000)
...

Priya: "show pending tickets"
Bot: ⛔ ECM domain is for operations team only. You have access to Wealth domain.
```

---

## Hackathon Implementation Strategy

### Hour 18-20: Multi-Tenancy Setup

**Person C** (Platform track):

1. **Extend aspora.config.yaml schema** to support `scope` and `requires_context`:
   ```yaml
   domain:
     scope: user | team | global
     data_isolation: strict | team_id | global

   skills:
     requires_context: [user_id, team_id, ...]
   ```

2. **Update SkillExecutor** to validate context before execution:
   ```python
   def _validate_context(self, skill, context):
       required = skill.get('requires_context', [])
       missing = [r for r in required if r not in context]
       if missing:
           raise ValueError(f"Skill {skill['name']} missing context: {missing}")

   def _enforce_data_isolation(self, domain, context):
       scope = domain.get('scope')
       if scope == 'user':
           # User can only access their own data
           if context.get('user_id') != context.get('requesting_user_id'):
               raise PermissionError("Cannot access another user's data")
       # Add team-scoped checks as needed
   ```

3. **Create user mapping database** (SQLite for demo):
   ```python
   # setup_demo_users.py
   import sqlite3

   conn = sqlite3.connect('aspora_demo.db')
   conn.execute('''
       CREATE TABLE users (
           id TEXT PRIMARY KEY,
           name TEXT,
           team_id TEXT,
           role TEXT,
           preferences TEXT
       )
   ''')

   conn.execute('''
       CREATE TABLE user_identities (
           user_id TEXT,
           channel TEXT,
           channel_user_id TEXT,
           PRIMARY KEY (channel, channel_user_id)
       )
   ''')

   # Demo users
   conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                ('sarah@aspora.com', 'Sarah', 'operations', 'field', '{"currency": "INR"}'))
   conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                ('raj@aspora.com', 'Raj', 'fincrime', 'analyst', '{"currency": "INR"}'))
   conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                ('priya@aspora.com', 'Priya', NULL, 'retail_user', '{"currency": "INR"}'))

   # Map Slack user IDs to Aspora users
   conn.execute("INSERT INTO user_identities VALUES (?, ?, ?)",
                ('sarah@aspora.com', 'slack', 'U_SARAH_DEMO'))
   conn.execute("INSERT INTO user_identities VALUES (?, ?, ?)",
                ('raj@aspora.com', 'slack', 'U_RAJ_DEMO'))
   conn.execute("INSERT INTO user_identities VALUES (?, ?, ?)",
                ('priya@aspora.com', 'slack', 'U_PRIYA_DEMO'))

   conn.commit()
   ```

4. **Update Slack bot** to inject user context:
   ```python
   @app.event("message")
   async def handle_message(event, say):
       slack_user_id = event['user']

       # Lookup Aspora user
       user = db.query("""
           SELECT u.* FROM users u
           JOIN user_identities ui ON u.id = ui.user_id
           WHERE ui.channel = 'slack' AND ui.channel_user_id = ?
       """, slack_user_id)

       if not user:
           await say("⛔ You're not registered in Aspora. Contact admin.")
           return

       # Route to appropriate skill based on message
       # (Use simple pattern matching for demo)
       text = event['text'].lower()

       if 'portfolio' in text or 'wealth' in text:
           result = await executor.execute(
               skill_id="wealth/portfolio-check",
               context={
                   "user_id": user['id'],
                   "requesting_user_id": user['id']
               }
           )
           await say(result['output'])

       elif 'tickets' in text or 'ecm' in text:
           if not user['team_id']:
               await say("⛔ ECM domain requires team membership. You have access to Wealth domain.")
               return

           result = await executor.execute(
               skill_id="ecm/field/my-tickets",
               context={
                   "user_id": user['id'],
                   "team_id": user['team_id'],
                   "requesting_user_id": user['id']
               }
           )
           await say(result['output'])

       elif 'alert' in text:
           if user['team_id'] != 'fincrime':
               await say("⛔ FinCrime domain is restricted to compliance team.")
               return

           # Extract alert ID from message
           alert_id = extract_alert_id(text)

           result = await executor.execute(
               skill_id="fincrime/investigate-alert",
               context={
                   "user_id": user['id'],
                   "team_id": user['team_id'],
                   "requesting_user_id": user['id'],
                   "alert_id": alert_id
               }
           )
           await say(result['output'])
   ```

### Demo Script Addition (30 seconds)

```
Act 5 (30s): "Multi-tenancy: Personal finance + Team operations"

  [Switch to Slack with 3 users: Sarah (operations), Raj (fincrime), Priya (retail)]

  Sarah: "show my tickets"
  Bot: 📋 Your Tickets (5 pending) — #1234 Stuck shipment...

  Sarah: "check my portfolio"
  Bot: 📊 Your Portfolio (₹15,45,000) — RELIANCE 12.3%, Bitcoin 8.5%
       🎯 House in Mumbai: 45%

  Raj: "show alerts"
  Bot: 🚨 FinCrime Queue (12 alerts) — Alert #5678 CRITICAL...

  Raj: "check my portfolio"
  Bot: ⛔ You don't have access to Wealth domain.

  Priya: "check my portfolio"
  Bot: 📊 Your Portfolio (₹8,50,000)...

  Priya: "show tickets"
  Bot: ⛔ ECM is for operations team. You have access to Wealth.

  "Same platform. Different scopes. Wealth is personal. Operations are team-based.
   Context injection + RBAC handles both."
```

---

## File Structure Update

```
aspora-platform/
├── domains/
│   ├── ecm/
│   │   ├── aspora.config.yaml  # scope: team, requires_context: [user_id, team_id]
│   │   └── skills/...
│   ├── fincrime/
│   │   ├── aspora.config.yaml  # scope: team, data_isolation: team_id
│   │   └── skills/...
│   ├── fraud-guardian/
│   │   ├── aspora.config.yaml  # scope: analyst
│   │   └── skills/...
│   └── wealth/
│       ├── aspora.config.yaml  # scope: user, data_isolation: strict
│       ├── skills/...
│       └── data/
│           ├── sarah@aspora.com/
│           │   ├── portfolio.csv
│           │   └── goals.csv
│           └── priya@aspora.com/
│               ├── portfolio.csv
│               └── goals.csv
├── packages/
│   └── executor/
│       ├── skill_executor.py  # Context validation, scope enforcement
│       └── user_db.py  # User lookup by channel identity
├── demo-bot.ts  # Slack adapter with user context injection
├── aspora_demo.db  # SQLite user database
└── setup_demo_users.py  # Seed demo users
```

---

## Summary

### Answer to "Will we deploy one agent per user like OpenClaw?"

**NO**. Aspora uses a **shared agent runtime with context-based scoping**.

- **One SkillExecutor instance** serves all users
- **Context injection** provides user_id, team_id, and other scoping data
- **Domain-declared scope** (`user` vs `team` vs `global`) determines isolation rules
- **Platform enforces** context requirements and permission checks before execution

### Why This Works

1. **Operations domains** (ECM, FinCrime) are team-shared — multiple users collaborate on same queue
2. **Wealth domain** is user-private — each user has isolated portfolio data
3. **Same platform executor** handles both by injecting different context
4. **Resource efficient** — one runtime vs N user instances
5. **Audit-friendly** — every execution logs user_id for compliance
6. **Scalable** — add new domains with different scope types without changing platform core

### Hackathon checklist
- [ ] Extend aspora.config.yaml schema (`scope`, `requires_context`)
- [ ] Update SkillExecutor with context validation
- [ ] Create SQLite user database
- [ ] Seed demo users (Sarah/operations, Raj/fincrime, Priya/retail)
- [ ] Update Slack bot with user context injection
- [ ] Add 30-second multi-tenancy demo to pitch
