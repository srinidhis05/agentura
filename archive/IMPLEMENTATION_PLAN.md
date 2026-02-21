# Aspora Platform — Detailed Implementation Plan

> **Designed**: 2026-02-16
> **Architecture**: See [ASPORA_PLATFORM_DESIGN.md](./ASPORA_PLATFORM_DESIGN.md)
> **Rhythm**: PRIMITIVE (< 2hrs) → DEMO → SHARPEN (per ENGINEERING_BRAIN.md)

---

## Project Structure

```
aspora-platform/
├── packages/
│   ├── gateway/              # Layer 1: Communication Gateway
│   │   ├── adapters/
│   │   │   ├── slack.ts      # Slack Bolt SDK adapter
│   │   │   ├── whatsapp.ts   # Meta WhatsApp SDK adapter
│   │   │   └── web.ts        # WebSocket adapter
│   │   ├── core/
│   │   │   ├── gateway.ts    # WebSocket gateway
│   │   │   ├── router.ts     # Domain classifier
│   │   │   └── auth.ts       # Authentication & rate limiting
│   │   ├── triggers/
│   │   │   ├── cron.ts       # Scheduler
│   │   │   ├── alerts.ts     # Alert bus
│   │   │   └── commands.ts   # Command parser
│   │   └── package.json
│   │
│   └── core/                 # Existing TypeScript core
│       └── ...
│
├── agents/                   # Layer 2: Pydantic AI Agents
│   ├── core/
│   │   ├── agent.py          # Base agent abstraction
│   │   ├── skill.py          # Skill registry & loader
│   │   ├── router.py         # Domain classifier agent
│   │   ├── executor.py       # Skill execution engine
│   │   └── types.py          # Domain types
│   ├── domains/
│   │   ├── wealth.py         # Wealth Copilot agent
│   │   ├── fraud.py          # Fraud Guardian agent
│   │   ├── ecm.py            # ECM Dev Agent
│   │   ├── retention.py      # Retention agent
│   │   ├── support.py        # Support Triage agent
│   │   └── ops.py            # Operations agent
│   ├── testing/
│   │   ├── feedback_loop.py  # Auto test generation
│   │   ├── deepeval_suite.py # DeepEval integration
│   │   └── promptfoo_config.yaml
│   ├── mcp/
│   │   ├── client.py         # MCP client setup
│   │   └── server.py         # Expose Aspora as MCP server
│   └── pyproject.toml
│
├── skills/                   # Layer 3: Skills Library
│   ├── wealth/
│   │   ├── create-goal.md
│   │   ├── suggest-allocation.md
│   │   ├── fx-timing.md
│   │   ├── DECISIONS.md
│   │   └── GUARDRAILS.md
│   ├── fraud/
│   │   ├── block-transaction.md
│   │   ├── sync-trm.md
│   │   └── investigate-pattern.md
│   ├── ecm/
│   ├── retention/
│   ├── support/
│   └── ops/
│
├── lib/
│   └── db/
│       └── schema.sql        # Existing PostgreSQL schema
│
├── turbo.json                # Turborepo config
├── package.json              # Root package
└── pnpm-workspace.yaml       # PNPM workspaces
```

---

## Phase 1: Gateway + Wealth Agent (8 hours)

### Primitive 1.1: Slack Adapter (1.5 hrs)

**TASK**: Build Slack adapter that routes messages to Python agent

**Files**:
```typescript
// packages/gateway/adapters/slack.ts
import { App, SlackEventMiddlewareArgs } from '@slack/bolt';

export interface AsporaMessage {
  userId: string;
  text: string;
  channel: 'slack' | 'whatsapp' | 'web';
  timestamp: number;
  sessionId: string;
}

export interface AsporaResponse {
  text: string;
  attachments?: any[];
}

export class SlackAdapter {
  private app: App;
  private gateway: AsporaGateway;

  constructor(config: { token: string; signingSecret: string }) {
    this.app = new App({
      token: config.token,
      signingSecret: config.signingSecret,
    });

    this.setupListeners();
  }

  private setupListeners() {
    // Direct messages
    this.app.message(async ({ message, say }) => {
      if (message.subtype) return; // Ignore bot messages

      const asporaMsg: AsporaMessage = {
        userId: message.user,
        text: message.text,
        channel: 'slack',
        timestamp: parseFloat(message.ts) * 1000,
        sessionId: message.channel,
      };

      const response = await this.gateway.route(asporaMsg);
      await say(response.text);
    });

    // Slash commands
    this.app.command('/skills', async ({ command, ack, respond }) => {
      await ack();
      const response = await this.gateway.handleCommand('skills', {
        userId: command.user_id,
      });
      await respond(response.text);
    });
  }

  async start(port: number = 3000) {
    await this.app.start(port);
    console.log(`⚡️ Slack adapter running on port ${port}`);
  }
}
```

**Test**:
```bash
# Start Slack adapter
cd packages/gateway
pnpm dev

# Send test message via Slack
# → Should receive "Gateway not connected" error (expected)
```

**DONE WHEN**:
- Slack messages received and parsed
- Can send responses back to Slack
- Slash commands work

---

### Primitive 1.2: Python Agent Core (2 hrs)

**TASK**: Pydantic AI agent that returns structured response

**Files**:
```python
# agents/core/types.py
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Currency(str, Enum):
    USD = "USD"
    INR = "INR"
    AED = "AED"


class AsporaMessage(BaseModel):
    user_id: str
    text: str
    channel: Literal["slack", "whatsapp", "web"]
    timestamp: int
    session_id: str


class AsporaResponse(BaseModel):
    text: str
    action: Optional[Literal["create_goal", "suggest_allocation", "execute_trade"]] = None
    confidence: float = Field(ge=0, le=1)
    reasoning: str


# agents/domains/wealth.py
from pydantic_ai import Agent
from .types import AsporaResponse

wealth_agent = Agent(
    'claude-sonnet-4-5-20250929',
    result_type=AsporaResponse,
    system_prompt="""You are the Wealth Copilot for cross-border individuals.

Help users achieve financial goals across countries (house deposits, education, retirement).

Be conversational like Cleo (friendly, encouraging, uses data to build trust).

When user mentions a goal, extract:
- Target amount and currency
- Target date
- Current savings
- Priority level

Respond with reasoning + suggested next action.
""",
)


# agents/core/agent.py
from pydantic_ai import Agent
from .types import AsporaMessage, AsporaResponse


class WealthCopilotAgent:
    def __init__(self):
        self.agent = wealth_agent

    async def run(self, message: AsporaMessage) -> AsporaResponse:
        result = await self.agent.run(
            message.text,
            deps={
                "user_id": message.user_id,
                "channel": message.channel,
            },
        )

        return result.data
```

**Test**:
```python
# agents/tests/test_wealth.py
import pytest
from agents.core.agent import WealthCopilotAgent
from agents.core.types import AsporaMessage


@pytest.mark.asyncio
async def test_goal_creation():
    agent = WealthCopilotAgent()

    msg = AsporaMessage(
        user_id="test_user",
        text="I want to save ₹50 lakhs for a house in Mumbai in 3 years",
        channel="slack",
        timestamp=1234567890,
        session_id="test_session",
    )

    response = await agent.run(msg)

    assert response.action == "create_goal"
    assert response.confidence > 0.7
    assert "₹50" in response.text or "50L" in response.text
```

**Run**:
```bash
cd agents
pytest tests/test_wealth.py -v
```

**DONE WHEN**:
- Agent returns structured `AsporaResponse`
- Test passes with >0.7 confidence
- Response includes reasoning

---

### Primitive 1.3: Gateway Bridge (TypeScript ↔ Python) (2 hrs)

**TASK**: Connect TypeScript gateway to Python agents via HTTP/RPC

**Options**:
1. **HTTP REST API** (simple, latency OK for now)
2. **gRPC** (faster, more complex)
3. **Message Queue** (Redis Pub/Sub — best for prod)

**Choose**: Start with HTTP (fastest to ship), upgrade to gRPC in Phase 4.

**Files**:
```python
# agents/server.py
from fastapi import FastAPI
from pydantic import BaseModel
from agents.core.agent import WealthCopilotAgent
from agents.core.types import AsporaMessage

app = FastAPI()
wealth_agent = WealthCopilotAgent()


@app.post("/agents/wealth")
async def run_wealth_agent(message: AsporaMessage):
    response = await wealth_agent.run(message)
    return response.dict()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```typescript
// packages/gateway/core/gateway.ts
import axios from 'axios';

export class AsporaGateway {
  private agentBaseUrl = 'http://localhost:8000';

  async route(message: AsporaMessage): Promise<AsporaResponse> {
    // 1. Classify domain (hardcode wealth for now)
    const domain = 'wealth';

    // 2. Call Python agent
    const response = await axios.post(
      `${this.agentBaseUrl}/agents/${domain}`,
      message
    );

    return response.data;
  }

  async handleCommand(command: string, context: any): Promise<AsporaResponse> {
    // TODO: Command handlers
    return { text: `Command ${command} not implemented yet` };
  }
}
```

**Test**:
```bash
# Terminal 1: Start Python agent server
cd agents
python server.py

# Terminal 2: Start TypeScript gateway
cd packages/gateway
pnpm dev

# Terminal 3: Send Slack message
# → Should hit Python agent and return response
```

**DONE WHEN**:
- Slack message → TypeScript gateway → Python agent → Slack response
- End-to-end flow works
- Latency < 3 seconds

---

### Primitive 1.4: First Skill (create-goal.md) (1.5 hrs)

**TASK**: Create "create-goal" skill following SAGE principles

**Files**:
```markdown
<!-- skills/wealth/create-goal.md -->
---
name: create-goal
description: >
  Creates a financial goal (house deposit, education, retirement, emergency fund).
  Use when user mentions "saving for", "goal", "want to buy", "target",
  or states a specific financial objective with amount/timeframe.
  Do NOT use for general investment questions or portfolio analysis.
allowed-tools: [Read, Write, Bash]
---

# Create Goal Skill

## Domain Model

A goal is a targeted financial objective with:
- **Target amount** in specific currency
- **Target date** (must be future)
- **Priority** (1-5, where 1 = most important)
- **Current progress** (how much already saved)

Goals drive allocation. Without explicit goals, we're just picking numbers.

## Why This Matters

Cross-border individuals have goals scattered across countries:
- House deposit in home country (INR)
- Education fund for kids in US (USD)
- Retirement in current country (AED)

Each goal has different currency, time horizon, risk tolerance.

## Execution

### Step 1: Extract Goal Parameters

From user message, identify:
- **Target amount**: "₹50 lakhs", "$200K", "AED 1M"
- **Currency**: INR, USD, AED, SGD, GBP, EUR
- **Goal type**: house_deposit, education_fund, retirement, emergency_fund, custom
- **Target date**: "in 3 years", "by 2027", "10 years from now"
- **Priority**: Explicit (user says "top priority") or inferred (1st goal = priority 1)

### Step 2: Validate

CRITICAL checks (fail-fast per SAGE principle):
1. Target amount > 0
2. Target date is in the future
3. Currency is supported (USD, INR, AED, SGD, GBP, EUR)
4. If user has 5+ goals, ask which to deprioritize

### Step 3: Calculate Monthly Contribution

Use formula:
```
monthly_needed = (target_amount - current_savings) / months_remaining
```

If current_savings not provided, assume 0.

**Show the math** to build trust.

### Step 4: Create Goal Record

Write to database (use Write tool to generate SQL):
```sql
INSERT INTO goals (
  user_id,
  type,
  name,
  target_amount,
  target_currency,
  target_date,
  current_amount,
  priority,
  created_at
) VALUES (
  '{user_id}',
  '{goal_type}',
  '{user_provided_name}',
  {target_amount},
  '{currency}',
  '{target_date}',
  {current_amount},
  {priority},
  NOW()
) RETURNING id;
```

### Step 5: Respond with Encouragement

Use Cleo-style messaging:
- "Great! You're saving for {goal_name} 🎯"
- "You'll need to save {amount} per month"
- "At your current pace, you'll hit this goal by {projected_date}"

Include reasoning in response.

## Guardrails

From GUARDRAILS.md:
- NEVER create a goal with target date in the past
- NEVER exceed 10 active goals per user (causes analysis paralysis)
- ALWAYS show monthly savings calculation (builds trust)

## Edge Cases

**User gives vague timeframe** ("someday", "eventually"):
→ Ask clarifying question: "When would you like to reach this goal? In 1 year, 3 years, or 5+ years?"

**Currency ambiguity** ("I want to save 50 lakhs"):
→ Infer based on user's location. If Dubai, confirm: "Did you mean AED 50 lakhs or ₹50 lakhs?"

**Unrealistic timeline**:
→ Flag it: "To save ₹50L in 6 months, you'd need to save ₹8.3L/month. Is that realistic? Want to extend the timeline?"
```

**Update agent to use skill**:
```python
# agents/domains/wealth.py - UPDATED
from pathlib import Path

# Load skill at initialization
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

create_goal_skill = (SKILLS_DIR / "wealth/create-goal.md").read_text()

wealth_agent = Agent(
    'claude-sonnet-4-5-20250929',
    result_type=AsporaResponse,
    system_prompt=f"""You are the Wealth Copilot for cross-border individuals.

When user wants to create a financial goal, execute the create-goal skill:

{create_goal_skill}

Follow SAGE principles:
- Scoped: One skill, one task
- Adaptive: Explain WHY, not just rules
- Gradual: Load only what's needed
- Evaluated: Test with real user messages
""",
)
```

**Test**:
```python
@pytest.mark.asyncio
async def test_create_goal_skill():
    agent = WealthCopilotAgent()

    msg = AsporaMessage(
        user_id="test_user",
        text="I want to save ₹50 lakhs for a house in Mumbai in 3 years. I have ₹5 lakhs already.",
        channel="slack",
        timestamp=1234567890,
        session_id="test_session",
    )

    response = await agent.run(msg)

    assert response.action == "create_goal"
    assert "₹50" in response.text
    assert "month" in response.text.lower()  # Should mention monthly savings
    assert response.confidence > 0.8
```

**DONE WHEN**:
- Skill file follows YAML frontmatter spec
- Agent uses skill to create goals
- Test passes with >0.8 confidence
- Response includes monthly savings calculation

---

### Primitive 1.5: Decision Record Room (1 hr)

**TASK**: Create DECISIONS.md + GUARDRAILS.md for wealth domain

**Files**:
```markdown
<!-- skills/wealth/DECISIONS.md -->
# Wealth Domain Decisions

## DEC-001: Use Kelly Criterion for position sizing (2026-02-16)
**Chose:** Kelly formula with half-Kelly cap (from packages/core/risk/risk-manager.ts)
**Over:** Fixed percentage (1%, 2%, etc.)
**Why:** Optimizes for geometric growth, adapts to win rate/loss rate dynamically
**Constraint:** NEVER exceed half-Kelly to prevent over-leveraging

## DEC-002: Currency hedging threshold at 20% (2026-02-16)
**Chose:** Auto-suggest hedge when single currency > 20% of portfolio value
**Over:** Manual user-initiated hedging
**Why:** Cross-border users unknowingly accumulate FX risk; 20% is materially risky
**Constraint:** ALWAYS offer hedge suggestion, NEVER auto-execute without explicit user approval

## DEC-003: Goal limit of 10 active goals (2026-02-16)
**Chose:** Max 10 active goals per user
**Over:** Unlimited goals
**Why:** Analysis paralysis — users with 10+ goals don't make progress on any
**Constraint:** NEVER create 11th goal without asking which to archive

## DEC-004: Excel formulas over Python calculations (2026-02-16)
**Chose:** Generate Excel files with formulas (=A1*B1), not hardcoded values
**Over:** Calculate in Python and write values
**Why:** Users change assumptions → values must update dynamically
**Constraint:** NEVER write calculated values to Excel cells — ALWAYS use formulas
```

```markdown
<!-- skills/wealth/GUARDRAILS.md -->
# Wealth Domain Guardrails

## From Incident: Hardcoded Excel values (2026-02-10)
**Mistake:** Generated financial model with Python-calculated values instead of formulas
**Impact:** User changed growth rate assumption, numbers didn't update → lost trust, churned
**Rule:** NEVER write calculated values to Excel cells — ALWAYS use Excel formulas
**Detection:** Run `scripts/validate-excel.py` — fails if any calculation cell lacks formula

## From Incident: Stale FX rates caused bad trade (2026-02-12)
**Mistake:** Used 24-hour cached FX rate for real-time trade execution
**Impact:** User executed ₹ → USD conversion at wrong rate, lost ₹15K
**Rule:** ALWAYS use real-time rates (< 5 min old) for trades, cache OK for analysis only
**Detection:** Check `fx_rate.timestamp` — error if > 300 seconds old for `action=execute_trade`

## From Incident: Goal created with past date (2026-02-13)
**Mistake:** User said "I wanted to save for retirement by 2020", agent created goal with target_date = 2020-12-31
**Impact:** Broke dashboard UI, monthly_needed calculation was negative
**Rule:** NEVER create goal with target_date in the past — ask clarifying question
**Detection:** `if target_date < Date.now()` → fail validation, prompt user
```

**Update executor to load these**:
```python
# agents/core/executor.py
from pathlib import Path

class SkillExecutor:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    async def execute(self, skill_name: str, agent: Agent, message: str):
        # Load skill
        skill_path = self.skills_dir / f"{skill_name}.md"
        skill_content = skill_path.read_text()

        # Load Decision Record Room
        domain = skill_path.parent.name  # e.g., "wealth"
        decisions = self.load_decisions(domain)
        guardrails = self.load_guardrails(domain)

        # Build context
        context = f"""
# SKILL: {skill_name}

{skill_content}

# DECISIONS (What we decided and why)
{decisions}

# GUARDRAILS (What we must NEVER do)
{guardrails}
"""

        # Execute
        result = await agent.run(
            f"{context}\n\n# USER MESSAGE\n{message}",
        )

        return result

    def load_decisions(self, domain: str) -> str:
        decisions_file = self.skills_dir / domain / "DECISIONS.md"
        return decisions_file.read_text() if decisions_file.exists() else ""

    def load_guardrails(self, domain: str) -> str:
        guardrails_file = self.skills_dir / domain / "GUARDRAILS.md"
        return guardrails_file.read_text() if guardrails_file.exists() else ""
```

**DONE WHEN**:
- DECISIONS.md has 4 entries (~200 tokens)
- GUARDRAILS.md has 3 entries from "incidents"
- Executor loads both before skill execution

---

## Phase 1 Demo (End of Day 1)

**DEMO**: End-to-end wealth goal creation via Slack

```
User (in Slack): "I want to save ₹50 lakhs for a house in 3 years"
     ↓
Slack Adapter → Gateway → Python Wealth Agent (with create-goal skill)
     ↓
Agent: [Loads skill + DECISIONS + GUARDRAILS]
       [Extracts: target=₹50L, currency=INR, date=3yrs, type=house]
       [Calculates: ₹50L / 36 months = ₹1.39L/month]
       [Creates goal in DB]
       [Returns response with reasoning]
     ↓
Slack: "Great! You're saving for a house in Mumbai 🏠
        To reach ₹50 lakhs in 3 years, you'll need to save ₹1.39 lakhs per month.
        Want me to suggest an allocation strategy? (Yes/Later)"
```

**Metrics**:
- Latency: < 5 seconds end-to-end
- Confidence: > 0.8 on goal creation tasks
- Skill loads: DECISIONS.md + GUARDRAILS.md present in context

---

## Phase 2: Skills Runtime + Testing (8 hours)

### Primitive 2.1: Skill Registry with Lazy Loading (2 hrs)

**TASK**: Dynamic skill loader that follows SAGE principles

**Files**:
```python
# agents/core/skill.py
from pathlib import Path
from typing import Dict, Optional
import yaml
from pydantic import BaseModel


class SkillMetadata(BaseModel):
    name: str
    description: str
    allowed_tools: list[str] = []
    context: Optional[str] = None  # "fork" for isolated subagent


class Skill(BaseModel):
    metadata: SkillMetadata
    body: str
    file_path: Path


class SkillRegistry:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self.load_all()

    def load_all(self):
        """Load all skill metadata (NOT bodies — lazy loading)"""
        for skill_file in self.skills_dir.rglob("*.md"):
            # Skip DECISIONS.md and GUARDRAILS.md
            if skill_file.name in ["DECISIONS.md", "GUARDRAILS.md"]:
                continue

            metadata = self.parse_frontmatter(skill_file)
            if metadata:
                # Store path only, load body on demand
                self.skills[metadata.name] = None  # Lazy
                self._metadata_cache[metadata.name] = metadata

    def parse_frontmatter(self, path: Path) -> Optional[SkillMetadata]:
        content = path.read_text()

        if not content.startswith("---"):
            print(f"Warning: {path} missing YAML frontmatter")
            return None

        try:
            _, frontmatter, _ = content.split("---", 2)
            data = yaml.safe_load(frontmatter)
            return SkillMetadata(**data)
        except Exception as e:
            print(f"Error parsing {path}: {e}")
            return None

    def get(self, name: str) -> Skill:
        """Lazy load skill body when needed"""
        if self.skills.get(name) is None:
            # Load now
            skill_file = self._find_skill_file(name)
            content = skill_file.read_text()
            _, frontmatter, body = content.split("---", 2)

            self.skills[name] = Skill(
                metadata=self._metadata_cache[name],
                body=body.strip(),
                file_path=skill_file,
            )

        return self.skills[name]

    def list_descriptions(self, domain: Optional[str] = None) -> Dict[str, str]:
        """Return skill name → description map (for agent discovery)"""
        if domain:
            # Filter by domain path
            return {
                name: meta.description
                for name, meta in self._metadata_cache.items()
                if domain in str(self._find_skill_file(name))
            }
        return {name: meta.description for name, meta in self._metadata_cache.items()}
```

**Test**:
```python
def test_lazy_loading():
    registry = SkillRegistry(Path("skills"))

    # Should load metadata only
    assert len(registry._metadata_cache) > 0
    assert all(v is None for v in registry.skills.values())

    # Load single skill
    skill = registry.get("create-goal")
    assert skill.body is not None
    assert "Domain Model" in skill.body  # Skill content loaded
```

---

### Primitive 2.2: DeepEval Integration (2 hrs)

**TASK**: Auto-generate test cases from user corrections

**Files**:
```python
# agents/testing/deepeval_suite.py
from deepeval import assert_test, evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from typing import List


class SkillTestSuite:
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.test_cases: List[LLMTestCase] = []

    def add_from_correction(
        self,
        user_input: str,
        agent_output: str,
        corrected_output: str,
        context: List[str] = [],
    ):
        """User corrected agent output → generate test case"""
        test_case = LLMTestCase(
            input=user_input,
            actual_output=agent_output,
            expected_output=corrected_output,
            context=context,
        )
        self.test_cases.append(test_case)

    def run(self) -> dict:
        """Run all test cases with metrics"""
        results = []

        for test_case in self.test_cases:
            # Metric 1: Answer Relevancy
            relevancy = AnswerRelevancyMetric(threshold=0.7)

            # Metric 2: Correctness (G-Eval)
            correctness = GEval(
                name="Correctness",
                criteria="Determine if actual output matches expected output semantically",
                evaluation_params=[
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                    LLMTestCaseParams.EXPECTED_OUTPUT,
                ],
                threshold=0.7,
            )

            # Run test
            result = evaluate([test_case], [relevancy, correctness])
            results.append(result)

        return {
            "skill": self.skill_name,
            "total_tests": len(self.test_cases),
            "passed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
        }

    def save(self, path: Path):
        """Persist test suite to disk"""
        import json

        data = {
            "skill_name": self.skill_name,
            "test_cases": [
                {
                    "input": tc.input,
                    "actual_output": tc.actual_output,
                    "expected_output": tc.expected_output,
                    "context": tc.context,
                }
                for tc in self.test_cases
            ],
        }

        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "SkillTestSuite":
        """Load test suite from disk"""
        import json

        data = json.loads(path.read_text())
        suite = cls(data["skill_name"])

        for tc_data in data["test_cases"]:
            suite.test_cases.append(
                LLMTestCase(
                    input=tc_data["input"],
                    actual_output=tc_data["actual_output"],
                    expected_output=tc_data["expected_output"],
                    context=tc_data.get("context", []),
                )
            )

        return suite
```

**Usage**:
```python
# When user corrects output
suite = SkillTestSuite("create-goal")

suite.add_from_correction(
    user_input="I want to save for a house",
    agent_output="Great! How much do you want to save?",
    corrected_output="Great! To help you save for a house, I need: (1) Target amount, (2) Target date, (3) How much you've saved already. Can you share these?",
)

# Run tests
results = suite.run()
print(f"Passed: {results['passed']}/{results['total_tests']}")

# Save for CI
suite.save(Path("agents/tests/suites/create-goal.json"))
```

---

### Primitive 2.3: Opik Tracing (1.5 hrs)

**TASK**: Log all agent executions for debugging and feedback loop

**Files**:
```python
# agents/testing/tracing.py
from opik import Opik, track
from opik.evaluation import evaluate
from typing import Optional

client = Opik()


@track
async def run_agent_with_tracing(
    agent: Agent,
    message: str,
    skill_name: Optional[str] = None,
    user_id: str = None,
):
    """Wrap agent execution with Opik tracing"""

    # Start trace
    with client.trace(
        name=f"agent.{agent.name}",
        input={"message": message, "skill": skill_name},
        metadata={"user_id": user_id},
    ) as trace:
        # Execute agent
        result = await agent.run(message)

        # Log output
        trace.update(output=result.data.dict())

        # Log cost (if available)
        if hasattr(result, "usage"):
            trace.update(
                usage={
                    "prompt_tokens": result.usage.prompt_tokens,
                    "completion_tokens": result.usage.completion_tokens,
                    "total_cost": result.usage.total_cost,
                }
            )

        return result


def log_user_feedback(trace_id: str, feedback: dict):
    """Log user correction or rating"""
    client.log_feedback(
        trace_id=trace_id,
        feedback_type=feedback["type"],  # "correction", "rating", "flag"
        value=feedback["value"],
    )
```

**Integration**:
```python
# agents/domains/wealth.py - UPDATED
from agents.testing.tracing import run_agent_with_tracing

class WealthCopilotAgent:
    async def run(self, message: AsporaMessage) -> AsporaResponse:
        result = await run_agent_with_tracing(
            agent=self.agent,
            message=message.text,
            user_id=message.user_id,
        )
        return result.data
```

---

### Primitive 2.4: Feedback Loop (1.5 hrs)

**TASK**: User corrections automatically become test cases

**Files**:
```python
# agents/testing/feedback_loop.py
from pathlib import Path
from .deepeval_suite import SkillTestSuite
from .tracing import log_user_feedback, client as opik_client


class FeedbackLoop:
    def __init__(self, test_suites_dir: Path):
        self.test_suites_dir = test_suites_dir
        self.test_suites_dir.mkdir(parents=True, exist_ok=True)

    async def handle_correction(
        self,
        trace_id: str,
        user_id: str,
        skill_name: str,
        user_input: str,
        agent_output: str,
        corrected_output: str,
    ):
        """User corrected agent output → create test case"""

        # 1. Log to Opik
        log_user_feedback(
            trace_id=trace_id,
            feedback={
                "type": "correction",
                "value": corrected_output,
            },
        )

        # 2. Load or create test suite
        suite_file = self.test_suites_dir / f"{skill_name}.json"

        if suite_file.exists():
            suite = SkillTestSuite.load(suite_file)
        else:
            suite = SkillTestSuite(skill_name)

        # 3. Add test case
        suite.add_from_correction(
            user_input=user_input,
            agent_output=agent_output,
            corrected_output=corrected_output,
        )

        # 4. Save updated suite
        suite.save(suite_file)

        print(f"✅ Added test case to {skill_name} suite (now {len(suite.test_cases)} tests)")

        return suite

    async def run_regression_tests(self, skill_name: str):
        """Run all test cases for a skill"""
        suite_file = self.test_suites_dir / f"{skill_name}.json"

        if not suite_file.exists():
            print(f"No test suite for {skill_name}")
            return

        suite = SkillTestSuite.load(suite_file)
        results = suite.run()

        return results
```

**Gateway Integration**:
```typescript
// packages/gateway/core/gateway.ts - UPDATED
export class AsporaGateway {
  async route(message: AsporaMessage): Promise<AsporaResponse> {
    const response = await this.callAgent(message);

    // Ask user for feedback (optional)
    if (Math.random() < 0.1) {
      // 10% of messages
      response.feedback_request = {
        question: "Was this helpful? (👍/👎/✏️ edit)",
        trace_id: response.trace_id,
      };
    }

    return response;
  }

  async handleFeedback(
    trace_id: string,
    feedback_type: 'thumbs_up' | 'thumbs_down' | 'correction',
    corrected_output?: string
  ) {
    if (feedback_type === 'correction' && corrected_output) {
      // Send to Python feedback loop
      await axios.post('http://localhost:8000/feedback/correction', {
        trace_id,
        corrected_output,
      });
    }
  }
}
```

---

### Primitive 2.5: Promptfoo A/B Testing (1 hr)

**TASK**: Compare skill versions

**Files**:
```yaml
# agents/testing/promptfoo-config.yaml
description: 'Wealth Copilot - create-goal skill A/B test'

prompts:
  - file://skills/wealth/create-goal.md  # Version A
  - file://skills/wealth/create-goal-v2.md  # Version B (experimental)

providers:
  - id: anthropic:claude-sonnet-4-5-20250929
    config:
      temperature: 0.7

tests:
  - vars:
      user_message: "I want to save ₹50 lakhs for a house in 3 years"
    assert:
      - type: llm-rubric
        value: "Response extracts target amount, currency, and timeframe correctly"
      - type: llm-rubric
        value: "Response calculates monthly savings needed"
      - type: contains
        value: "₹50"

  - vars:
      user_message: "Save $200K for kids' education"
    assert:
      - type: llm-rubric
        value: "Response identifies education fund goal type"
      - type: contains
        value: "$200"

defaultTest:
  assert:
    - type: latency
      threshold: 5000  # 5 seconds max

outputPath: ./agents/tests/promptfoo-results/
```

**Run**:
```bash
cd agents
promptfoo eval -c testing/promptfoo-config.yaml
promptfoo view  # Opens UI to compare A vs B
```

---

## Phase 2 Demo (End of Day 2)

**DEMO**: Feedback loop in action

```
1. User: "I want to save for a house"
2. Agent: "Great! How much do you want to save?"
3. User: 👎 (thumbs down)
4. Agent: "How would you like me to respond instead?"
5. User: "Ask me for target amount, date, and current savings upfront"
   ↓
   System auto-generates test case:
   - Input: "I want to save for a house"
   - Expected: "To help you save for a house, I need: (1) Target amount..."
6. Test suite now has 1 test case
7. Next time skill is updated, test runs automatically
```

**Metrics**:
- Test suite for create-goal skill: 5+ test cases
- Opik tracing: 100% of executions logged
- Promptfoo: Skill A vs B comparison complete

---

## Timeline Summary

### Week 1: Gateway + Wealth Agent
- **Day 1**: Phase 1 primitives (8 hrs) → END-TO-END DEMO
- **Day 2**: Phase 2 primitives (8 hrs) → FEEDBACK LOOP DEMO
- **Day 3**: Add 2 more wealth skills (suggest-allocation, fx-timing) (6 hrs)
- **Day 4**: Polish + docs (4 hrs)

### Week 2: Multi-Domain
- **Day 1**: Fraud Guardian agent + skills (8 hrs)
- **Day 2**: ECM Dev Agent + codebase RAG (8 hrs)
- **Day 3**: WhatsApp adapter + MCP integration (8 hrs)
- **Day 4**: Testing + iteration (8 hrs)

### Week 3: Triggers + Production
- **Day 1**: Cron scheduler + alert bus (8 hrs)
- **Day 2**: Command system + Langfuse (8 hrs)
- **Day 3**: Performance optimization (8 hrs)
- **Day 4**: Security audit + deployment (8 hrs)

---

## Success Criteria

### Phase 1 (Week 1)
✅ Slack → Gateway → Wealth Agent → Response (< 5 sec latency)
✅ 3 wealth skills implemented following SAGE principles
✅ DECISIONS.md + GUARDRAILS.md per domain
✅ Feedback loop: Corrections → Test cases

### Phase 2 (Week 2)
✅ 3 domain agents (Wealth, Fraud, ECM)
✅ 10+ total skills across domains
✅ WhatsApp adapter working
✅ MCP client consuming 2+ external servers

### Phase 3 (Week 3)
✅ Cron scheduler running 3+ jobs
✅ Alert bus handling Datadog/PagerDuty
✅ Command system (/skills, /feedback, /help)
✅ Prod deployment with 10 test users

---

## Next Immediate Action

Start **Primitive 1.1** (Slack Adapter) → ship in < 2 hours per ENGINEERING_BRAIN.md rhythm.

```bash
# Initialize packages/gateway
mkdir -p packages/gateway/adapters
cd packages/gateway
pnpm init
pnpm add @slack/bolt dotenv

# Create slack.ts
# ...copy code from Primitive 1.1...

# Test
pnpm dev
```
