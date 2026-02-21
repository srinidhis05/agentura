# Aspora Agentic Skills Platform

> **Vision:** A unified skills-based platform that any Aspora team can extend to build intelligent agents for their domain — wealth, fraud, retention, support, operations.

---

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ASPORA AGENTIC SKILLS PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        DOMAIN APPLICATIONS                           │    │
│  ├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┤    │
│  │   WEALTH    │   FRAUD     │  RETENTION  │   SUPPORT   │  OPERATIONS │    │
│  │   COPILOT   │   GUARDIAN  │   AGENT     │   TRIAGE    │    OPS      │    │
│  ├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤    │
│  │ • Trading   │ • Block     │ • Churn     │ • Escalate  │ • SLA       │    │
│  │ • Goals     │ • Blacklist │ • Win-back  │ • Classify  │ • Routing   │    │
│  │ • Rebalance │ • TRM sync  │ • Campaigns │ • Dedupe    │ • Alerts    │    │
│  └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘    │
│                                     │                                        │
│  ┌──────────────────────────────────▼──────────────────────────────────┐    │
│  │                      SKILLS RUNTIME ENGINE                           │    │
│  │  • Skill discovery & loading                                         │    │
│  │  • Execution & caching                                               │    │
│  │  • Feedback collection                                               │    │
│  │  • Test generation & validation                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│  ┌──────────────────────────────────▼──────────────────────────────────┐    │
│  │                      AGENT ORCHESTRATION                             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │    │
│  │  │ Pydantic │  │ OpenClaw │  │ Claude   │  │ Custom   │            │    │
│  │  │    AI    │  │  /Molt   │  │ Computer │  │ Agents   │            │    │
│  │  │ (Pi.dev) │  │   Bot    │  │   Use    │  │          │            │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│  ┌──────────────────────────────────▼──────────────────────────────────┐    │
│  │                      CONNECTORS & INTEGRATIONS                       │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │    │
│  │  │ Slack  │ │ Email  │ │Metabase│ │  TRM   │ │ Column │ │Codebase│ │    │
│  │  │        │ │        │ │        │ │        │ │  APIs  │ │  RAG   │ │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│  ┌──────────────────────────────────▼──────────────────────────────────┐    │
│  │                      FEEDBACK & LEARNING LOOP                        │    │
│  │  • Execution logging • Auto test generation • Skill metrics          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Where Agent Frameworks Fit

### Framework Comparison

| Framework | Best For | We Use It For | Security |
|-----------|----------|---------------|----------|
| **Pydantic AI (Pi.dev)** | Type-safe agents, structured outputs | Core agent definitions, all domains | ✅ Battle-tested |
| **Claude Computer Use** | Browser automation, screenshot analysis | Vision-based issue extraction | ✅ Anthropic-backed |
| **Custom Channel Adapters** | Multi-channel delivery | Slack, WhatsApp, Web | ✅ Official SDKs |
| **LangGraph** | Complex workflows | Optional, for complex chains | ⚠️ Use carefully |
| ~~OpenClaw/MoltBot~~ | ~~Multi-channel~~ | ~~Not using~~ | ❌ Too new, unaudited |

### Architecture: Pydantic AI Core

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OUR LAYER: SKILLS + LEARNING                      │
│  • Skill definitions (YAML + code)                                   │
│  • Feedback collection & test generation                             │
│  • Metrics & health monitoring                                       │
│  • Configuration-driven behavior                                     │
│  • Multi-channel adapters (built on official SDKs)                   │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────┐
│                    PYDANTIC AI (THE FOUNDATION)                      │
├─────────────────────────────────────────────────────────────────────┤
│  • Type-safe structured outputs (Pydantic models)                    │
│  • Dependency injection for tools (easy mocking)                     │
│  • Function calling with validation                                  │
│  • Built on Pydantic (2.5B+ downloads, battle-tested)                │
│  • Active maintenance by Pydantic team                               │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────┐
│                    CHANNEL ADAPTERS (CUSTOM, SECURE)                 │
├───────────────┬───────────────┬───────────────┬─────────────────────┤
│    Slack      │   WhatsApp    │     Web       │      Email          │
│  (Bolt SDK)   │  (Meta SDK)   │ (WebSocket)   │   (SendGrid)        │
├───────────────┴───────────────┴───────────────┴─────────────────────┤
│  All built on official, audited SDKs - no unknown dependencies       │
└─────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────┐
│                    LLM PROVIDERS                                     │
│  Claude 3.5 Sonnet │ GPT-4 │ Gemini │ Local (Ollama)                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Pydantic AI (Pi.dev) Integration

### Why Pydantic AI

- **Type-safe agents**: Define inputs/outputs with Pydantic models
- **Structured outputs**: Guaranteed JSON schema compliance
- **Tool use**: Built-in function calling
- **Streaming**: Real-time responses
- **Testing**: Easy to mock and test

### Integration Pattern

```python
# agents/base.py - Pydantic AI as the agent foundation

from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Literal

# Structured output for fraud detection
class FraudDecision(BaseModel):
    action: Literal["block", "flag", "allow"]
    confidence: float
    reason: str
    affected_user_id: str
    affected_order_id: str | None

# Pydantic AI agent with type-safe output
fraud_agent = Agent(
    'claude-3-5-sonnet-20241022',
    result_type=FraudDecision,
    system_prompt="""You are a fraud detection agent for Aspora.
    Analyze the input and decide whether to block, flag, or allow.
    Always provide reasoning."""
)

# Usage in our skills layer
async def execute_fraud_skill(context: SkillContext) -> SkillResult:
    # Pydantic AI handles the LLM call with type safety
    result = await fraud_agent.run(context.input)

    # Our layer adds feedback collection
    await log_skill_execution(
        skill_name="fraud-detection",
        inputs=context.input,
        outputs=result.data.model_dump(),
        confidence=result.data.confidence
    )

    return SkillResult(
        success=True,
        outputs=result.data.model_dump(),
        reasoning=result.data.reason
    )
```

### Pydantic AI for Each Domain

```python
# Wealth Copilot
class TradeRecommendation(BaseModel):
    action: Literal["buy", "sell", "hold"]
    symbol: str
    quantity: float
    reasoning: str
    confidence: float
    risk_score: float

# Fraud Guardian
class FraudAlert(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    action: Literal["block_beneficiary", "blacklist_user", "flag_for_review"]
    affected_entities: list[str]
    evidence: list[str]

# Retention Agent
class ChurnIntervention(BaseModel):
    user_id: str
    churn_risk_score: float
    recommended_action: Literal["rate_alert", "bonus_offer", "human_outreach", "no_action"]
    expected_success_probability: float
    estimated_roi: float

# Support Triage
class EscalationClassification(BaseModel):
    issue_type: str
    severity: Literal["critical", "high", "medium", "low"]
    duplicate_of: str | None
    affected_users_count: int
    likely_source_files: list[str]
    recommended_priority: int
```

---

## Part 3: Multi-Channel Adapters (Custom, Secure)

### Why NOT OpenClaw

- **Security concern**: Too new, unaudited dependencies
- **Unknown attack surface**: No security audit history
- **Compliance risk**: Cannot verify data handling
- **Alternative**: Build on official, battle-tested SDKs

### Custom Channel Adapter Pattern

```typescript
// lib/channels/types.ts - Channel abstraction
interface ChannelAdapter {
  name: string;
  send(message: AgentResponse): Promise<void>;
  onMessage(handler: (msg: IncomingMessage) => Promise<void>): void;
}

interface IncomingMessage {
  channelType: 'slack' | 'whatsapp' | 'web' | 'email';
  userId: string;
  text: string;
  attachments?: Attachment[];
  threadId?: string;
}
```

### Slack Adapter (Built on Official Bolt SDK)

```typescript
// lib/channels/slack.ts
import { App } from '@slack/bolt';  // Official Slack SDK

export class SlackAdapter implements ChannelAdapter {
  name = 'slack';
  private app: App;

  constructor(config: SlackConfig) {
    this.app = new App({
      token: config.botToken,
      signingSecret: config.signingSecret,
    });
  }

  async send(message: AgentResponse): Promise<void> {
    await this.app.client.chat.postMessage({
      channel: message.channelId,
      text: message.text,
      thread_ts: message.threadId,
      blocks: this.formatBlocks(message),
    });
  }

  onMessage(handler: (msg: IncomingMessage) => Promise<void>): void {
    this.app.message(async ({ message, say }) => {
      await handler({
        channelType: 'slack',
        userId: message.user,
        text: message.text,
        threadId: message.thread_ts,
      });
    });
  }
}
```

### WhatsApp Adapter (Built on Meta Business SDK)

```typescript
// lib/channels/whatsapp.ts
import { WhatsAppBusinessAPI } from '@anthropic-ai/sdk';  // Or official Meta SDK

export class WhatsAppAdapter implements ChannelAdapter {
  name = 'whatsapp';

  async send(message: AgentResponse): Promise<void> {
    // Uses official Meta WhatsApp Business API
    await this.client.messages.send({
      to: message.recipient,
      type: 'text',
      text: { body: message.text },
    });
  }
}
```

### Channel Router (Unified Entry Point)

```typescript
// lib/channels/router.ts
export class ChannelRouter {
  private adapters: Map<string, ChannelAdapter> = new Map();

  register(adapter: ChannelAdapter): void {
    this.adapters.set(adapter.name, adapter);
  }

  async route(message: AgentResponse, channel: string): Promise<void> {
    const adapter = this.adapters.get(channel);
    if (!adapter) throw new Error(`Unknown channel: ${channel}`);
    await adapter.send(message);
  }
}

// Usage
const router = new ChannelRouter();
router.register(new SlackAdapter(slackConfig));
router.register(new WhatsAppAdapter(whatsappConfig));
router.register(new WebSocketAdapter(wsConfig));
```

---

## Part 4: Domain-Specific Agents

### Domain 1: Fraud Guardian

```yaml
# domains/fraud/plugin.yaml
---
domain: fraud
name: Fraud Guardian
description: Real-time fraud detection and response

triggers:
  - source: email
    pattern: "complaint|fraud|unauthorized"
  - source: metabase_alert
    dashboard: instant-nsf-alerts
  - source: column_webhook
    event: transaction.flagged

skills:
  - name: parse-complaint-email
    description: Extract order ID, user ID, complaint type from email

  - name: block-beneficiary
    description: Block beneficiary across TRM platforms
    requires_approval: true

  - name: blacklist-user
    description: Blacklist user for future instant transfers
    requires_approval: true

  - name: sync-to-trm
    description: Sync fraud decision to TRM platforms
    connectors: [trm-chainalysis, trm-elliptic]

workflows:
  complaint-to-block:
    trigger: email_complaint
    steps:
      - skill: parse-complaint-email
      - skill: lookup-order-details
      - skill: assess-fraud-risk
      - skill: block-beneficiary
        condition: risk_score > 0.8
      - skill: sync-to-trm
      - skill: notify-compliance-team
```

### Domain 2: Retention Agent

```yaml
# domains/retention/plugin.yaml
---
domain: retention
name: Retention Agent
description: Predict churn and automate win-back

data_sources:
  - name: churn_scores
    type: ml_model
    endpoint: /api/ml/churn-score
    refresh: daily

  - name: user_segments
    type: database
    query: SELECT * FROM user_segments WHERE updated_at > NOW() - INTERVAL '1 day'

skills:
  - name: score-churn-risk
    description: Get ML churn score (0-100) for user

  - name: select-intervention
    description: Choose best intervention based on segment and history
    playbooks:
      high_value_recent:
        - human_outreach
        - premium_rate_alert
      high_value_dormant:
        - bonus_offer
        - win_back_campaign
      low_value:
        - automated_rate_alert
        - no_action

  - name: estimate-intervention-roi
    description: Predict success probability and expected LTV gain

  - name: trigger-campaign
    description: Send intervention via appropriate channel
    channels: [email, push, sms, in_app]

  - name: track-outcome
    description: Record whether user transacted after intervention

workflows:
  daily-churn-sweep:
    schedule: "0 9 * * *"  # 9 AM daily
    steps:
      - skill: score-churn-risk
        for_each: active_users
      - skill: select-intervention
        condition: churn_score > 60
      - skill: estimate-intervention-roi
      - skill: trigger-campaign
        condition: expected_roi > intervention_cost
      - skill: track-outcome
        delay: 7_days
```

### Domain 3: Support Triage Agent

```yaml
# domains/support/plugin.yaml
---
domain: support
name: Support Triage Agent
description: Auto-classify and prioritize tech escalations

sources:
  - type: slack
    channel: tech-escalation
  - type: clickup
    list: support-issues

skills:
  - name: extract-error-details
    description: Parse post and extract error info (including from screenshots)
    uses: claude_vision

  - name: classify-issue-type
    description: Categorize issue (payment_rejection, kyc_failure, screen_error, etc.)

  - name: semantic-deduplicate
    description: Find similar existing issues
    uses: embeddings
    threshold: 0.85

  - name: trace-to-codebase
    description: Find likely source files using codebase RAG
    uses: codebase_agent

  - name: rank-by-impact
    description: Score by frequency * affected_users

  - name: generate-sprint-report
    description: Weekly prioritized issue list

workflows:
  continuous-triage:
    trigger: new_slack_message
    steps:
      - skill: extract-error-details
      - skill: classify-issue-type
      - skill: semantic-deduplicate
      - skill: trace-to-codebase
      - skill: rank-by-impact
      - action: reply_in_thread
        template: triage-summary

  weekly-report:
    schedule: "0 8 * * 1"  # Monday 8 AM
    steps:
      - skill: aggregate-weekly-issues
      - skill: rank-by-impact
      - skill: generate-sprint-report
      - action: post_to_channel
        channel: engineering-planning
```

---

## Part 5: Codebase RAG for Source Tracing

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CODEBASE INTELLIGENCE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    INDEXING PIPELINE                         │    │
│  │  1. Clone/pull repository                                    │    │
│  │  2. Parse code → AST (functions, classes, imports)           │    │
│  │  3. Generate embeddings per function/file                    │    │
│  │  4. Store in vector DB (Pinecone/Weaviate)                  │    │
│  │  5. Build dependency graph                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│  ┌───────────────────────────▼─────────────────────────────────┐    │
│  │                    QUERY PIPELINE                            │    │
│  │  1. Error message → embedding                                │    │
│  │  2. Semantic search for relevant code                        │    │
│  │  3. Follow imports/dependencies                              │    │
│  │  4. LLM reasoning: "Given this error, which code?"           │    │
│  │  5. Return ranked file:line:function list                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# skills/support/trace-to-codebase.py

from pydantic_ai import Agent
from pydantic import BaseModel

class CodeLocation(BaseModel):
    file: str
    line: int
    function: str
    confidence: float
    reasoning: str

class CodeTraceResult(BaseModel):
    locations: list[CodeLocation]
    search_queries_used: list[str]
    files_examined: int

codebase_agent = Agent(
    'claude-3-5-sonnet-20241022',
    result_type=CodeTraceResult,
    system_prompt="""You are a codebase expert for Aspora.
    Given an error description, find the likely source code locations.
    Use the provided code search tools."""
)

@codebase_agent.tool
async def search_code(query: str) -> list[dict]:
    """Semantic search over codebase embeddings"""
    results = await vector_db.search(
        collection="aspora_codebase",
        query=query,
        top_k=10
    )
    return [
        {
            "file": r.metadata["file"],
            "line": r.metadata["line"],
            "function": r.metadata["function"],
            "snippet": r.metadata["snippet"],
            "score": r.score
        }
        for r in results
    ]

@codebase_agent.tool
async def get_file_content(file_path: str) -> str:
    """Get full file content for deeper analysis"""
    return await repo.read_file(file_path)

@codebase_agent.tool
async def get_function_callers(function_name: str) -> list[dict]:
    """Find all places that call this function"""
    return await dependency_graph.get_callers(function_name)

# Usage
async def trace_error_to_code(error: ExtractedError) -> CodeTraceResult:
    result = await codebase_agent.run(f"""
        Error: {error.message}
        Error Code: {error.code}
        Screen: {error.screen}

        Find the likely source code locations that could cause this error.
        Consider:
        1. Error message text matching
        2. Screen/route name matching
        3. Error code definitions
        4. Related API endpoints
    """)
    return result.data
```

---

## Part 6: Platform SDK for Teams

### SDK Design

```typescript
// @aspora/agent-sdk

// Define a new domain agent
import { defineAgent, defineSkill, defineTrigger } from '@aspora/agent-sdk';

// 1. Define skills
const parseEmailSkill = defineSkill({
  name: 'parse-complaint-email',
  description: 'Extract order ID and complaint type from email',

  input: z.object({
    emailBody: z.string(),
    subject: z.string(),
    from: z.string(),
  }),

  output: z.object({
    orderId: z.string().optional(),
    userId: z.string().optional(),
    complaintType: z.enum(['fraud', 'unauthorized', 'failed_transaction', 'other']),
    urgency: z.enum(['critical', 'high', 'medium', 'low']),
  }),

  async execute(input, context) {
    // Use Pydantic AI under the hood
    const result = await context.llm.structured({
      prompt: `Parse this complaint email...`,
      schema: this.output,
    });
    return result;
  },

  tests: [
    {
      name: 'fraud_complaint',
      input: { emailBody: 'I did not authorize order #12345...', subject: 'Fraud', from: 'user@email.com' },
      expected: { orderId: '12345', complaintType: 'fraud', urgency: 'critical' },
    },
  ],
});

// 2. Define triggers
const emailTrigger = defineTrigger({
  type: 'email',
  filter: {
    to: 'complaints@aspora.com',
    subject: /fraud|unauthorized|complaint/i,
  },
});

const metabaseAlertTrigger = defineTrigger({
  type: 'webhook',
  source: 'metabase',
  event: 'alert.fired',
  filter: {
    dashboard: 'instant-nsf-alerts',
  },
});

// 3. Define the agent
export const fraudGuardian = defineAgent({
  name: 'fraud-guardian',
  description: 'Real-time fraud detection and response',

  triggers: [emailTrigger, metabaseAlertTrigger],

  skills: [
    parseEmailSkill,
    blockBeneficiarySkill,
    blacklistUserSkill,
    syncToTrmSkill,
  ],

  workflows: {
    'complaint-to-block': {
      trigger: 'email',
      steps: [
        { skill: 'parse-complaint-email' },
        { skill: 'lookup-order-details' },
        { skill: 'assess-fraud-risk' },
        {
          skill: 'block-beneficiary',
          condition: (ctx) => ctx.results['assess-fraud-risk'].risk_score > 0.8,
          requiresApproval: true,
        },
        { skill: 'sync-to-trm' },
        { skill: 'notify-compliance-team' },
      ],
    },
  },
});
```

### CLI for Teams

```bash
# Create new domain agent
npx @aspora/agent-sdk create fraud-guardian

# Add a skill
npx @aspora/agent-sdk skill add parse-complaint-email

# Run tests
npx @aspora/agent-sdk test

# Deploy to platform
npx @aspora/agent-sdk deploy --env staging

# Monitor
npx @aspora/agent-sdk monitor fraud-guardian
```

---

## Part 7: Unified Feedback Loop

### Cross-Domain Learning

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED FEEDBACK SYSTEM                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DOMAIN: Wealth          DOMAIN: Fraud         DOMAIN: Support       │
│  ┌─────────────────┐    ┌─────────────────┐   ┌─────────────────┐   │
│  │ trade-suggest   │    │ fraud-detect    │   │ issue-classify  │   │
│  │ approval: 78%   │    │ accuracy: 94%   │   │ accuracy: 86%   │   │
│  │ tests: 45       │    │ tests: 32       │   │ tests: 28       │   │
│  └────────┬────────┘    └────────┬────────┘   └────────┬────────┘   │
│           │                      │                      │            │
│           └──────────────────────┼──────────────────────┘            │
│                                  │                                    │
│  ┌───────────────────────────────▼───────────────────────────────┐   │
│  │                 SHARED LEARNING INFRASTRUCTURE                 │   │
│  │  • Execution logs (all domains)                                │   │
│  │  • User corrections → test cases                               │   │
│  │  • Cross-domain patterns (e.g., fraud signals in support)      │   │
│  │  • Skill health dashboard                                      │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Metrics Dashboard

```typescript
// All domains report to unified metrics

interface DomainMetrics {
  domain: string;
  skills: SkillMetrics[];
  workflows: WorkflowMetrics[];
  feedback: {
    totalExecutions: number;
    approvalRate: number;
    correctionRate: number;
    autoGeneratedTests: number;
  };
}

// Example output
{
  "domains": [
    {
      "domain": "wealth",
      "skills": [
        { "name": "trade-suggest", "approvalRate": 0.78, "avgLatency": 1200 },
        { "name": "rebalance", "approvalRate": 0.85, "avgLatency": 2400 }
      ],
      "feedback": { "totalExecutions": 1250, "autoGeneratedTests": 45 }
    },
    {
      "domain": "fraud",
      "skills": [
        { "name": "fraud-detect", "accuracy": 0.94, "falsePositiveRate": 0.03 },
        { "name": "block-beneficiary", "executionRate": 0.12 }
      ],
      "feedback": { "totalExecutions": 890, "autoGeneratedTests": 32 }
    },
    {
      "domain": "support",
      "skills": [
        { "name": "issue-classify", "accuracy": 0.86 },
        { "name": "trace-to-codebase", "relevanceScore": 0.72 }
      ],
      "feedback": { "totalExecutions": 340, "autoGeneratedTests": 28 }
    }
  ]
}
```

---

## Part 8: Hackathon Strategy (Updated)

### What to Build in 48 Hours

```
HOUR 0-24: CORE PLATFORM
├── Skills runtime (shared across domains)
├── Feedback collection system
├── Pydantic AI integration
├── Basic UI shell

HOUR 24-36: WEALTH COPILOT (Primary Demo)
├── Trading skills
├── Goal tracking
├── Chat interface
├── Multi-agent panel

HOUR 36-44: ONE MORE DOMAIN (Show Extensibility)
├── Fraud Guardian OR Support Triage
├── 3-4 skills
├── Slack integration (OpenClaw)
├── Basic workflow

HOUR 44-48: DEMO POLISH
├── Unified dashboard showing both domains
├── Metrics across domains
├── "Add your own domain" pitch
```

### Demo Script (Updated)

```
MINUTE 0:00-1:00 — WEALTH COPILOT
"Our AI wealth manager for NRIs..."
[Show trading, goals, multi-agent collaboration]

MINUTE 1:00-2:00 — PLATFORM POWER
"But here's what's really powerful..."
[Show Fraud Guardian auto-blocking from email complaint]
[Show Support Triage classifying Slack escalation]

MINUTE 2:00-2:30 — EXTENSIBILITY
"Any Aspora team can build on this..."
[Show SDK: `defineAgent`, `defineSkill`]
[Show unified metrics dashboard]

MINUTE 2:30-3:00 — THE MOAT
"Skills are trainable. Feedback is automatic.
Every domain gets smarter together."
```

---

## Summary

| Component | Technology | Purpose | Security |
|-----------|------------|---------|----------|
| **Agent Core** | Pydantic AI (Pi.dev) | Type-safe agents, structured outputs | ✅ Battle-tested |
| **Multi-Channel** | Custom adapters (official SDKs) | Slack, WhatsApp, Web delivery | ✅ Audited SDKs |
| **Vision** | Claude Computer Use | Screenshot analysis, error extraction | ✅ Anthropic |
| **Codebase RAG** | Embeddings + LLM | Trace errors to source code | ✅ Self-hosted |
| **Skills Layer** | Custom (our moat) | Trainable, testable, learnable | ✅ Full control |
| **Feedback Loop** | Unified system | Cross-domain learning | ✅ Self-hosted |

**The pitch:** "We didn't just build a wealth app. We built a platform. Fraud team can use it. Support team can use it. Retention team can use it. Every skill gets smarter with every interaction. And it's built on battle-tested foundations — no unproven frameworks."

---

*This is how you win: show a platform, not just an app. A secure, reliable platform.*
