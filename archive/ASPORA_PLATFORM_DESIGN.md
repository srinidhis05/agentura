# Aspora Agentic Skills Platform — Architecture Design

> **Built on**: Pydantic AI + Custom Communication Gateway + Skills Runtime
> **NOT using**: OpenClaw (security concerns — too new, unaudited)
> **Designed**: 2026-02-16

---

## Executive Summary

**The Answer**: We use **Pydantic AI** for agent logic + **custom communication gateway** (OpenClaw-inspired) for multi-channel/triggers.

**Why not OpenClaw alone?**
- Launched Jan 2026 — too new, unaudited (per TECHNICAL_CHOICES.md)
- Need full control over skills runtime for competitive moat
- Testing infrastructure (DeepEval, Promptfoo) integrates with Pydantic AI

**Why not Pydantic AI alone?**
- No native multi-channel orchestration (Slack, WhatsApp, Telegram)
- No built-in trigger system (cron, alerts, commands)
- MCP support exists but needs coordination layer

**The Solution**: Three-layer architecture

---

## Architecture: Three Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ASPORA AGENTIC SKILLS PLATFORM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ╔══════════════════════════════════════════════════════════════════╗  │
│  ║  LAYER 1: COMMUNICATION GATEWAY (Custom, OpenClaw-Inspired)      ║  │
│  ╠══════════════════════════════════════════════════════════════════╣  │
│  ║  ┌────────────┬────────────┬────────────┬────────────────────┐  ║  │
│  ║  │   Slack    │  WhatsApp  │  Telegram  │   Web/WebSocket    │  ║  │
│  ║  │ (Bolt SDK) │ (Meta SDK) │(Official)  │    (Socket.io)     │  ║  │
│  ║  └────────────┴────────────┴────────────┴────────────────────┘  ║  │
│  ║                                │                                  ║  │
│  ║  ┌─────────────────────────────▼────────────────────────────┐   ║  │
│  ║  │        WEBSOCKET GATEWAY (Control Plane)                  │   ║  │
│  ║  │  • Message routing • Authentication • Rate limiting       │   ║  │
│  ║  │  • Session management • User context                      │   ║  │
│  ║  └───────────────────────────┬───────────────────────────────┘   ║  │
│  ║                              │                                    ║  │
│  ║  ┌──────────────────────────▼─────────────────────────────┐     ║  │
│  ║  │        TRIGGER SYSTEM                                   │     ║  │
│  ║  │  • Message received → route to agent                    │     ║  │
│  ║  │  • Cron scheduler → periodic tasks                      │     ║  │
│  ║  │  • Alert bus → external events (PagerDuty, Datadog)    │     ║  │
│  ║  │  • Command parser → /skills, /help, /status            │     ║  │
│  ║  └─────────────────────────────────────────────────────────┘     ║  │
│  ╚══════════════════════════════════════════════════════════════════╝  │
│                                  │                                      │
│  ╔══════════════════════════════▼══════════════════════════════════╗  │
│  ║  LAYER 2: AGENT ORCHESTRATION (Pydantic AI)                     ║  │
│  ╠══════════════════════════════════════════════════════════════════╣  │
│  ║  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        ║  │
│  ║  │  WEALTH  │  │  FRAUD   │  │   ECM    │  │RETENTION │  ...   ║  │
│  ║  │ COPILOT  │  │ GUARDIAN │  │DEV AGENT │  │  AGENT   │        ║  │
│  ║  │ (Pydantic│  │(Pydantic │  │(Pydantic │  │(Pydantic │        ║  │
│  ║  │   AI)    │  │   AI)    │  │   AI)    │  │   AI)    │        ║  │
│  ║  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        ║  │
│  ║       │             │             │             │               ║  │
│  ║  ┌────▼─────────────▼─────────────▼─────────────▼──────────┐   ║  │
│  ║  │      DOMAIN CLASSIFIER (Routes to correct agent)         │   ║  │
│  ║  │  • Intent detection • Entity extraction • Context        │   ║  │
│  ║  └──────────────────────────────────────────────────────────┘   ║  │
│  ╚══════════════════════════════════════════════════════════════════╝  │
│                                  │                                      │
│  ╔══════════════════════════════▼══════════════════════════════════╗  │
│  ║  LAYER 3: SKILLS RUNTIME (Competitive Moat)                     ║  │
│  ╠══════════════════════════════════════════════════════════════════╣  │
│  ║  ┌──────────────────────────────────────────────────────────┐   ║  │
│  ║  │  SKILLS DISCOVERY & LOADING (SAGE Principles)            │   ║  │
│  ║  │  • YAML frontmatter parsing                              │   ║  │
│  ║  │  • Lazy context loading                                  │   ║  │
│  ║  │  • Skill → Agent registration                            │   ║  │
│  ║  └──────────────────────────────────────────────────────────┘   ║  │
│  ║  ┌──────────────────────────────────────────────────────────┐   ║  │
│  ║  │  EXECUTION ENGINE                                        │   ║  │
│  ║  │  • Phased execution (Pre-Flight → Execute → Verify)     │   ║  │
│  ║  │  • Decision Record Room (DECISIONS.md, GUARDRAILS.md)   │   ║  │
│  ║  │  • Tool calling with validation                          │   ║  │
│  ║  └──────────────────────────────────────────────────────────┘   ║  │
│  ║  ┌──────────────────────────────────────────────────────────┐   ║  │
│  ║  │  FEEDBACK & LEARNING LOOP (Primary Moat)                 │   ║  │
│  ║  │  • Execution logging → Opik/Langfuse                     │   ║  │
│  ║  │  • User corrections → Auto test generation (DeepEval)    │   ║  │
│  ║  │  • A/B testing → Promptfoo                               │   ║  │
│  ║  │  • Skill metrics → Continuous improvement                │   ║  │
│  ║  └──────────────────────────────────────────────────────────┘   ║  │
│  ╚══════════════════════════════════════════════════════════════════╝  │
│                                  │                                      │
│  ┌───────────────────────────────▼──────────────────────────────────┐  │
│  │  INTEGRATIONS & MCPs                                             │  │
│  ├────────┬────────┬────────┬────────┬────────┬──────────┬─────────┤  │
│  │  TRM   │ Column │Metabase│ Slack  │ GitHub │ Codebase │ Custom  │  │
│  │  API   │  APIs  │        │  API   │  API   │   RAG    │  MCPs   │  │
│  └────────┴────────┴────────┴────────┴────────┴──────────┴─────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Communication Gateway (Custom Implementation)

### Why Build This?

OpenClaw does this out-of-box BUT:
- Too new (Jan 2026) — unaudited
- We need custom rate limiting per domain
- Skills-first routing (not generic chatbot routing)
- Multi-tenancy for Aspora (different customers, different configs)

### Components

#### 1.1 Channel Adapters

**Built on official SDKs** — no dependencies on unaudited frameworks.

```typescript
// packages/gateway/adapters/slack.ts
import { App } from '@slack/bolt'; // Official SDK

export class SlackAdapter implements ChannelAdapter {
  private app: App;

  constructor(config: SlackConfig) {
    this.app = new App({
      token: config.botToken,
      signingSecret: config.signingSecret,
    });

    // Map Slack events → Aspora events
    this.app.message(async ({ message, say }) => {
      const event = this.toAsporaMessage(message);
      const response = await this.gateway.route(event);
      await say(response.text);
    });
  }

  private toAsporaMessage(slackMsg: any): AsporaMessage {
    return {
      userId: slackMsg.user,
      text: slackMsg.text,
      channel: 'slack',
      timestamp: slackMsg.ts,
      sessionId: slackMsg.channel, // Slack channel = session
    };
  }
}
```

**Supported Channels (MVP)**:
- Slack (Bolt SDK)
- WhatsApp (Meta Official SDK)
- Web (Socket.io)

**Post-MVP**:
- Telegram (Official)
- Email (SendGrid)
- Discord (Official)

#### 1.2 WebSocket Gateway

```typescript
// packages/gateway/core/gateway.ts
export class AsporaGateway {
  private adapters: Map<string, ChannelAdapter>;
  private router: DomainRouter;
  private triggerSystem: TriggerSystem;

  async routeMessage(msg: AsporaMessage): Promise<AsporaResponse> {
    // 1. Authenticate & rate-limit
    await this.auth.verify(msg.userId);
    await this.rateLimiter.check(msg.userId);

    // 2. Load user context
    const context = await this.contextStore.get(msg.userId);

    // 3. Classify domain
    const domain = await this.router.classify(msg, context);

    // 4. Get agent for domain
    const agent = this.agentRegistry.get(domain);

    // 5. Execute with Pydantic AI
    const response = await agent.run(msg.text, {
      context,
      channel: msg.channel,
    });

    // 6. Log for feedback loop
    await this.logger.log({
      userId: msg.userId,
      domain,
      input: msg,
      output: response,
      timestamp: Date.now(),
    });

    return response;
  }
}
```

#### 1.3 Trigger System

```typescript
// packages/gateway/triggers/scheduler.ts
import { CronJob } from 'cron';

export class TriggerSystem {
  private cronJobs: Map<string, CronJob>;
  private alertSubscriptions: Map<string, AlertHandler>;

  // Cron triggers
  registerCron(schedule: string, handler: AgentHandler) {
    const job = new CronJob(schedule, async () => {
      const agent = handler.agent;
      await agent.run(handler.prompt, { trigger: 'cron' });
    });
    job.start();
    this.cronJobs.set(handler.id, job);
  }

  // Alert triggers (Datadog, PagerDuty, etc.)
  subscribeToAlerts(source: string, filter: AlertFilter, handler: AgentHandler) {
    this.alertBus.subscribe(source, async (alert) => {
      if (filter.matches(alert)) {
        const agent = handler.agent;
        await agent.run({
          type: 'alert',
          source,
          alert,
        });
      }
    });
  }

  // Command triggers (/skills, /help, /deploy)
  registerCommand(command: string, handler: CommandHandler) {
    this.commandRegistry.set(command, handler);
  }
}
```

---

## Layer 2: Agent Orchestration (Pydantic AI)

### Why Pydantic AI?

✅ **Type-safe structured outputs** — Critical for multi-domain platform
✅ **Battle-tested** — Built on Pydantic (2.5B+ downloads)
✅ **MCP support** — Native client/server capabilities
✅ **Observability** — Logfire integration
✅ **Durable execution** — HITL, retries, failure handling
✅ **Multi-model** — OpenAI, Anthropic, Google, Groq, Mistral

### Domain Agents

Each domain = One Pydantic AI agent.

```python
# agents/domains/wealth.py
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Literal

class WealthAction(BaseModel):
    type: Literal["analyze_goal", "suggest_allocation", "execute_trade"]
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    payload: dict

wealth_agent = Agent(
    'claude-sonnet-4-5-20250929',  # Primary model
    result_type=WealthAction,
    system_prompt="""You are the Wealth Copilot for cross-border individuals.

    Your role: Help users achieve financial goals across countries.
    Core capabilities:
    - Goal-based planning (house deposits, education, retirement)
    - Currency-aware allocation
    - Cross-border intelligence

    Load skills from /skills/wealth/ based on user intent.
    Follow SAGE principles: Scoped, Adaptive, Gradual, Evaluated.
    """,
    deps_type=WealthContext,  # DI for tools
)

# Register skills
wealth_agent.register_skill("create-goal", "/skills/wealth/create-goal.md")
wealth_agent.register_skill("suggest-allocation", "/skills/wealth/suggest-allocation.md")
wealth_agent.register_skill("analyze-fx-timing", "/skills/wealth/fx-timing.md")
```

### Domain Router

```python
# agents/core/router.py
from pydantic_ai import Agent

class DomainClassifier(BaseModel):
    domain: Literal["wealth", "fraud", "ecm", "retention", "support", "ops"]
    confidence: float
    reasoning: str

classifier_agent = Agent(
    'claude-haiku-4-5-20251001',  # Fast, cheap for routing
    result_type=DomainClassifier,
    system_prompt="""Classify user messages into domains:

    - wealth: Financial goals, investments, cross-border money, FX
    - fraud: Suspicious transactions, account blocks, TRM integration
    - ecm: Product features, development requests, codebase questions
    - retention: User churn, engagement, win-back campaigns
    - support: General help, account issues, escalations
    - ops: SLA monitoring, alerts, incident response

    Return domain with confidence.
    """,
)

async def classify(message: str, context: UserContext) -> str:
    result = await classifier_agent.run(message, deps=context)
    return result.data.domain
```

### MCP Integration

Pydantic AI has native MCP support:

```python
# agents/core/mcp_tools.py
from pydantic_ai.mcp import MCPClient

# Connect to MCP servers
async def setup_mcp_tools(agent: Agent):
    # Superchat MCP (unified messaging)
    superchat = MCPClient("http://localhost:3000/mcp/superchat")
    await agent.add_mcp_tools(superchat)

    # Custom MCP servers
    trm_mcp = MCPClient("http://localhost:3001/mcp/trm")
    await agent.add_mcp_tools(trm_mcp)

    # Tools are now available to agent automatically
```

---

## Layer 3: Skills Runtime (Competitive Moat)

### Why Skills Are the Moat

From engineering brain:
> "In agentic projects, the deliverable is a SKILL, not Python/Java/Go code."

**The feedback loop**:
```
User request → Agent executes skill → Result → User correction
     ↓                                              ↓
Logged to Opik/Langfuse  ← Auto test case ← DeepEval
     ↓
Regression suite grows → Skill quality improves → Competitive moat
```

### Skill Structure (SAGE Principles)

```
skills/
├── wealth/
│   ├── create-goal.md           # 1 skill = 1 bounded context
│   ├── suggest-allocation.md
│   ├── fx-timing.md
│   ├── DECISIONS.md             # What we decided, max 20 entries
│   └── GUARDRAILS.md            # What we must NEVER do
├── fraud/
│   ├── block-transaction.md
│   ├── sync-trm.md
│   └── investigate-pattern.md
├── ecm/
│   ├── search-codebase.md
│   ├── generate-spec.md
│   └── file-jira.md
└── ...
```

### Skill Frontmatter (Official Spec)

```yaml
---
name: create-goal
description: >
  Creates a financial goal (house deposit, education, retirement).
  Use when user mentions "saving for", "goal", "target amount", or
  "I want to buy a house".
  Do NOT use for portfolio analysis or investment research.
allowed-tools: [Read, Write, Bash]
---

# Create Goal Skill

## Domain Model
A goal is a target amount in a specific currency with a target date...

## Why This Matters
Goals drive allocation. Without explicit goals, we're just picking stocks...

## Execution
1. Extract: Target amount, currency, date, priority
2. Validate: Amount > 0, date in future, currency supported
3. Calculate: Monthly contribution needed given current portfolio
4. Create: Write to database, return goal ID
...
```

### Skills Loader

```python
# agents/core/skill_loader.py
import yaml
from pathlib import Path

class SkillRegistry:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills = {}

    def load_all(self):
        for skill_file in self.skills_dir.rglob("*.md"):
            skill = self.parse_skill(skill_file)
            self.skills[skill.name] = skill

    def parse_skill(self, path: Path) -> Skill:
        content = path.read_text()

        # Parse YAML frontmatter
        if content.startswith("---"):
            _, frontmatter, body = content.split("---", 2)
            metadata = yaml.safe_load(frontmatter)
        else:
            raise ValueError(f"Skill {path} missing YAML frontmatter")

        return Skill(
            name=metadata['name'],
            description=metadata['description'],
            body=body,
            allowed_tools=metadata.get('allowed-tools', []),
            file_path=path,
        )

    def get(self, name: str) -> Skill:
        return self.skills.get(name)
```

### Execution Engine with Decision Record Room

Every skill execution follows **Pre-Flight → Execute → Verify**:

```python
# agents/core/executor.py
class SkillExecutor:
    async def execute(self, skill: Skill, agent: Agent, context: dict):
        # PRE-FLIGHT: Load Decision Record Room
        decisions = self.load_decisions(skill)
        guardrails = self.load_guardrails(skill)

        # Inject into context
        context['decisions'] = decisions
        context['guardrails'] = guardrails

        # EXECUTE: Run skill
        result = await agent.run(
            f"Execute skill: {skill.name}\n\n{skill.body}",
            deps=context,
        )

        # VERIFY: Check guardrails
        violations = self.check_guardrails(result, guardrails)
        if violations:
            raise GuardrailViolation(violations)

        return result

    def load_decisions(self, skill: Skill) -> str:
        decisions_file = skill.file_path.parent / "DECISIONS.md"
        if decisions_file.exists():
            return decisions_file.read_text()
        return ""
```

### Feedback Loop & Testing

```python
# agents/testing/feedback_loop.py
from deepeval import assert_test
from deepeval.metrics import GEval, AnswerRelevancy
from deepeval.test_case import LLMTestCase

class FeedbackLoop:
    def __init__(self):
        self.opik_client = OpikClient()  # Tracing
        self.langfuse = LangfuseClient()  # Logging

    async def log_execution(self, skill, input, output, user_feedback):
        # Log to Opik for tracing
        await self.opik_client.log({
            "skill": skill.name,
            "input": input,
            "output": output,
            "feedback": user_feedback,
        })

        # If user corrected output → generate test case
        if user_feedback.type == "correction":
            test_case = LLMTestCase(
                input=input,
                actual_output=output,
                expected_output=user_feedback.corrected_output,
            )

            # Add to regression suite
            self.test_suite.add(skill.name, test_case)

            # Run DeepEval metrics
            relevancy_metric = AnswerRelevancy()
            assert_test(test_case, [relevancy_metric])
```

---

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Gateway** | TypeScript + Node.js | Official SDK compatibility |
| **Channel Adapters** | Slack Bolt, Meta WhatsApp, Socket.io | Official, audited SDKs |
| **Agent Core** | Python + Pydantic AI | Type-safe, production-ready |
| **Skills** | Markdown (YAML frontmatter) | Language-agnostic, human + LLM readable |
| **Database** | PostgreSQL + Prisma | Type-safe queries, multi-domain data |
| **Tracing** | Opik (Apache 2.0) | Open-source, production tracing |
| **Logging** | Langfuse (AGPL) | Self-hosted, compliance audit trails |
| **Testing** | DeepEval + Promptfoo | LLM unit tests + A/B testing |
| **Observability** | Pydantic Logfire | Native Pydantic AI integration |

---

## Multi-Domain Support

Each domain is a separate Pydantic AI agent with domain-specific skills:

| Domain | Agent | Key Skills | External Integrations |
|--------|-------|------------|---------------------|
| **Wealth Copilot** | `wealth_agent` | create-goal, suggest-allocation, fx-timing | Column APIs, Market data |
| **Fraud Guardian** | `fraud_agent` | block-transaction, sync-trm, investigate-pattern | TRM API, Compliance  |
| **ECM Dev Agent** | `ecm_agent` | search-codebase, generate-spec, file-jira | GitHub API, Codebase RAG |
| **Retention** | `retention_agent` | churn-analysis, win-back, campaign | Metabase, Analytics |
| **Support Triage** | `support_agent` | escalate, classify, dedupe | Zendesk, Intercom |
| **Operations** | `ops_agent` | sla-monitor, routing, alerts | PagerDuty, Datadog |

---

## Custom MCP Support

Pydantic AI has native MCP client/server support:

### As MCP Client (Consuming tools from MCP servers)

```python
from pydantic_ai.mcp import MCPClient

# Connect to external MCP servers
async def setup_domain_tools(agent: Agent, domain: str):
    if domain == "wealth":
        # Market data MCP
        market_mcp = MCPClient("http://market-data-mcp:3000")
        await agent.add_mcp_tools(market_mcp)

        # Column API MCP
        column_mcp = MCPClient("http://column-mcp:3001")
        await agent.add_mcp_tools(column_mcp)

    elif domain == "fraud":
        # TRM MCP
        trm_mcp = MCPClient("http://trm-mcp:3002")
        await agent.add_mcp_tools(trm_mcp)
```

### As MCP Server (Exposing Aspora skills to external tools)

```python
# agents/mcp_server/server.py
from pydantic_ai.mcp import MCPServer

mcp_server = MCPServer(name="aspora-skills")

# Expose skills as MCP tools
@mcp_server.tool()
async def create_wealth_goal(
    target_amount: float,
    currency: str,
    target_date: str,
    user_id: str,
) -> dict:
    """Create a financial goal for a user"""
    skill = skill_registry.get("create-goal")
    result = await executor.execute(skill, wealth_agent, {
        "target_amount": target_amount,
        "currency": currency,
        "target_date": target_date,
        "user_id": user_id,
    })
    return result

# Now external MCP clients can call Aspora skills!
```

---

## Trigger System Design

### 1. Message Triggers

```python
# Automatic — handled by gateway
message = AsporaMessage(
    userId="user123",
    text="I want to save for a house",
    channel="slack",
)

response = await gateway.route(message)
# → classifier determines domain = "wealth"
# → wealth_agent executes "create-goal" skill
```

### 2. Cron Triggers

```python
# agents/triggers/cron.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Daily portfolio rebalance check
@scheduler.scheduled_job('cron', hour=9, minute=0)
async def daily_rebalance():
    # Get all users with auto-rebalance enabled
    users = await db.users.find({"autoRebalance": True})

    for user in users:
        # Invoke wealth agent
        await wealth_agent.run(
            "Check if portfolio needs rebalancing",
            deps={"userId": user.id, "trigger": "cron"},
        )

# Weekly fraud pattern analysis
@scheduler.scheduled_job('cron', day_of_week='mon', hour=0)
async def weekly_fraud_analysis():
    await fraud_agent.run(
        "Analyze transaction patterns from last week",
        deps={"trigger": "cron"},
    )
```

### 3. Alert Triggers

```python
# agents/triggers/alerts.py
from datadog import DogStatsd

alert_bus = AlertBusMCP:3003")

# Subscribe fraud agent to Datadog anomaly alerts
await alert_bus.subscribe({
    "source": "datadog",
    "event_type": "anomaly_detected",
    "tags": ["fraud", "high_risk"],
}, async (alert) => {
    await fraud_agent.run({
        "type": "alert",
        "source": "datadog",
        "alert": alert,
        "action": "investigate",
    })
})

# Subscribe ops agent to PagerDuty incidents
await alert_bus.subscribe({
    "source": "pagerduty",
    "severity": ["critical", "high"],
}, async (incident) => {
    await ops_agent.run({
        "type": "incident",
        "source": "pagerduty",
        "incident": incident,
        "action": "triage",
    })
})
```

### 4. Command Triggers

```python
# Gateway command handler
@gateway.command("/skills")
async def list_skills(user_id: str, channel: str):
    skills = skill_registry.list_for_user(user_id)
    return {
        "type": "skills_list",
        "skills": skills,
    }

@gateway.command("/feedback")
async def submit_feedback(user_id: str, correction: str):
    # User corrected an output → generate test case
    await feedback_loop.handle_correction(user_id, correction)
    return {"status": "Test case created"}
```

---

## Decision Record Room Structure

Every domain has DECISIONS.md + GUARDRAILS.md:

```markdown
# wealth/DECISIONS.md

## DEC-001: Use Kelly Criterion for position sizing (2026-02-15)
**Chose:** Kelly formula with half-Kelly cap
**Over:** Fixed percentage (1%, 2%, etc.)
**Why:** Optimizes for geometric growth, adapts to win rate
**Constraint:** NEVER exceed half-Kelly (prevents over-leveraging)

## DEC-002: Currency hedging at 20% threshold (2026-02-15)
**Chose:** Auto-hedge when single currency > 20% of portfolio
**Over:** Manual user hedging
**Why:** Cross-border users accumulate FX risk unknowingly
**Constraint:** ALWAYS offer hedge suggestion, never auto-execute without approval

---

# wealth/GUARDRAILS.md

## From Incident: Hardcoded values destroyed user's model (2026-02-10)
**Mistake:** Generated Excel with Python-calculated values instead of formulas
**Impact:** User changed assumptions, values didn't update → lost trust
**Rule:** NEVER write calculated values to cells — ALWAYS use Excel formulas
**Detection:** Run scripts/validate-excel.py — fails if any cell lacks formula

## From Incident: FX rate from outdated cache (2026-02-12)
**Mistake:** Used 24-hour cached FX rates for real-time trade
**Impact:** User executed trade at wrong rate, lost money
**Rule:** ALWAYS use real-time rates for trade execution, cache only for analysis
**Detection:** Check timestamp on FX data — error if > 5 minutes old for trades
```

---

## Implementation Priorities

### Phase 1: Gateway + Wealth Agent (Week 1)
- ✅ Slack adapter (Bolt SDK)
- ✅ WebSocket gateway
- ✅ Domain router (Haiku for speed)
- ✅ Wealth Copilot agent (Pydantic AI + Sonnet 4.5)
- ✅ 3 core skills: create-goal, suggest-allocation, fx-timing
- ✅ DECISIONS.md + GUARDRAILS.md for wealth domain

### Phase 2: Skills Runtime + Testing (Week 2)
- ✅ Skill loader with YAML parsing
- ✅ Pre-Flight → Execute → Verify pattern
- ✅ DeepEval integration
- ✅ Opik tracing
- ✅ Feedback loop (corrections → test cases)

### Phase 3: Multi-Domain (Week 3)
- ✅ Fraud Guardian agent
- ✅ ECM Dev Agent
- ✅ WhatsApp adapter (Meta SDK)
- ✅ MCP client setup (TRM, Column)

### Phase 4: Triggers + Production (Week 4)
- ✅ Cron scheduler (APScheduler)
- ✅ Alert bus (Datadog, PagerDuty)
- ✅ Command parser
- ✅ Langfuse logging
- ✅ Promptfoo A/B testing

---

## Summary: Why This Architecture Wins

| Component | Technology | Competitive Advantage |
|-----------|-----------|---------------------|
| **Communication Gateway** | Custom (OpenClaw-inspired) | Multi-channel without security risk |
| **Agent Brain** | Pydantic AI | Type-safe, production-grade, battle-tested |
| **Skills Runtime** | SAGE principles | Feedback loop → auto test generation → moat |
| **Testing Stack** | DeepEval + Promptfoo + Opik | Licenses, compliance, trust = enterprise sales |
| **MCP Support** | Native Pydantic AI | Extensibility for domain-specific integrations |
| **Trigger System** | Custom (cron + alerts + commands) | Autonomous operation beyond chat |

**The Moat**: Every user correction becomes a regression test. After 1000 users:
- Wealth domain: 5000+ test cases
- Fraud domain: 3000+ test cases
- ECM domain: 2000+ test cases

**Newcomers can't replicate this** — it's locked behind real user interactions.

---

**Next Step**: Implement Phase 1 (Gateway + Wealth Agent) in < 2 hours per ENGINEERING_BRAIN.md rhythm.
