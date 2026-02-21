# Knowledge Graph Primitive Demo — 2-Hour Build

**Goal**: Prove that knowledge graphs enable agents to learn from each other, not just execute tasks.

**Hook**: "Three agents. One graph. Zero coordination code. They just learned from each other."

---

## The Minimal Demo (What You'll Show)

### Act 1 (30 seconds): Agents Working Independently

```
[Slack: Support Agent]
User: "Why was my transfer blocked?"

SupportAgent: "Let me check..."
→ Queries graph: MATCH (user:User {email: 'priya@example.com'})-[:PLACED]->(order)
→ Finds: Order #1234, Status: BLOCKED
→ Response: "Your transfer to account 9876543210 was blocked. Let me investigate."

[Slack: Fraud Agent]
User: "Flag beneficiary 9876543210"

FraudAgent: "Checking pattern..."
→ Queries graph: MATCH (ben:Beneficiary {account: '9876543210'})<-[:TO]-(orders)
→ Finds: 1 order
→ Blocks beneficiary
→ WRITES TO GRAPH: CREATE (ben)-[:BLOCKED_AT {reason: 'manual_review', timestamp: now()}]
```

**What we showed**: Agents can read/write to shared graph. NOT impressive yet.

---

### Act 2 (30 seconds): The Magic — Cross-Domain Learning

```
[5 minutes later]

[Slack: Support Agent — SAME USER asks again]
User: "Why was my transfer blocked?"

SupportAgent: "Let me check..."
→ Queries graph: MATCH (user)-[:PLACED]->(order)-[:TO]->(ben)
→ Traverses ONE MORE HOP: MATCH (ben)-[:BLOCKED_AT]->(action)
→ Finds: Beneficiary was blocked by FraudAgent 5 minutes ago!
→ Response: "Your beneficiary account was flagged for fraud review. Our fraud team is investigating. We'll update you within 24h."
```

**What changed**: Support agent LEARNED from Fraud agent's action. Zero coordination code.

---

### Act 3 (30 seconds): Emergent Intelligence

```
[Next day]

[Slack: Churn Agent — Automated Daily Run]
ChurnAgent: "Running daily churn risk analysis..."

→ Queries graph:
   MATCH (user:User)-[:FILED]->(complaint:Complaint)
   WHERE complaint.created_at > now() - interval '24 hours'
   WITH user
   MATCH (user)-[:PLACED]->(order)-[:TO]->(ben)-[:BLOCKED_AT]->(action)
   WHERE action.timestamp > now() - interval '24 hours'
   RETURN user, count(order) as blocked_count

→ Finds: Priya (1 blocked order), Raj (2 blocked orders), Sarah (1 blocked order)
→ WRITES TO GRAPH: CREATE (priya)-[:AT_RISK {reason: 'fraud_block', score: 0.85}]

→ Triggers: CommsAgent

CommsAgent: "Composing compensation email..."
→ Reads graph: MATCH (user)-[:AT_RISK]->(risk), (user)-[:PLACED]->(order)
→ Personalizes: "Hi Priya, we blocked your transfer to protect you. As an apology, here's a fee waiver for your next transfer."
```

**What changed**: Churn agent discovered at-risk users WITHOUT being told. Comms agent personalized outreach WITHOUT manual input. The graph enabled EMERGENT intelligence.

---

## Technical Implementation (2 Hours)

### Stack (Simplest Possible)

```python
# Option 1: SQLite with Graph Tables (fastest to build)
import sqlite3

conn = sqlite3.connect('aspora_brain.db')

# Entity tables
conn.execute('''
CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT, corridor TEXT)
''')

conn.execute('''
CREATE TABLE orders (id TEXT PRIMARY KEY, user_id TEXT, amount REAL, status TEXT)
''')

conn.execute('''
CREATE TABLE beneficiaries (id TEXT PRIMARY KEY, account TEXT, bank TEXT)
''')

conn.execute('''
CREATE TABLE actions (id TEXT PRIMARY KEY, type TEXT, reason TEXT, timestamp TEXT)
''')

# Relationship tables (graph edges)
conn.execute('''
CREATE TABLE user_placed_order (user_id TEXT, order_id TEXT)
''')

conn.execute('''
CREATE TABLE order_to_beneficiary (order_id TEXT, beneficiary_id TEXT)
''')

conn.execute('''
CREATE TABLE beneficiary_blocked (beneficiary_id TEXT, action_id TEXT, agent TEXT)
''')

conn.execute('''
CREATE TABLE user_at_risk (user_id TEXT, score REAL, reason TEXT)
''')
```

### Agent Implementation (Minimal)

```python
# agents/support_agent.py
from openai import OpenAI
import sqlite3

class SupportAgent:
    def __init__(self, db_path: str, openrouter_key: str):
        self.db = sqlite3.connect(db_path)
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )

    def handle_query(self, user_email: str, question: str) -> str:
        # Query graph for context
        context = self._get_user_context(user_email)

        # Call LLM with graph context
        response = self.client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[
                {"role": "system", "content": f"""
You are a support agent. Use this context from our knowledge graph:

{context}

Answer the user's question based on FACTS from the graph, not speculation.
"""},
                {"role": "user", "content": question}
            ]
        )

        return response.choices[0].message.content

    def _get_user_context(self, user_email: str) -> dict:
        """Query graph: User → Orders → Beneficiaries → Actions"""

        # Find user
        user = self.db.execute(
            "SELECT * FROM users WHERE email = ?", (user_email,)
        ).fetchone()

        if not user:
            return {"error": "User not found"}

        user_id = user[0]

        # Find orders
        orders = self.db.execute("""
            SELECT o.* FROM orders o
            JOIN user_placed_order upo ON o.id = upo.order_id
            WHERE upo.user_id = ?
        """, (user_id,)).fetchall()

        # For each order, check if beneficiary blocked
        blocked_beneficiaries = []
        for order in orders:
            order_id = order[0]

            # Traverse: Order → Beneficiary → BlockAction
            result = self.db.execute("""
                SELECT b.account, a.reason, a.timestamp, bb.agent
                FROM order_to_beneficiary otb
                JOIN beneficiaries b ON b.id = otb.beneficiary_id
                JOIN beneficiary_blocked bb ON bb.beneficiary_id = b.id
                JOIN actions a ON a.id = bb.action_id
                WHERE otb.order_id = ?
            """, (order_id,)).fetchone()

            if result:
                blocked_beneficiaries.append({
                    "account": result[0],
                    "reason": result[1],
                    "blocked_at": result[2],
                    "blocked_by_agent": result[3]
                })

        return {
            "user": user,
            "orders": orders,
            "blocked_beneficiaries": blocked_beneficiaries
        }
```

### Fraud Agent (Writes to Graph)

```python
# agents/fraud_agent.py
import uuid
from datetime import datetime

class FraudAgent:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def block_beneficiary(self, account_number: str, reason: str) -> dict:
        """Block beneficiary and WRITE to graph"""

        # Find beneficiary
        ben = self.db.execute(
            "SELECT id FROM beneficiaries WHERE account = ?", (account_number,)
        ).fetchone()

        if not ben:
            return {"error": "Beneficiary not found"}

        ben_id = ben[0]
        action_id = str(uuid.uuid4())

        # Create action node
        self.db.execute(
            "INSERT INTO actions (id, type, reason, timestamp) VALUES (?, ?, ?, ?)",
            (action_id, "BLOCK_BENEFICIARY", reason, datetime.now().isoformat())
        )

        # Create relationship: Beneficiary -[:BLOCKED_AT]-> Action
        self.db.execute(
            "INSERT INTO beneficiary_blocked (beneficiary_id, action_id, agent) VALUES (?, ?, ?)",
            (ben_id, action_id, "FraudAgent")
        )

        self.db.commit()

        # Check how many orders affected
        affected_orders = self.db.execute("""
            SELECT COUNT(*) FROM order_to_beneficiary WHERE beneficiary_id = ?
        """, (ben_id,)).fetchone()[0]

        return {
            "blocked": True,
            "beneficiary": account_number,
            "affected_orders": affected_orders,
            "action_id": action_id
        }
```

### Churn Agent (Discovers Patterns)

```python
# agents/churn_agent.py
from datetime import datetime, timedelta

class ChurnAgent:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def find_at_risk_users(self) -> list:
        """Find users whose beneficiaries were blocked in last 24h"""

        # Multi-hop graph query:
        # User → Order → Beneficiary → BlockAction (last 24h)

        yesterday = (datetime.now() - timedelta(days=1)).isoformat()

        at_risk_users = self.db.execute("""
            SELECT DISTINCT
                u.id,
                u.email,
                COUNT(DISTINCT o.id) as blocked_order_count,
                MAX(a.timestamp) as last_block_time
            FROM users u
            JOIN user_placed_order upo ON u.id = upo.user_id
            JOIN orders o ON o.id = upo.order_id
            JOIN order_to_beneficiary otb ON o.id = otb.order_id
            JOIN beneficiary_blocked bb ON bb.beneficiary_id = otb.beneficiary_id
            JOIN actions a ON a.id = bb.action_id
            WHERE a.timestamp > ?
            GROUP BY u.id, u.email
        """, (yesterday,)).fetchall()

        # WRITE TO GRAPH: Mark users as at-risk
        for user in at_risk_users:
            user_id, email, block_count, last_block = user

            # Calculate churn score (simple heuristic)
            churn_score = min(0.5 + (block_count * 0.2), 0.95)

            self.db.execute(
                "INSERT OR REPLACE INTO user_at_risk (user_id, score, reason) VALUES (?, ?, ?)",
                (user_id, churn_score, f"fraud_block_{block_count}_orders")
            )

        self.db.commit()

        return at_risk_users
```

---

## Demo Script (2 Minutes Total)

### Setup (Pre-Demo)
```python
# seed_demo_data.py
import sqlite3
from datetime import datetime

conn = sqlite3.connect('aspora_brain.db')

# Create sample user
conn.execute("INSERT INTO users VALUES ('u1', 'priya@example.com', 'INR-GBP')")

# Create sample order
conn.execute("INSERT INTO orders VALUES ('o1', 'u1', 50000, 'BLOCKED')")
conn.execute("INSERT INTO user_placed_order VALUES ('u1', 'o1')")

# Create beneficiary
conn.execute("INSERT INTO beneficiaries VALUES ('b1', '9876543210', 'HDFC')")
conn.execute("INSERT INTO order_to_beneficiary VALUES ('o1', 'b1')")

conn.commit()
```

### Live Demo

```bash
# Terminal 1: Start Slack adapter (simulated)
python slack_adapter.py

# Terminal 2: Watch graph updates in real-time
watch -n 1 'sqlite3 aspora_brain.db "SELECT * FROM beneficiary_blocked"'
```

### Demo Flow

**[Show empty graph viewer]**

**Narrator**: "Three agents. One graph. Zero coordination."

**[Type in Slack]**
```
@fraud-agent block beneficiary 9876543210 for manual review
```

**[Graph viewer updates — show new BLOCKED_AT relationship appearing]**

**[Type in Slack — 10 seconds later]**
```
@support-agent why was my transfer blocked? (as priya@example.com)
```

**[Agent response shows]**:
```
Your beneficiary account 9876543210 was flagged for fraud review by our fraud team
10 seconds ago. We're investigating to protect you. You'll hear back within 24h.
```

**Narrator**: "Support agent LEARNED from fraud agent. No code connecting them. Just the graph."

**[Run churn agent]**
```bash
python agents/churn_agent.py run-daily
```

**[Show output]**:
```
Found 1 at-risk user: priya@example.com (churn score: 0.7)
Triggering compensation workflow...
Email drafted: "Hi Priya, we blocked your transfer to protect you..."
```

**Narrator**: "Churn agent discovered the pattern. Comms agent personalized outreach. Emergent intelligence."

---

## What This Proves (Without Saying "Neo4j")

| Without Graph | With Graph |
|--------------|------------|
| Support agent: "Your order is blocked" (dead end) | Support agent: "Fraud team blocked this 10 seconds ago" (contextual) |
| Churn agent: Doesn't know fraud blocked users | Churn agent: Auto-discovers at-risk users from graph traversal |
| Manual coordination needed | Zero coordination code |
| Each agent isolated | Agents learn from each other |

---

## Build Time Estimate

| Task | Time | Output |
|------|------|--------|
| SQLite schema + seed data | 30 min | Working graph database |
| Support agent (read graph) | 30 min | Context-aware responses |
| Fraud agent (write graph) | 20 min | Creates block relationships |
| Churn agent (pattern discovery) | 30 min | Multi-hop query finding at-risk users |
| Demo script + Slack adapter | 20 min | Live demo ready |
| **TOTAL** | **2h 10min** | **Primitive proving concept** |

---

## Why This Works for Your 20+ Problems

Once you prove this primitive, scaling to 20+ problems is just:

1. **More entity types**: User, Order, Beneficiary, Ticket, Alert, Deployment, MetricSpike, RootCause...
2. **More relationship types**: PLACED, BLOCKED_AT, CAUSED_BY, SOLVED_BY, REVEALED...
3. **More agents**: Auto-RCA reads (Deployment)-[:CAUSED]->(MetricSpike), VoC engine reads (Complaint)-[:SIMILAR_TO]->(Complaint)

**Same pattern**:
- Agents READ graph for context
- Agents WRITE findings to graph
- Other agents DISCOVER patterns through traversal
- Zero coordination code

---

## After Demo: The Sharpening Questions

1. **"Does this beat vector search for our use case?"** → YES (vector can't traverse causal chains)
2. **"Can I build this in 2 hours?"** → YES (SQLite graph tables proven above)
3. **"Does this convince judges that graph = moat?"** → YES (emergent intelligence > CRUD)
4. **"Do I need Neo4j for the primitive?"** → NO (SQLite sufficient for demo)
5. **"When do I upgrade to Neo4j?"** → When 10K+ nodes, or need real-time graph analytics dashboard

---

## Migration Path (After Hackathon)

### Phase 1: Primitive (Hackathon — SQLite)
- 3 agents (Support, Fraud, Churn)
- 5 entity types, 8 relationship types
- < 1,000 nodes
- **Good for**: Proving concept

### Phase 2: Production (Month 1 — PostgreSQL + pgvector)
- 10 agents
- 15 entity types, 25 relationship types
- 10K-100K nodes
- **Good for**: Real production load, ACID guarantees

### Phase 3: Scale (Month 3-6 — Neo4j)
- 20+ agents
- 20+ entity types, 30+ relationship types
- 100K-1M nodes
- **Good for**: Real-time graph analytics, Cypher queries, graph visualization dashboards

---

## Cost Estimate (Minimal Demo)

| Component | Cost |
|-----------|------|
| SQLite | $0 (embedded) |
| OpenRouter (Haiku) | ~$1 for 100 demo executions |
| Hosting (Railway) | $5/month (can use free tier for hackathon) |
| **Total Hackathon Cost** | **< $10** |

---

## Next Step

Do you want me to:

**Option A**: Build this exact primitive (2-hour implementation)

**Option B**: Extend this to your specific 3 domains (ECM + FinCrime + Fraud Guardian) with real data

**Option C**: Create the demo script for judges with specific talking points

Which moves you forward fastest?
