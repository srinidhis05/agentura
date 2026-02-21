# Aspora Platform SDK — Skill Marketplace Architecture

> **Platform Vision**: Any team can build, test, deploy, and monetize skills on Aspora — like Shopify apps or VS Code extensions.
> **Designed**: 2026-02-16

---

## Platform Mindset Shift

### From Application to Platform

**Before** (Application thinking):
```
Wealth Copilot team builds all skills → Tight coupling → Slow iteration
```

**After** (Platform thinking):
```
┌─────────────────────────────────────────────────────────────┐
│                    ASPORA SKILL MARKETPLACE                  │
├─────────────────────────────────────────────────────────────┤
│  Wealth Team    │  Fraud Team   │  ECM Team   │  External   │
│  builds wealth  │  builds fraud │  builds dev │  developers │
│  skills         │  skills       │  skills     │  build custom│
└─────────────────────────────────────────────────────────────┘
          ↓               ↓              ↓             ↓
┌─────────────────────────────────────────────────────────────┐
│              ASPORA PLATFORM (Shared Infrastructure)         │
│  • Skill Runtime  • Model Gateway  • Monitoring  • Billing  │
└─────────────────────────────────────────────────────────────┘
```

---

## Platform Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                    DEVELOPER EXPERIENCE LAYER                      │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Aspora CLI  │  │ Skill Studio │  │  Dev Portal  │           │
│  │              │  │  (Web IDE)   │  │ (Docs+Tests) │           │
│  │ $ aspora     │  │              │  │              │           │
│  │   create     │  │  Live reload │  │  Analytics   │           │
│  │   test       │  │  Playground  │  │  Marketplace │           │
│  │   deploy     │  │  Debug tools │  │  Billing     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    SKILL REGISTRY & DISCOVERY                      │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Skill Metadata Store (PostgreSQL)                       │    │
│  │  • skill_id, name, version, domain                       │    │
│  │  • description (for LLM discovery)                       │    │
│  │  • triggers (message, cron, alert, command)              │    │
│  │  • model_preference (haiku, sonnet, opus, custom)        │    │
│  │  • cost_budgets (max_tokens, max_cost_per_run)           │    │
│  │  • owner_team, visibility (public, private, internal)    │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Skill Code Store (S3/R2)                                │    │
│  │  s3://aspora-skills/{domain}/{skill_name}/{version}/     │    │
│  │  ├── SKILL.md                                            │    │
│  │  ├── DECISIONS.md                                        │    │
│  │  ├── GUARDRAILS.md                                       │    │
│  │  ├── code/ (TypeScript/Python/Go)                        │    │
│  │  └── tests/                                              │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    EXECUTION RUNTIME                               │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Sandbox    │  │  Skill Cache │  │ Tool Library │           │
│  │ (Firecracker)│  │   (Redis)    │  │  (Built-in)  │           │
│  │              │  │              │  │              │           │
│  │ Isolated VM  │  │ Hot skills   │  │ • Read       │           │
│  │ CPU/mem caps │  │ Fast startup │  │ • Write      │           │
│  │ Network jail │  │ Evict LRU    │  │ • Bash       │           │
│  └──────────────┘  └──────────────┘  │ • WebFetch   │           │
│                                       │ • Grep       │           │
│                                       │ • Custom...  │           │
│                                       └──────────────┘           │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    MODEL GATEWAY (OpenRouter)                      │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Router Logic                                            │    │
│  │  • Task complexity → Model selection                     │    │
│  │  • Cost optimization (Haiku for routing, Sonnet for work)│    │
│  │  • Automatic fallback (primary fails → secondary)        │    │
│  │  • Rate limiting per domain/skill                        │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐   │
│  │  Claude 4.5  │   GPT-4o     │  Gemini 2.0  │   Custom    │   │
│  │  (via OR)    │  (via OR)    │  (via OR)    │   Models    │   │
│  └──────────────┴──────────────┴──────────────┴─────────────┘   │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    OBSERVABILITY & MONITORING                      │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │    Opik      │  │  Langfuse    │  │  Prometheus  │           │
│  │  (Tracing)   │  │  (Logging)   │  │  (Metrics)   │           │
│  │              │  │              │  │              │           │
│  │ Execution    │  │ Conversations│  │ • Latency    │           │
│  │ traces       │  │ Feedback     │  │ • Error rate │           │
│  │ Tool calls   │  │ Corrections  │  │ • Token cost │           │
│  └──────────────┘  └──────────────┘  │ • Success %  │           │
│                                       └──────────────┘           │
└───────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Developer SDK

### 1.1 Aspora CLI

```bash
# Install globally
npm install -g @aspora/cli

# Create new skill
aspora create skill fraud/block-transaction

# Output:
# ✓ Created skills/fraud/block-transaction/
# ├── SKILL.md (with YAML frontmatter template)
# ├── DECISIONS.md
# ├── GUARDRAILS.md
# ├── code/
# │   └── handler.ts (or .py, .go based on preference)
# ├── tests/
# │   └── block-transaction.test.ts
# └── aspora.config.yaml

# Test locally
aspora test fraud/block-transaction

# Deploy to staging
aspora deploy --env staging fraud/block-transaction

# Deploy to production
aspora deploy --env production fraud/block-transaction

# Monitor
aspora logs fraud/block-transaction --follow
aspora metrics fraud/block-transaction --last 24h
```

### 1.2 Skill Template (Language-Agnostic)

**Directory Structure**:
```
skills/{domain}/{skill-name}/
├── SKILL.md                 # LLM instructions (YAML frontmatter)
├── DECISIONS.md             # Architecture decisions
├── GUARDRAILS.md            # What to NEVER do
├── code/                    # Deterministic logic
│   ├── handler.ts|.py|.go   # Main entry point
│   ├── utils/               # Helper functions
│   └── integrations/        # External APIs
├── tests/
│   ├── unit/                # Code tests
│   └── deepeval/            # LLM tests
├── assets/                  # Templates, data files
└── aspora.config.yaml       # Skill configuration
```

**aspora.config.yaml**:
```yaml
# Skill metadata
skill:
  name: block-transaction
  domain: fraud
  version: 1.0.0
  description: >
    Blocks suspicious transactions and syncs with TRM.
    Use when fraud score > 0.8 or user flags transaction.
    Do NOT use for chargebacks or refund disputes.

# Runtime configuration
runtime:
  language: typescript  # typescript | python | go
  entry_point: code/handler.ts
  timeout: 30s
  memory: 512MB
  cpu: 0.5

# Model preferences
model:
  primary: claude-sonnet-4-5      # Via OpenRouter
  fallback: gpt-4o-mini            # Via OpenRouter
  temperature: 0.3
  max_tokens: 4096
  cost_budget:
    max_per_execution: 0.10       # $0.10 max per run
    monthly_limit: 1000.00        # $1000/month cap

# Triggers
triggers:
  - type: message
    patterns:
      - "fraud"
      - "suspicious transaction"
      - "block this payment"

  - type: alert
    sources: [datadog, pagerduty]
    filters:
      severity: [critical, high]
      tags: [fraud, high_risk]

  - type: cron
    schedule: "0 * * * *"  # Hourly
    enabled: true

# Permissions (what tools/APIs this skill can access)
permissions:
  tools: [Read, Write, Bash]
  apis:
    - trm_api
    - internal_fraud_db
  secrets:
    - TRM_API_KEY
    - FRAUD_DB_URL

# Testing
testing:
  deepeval:
    metrics: [AnswerRelevancy, Faithfulness, Correctness]
    threshold: 0.8

  promptfoo:
    compare_versions: true
    test_cases: tests/deepeval/*.yaml

# Versioning
versioning:
  strategy: semver  # semver | timestamp
  rollback_on_error: true
  canary_percentage: 10  # 10% traffic to new version first

# Monitoring
monitoring:
  success_rate_threshold: 0.95
  latency_p95_threshold: 3000  # 3 seconds
  alert_on_failure: true
  alert_channels: [slack, pagerduty]

# Multi-tenancy
visibility: internal  # public | private | internal
owner_team: fraud-team
cost_center: fraud-detection
```

### 1.3 Code Handler Interface

**TypeScript**:
```typescript
// code/handler.ts
import { AsporaSkillHandler, SkillContext, SkillResult } from '@aspora/sdk';

export const handler: AsporaSkillHandler = async (
  context: SkillContext
): Promise<SkillResult> => {
  // 1. Access skill inputs
  const { userMessage, userId, domain } = context.input;

  // 2. Access tools (Read, Write, Bash, etc.)
  const decisions = await context.tools.read({
    path: 'DECISIONS.md',
  });

  // 3. Call external APIs (with automatic rate limiting)
  const fraudScore = await context.apis.trm.checkTransaction({
    transactionId: context.input.metadata.transactionId,
  });

  // 4. Execute deterministic logic
  if (fraudScore > 0.8) {
    await context.apis.internal_fraud_db.blockTransaction({
      transactionId: context.input.metadata.transactionId,
      reason: 'High fraud score',
    });

    return {
      success: true,
      message: '🚫 Transaction blocked due to high fraud score',
      data: {
        fraudScore,
        action: 'blocked',
      },
      confidence: 0.95,
    };
  }

  return {
    success: true,
    message: '✅ Transaction approved',
    data: { fraudScore, action: 'approved' },
    confidence: 0.85,
  };
};

// Optional: Define custom tools for this skill
export const tools = {
  async syncToTRM(transactionId: string) {
    // Custom tool logic
  },
};
```

**Python**:
```python
# code/handler.py
from aspora_sdk import SkillContext, SkillResult, skill_handler

@skill_handler
async def handler(context: SkillContext) -> SkillResult:
    """Block suspicious transactions"""

    # Access inputs
    user_message = context.input.user_message
    transaction_id = context.input.metadata["transaction_id"]

    # Call TRM API (auto rate-limited)
    fraud_score = await context.apis.trm.check_transaction(
        transaction_id=transaction_id
    )

    # Deterministic logic
    if fraud_score > 0.8:
        await context.apis.fraud_db.block_transaction(
            transaction_id=transaction_id,
            reason="High fraud score"
        )

        return SkillResult(
            success=True,
            message="🚫 Transaction blocked due to high fraud score",
            data={"fraud_score": fraud_score, "action": "blocked"},
            confidence=0.95,
        )

    return SkillResult(
        success=True,
        message="✅ Transaction approved",
        data={"fraud_score": fraud_score, "action": "approved"},
        confidence=0.85,
    )
```

**Go**:
```go
// code/handler.go
package main

import (
    aspora "github.com/aspora/sdk-go"
)

func Handler(ctx *aspora.SkillContext) (*aspora.SkillResult, error) {
    // Access inputs
    transactionID := ctx.Input.Metadata["transaction_id"].(string)

    // Call TRM API
    fraudScore, err := ctx.APIs.TRM.CheckTransaction(transactionID)
    if err != nil {
        return nil, err
    }

    // Deterministic logic
    if fraudScore > 0.8 {
        err := ctx.APIs.FraudDB.BlockTransaction(transactionID, "High fraud score")
        if err != nil {
            return nil, err
        }

        return &aspora.SkillResult{
            Success: true,
            Message: "🚫 Transaction blocked due to high fraud score",
            Data: map[string]interface{}{
                "fraud_score": fraudScore,
                "action": "blocked",
            },
            Confidence: 0.95,
        }, nil
    }

    return &aspora.SkillResult{
        Success: true,
        Message: "✅ Transaction approved",
        Data: map[string]interface{}{
            "fraud_score": fraudScore,
            "action": "approved",
        },
        Confidence: 0.85,
    }, nil
}
```

---

## Part 2: Skill Registry & Discovery

### 2.1 Database Schema

```sql
-- PostgreSQL schema for skill marketplace

CREATE TABLE skills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  domain VARCHAR(100) NOT NULL,
  version VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,  -- For LLM discovery

  owner_team VARCHAR(100) NOT NULL,
  visibility VARCHAR(20) CHECK (visibility IN ('public', 'private', 'internal')),

  -- Runtime config
  runtime_language VARCHAR(20) CHECK (runtime_language IN ('typescript', 'python', 'go')),
  entry_point TEXT NOT NULL,
  timeout_seconds INT DEFAULT 30,
  memory_mb INT DEFAULT 512,
  cpu_cores DECIMAL(3,2) DEFAULT 0.5,

  -- Model config
  primary_model VARCHAR(100) DEFAULT 'claude-sonnet-4-5',
  fallback_model VARCHAR(100),
  temperature DECIMAL(3,2) DEFAULT 0.7,
  max_tokens INT DEFAULT 4096,

  -- Cost budgets
  cost_per_execution_limit DECIMAL(10,4),
  monthly_cost_limit DECIMAL(10,2),

  -- Storage
  code_s3_path TEXT NOT NULL,

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deployed_at TIMESTAMP,

  UNIQUE(domain, name, version)
);

CREATE INDEX idx_skills_domain ON skills(domain);
CREATE INDEX idx_skills_visibility ON skills(visibility);
CREATE INDEX idx_skills_owner ON skills(owner_team);

-- Skill triggers
CREATE TABLE skill_triggers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,

  trigger_type VARCHAR(20) CHECK (trigger_type IN ('message', 'cron', 'alert', 'command')),

  -- For message triggers
  patterns TEXT[],  -- Array of trigger phrases

  -- For cron triggers
  cron_schedule VARCHAR(100),
  cron_enabled BOOLEAN DEFAULT true,

  -- For alert triggers
  alert_sources TEXT[],  -- [datadog, pagerduty]
  alert_filters JSONB,   -- {severity: ['critical'], tags: ['fraud']}

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_triggers_skill ON skill_triggers(skill_id);
CREATE INDEX idx_triggers_type ON skill_triggers(trigger_type);

-- Skill permissions
CREATE TABLE skill_permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,

  allowed_tools TEXT[],  -- [Read, Write, Bash, WebFetch]
  allowed_apis TEXT[],   -- [trm_api, fraud_db, column_api]
  required_secrets TEXT[],  -- [TRM_API_KEY, DB_URL]

  created_at TIMESTAMP DEFAULT NOW()
);

-- Skill execution logs (for monitoring)
CREATE TABLE skill_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID REFERENCES skills(id),

  user_id VARCHAR(255),
  trigger_type VARCHAR(20),

  -- Execution metrics
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  duration_ms INT,

  success BOOLEAN,
  error_message TEXT,

  -- Model usage
  model_used VARCHAR(100),
  prompt_tokens INT,
  completion_tokens INT,
  total_cost DECIMAL(10,6),

  -- User feedback
  user_rating INT CHECK (user_rating BETWEEN 1 AND 5),
  user_correction TEXT,

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_executions_skill ON skill_executions(skill_id);
CREATE INDEX idx_executions_user ON skill_executions(user_id);
CREATE INDEX idx_executions_success ON skill_executions(success);
CREATE INDEX idx_executions_created ON skill_executions(created_at DESC);

-- Skill versions (for rollback)
CREATE TABLE skill_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,

  version VARCHAR(50) NOT NULL,
  code_s3_path TEXT NOT NULL,
  deployed_at TIMESTAMP,
  rolled_back_at TIMESTAMP,

  -- Canary deployment
  is_canary BOOLEAN DEFAULT false,
  canary_percentage INT,
  canary_success_rate DECIMAL(5,4),

  created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 Skill Discovery API

```typescript
// Platform API for LLM to discover skills
interface SkillDiscoveryAPI {
  // List all skills for a domain
  listSkills(domain: string): Promise<SkillMetadata[]>;

  // Search skills by description (semantic search)
  searchSkills(query: string): Promise<SkillMetadata[]>;

  // Get full skill details
  getSkill(skillId: string): Promise<Skill>;

  // Load skill for execution
  loadSkill(skillId: string, version?: string): Promise<LoadedSkill>;
}

// Example usage in domain classifier agent
const classifier = Agent(
  'claude-haiku-4-5',
  result_type=DomainClassification,
  system_prompt=`You have access to skill discovery API.

When user sends message, determine which skill to use:

1. Classify domain (wealth, fraud, ecm, retention, support, ops)
2. Search skills in that domain: await searchSkills(query)
3. Return best matching skill

Available skills are discovered dynamically — you don't need to know them upfront.
`,
);
```

---

## Part 3: OpenRouter Integration

### 3.1 Model Gateway Architecture

```typescript
// packages/model-gateway/openrouter.ts
import OpenAI from 'openai';

export class OpenRouterGateway {
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({
      baseURL: 'https://openrouter.ai/api/v1',
      apiKey,
      defaultHeaders: {
        'HTTP-Referer': 'https://aspora.dev',
        'X-Title': 'Aspora Skills Platform',
      },
    });
  }

  async complete(params: ModelRequest): Promise<ModelResponse> {
    const { task, skillConfig, fallbackStrategy } = params;

    // 1. Select model based on task complexity
    const primaryModel = this.selectModel(task, skillConfig);

    try {
      // 2. Execute with primary model
      const response = await this.client.chat.completions.create({
        model: primaryModel,
        messages: task.messages,
        temperature: skillConfig.temperature ?? 0.7,
        max_tokens: skillConfig.max_tokens ?? 4096,
      });

      // 3. Track cost
      await this.trackCost({
        skillId: task.skillId,
        model: primaryModel,
        usage: response.usage,
      });

      return this.parseResponse(response);

    } catch (error) {
      // 4. Fallback to secondary model
      if (fallbackStrategy === 'auto') {
        console.warn(`Primary model ${primaryModel} failed, trying fallback`);
        return this.executeWithFallback(params);
      }
      throw error;
    }
  }

  private selectModel(task: ModelTask, config: SkillConfig): string {
    // Smart model selection based on task
    if (config.primary_model) {
      return this.mapToOpenRouter(config.primary_model);
    }

    // Auto-select based on task type
    if (task.type === 'classification' || task.type === 'routing') {
      return 'anthropic/claude-haiku-4-5';  // Fast, cheap
    }

    if (task.type === 'skill_execution') {
      return 'anthropic/claude-sonnet-4-5';  // Balanced
    }

    if (task.type === 'complex_reasoning') {
      return 'anthropic/claude-opus-4-6';  // Powerful
    }

    return 'anthropic/claude-sonnet-4-5';  // Default
  }

  private mapToOpenRouter(model: string): string {
    const mapping: Record<string, string> = {
      'claude-haiku-4-5': 'anthropic/claude-haiku-4-5',
      'claude-sonnet-4-5': 'anthropic/claude-sonnet-4-5-20250929',
      'claude-opus-4-6': 'anthropic/claude-opus-4-6',
      'gpt-4o': 'openai/gpt-4o',
      'gpt-4o-mini': 'openai/gpt-4o-mini',
      'gemini-2.0-flash': 'google/gemini-2.0-flash-exp:free',
    };

    return mapping[model] ?? model;
  }

  private async executeWithFallback(params: ModelRequest): Promise<ModelResponse> {
    const fallbackModel = params.skillConfig.fallback_model ?? 'gpt-4o-mini';

    console.log(`Executing with fallback model: ${fallbackModel}`);

    const response = await this.client.chat.completions.create({
      model: this.mapToOpenRouter(fallbackModel),
      messages: params.task.messages,
      temperature: params.skillConfig.temperature ?? 0.7,
      max_tokens: params.skillConfig.max_tokens ?? 4096,
    });

    await this.trackCost({
      skillId: params.task.skillId,
      model: fallbackModel,
      usage: response.usage,
      is_fallback: true,
    });

    return this.parseResponse(response);
  }

  private async trackCost(data: CostTrackingData) {
    // Track to PostgreSQL + Prometheus
    await db.skill_costs.create({
      skill_id: data.skillId,
      model: data.model,
      prompt_tokens: data.usage.prompt_tokens,
      completion_tokens: data.usage.completion_tokens,
      total_cost: this.calculateCost(data.model, data.usage),
      is_fallback: data.is_fallback ?? false,
      timestamp: new Date(),
    });
  }

  private calculateCost(model: string, usage: any): number {
    // OpenRouter pricing (simplified)
    const pricing: Record<string, { prompt: number; completion: number }> = {
      'anthropic/claude-haiku-4-5': { prompt: 0.25, completion: 1.25 },  // per 1M tokens
      'anthropic/claude-sonnet-4-5-20250929': { prompt: 3.0, completion: 15.0 },
      'anthropic/claude-opus-4-6': { prompt: 15.0, completion: 75.0 },
      'openai/gpt-4o-mini': { prompt: 0.15, completion: 0.60 },
      'openai/gpt-4o': { prompt: 2.5, completion: 10.0 },
    };

    const modelPricing = pricing[model] ?? { prompt: 1.0, completion: 3.0 };

    const promptCost = (usage.prompt_tokens / 1_000_000) * modelPricing.prompt;
    const completionCost = (usage.completion_tokens / 1_000_000) * modelPricing.completion;

    return promptCost + completionCost;
  }
}
```

### 3.2 Cost Optimization Rules

```yaml
# Platform-level cost optimization config

cost_optimization:
  # Auto-select cheaper models for simple tasks
  auto_downgrade:
    enabled: true
    rules:
      - if: task.type == 'classification'
        use: claude-haiku-4-5

      - if: task.input_tokens < 1000 AND task.complexity == 'low'
        use: gpt-4o-mini

      - if: task.requires_reasoning == true
        use: claude-sonnet-4-5

  # Rate limiting per skill
  rate_limits:
    per_skill_per_hour: 1000
    per_domain_per_day: 10000
    per_platform_per_month: 1000000

  # Budget alerts
  alerts:
    - threshold: 80%  # of monthly budget
      action: notify_owner_team

    - threshold: 95%
      action: throttle_skill

    - threshold: 100%
      action: pause_skill

  # Caching strategy
  caching:
    enabled: true
    ttl: 3600  # 1 hour
    cache_keys:
      - skill_id
      - user_input_hash  # Semantic dedup
```

---

## Part 4: Observability Dashboard

### 4.1 Metrics Hierarchy

```
Platform Level
├── Total skills deployed
├── Total executions today/week/month
├── Platform success rate
├── Platform cost (total spend)
└── Platform latency (p50, p95, p99)

Domain Level (Wealth, Fraud, ECM, etc.)
├── Skills in domain
├── Executions per domain
├── Domain success rate
├── Domain cost
└── Domain latency

Skill Level (create-goal, block-transaction, etc.)
├── Executions (count)
├── Success rate (%)
├── Latency (p50, p95, p99)
├── Cost ($ per execution, total)
├── User satisfaction (thumbs up/down ratio)
├── Test coverage (# of DeepEval tests, pass rate)
└── Error rate (% of failures)
```

### 4.2 Dashboard UI (Grafana/Custom)

```yaml
# Grafana dashboard config
dashboard:
  title: "Aspora Skills Platform"

  panels:
    - title: "Skill Health Overview"
      type: table
      query: |
        SELECT
          s.domain,
          s.name,
          COUNT(e.id) as executions_24h,
          AVG(CASE WHEN e.success THEN 1.0 ELSE 0.0 END as success_rate,
          PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY e.duration_ms) as p95_latency,
          SUM(e.total_cost) as cost_24h
        FROM skills s
        LEFT JOIN skill_executions e ON s.id = e.skill_id
        WHERE e.created_at > NOW() - INTERVAL '24 hours'
        GROUP BY s.domain, s.name
        ORDER BY executions_24h DESC

    - title: "Cost by Domain"
      type: pie_chart
      query: |
        SELECT
          s.domain,
          SUM(e.total_cost) as total_cost
        FROM skills s
        JOIN skill_executions e ON s.id = e.skill_id
        WHERE e.created_at > NOW() - INTERVAL '7 days'
        GROUP BY s.domain

    - title: "User Satisfaction"
      type: gauge
      query: |
        SELECT
          AVG(user_rating) as avg_rating
        FROM skill_executions
        WHERE user_rating IS NOT NULL
          AND created_at > NOW() - INTERVAL '7 days'

    - title: "Top Errors"
      type: logs
      query: |
        SELECT
          s.name,
          e.error_message,
          COUNT(*) as error_count
        FROM skill_executions e
        JOIN skills s ON s.id = e.skill_id
        WHERE e.success = false
          AND e.created_at > NOW() - INTERVAL '24 hours'
        GROUP BY s.name, e.error_message
        ORDER BY error_count DESC
        LIMIT 10
```

### 4.3 Real-Time Alerts

```python
# agents/monitoring/alerting.py
from dataclasses import dataclass
from typing import List

@dataclass
class AlertRule:
    name: str
    condition: str  # SQL WHERE clause
    threshold: float
    channels: List[str]  # [slack, pagerduty, email]

# Platform alerts
ALERTS = [
    AlertRule(
        name="High Error Rate",
        condition="""
            SELECT AVG(CASE WHEN success THEN 0 ELSE 1 END) as error_rate
            FROM skill_executions
            WHERE created_at > NOW() - INTERVAL '5 minutes'
        """,
        threshold=0.05,  # 5% error rate
        channels=["slack", "pagerduty"],
    ),

    AlertRule(
        name="Cost Spike",
        condition="""
            SELECT SUM(total_cost)
            FROM skill_executions
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """,
        threshold=100.0,  # $100/hour
        channels=["slack", "email"],
    ),

    AlertRule(
        name="Latency Degradation",
        condition="""
            SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)
            FROM skill_executions
            WHERE created_at > NOW() - INTERVAL '5 minutes'
        """,
        threshold=5000,  # 5 seconds p95
        channels=["slack"],
    ),
]

async def check_alerts():
    """Run every minute"""
    for rule in ALERTS:
        result = await db.query(rule.condition)
        value = result[0][0]

        if value > rule.threshold:
            await notify_channels(
                channels=rule.channels,
                alert=f"🚨 {rule.name}: {value} (threshold: {rule.threshold})"
            )
```

---

## Part 5: Platform Buildability

### Can This Be Built Alongside Existing Work?

**YES** — Modular architecture allows incremental buildout.

### Phase 1: MVP Platform (2 weeks)

**Week 1**: Core platform
- ✅ Skill registry (PostgreSQL schema)
- ✅ Aspora CLI (`create`, `test`, `deploy` commands)
- ✅ OpenRouter gateway (model selection + fallback)
- ✅ Basic observability (Prometheus metrics)

**Week 2**: First domain (Wealth)
- ✅ Migrate existing Wealth Copilot to platform
- ✅ 3 skills: create-goal, suggest-allocation, fx-timing
- ✅ DeepEval test suite
- ✅ Dashboard (Grafana)

### Phase 2: Multi-Domain (2 weeks)

**Week 3**: Onboard Fraud + ECM
- ✅ Fraud team deploys 3 skills via CLI
- ✅ ECM team deploys 2 skills
- ✅ Cross-domain testing

**Week 4**: Advanced features
- ✅ Canary deployments
- ✅ Cost budgets + alerts
- ✅ Skill versioning + rollback

### Parallel Workstreams

| Team | Work | Dependencies |
|------|------|--------------|
| **Platform Team** | Build registry, CLI, gateway | None (greenfield) |
| **Wealth Team** | Continue building wealth skills | Migrate to platform Week 2 |
| **Fraud Team** | Build fraud skills in sandbox | Onboard to platform Week 3 |
| **ECM Team** | Build ECM skills locally | Onboard to platform Week 3 |

**NO BLOCKERS** — teams can build skills independently, platform team builds infrastructure in parallel.

---

## Summary: Platform Benefits

| Capability | Without Platform | With Platform |
|------------|-----------------|---------------|
| **Skill Deployment** | Manual copy-paste, coordination needed | `aspora deploy` (30 seconds) |
| **Monitoring** | Per-domain custom dashboards | Unified platform dashboard |
| **Cost Tracking** | Manual spreadsheet | Real-time per-skill cost metrics |
| **Model Selection** | Hardcoded in each skill | OpenRouter auto-selection + fallback |
| **Testing** | Ad-hoc, inconsistent | DeepEval + Promptfoo built-in |
| **Versioning** | Git tags, manual rollback | Auto rollback on errors, canary deploys |
| **Discovery** | LLM needs to know all skills upfront | Dynamic discovery via registry |

**The Moat**: After 6 months:
- 50+ skills across 6 domains
- 10,000+ test cases (from user corrections)
- Cost optimization data (which models for which tasks)
- Production-grade observability

New competitor would need to rebuild ALL of this.

---

**Next**: Implement Phase 1 primitives (Skill Registry + CLI + OpenRouter)?
