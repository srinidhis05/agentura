# Aspora Platform — Production Engineering Architecture

> **Scope**: Observability, Model Training, SDLC, Isolation, Kubernetes-Native Deployment
> **Mindset**: Platform Engineering, Multi-Tenancy, Production-Grade
> **Research**: Based on 2026 industry patterns (Dust.tt, Braintrust, Agent Sandbox, TrueFoundry)

---

## Table of Contents

1. [Platform Vision](#platform-vision)
2. [Observability Architecture](#observability-architecture)
3. [Model Training & Feedback Loop](#model-training--feedback-loop)
4. [SDLC Pipeline (Skill Onboarding)](#sdlc-pipeline-skill-onboarding)
5. [Isolation Layer (Multi-Tenancy)](#isolation-layer-multi-tenancy)
6. [Kubernetes Architecture](#kubernetes-architecture)
7. [Engineering Principles](#engineering-principles)

---

## Platform Vision

### The Office Platform Analogy

Think of Aspora as **"Salesforce for AI Agents"** — not individual tools, but a complete platform:

```
┌──────────────────────────────────────────────────────────────┐
│             ASPORA AGENT PLATFORM (The Office)               │
├──────────────────────────────────────────────────────────────┤
│  DOMAIN: Wealth    │  DOMAIN: Fraud    │  DOMAIN: ECM        │
│  ┌──────────────┐  │  ┌──────────────┐ │  ┌──────────────┐  │
│  │ Manager Agent│  │  │ Risk Agent   │ │  │ Manager Agent│  │
│  │ Advisor Agent│  │  │ Compliance   │ │  │ Field Agent  │  │
│  └──────────────┘  │  └──────────────┘ │  └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│           SHARED PLATFORM SERVICES (The IT Dept)             │
│  • Observability    • Model Training   • CI/CD Pipeline      │
│  • Multi-Tenancy    • Security         • Cost Management     │
└──────────────────────────────────────────────────────────────┘
```

**Key Insight**: Just like Salesforce has Sales Cloud, Service Cloud, Marketing Cloud — we have Wealth Domain, Fraud Domain, ECM Domain. Each domain has multiple agents, each agent has multiple skills.

---

## Observability Architecture

### The Three Questions Every CTO Asks

1. **"What are my agents doing right now?"** → Real-time tracing
2. **"Why did quality drop last week?"** → Regression detection
3. **"How much is this costing me?"** → Cost attribution

### Observability Stack (2026 Best Practices)

Based on [TrueFoundry](https://www.truefoundry.com), [Langfuse](https://langfuse.com), and [Braintrust](https://www.braintrust.dev) architectures:

```
┌────────────────────────────────────────────────────────────────┐
│  LAYER 1: TELEMETRY COLLECTION (OpenTelemetry Native)          │
├────────────────────────────────────────────────────────────────┤
│  Every skill execution emits:                                  │
│  • Traces (OpenTelemetry spans)                                │
│  • Logs (structured JSON)                                      │
│  • Metrics (Prometheus format)                                 │
│  • Events (user feedback, corrections, ratings)                │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  LAYER 2: DATA PLANE (Where Data Lives)                       │
├────────────────────────────────────────────────────────────────┤
│  Option A: Self-Hosted (Your AWS/GCP Account)                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL          → Metadata, evaluations, users      │ │
│  │  ClickHouse          → Fast columnar storage for traces  │ │
│  │  S3 / R2             → Raw LLM logs, artifacts           │ │
│  │  Redis               → Real-time aggregations            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Option B: Managed (e.g., Langfuse Cloud, Braintrust)         │
│  • Data never leaves your region (EU/US compliance)           │
│  • Braintrust model: Data plane in YOUR AWS account           │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  LAYER 3: ANALYTICS & INSIGHTS                                │
├────────────────────────────────────────────────────────────────┤
│  • Opik (Apache 2.0)      → 7-14x faster than Langfuse        │
│  • Langfuse (MIT)         → Prompt management, evaluations    │
│  • Arize Phoenix          → Agent-specific evals              │
│  • Grafana                → Custom dashboards                 │
└────────────────────────────────────────────────────────────────┘
```

### Recommended: Multi-Tool Strategy

**Do NOT pick one tool. Use specialized tools for each layer:**

| Layer | Tool | Why | License |
|-------|------|-----|---------|
| **Tracing** | Opik | 7-14x faster trace logging | Apache 2.0 |
| **Prompt Management** | Langfuse | Best-in-class versioning | MIT |
| **Agent Evals** | Arize Phoenix | Deeper agent support | Elastic 2.0 |
| **Infrastructure Metrics** | Prometheus + Grafana | K8s native | Apache 2.0 |
| **Cost Attribution** | Helicone or custom | LLM cost tracking | - |

**Total Cost**: $0 (all open-source, self-hosted)

---

### Observability Data Model

```typescript
// OpenTelemetry span for skill execution
interface SkillExecutionTrace {
  // Trace metadata
  trace_id: string;                    // Links spans across services
  span_id: string;
  parent_span_id?: string;             // Multi-agent workflows

  // Skill context
  domain: string;                      // "ecm", "wealth", "fraud"
  agent_role: string;                  // "manager", "field", "analyst"
  skill_name: string;                  // "triage-and-assign", "my-tickets"
  skill_version: string;               // "1.2.0"

  // Execution metadata
  trigger_type: 'cron' | 'message' | 'alert' | 'command';
  user_id?: string;                    // For interactive executions
  session_id?: string;

  // Timing
  started_at: timestamp;
  completed_at: timestamp;
  duration_ms: number;

  // LLM observability
  model_calls: ModelCall[];            // Each LLM API call
  total_tokens: {
    prompt: number;
    completion: number;
    total: number;
  };

  // Outcomes
  success: boolean;
  error?: {
    type: string;
    message: string;
    stack: string;
  };

  // Business metrics
  output: {
    data: any;                         // Skill-specific output
    confidence?: number;               // Agent confidence
    actions_taken?: string[];
  };

  // User feedback (for training)
  feedback?: {
    rating: 1 | 2 | 3 | 4 | 5;
    correction?: string;               // What user changed
    accepted: boolean;                 // Did user accept result?
  };

  // Cost attribution
  cost: {
    model_cost: number;                // LLM API cost
    compute_cost: number;              // K8s pod cost
    total_cost: number;
  };

  // Resource usage
  resources: {
    cpu_millis: number;
    memory_mb: number;
    io_bytes: number;
  };
}

interface ModelCall {
  model: string;                       // "claude-sonnet-4-5"
  provider: string;                    // "openrouter", "anthropic"

  request: {
    messages: Message[];
    temperature: number;
    max_tokens: number;
  };

  response: {
    content: string;
    finish_reason: string;
    tokens: {
      prompt: number;
      completion: number;
    };
  };

  timing: {
    latency_ms: number;
    time_to_first_token_ms?: number;
  };

  cost: number;                        // Calculated from provider pricing
}
```

---

### Real-Time Dashboard (Grafana)

#### Panel 1: Agent Activity Map

```
┌─────────────────────────────────────────────────────────────┐
│  LIVE AGENT ACTIVITY (Last 5 Minutes)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WEALTH DOMAIN                                              │
│  ├─ Manager Agent     ████░░░░░░ 40% busy                  │
│  └─ Advisor Agent     ██░░░░░░░░ 20% busy                  │
│                                                             │
│  FRAUD DOMAIN                                               │
│  ├─ Risk Agent        ██████████ 100% busy ⚠️ SATURATED    │
│  └─ Compliance Agent  ███░░░░░░░ 30% busy                  │
│                                                             │
│  ECM DOMAIN                                                 │
│  ├─ Manager Agent     █░░░░░░░░░ 10% busy (cron idle)      │
│  └─ Field Agent       ████████░░ 80% busy                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Prometheus Query**:
```promql
# Agent busy percentage (last 5 min)
sum(rate(skill_execution_duration_seconds[5m])) by (domain, agent_role) / 300 * 100
```

#### Panel 2: Quality Regression Detector

```
┌─────────────────────────────────────────────────────────────┐
│  QUALITY METRICS (7-Day Rolling Average)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Success Rate             98.5% ↓ -0.3%  ⚠️ ALERT          │
│  User Acceptance Rate     94.2% ↑ +1.1%  ✅ HEALTHY        │
│  Avg Confidence Score     0.87  ↓ -0.05  ⚠️ DECLINING      │
│  Hallucination Rate       2.1%  ↑ +0.4%  🚨 CRITICAL       │
│                                                             │
│  REGRESSION ALERTS:                                         │
│  • ecm/field/my-tickets: Success rate dropped 5% (v1.2.1)  │
│    Rollback? [Yes] [Investigate]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Panel 3: Cost Attribution

```
┌─────────────────────────────────────────────────────────────┐
│  COST BREAKDOWN (Today: $47.23)                             │
├─────────────────────────────────────────────────────────────┤
│  By Domain:                                                 │
│  ├─ ECM      $18.50 (39%)  ████████░░                      │
│  ├─ Fraud    $15.20 (32%)  ███████░░░                      │
│  └─ Wealth   $13.53 (29%)  ██████░░░░                      │
│                                                             │
│  By Model:                                                  │
│  ├─ Haiku     $8.10 (17%)   ████░░░░░░                     │
│  ├─ Sonnet   $28.90 (61%)   ████████████                   │
│  └─ Opus     $10.23 (22%)   █████░░░░░                     │
│                                                             │
│  Top Spenders (Skills):                                     │
│  1. ecm/manager/triage-and-assign  $6.50                   │
│  2. fraud/risk/analyze-transaction $5.20                   │
│  3. wealth/advisor/suggest-allocation $4.80                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Alerting Rules (PagerDuty Integration)

```yaml
# platform-alerts.yaml
alerts:
  # Quality regression
  - name: skill_success_rate_drop
    condition: |
      (
        avg_over_time(skill_success_rate[24h]) -
        avg_over_time(skill_success_rate[7d] offset 24h)
      ) < -0.05  # 5% drop
    severity: high
    channels: [pagerduty, slack]
    message: |
      Skill ${skill_name} success rate dropped ${drop_percentage}% in last 24h.
      Current: ${current_rate}% | 7-day avg: ${baseline_rate}%

      Likely causes:
      • Recent deployment (check canary status)
      • Upstream API change (check integration logs)
      • Prompt regression (run evals)

      Runbook: /docs/runbooks/quality-regression.md

  # Cost spike
  - name: daily_cost_spike
    condition: |
      sum(rate(skill_execution_cost[1h])) * 24 >
      avg_over_time(sum(rate(skill_execution_cost[1h])) * 24[7d]) * 2
    severity: medium
    channels: [slack, email]
    message: |
      Today's projected cost: $${projected_cost} (2x normal)

      Top contributors:
      ${top_5_skills_by_cost}

      Possible causes:
      • Agent entered recursive loop (check trace for cycles)
      • Traffic spike (check request volume)
      • Model upgrade without cost review

  # Latency degradation
  - name: p95_latency_spike
    condition: |
      histogram_quantile(0.95,
        rate(skill_execution_duration_seconds_bucket[5m])
      ) > 10
    severity: medium
    channels: [slack]
    message: |
      P95 latency for ${skill_name}: ${current_p95}s (threshold: 10s)

      Check:
      • Database slow queries (pg_stat_statements)
      • External API timeouts (check MCP gateway)
      • Model provider outage (OpenRouter status)
```

---

## Model Training & Feedback Loop

### Industry Pattern: Continuous Learning, Not One-Time Fine-Tuning

Based on [Nebuly](https://nebuly.com), [Fireworks AI](https://fireworks.ai), and DeepLearning.AI course patterns:

```
┌────────────────────────────────────────────────────────────────┐
│  STAGE 1: PRODUCTION USAGE                                     │
├────────────────────────────────────────────────────────────────┤
│  → User interacts with agent                                   │
│  → System logs input + output + metadata                       │
│  → User provides feedback (explicit or implicit)               │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 2: FEEDBACK COLLECTION                                  │
├────────────────────────────────────────────────────────────────┤
│  Explicit Feedback:                                            │
│  • Thumbs up/down                                              │
│  • User edits output (correction)                              │
│  • User flags as "incorrect" or "hallucination"                │
│                                                                │
│  Implicit Feedback:                                            │
│  • User accepted suggestion without edits                      │
│  • Task completed successfully (e.g., ticket resolved)         │
│  • User abandoned workflow (negative signal)                   │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 3: DATASET CURATION (Labelbox / Nebuly Pattern)        │
├────────────────────────────────────────────────────────────────┤
│  Weekly batch job:                                             │
│  1. Query Langfuse/Opik for executions with feedback           │
│  2. Filter high-quality examples:                              │
│     • User rating ≥ 4/5 → Positive example                     │
│     • User correction provided → Preference pair               │
│     • Hallucination flagged → Negative example                 │
│  3. Deduplicate (semantic similarity < 0.9)                    │
│  4. Balance dataset (equal positive/negative)                  │
│  5. Export to JSONL format for fine-tuning                     │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 4: EVALUATION DATASET GENERATION                        │
├────────────────────────────────────────────────────────────────┤
│  Split curated data:                                           │
│  • 80% → Fine-tuning dataset                                   │
│  • 10% → Validation set (prevent overfitting)                  │
│  • 10% → Golden test set (regression detection)                │
│                                                                │
│  Golden test set requirements:                                 │
│  • Representative of production distribution                   │
│  • Covers all skill capabilities                              │
│  • Includes edge cases (user-reported bugs)                    │
│  • Versioned in Git (test cases are code)                      │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 5: MODEL IMPROVEMENT (Multi-Strategy)                   │
├────────────────────────────────────────────────────────────────┤
│  Strategy A: Prompt Tuning (Fast, No Training)                 │
│  • Update system prompt based on patterns                      │
│  • Add few-shot examples from corrections                      │
│  • Test via A/B test (10% traffic)                             │
│  • Deploy if eval score improves > 5%                          │
│                                                                │
│  Strategy B: RAG Enhancement (Medium, No Training)             │
│  • Add user corrections to vector DB                           │
│  • Retrieve similar past corrections                           │
│  • Append to context: "In similar cases, users preferred..."  │
│                                                                │
│  Strategy C: Fine-Tuning (Slow, Expensive, High Impact)        │
│  • Use Fireworks AI / OpenAI fine-tuning API                   │
│  • Train LoRA adapter (cheaper than full fine-tune)            │
│  • Run shadow deployment (compare with base model)             │
│  • Promote if hallucination rate drops > 10%                   │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 6: CONTINUOUS EVALUATION                                │
├────────────────────────────────────────────────────────────────┤
│  Every deployment runs golden test set:                        │
│  • Faithfulness (does output match facts?)                     │
│  • Relevance (does output answer question?)                    │
│  • Correctness (matches ground truth?)                         │
│  • Hallucination (invented facts?)                             │
│  • Toxicity (harmful content?)                                 │
│                                                                │
│  Block deployment if:                                          │
│  • ANY metric drops > 5%                                       │
│  • Hallucination rate increases                                │
│  • Cost per execution increases > 20%                          │
└────────────────────────────────────────────────────────────────┘
```

---

### Feedback Loop Implementation

#### 1. Capture Feedback (Frontend)

```typescript
// packages/web/components/AgentChat.tsx
export function AgentChat() {
  const handleFeedback = async (executionId: string, feedback: Feedback) => {
    // Log to Langfuse
    await langfuse.score({
      traceId: executionId,
      name: 'user_rating',
      value: feedback.rating,
      comment: feedback.correction,
    });

    // Also log to our DB for curation pipeline
    await db.skill_executions.update(executionId, {
      user_rating: feedback.rating,
      user_correction: feedback.correction,
      user_accepted: feedback.accepted,
    });
  };

  return (
    <div>
      <AgentMessage content={output} />

      {/* Feedback UI */}
      <FeedbackButtons
        onThumbsUp={() => handleFeedback(executionId, { rating: 5, accepted: true })}
        onThumbsDown={() => setShowCorrectionForm(true)}
      />

      {showCorrectionForm && (
        <CorrectionForm
          originalOutput={output}
          onSubmit={(correction) => handleFeedback(executionId, {
            rating: 1,
            correction,
            accepted: false,
          })}
        />
      )}
    </div>
  );
}
```

#### 2. Weekly Curation Job (Python)

```python
# scripts/curate_training_data.py
from datetime import datetime, timedelta
from typing import List
import openai

async def curate_weekly_dataset(skill_name: str) -> str:
    """
    Curate training dataset from last week's production data.
    Returns: S3 path to JSONL file
    """

    # 1. Fetch executions with feedback from last 7 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    executions = await db.query("""
        SELECT
            e.id,
            e.skill_id,
            e.user_id,
            e.started_at,
            e.model_used,
            e.user_rating,
            e.user_correction,
            t.request_messages,
            t.response_content
        FROM skill_executions e
        JOIN llm_traces t ON t.execution_id = e.id
        WHERE e.skill_id = %(skill_id)s
          AND e.created_at BETWEEN %(start)s AND %(end)s
          AND e.user_rating IS NOT NULL
        ORDER BY e.created_at DESC
    """, {'skill_id': skill_name, 'start': start_date, 'end': end_date})

    # 2. Filter high-quality examples
    positive_examples = []
    preference_pairs = []

    for ex in executions:
        # High-quality positive example
        if ex['user_rating'] >= 4:
            positive_examples.append({
                'messages': ex['request_messages'],
                'completion': ex['response_content'],
                'metadata': {
                    'rating': ex['user_rating'],
                    'execution_id': ex['id'],
                    'timestamp': ex['started_at'].isoformat(),
                }
            })

        # User provided correction → preference pair
        if ex['user_correction']:
            preference_pairs.append({
                'messages': ex['request_messages'],
                'chosen': ex['user_correction'],      # What user wanted
                'rejected': ex['response_content'],    # What model gave
                'metadata': {
                    'rating': ex['user_rating'],
                    'execution_id': ex['id'],
                }
            })

    # 3. Deduplicate using semantic similarity
    deduplicated = await deduplicate_examples(
        positive_examples,
        threshold=0.9  # Keep if similarity < 0.9
    )

    # 4. Balance dataset
    balanced = balance_dataset(
        positive=deduplicated,
        negative=preference_pairs,
        target_ratio=0.5
    )

    # 5. Export to JSONL
    output_path = f's3://aspora-training-data/{skill_name}/{end_date.strftime("%Y-%m-%d")}.jsonl'
    await upload_to_s3(balanced, output_path)

    print(f"✅ Curated {len(balanced)} examples for {skill_name}")
    print(f"   Positive: {len(deduplicated)}")
    print(f"   Preference pairs: {len(preference_pairs)}")
    print(f"   Output: {output_path}")

    return output_path

async def deduplicate_examples(examples: List[dict], threshold: float) -> List[dict]:
    """Remove near-duplicate examples using embeddings."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Generate embeddings for all examples
    texts = [ex['completion'] for ex in examples]
    embeddings = model.encode(texts)

    # Keep first occurrence of similar examples
    kept = []
    kept_embeddings = []

    for i, ex in enumerate(examples):
        # Check similarity with already kept examples
        if kept_embeddings:
            similarities = cosine_similarity([embeddings[i]], kept_embeddings)[0]
            if max(similarities) >= threshold:
                continue  # Skip this duplicate

        kept.append(ex)
        kept_embeddings.append(embeddings[i])

    return kept
```

#### 3. Fine-Tuning Job (Fireworks AI / OpenAI)

```python
# scripts/finetune_model.py
import openai
from fireworks.client import Fireworks

async def finetune_with_fireworks(
    skill_name: str,
    training_data_path: str,
    base_model: str = "accounts/fireworks/models/llama-v3p1-70b-instruct"
) -> str:
    """
    Fine-tune model using Fireworks AI.
    Returns: Fine-tuned model ID
    """

    client = Fireworks(api_key=os.getenv("FIREWORKS_API_KEY"))

    # 1. Upload training data
    print(f"Uploading training data from {training_data_path}...")
    training_file = client.files.create(
        file=open(training_data_path, "rb"),
        purpose="fine-tune"
    )

    # 2. Create fine-tuning job
    print(f"Starting fine-tuning job for {skill_name}...")
    job = client.fine_tuning.jobs.create(
        training_file=training_file.id,
        model=base_model,
        suffix=f"{skill_name}-{datetime.now().strftime('%Y%m%d')}",
        hyperparameters={
            "n_epochs": 3,
            "learning_rate_multiplier": 0.1,
            "batch_size": 4,
        }
    )

    # 3. Wait for completion (or poll asynchronously)
    print(f"Fine-tuning job: {job.id}")
    print(f"Status: {job.status}")

    # In production, this would be async with webhook callback
    while job.status in ["pending", "running"]:
        await asyncio.sleep(60)
        job = client.fine_tuning.jobs.retrieve(job.id)
        print(f"Status: {job.status} | Progress: {job.progress}%")

    if job.status == "succeeded":
        print(f"✅ Fine-tuning complete!")
        print(f"   Model ID: {job.fine_tuned_model}")
        return job.fine_tuned_model
    else:
        raise Exception(f"Fine-tuning failed: {job.error}")

# Alternative: OpenAI fine-tuning
async def finetune_with_openai(
    skill_name: str,
    training_data_path: str,
    base_model: str = "gpt-4o-2024-08-06"
) -> str:
    """Fine-tune using OpenAI API."""

    # Upload file
    with open(training_data_path, "rb") as f:
        training_file = openai.files.create(file=f, purpose="fine-tune")

    # Create fine-tuning job
    job = openai.fine_tuning.jobs.create(
        training_file=training_file.id,
        model=base_model,
        suffix=skill_name,
    )

    # Poll for completion
    while job.status in ["pending", "running"]:
        await asyncio.sleep(60)
        job = openai.fine_tuning.jobs.retrieve(job.id)

    return job.fine_tuned_model
```

#### 4. Shadow Deployment for Validation

```python
# packages/platform-runtime/canary.py
async def deploy_shadow_model(
    skill_id: str,
    new_model_id: str,
    shadow_percentage: float = 1.0  # 100% shadow (no user impact)
):
    """
    Deploy new model in shadow mode.
    Runs both old and new models, compares outputs, no user impact.
    """

    # Update skill config
    await db.query("""
        INSERT INTO skill_versions (skill_id, version, model_id, deployment_mode)
        VALUES (%(skill_id)s, %(version)s, %(model_id)s, 'shadow')
    """, {
        'skill_id': skill_id,
        'version': get_next_version(skill_id),
        'model_id': new_model_id,
    })

    # Shadow execution logic
    async def execute_with_shadow(request):
        # Execute with BOTH models in parallel
        old_result, new_result = await asyncio.gather(
            execute_with_model(request, old_model_id),
            execute_with_model(request, new_model_id),
        )

        # Return old result to user (no impact)
        user_response = old_result

        # Log comparison for analysis
        await log_shadow_comparison({
            'request': request,
            'old_output': old_result,
            'new_output': new_result,
            'outputs_match': old_result == new_result,
            'semantic_similarity': compute_similarity(old_result, new_result),
        })

        return user_response

    print(f"✅ Shadow deployment active for {skill_id}")
    print(f"   Old model: {old_model_id}")
    print(f"   New model: {new_model_id}")
    print(f"   Shadow %: {shadow_percentage * 100}%")
```

---

### Training Strategy Matrix

| Improvement Type | Speed | Cost | Impact | When to Use |
|------------------|-------|------|--------|-------------|
| **Prompt Tuning** | Hours | $0 | Low-Medium | Weekly iteration, quick fixes |
| **Few-Shot Examples** | Hours | $0 | Medium | Add 3-5 examples from corrections |
| **RAG Enhancement** | Days | Low | Medium | Domain knowledge gaps |
| **LoRA Fine-Tuning** | Days | $$$ | High | Consistent behavior changes needed |
| **Full Fine-Tuning** | Weeks | $$$$ | Very High | Specialized domain (legal, medical) |

**Recommended Cadence**:
- **Daily**: Prompt tuning based on corrections
- **Weekly**: Dataset curation + few-shot update
- **Monthly**: RAG index refresh
- **Quarterly**: LoRA fine-tuning if > 500 corrections
- **Annually**: Full fine-tuning for specialized domains

---

## SDLC Pipeline (Skill Onboarding)

### Industry Pattern: Agentic SDLC with Quality Gates

Based on [2026 CI/CD patterns](https://www.anthropic.com) and [Agent Skills Marketplace](https://skillsmp.com):

```
┌────────────────────────────────────────────────────────────────┐
│  PHASE 1: DEVELOPMENT (Local, No Platform Access)             │
├────────────────────────────────────────────────────────────────┤
│  Developer workflow:                                           │
│  1. $ aspora create skill fraud/detect-velocity                │
│  2. Edit SKILL.md (add logic)                                  │
│  3. $ aspora test fraud/detect-velocity --local                │
│  4. Iterate until tests pass                                   │
│                                                                │
│  Local test suite runs:                                        │
│  • Unit tests (code logic)                                     │
│  • Skill syntax validation (YAML frontmatter)                  │
│  • Resource access checks (validate paths exist)               │
│  • Cost estimation (based on mock data)                        │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  PHASE 2: PR CREATION (Git Push)                              │
├────────────────────────────────────────────────────────────────┤
│  Developer:                                                    │
│  $ git checkout -b feature/fraud-detect-velocity               │
│  $ git add skills/fraud/detect-velocity/                      │
│  $ git commit -m "feat(fraud): add velocity detection skill"  │
│  $ git push origin feature/fraud-detect-velocity              │
│  $ gh pr create                                                │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  PHASE 3: CI PIPELINE (GitHub Actions / GitLab CI)            │
├────────────────────────────────────────────────────────────────┤
│  Triggered on: Pull Request                                    │
│                                                                │
│  Job 1: Static Analysis (30 seconds)                           │
│  ├─ Lint SKILL.md (frontmatter schema)                         │
│  ├─ Validate aspora.config.yaml                                │
│  ├─ Check DECISIONS.md + GUARDRAILS.md exist                   │
│  ├─ Security scan (detect secrets in code/)                    │
│  └─ Cost budget check (max_per_execution < threshold)          │
│                                                                │
│  Job 2: Unit Tests (1 minute)                                  │
│  ├─ Run code/handler.test.ts                                   │
│  ├─ Mock external APIs                                         │
│  └─ Assert outputs match expected                              │
│                                                                │
│  Job 3: LLM Evaluation (3-5 minutes) ⚠️ CRITICAL               │
│  ├─ Load golden test dataset (tests/*.yaml)                    │
│  ├─ Execute skill with REAL model (staging API key)            │
│  ├─ Run evals:                                                 │
│  │   • Faithfulness (DeepEval)                                 │
│  │   • Relevance (DeepEval)                                    │
│  │   • Hallucination detection (Phoenix)                       │
│  │   • Correctness (ground truth comparison)                   │
│  ├─ Compare with baseline (main branch scores)                 │
│  └─ BLOCK if ANY metric drops > 5%                             │
│                                                                │
│  Job 4: Regression Tests (2-3 minutes)                         │
│  ├─ Run ALL existing skills' tests (not just new one)          │
│  ├─ Ensure new skill doesn't break existing workflows          │
│  └─ Check shared resource changes (queries/, config/)          │
│                                                                │
│  Job 5: Cost Simulation (1 minute)                             │
│  ├─ Estimate monthly cost based on test runs                   │
│  ├─ Flag if > $500/month without approval                      │
│  └─ Post comment on PR with cost estimate                      │
│                                                                │
│  Job 6: Security Scan (1 minute)                               │
│  ├─ RBAC validation (blocked_resources enforced)               │
│  ├─ Dependency vulnerability scan (npm audit, pip-audit)       │
│  └─ Secrets detection (no API keys in code)                    │
│                                                                │
│  MERGE GATE: ALL jobs must pass ✅                             │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  PHASE 4: STAGING DEPLOYMENT (Auto on Merge)                  │
├────────────────────────────────────────────────────────────────┤
│  Triggered on: Merge to main                                   │
│                                                                │
│  1. Build skill artifact                                       │
│     ├─ Package code/ directory                                 │
│     ├─ Upload to S3: s3://aspora-skills/{domain}/{skill}/      │
│     └─ Create registry entry (PostgreSQL)                      │
│                                                                │
│  2. Deploy to staging namespace (K8s)                          │
│     ├─ kubectl apply -f skill-deployment-staging.yaml          │
│     ├─ Wait for pod ready (health check)                       │
│     └─ Run smoke tests                                         │
│                                                                │
│  3. Post-deploy validation (15 minutes)                        │
│     ├─ Execute 10 test cases from golden set                   │
│     ├─ Monitor error rate                                      │
│     └─ If success rate < 95%, auto-rollback                    │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  PHASE 5: CANARY DEPLOYMENT (Manual Approval)                 │
├────────────────────────────────────────────────────────────────┤
│  Platform engineer approves via:                               │
│  $ aspora promote fraud/detect-velocity --canary 10            │
│                                                                │
│  Canary config:                                                │
│  ├─ 10% of production traffic → new version                    │
│  ├─ 90% of production traffic → old version                    │
│  ├─ Monitor for 24-48 hours                                    │
│  └─ Compare metrics:                                           │
│      • Success rate (must be ≥ baseline)                       │
│      • Latency p95 (must be ≤ baseline + 10%)                  │
│      • User rating (must be ≥ baseline)                        │
│      • Cost per execution (warn if > baseline + 20%)           │
│                                                                │
│  Auto-promote if all metrics pass after 48h                    │
│  Auto-rollback if ANY metric fails                             │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  PHASE 6: PRODUCTION DEPLOYMENT (Auto or Manual)              │
├────────────────────────────────────────────────────────────────┤
│  Option A: Auto-promote (if canary passed)                     │
│  $ aspora promote fraud/detect-velocity --prod                 │
│                                                                │
│  Option B: Blue-Green (zero-downtime)                          │
│  ├─ Deploy new version to "green" namespace                    │
│  ├─ Run final validation                                       │
│  ├─ Switch traffic: blue → green (via Istio VirtualService)    │
│  └─ Keep blue running for 24h (rollback safety)                │
│                                                                │
│  Post-deployment:                                              │
│  ├─ Update registry (mark as "production")                     │
│  ├─ Tag Docker image: fraud-detect-velocity:v1.2.0-prod        │
│  ├─ Create GitHub release                                      │
│  └─ Post announcement to #platform-releases Slack              │
└────────────────────────────────────────────────────────────────┘
```

---

### CI Pipeline Code (GitHub Actions)

```yaml
# .github/workflows/skill-ci.yml
name: Skill CI/CD Pipeline

on:
  pull_request:
    paths:
      - 'skills/**'
  push:
    branches: [main]

jobs:
  # Job 1: Static Analysis
  static-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate skill schema
        run: |
          npm install -g @aspora/cli
          aspora validate skills/**/*.yaml

      - name: Security scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD

      - name: Cost budget check
        run: |
          aspora estimate-cost --changed-skills \
            --threshold 500 \
            --fail-on-exceed

  # Job 2: Unit Tests
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --changed-skills

  # Job 3: LLM Evaluation (CRITICAL)
  llm-evaluation:
    runs-on: ubuntu-latest
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_STAGING }}
      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY_STAGING }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install evaluation tools
        run: |
          pip install deepeval opik-python promptfoo

      - name: Run LLM evals
        run: |
          # Get changed skills
          CHANGED_SKILLS=$(aspora list-changed-skills)

          for skill in $CHANGED_SKILLS; do
            echo "Evaluating $skill..."

            # Run DeepEval metrics
            deepeval test run \
              --test-file skills/$skill/tests/deepeval/*.py \
              --min-score 0.8

            # Compare with baseline (main branch)
            aspora eval compare \
              --skill $skill \
              --baseline main \
              --threshold 0.05 \
              --fail-on-regression
          done

      - name: Post eval results to PR
        uses: actions/github-script@v7
        with:
          script: |
            const results = require('./eval-results.json');
            const body = `
            ## LLM Evaluation Results

            | Metric | Baseline | New | Change |
            |--------|----------|-----|--------|
            | Faithfulness | ${results.baseline.faithfulness} | ${results.new.faithfulness} | ${results.delta.faithfulness} |
            | Relevance | ${results.baseline.relevance} | ${results.new.relevance} | ${results.delta.relevance} |
            | Hallucination | ${results.baseline.hallucination} | ${results.new.hallucination} | ${results.delta.hallucination} |

            ${results.passed ? '✅ All metrics passed!' : '❌ Regression detected!'}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

  # Job 4: Regression Tests
  regression-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch all history for diff

      - name: Run regression suite
        run: |
          # Run ALL skills' tests, not just changed ones
          aspora test all \
            --include-integration \
            --parallel 4 \
            --timeout 300

      - name: Check shared resource impact
        run: |
          # If shared/ resources changed, test ALL skills using them
          CHANGED_SHARED=$(git diff main -- shared/)

          if [ -n "$CHANGED_SHARED" ]; then
            echo "⚠️ Shared resources changed, testing all dependent skills..."
            aspora test --using-shared-resources
          fi

  # Job 5: Deploy to Staging (on merge to main)
  deploy-staging:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [static-analysis, unit-tests, llm-evaluation, regression-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBECONFIG_STAGING }}

      - name: Deploy changed skills
        run: |
          CHANGED_SKILLS=$(aspora list-changed-skills)

          for skill in $CHANGED_SKILLS; do
            echo "Deploying $skill to staging..."

            # Build and push Docker image
            aspora build $skill --tag staging

            # Deploy to K8s staging namespace
            aspora deploy $skill \
              --env staging \
              --namespace aspora-staging \
              --wait

            # Run smoke tests
            aspora smoke-test $skill --env staging
          done

      - name: Post deployment summary
        run: |
          aspora deployment-summary \
            --env staging \
            --output markdown \
            > deployment-summary.md

          gh pr comment ${{ github.event.pull_request.number }} \
            --body-file deployment-summary.md
```

---

### Evaluation Test Example

```python
# skills/fraud/detect-velocity/tests/deepeval/test_velocity_detection.py
import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

from aspora_sdk import load_skill

@pytest.fixture
def skill():
    return load_skill("fraud/detect-velocity")

def test_normal_transaction_velocity(skill):
    """Normal transaction should NOT trigger velocity alert."""

    # Arrange
    input_data = {
        "user_id": "user_123",
        "transaction": {
            "amount": 100,
            "currency": "AED",
            "timestamp": "2026-02-16T10:00:00Z"
        },
        "recent_transactions": [
            {"amount": 95, "timestamp": "2026-02-15T10:00:00Z"},
            {"amount": 80, "timestamp": "2026-02-14T10:00:00Z"},
        ]
    }

    # Act
    result = skill.execute(input_data)

    # Assert
    test_case = LLMTestCase(
        input=str(input_data),
        actual_output=result.message,
        expected_output="Transaction approved. Velocity is normal.",
        context=["User has consistent transaction pattern"],
    )

    faithfulness_metric = FaithfulnessMetric(threshold=0.8)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.8)

    assert_test(test_case, [faithfulness_metric, relevancy_metric])
    assert result.success == True
    assert result.data['velocity_score'] < 0.5

def test_high_velocity_attack(skill):
    """10 transactions in 1 minute should trigger alert."""

    input_data = {
        "user_id": "user_456",
        "transaction": {
            "amount": 500,
            "currency": "AED",
            "timestamp": "2026-02-16T10:05:00Z"
        },
        "recent_transactions": [
            {"amount": 500, "timestamp": "2026-02-16T10:04:55Z"},
            {"amount": 500, "timestamp": "2026-02-16T10:04:50Z"},
            {"amount": 500, "timestamp": "2026-02-16T10:04:45Z"},
            # ... 7 more in last minute
        ]
    }

    result = skill.execute(input_data)

    # High velocity should be detected
    assert result.success == True
    assert result.data['velocity_score'] > 0.9
    assert "block" in result.message.lower() or "suspicious" in result.message.lower()

    # Hallucination check: Should NOT mention unrelated fraud types
    assert "credit card fraud" not in result.message.lower()
    assert "phishing" not in result.message.lower()

def test_regression_user_123_case(skill):
    """
    Regression test: User reported false positive on 2026-02-10.
    This specific case should NOT trigger alert.
    """

    # Real production data that caused false positive
    input_data = load_test_case("regression/user-123-false-positive.json")

    result = skill.execute(input_data)

    # Should NOT block (this was the bug)
    assert result.data['velocity_score'] < 0.7
    assert "approved" in result.message.lower()
```

---

## Isolation Layer (Multi-Tenancy)

### Kubernetes Multi-Tenancy Pattern

Based on [Google Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox), [gVisor](https://gvisor.dev), and [K8s multi-tenancy best practices](https://kubernetes.io/docs/concepts/security/multi-tenancy/):

```
┌────────────────────────────────────────────────────────────────┐
│  ISOLATION LEVEL 1: NAMESPACE SEPARATION                       │
├────────────────────────────────────────────────────────────────┤
│  aspora-platform/                 # Platform team owns          │
│  ├─ aspora-registry              # Skill registry (Postgres)   │
│  ├─ aspora-gateway               # OpenRouter gateway          │
│  ├─ aspora-observability         # Langfuse, Opik, Grafana     │
│  └─ aspora-control-plane         # Platform controllers        │
│                                                                │
│  aspora-wealth/                   # Wealth domain team owns     │
│  ├─ wealth-manager-agent         # Manager agent pod           │
│  ├─ wealth-advisor-agent         # Advisor agent pod           │
│  └─ wealth-*-skill-*             # Skill execution pods        │
│                                                                │
│  aspora-fraud/                    # Fraud domain team owns      │
│  ├─fraud-risk-agent              # Risk agent pod              │
│  ├─ fraud-compliance-agent       # Compliance agent pod        │
│  └─ fraud-*-skill-*              # Skill execution pods        │
│                                                                │
│  aspora-ecm/                      # ECM domain team owns        │
│  ├─ ecm-manager-agent            # Manager agent (CronJob)     │
│  ├─ ecm-field-agent              # Field agent pools           │
│  └─ ecm-*-skill-*                # Skill execution pods        │
└────────────────────────────────────────────────────────────────┘
```

### Namespace RBAC

```yaml
# k8s/rbac/wealth-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aspora-wealth
  labels:
    domain: wealth
    owner-team: wealth-team
    cost-center: wealth-product

---
# ResourceQuota: Prevent wealth team from monopolizing cluster
apiVersion: v1
kind: ResourceQuota
metadata:
  name: wealth-quota
  namespace: aspora-wealth
spec:
  hard:
    requests.cpu: "20"          # Max 20 CPU cores
    requests.memory: 40Gi       # Max 40GB RAM
    requests.storage: 100Gi     # Max 100GB disk
    pods: "50"                  # Max 50 pods
    services.loadbalancers: "2" # Max 2 load balancers

---
# LimitRange: Prevent runaway pods
apiVersion: v1
kind: LimitRange
metadata:
  name: wealth-limits
  namespace: aspora-wealth
spec:
  limits:
  - max:
      cpu: "4"         # No pod > 4 CPU
      memory: 8Gi      # No pod > 8GB RAM
    min:
      cpu: "100m"
      memory: 128Mi
    type: Container

---
# NetworkPolicy: Deny all by default, allow specific
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: wealth-network-policy
  namespace: aspora-wealth
spec:
  podSelector: {}  # Apply to all pods in namespace
  policyTypes:
  - Ingress
  - Egress

  # Ingress: ONLY from platform gateway
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: aspora-platform
      podSelector:
        matchLabels:
          app: aspora-gateway
    ports:
    - protocol: TCP
      port: 8080

  # Egress: Allow ONLY specific destinations
  egress:
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53

  # Allow OpenRouter API
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443
    # NOTE: Cannot filter by external IP in NetworkPolicy
    # Use Istio ServiceEntry for external service mesh

  # Allow Postgres in platform namespace
  - to:
    - namespaceSelector:
        matchLabels:
          name: aspora-platform
      podSelector:
        matchLabels:
        app: postgresql
    ports:
    - protocol: TCP
      port: 5432

  # DENY all other egress (blocks wealth → fraud communication)

---
# RBAC: Wealth team can ONLY deploy to wealth namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: wealth-deployer
  namespace: aspora-wealth
rules:
- apiGroups: ["apps", "batch"]
  resources: ["deployments", "cronjobs", "jobs"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets", "configmaps"]
  verbs: ["get", "list"]  # Read-only (no create/update)

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: wealth-team-binding
  namespace: aspora-wealth
subjects:
- kind: Group
  name: wealth-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: wealth-deployer
  apiGroup: rbac.authorization.k8s.io
```

---

### Agent Sandbox (gVisor Isolation)

Based on [Google Agent Sandbox announcement](https://cloud.google.com/blog/products/containers-kubernetes/introducing-agent-sandbox-kubernetes):

```yaml
# k8s/agent-sandbox/ecm-field-agent.yaml
apiVersion: agentsandbox.k8s.io/v1alpha1
kind: AgentSandbox
metadata:
  name: ecm-field-agent-sandbox
  namespace: aspora-ecm
spec:
  # Isolation backend (gVisor or Kata Containers)
  runtime: gvisor

  # Resource limits
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi

  # Storage (persistent for agent state)
  storage:
    size: 10Gi
    storageClassName: fast-ssd

  # Network isolation
  networkPolicy:
    # Agent can ONLY call ecm-gateway MCP
    allowedEndpoints:
    - host: ecm-gateway.aspora-platform.svc.cluster.local
      port: 8080
    - host: openrouter.ai
      port: 443

  # Security context
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    readOnlyRoot Filesystem: true
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]

  # Warm pool (pre-initialized sandboxes for <1s startup)
  warmPool:
    size: 5              # Keep 5 warm sandboxes ready
    ttl: 300             # Recycle after 5 minutes idle

  # Container image
  image: aspora/ecm-field-agent:v1.0.5

  # Environment variables
  env:
  - name: SKILL_REGISTRY_URL
    value: "postgresql://aspora-registry.aspora-platform.svc.cluster.local:5432/skills"
  - name: OPENROUTER_API_KEY
    valueFrom:
      secretKeyRef:
        name: openrouter-credentials
        key: api-key
  - name: LANGFUSE_PUBLIC_KEY
    valueFrom:
      secretKeyRef:
        name: langfuse-credentials
        key: public-key
```

**Key Benefits**:
- **Sub-second startup** (90% faster than cold Docker)
- **Kernel-level isolation** (gVisor sandboxes syscalls)
- **Resource caps enforced** (CPU, memory, I/O)
- **Network jail** (cannot call fraud/ services)

---

### Istio Service Mesh (Advanced Isolation)

```yaml
# k8s/istio/wealth-namespace.yaml
apiVersion: networking.istio.io/v1beta1
kind: Sidecar
metadata:
  name: wealth-sidecar
  namespace: aspora-wealth
spec:
  workloadSelector:
    labels:
      domain: wealth

  egress:
  - hosts:
    - "aspora-platform/*"           # Can call platform services
    - "istio-system/*"              # Can call Istio control plane
    - "./openrouter.ai"             # Can call OpenRouter

  # DENY all other egress (blocks wealth → fraud traffic)

---
# ServiceEntry: Define allowed external services
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: openrouter-external
  namespace: aspora-wealth
spec:
  hosts:
  - "openrouter.ai"
  - "*.openrouter.ai"
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  location: MESH_EXTERNAL
  resolution: DNS

---
# AuthorizationPolicy: Require mTLS between services
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: wealth-authz
  namespace: aspora-wealth
spec:
  action: ALLOW
  rules:
  # Allow platform gateway to call wealth agents
  - from:
    - source:
       namespaces: ["aspora-platform"]
       principals: ["cluster.local/ns/aspora-platform/sa/aspora-gateway"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/execute"]

  # Deny everything else by default
```

---

## Kubernetes Architecture

### Full K8s Stack

```
┌────────────────────────────────────────────────────────────────┐
│  CONTROL PLANE ( managed by EKS/GKE/AKS)                      │
│  • API Server                                                  │
│  • Controller Manager                                          │
│  • Scheduler                                                   │
│  • etcd                                                        │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  PLATFORM COMPONENTS                                           │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Istio Service Mesh (Traffic Management + Security)     │ │
│  │  • Ingress Gateway (external traffic)                   │ │
│  │  • Egress Gateway (external API calls)                  │ │
│  │  • mTLS between services                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Agent Sandbox Operator (CRD Controller)                │ │
│  │  • Manages gVisor/Kata runtimes                         │ │
│  │  • Warm pool management                                 │ │
│  │  • Resource enforcement                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Prometheus + Grafana (Observability)                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Argo CD (GitOps Deployment)                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Cert-Manager (TLS Certificates)                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  External Secrets Operator (Secrets from AWS Secrets)   │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│  WORKLOAD NAMESPACES (Domain Teams)                           │
├────────────────────────────────────────────────────────────────┤
│  aspora-wealth/  aspora-fraud/  aspora-ecm/  aspora-support/  │
│  (Each with AgentSandbox pods + NetworkPolicies)              │
└────────────────────────────────────────────────────────────────┘
```

### Deployment Manifests

**Manager Agent (CronJob)**:
```yaml
# k8s/deployments/ecm-manager-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ecm-manager-triage
  namespace: aspora-ecm
spec:
  schedule: "0 7,14,20 * * *"  # 7AM, 2PM, 8PM UAE
  timezone: "Asia/Dubai"

  jobTemplate:
    spec:
      template:
        metadata:
          annotations:
            instrumentation.opentelemetry.io/inject-sdk: "true"
        spec:
          # Use Agent Sandbox runtime
          runtimeClassName: gvisor

          containers:
          - name: ecm-manager
            image: aspora/ecm-manager:v1.2.0

            resources:
              requests:
                cpu: 500m
                memory: 1Gi
              limits:
                cpu: 2000m
                memory: 4Gi

            env:
            - name: SKILL_NAME
              value: "ecm/manager/triage-and-assign"
            - name: MODEL
              value: "claude-sonnet-4-5"
            - name: OPENROUTER_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openrouter-credentials
                  key: api-key
            - name: LANGFUSE_PUBLIC_KEY
              valueFrom:
                secretKeyRef:
                  name: langfuse-credentials
                  key: public-key

            # ReadOnly root filesystem (security)
            securityContext:
              runAsNonRoot: true
              runAsUser: 1000
              readOnlyRootFilesystem: true
              allowPrivilegeEscalation: false

            # Writable /tmp (in-memory)
            volumeMounts:
            - name: tmp
              mountPath: /tmp

          volumes:
          - name: tmp
            emptyDir:
              medium: Memory

          restartPolicy: OnFailure

          # Tolerations for spot instances (cost optimization)
          tolerations:
          - key: "spot"
            operator: "Equal"
            value: "true"
            effect: "NoSchedule"
```

**Field Agent (Deployment with HPA)**:
```yaml
# k8s/deployments/ecm-field-agent.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecm-field-agent
  namespace: aspora-ecm
spec:
  replicas: 3  # Min 3 pods, auto-scale to 20

  selector:
    matchLabels:
      app: ecm-field-agent
      domain: ecm
      role: field

  template:
    metadata:
      labels:
        app: ecm-field-agent
        domain: ecm
        role: field
    spec:
      runtimeClassName: gvisor

      containers:
      - name: field-agent
        image: aspora/ecm-field-agent:v1.0.5

        ports:
        - containerPort: 8080
          name: http

        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi

        env:
        - name: AGENT_ROLE
          value: "field"
        - name: DOMAIN
          value: "ecm"
        - name: MODEL
          value: "claude-haiku-4-5"  # Cheaper for field

---
# HorizontalPodAutoscaler: Auto-scale based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ecm-field-agent-hpa
  namespace: aspora-ecm
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ecm-field-agent

  minReplicas: 3
  maxReplicas: 20

  metrics:
  # Scale on CPU
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

  # Scale on custom metric (queue depth from Prometheus)
  - type: Pods
    pods:
      metric:
        name: skill_execution_queue_depth
      target:
        type: AverageValue
        averageValue: "10"

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50        # Scale up max 50% at a time
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scale down
      policies:
      - type: Pods
        value: 1         # Remove 1 pod at a time
        periodSeconds: 120
```

---

### GitOps with Argo CD

```yaml
# argocd/applications/ecm-domain.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: aspora-ecm
  namespace: argocd
spec:
  project: aspora-platform

  source:
    repoURL: https://github.com/aspora/platform
    targetRevision: main
    path: k8s/domains/ecm

  destination:
    server: https://kubernetes.default.svc
    namespace: aspora-ecm

  syncPolicy:
    automated:
      prune: true      # Delete resources not in Git
      selfHeal: true   # Auto-sync if cluster state drifts

    syncOptions:
    - CreateNamespace=true

    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  # Health check readiness
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas  # Ignore HPA-managed replicas
```

---

## Engineering Principles

### 1. **Platform as a Product** (Not a Project)

- Platform team = internal product team
- Domain teams = customers
- SLAs for platform services (99.9% uptime)
- Developer experience = primary metric

### 2. **Shift-Left Quality** (Catch Bugs Early)

```
Local Dev   →   PR    →  Staging  →  Canary  →  Production
(seconds)    (minutes)  (hours)    (days)    (weeks)

✅ Unit tests        ✅ CI evals  ✅ Smoke  ✅ A/B   ✅ Monitor
✅ Linting           ✅ Regression✅ 15min  ✅ 48h   ✅ Alert
✅ Cost estimate     ✅ Security  ✅ Auto-  ✅ Auto- ✅ Rollback
                                  rollback  promote
```

**Cost of Bug Fix**:
- Local: $1 (1 hour dev time)
- Staging: $10 (rollback + debug)
- Production: $1000 (customer impact + SEV-1 incident)

### 3. **Defense in Depth** (Multi-Layer Security)

| Layer | Control | Example |
|-------|---------|---------|
| **L1: Code** | Input validation | Reject SQL injection in user input |
| **L2: Runtime** | RBAC enforcement | Block manager from loading runbooks |
| **L3: Network** | NetworkPolicy | Block wealth → fraud traffic |
| **L4: Container** | gVisor sandbox | Isolate syscalls |
| **L5: K8s** | ResourceQuota | Prevent DoS via pod explosion |
| **L6: Cloud** | IAM roles | S3 bucket access per namespace |

### 4. **Observability-Driven Development**

**Before writing code, ask**:
1. How will I know if this works in production?
2. How will I debug when it fails?
3. How much will this cost?

**Then instrument**:
- Traces for "what happened"
- Logs for "why it happened"
- Metrics for "how often it happens"
- Evals for "did quality drop"

### 5. **Cost as First-Class Metric**

```typescript
// WRONG: No cost tracking
const result = await model.complete(prompt);

// RIGHT: Cost-aware execution
const result = await executeWithBudget({
  model: "claude-sonnet-4-5",
  prompt,
  maxCost: 0.10,  // Fail if > $0.10
  fallbackModel: "haiku",  // Cheaper fallback
});

await trackCost({
  skill: "ecm/manager/triage-and-assign",
  cost: result.cost,
  tokens: result.tokens,
  model: result.model,
});
```

### 6. **Continuous Everything**

- Continuous Integration (every PR)
- Continuous Deployment (every merge)
- Continuous Evaluation (every execution)
- Continuous Training (weekly curation)
- Continuous Monitoring (real-time)

**NOT**:
- Deploy Friday afternoon
- Manual releases
- "Test in production"
- Quarterly evaluations

---

## Summary: Make vs Buy

### Components to Build

| Component | Why Build | Effort |
|-----------|-----------|--------|
| **Skill Registry** | Core differentiator | 2 weeks |
| **RBAC Enforcement** | Custom role model | 1 week |
| **Cost Attribution** | Skill-level tracking | 1 week |
| **SDLC Pipeline** | GitHub Actions templates | 2 weeks |
| **K8s Manifests** | Domain-specific config | 2 weeks |

**Total**: 8 weeks (2 months)

### Components to Buy/Use Open-Source

| Component | Tool | Cost | Why |
|-----------|------|------|-----|
| **Tracing** | Opik (self-hosted) | $0 | 7x faster than Langfuse |
| **Prompt Management** | Langfuse (self-hosted) | $0 | Best-in-class versioning |
| **Agent Evals** | Arize Phoenix | $0 | Deeper agent support |
| **Service Mesh** | Istio | $0 | Industry standard |
| **Agent Sandbox** | K8s Agent Sandbox + gVisor | $0 | Google-backed |
| **GitOps** | Argo CD | $0 | CNCF graduated |
| **Fine-tuning** | Fireworks AI or OpenAI | $$$ | Managed infrastructure |

**Compute Cost** (AWS/GCP):
- **Development**: ~$500/month (staging cluster)
- **Production**: ~$2000-5000/month (depends on scale)

---

## Next Steps

**Week 1-2**: Platform Foundation
- [ ] Set up K8s cluster (EKS/GKE with gVisor support)
- []Deploy observability stack (Opik + Langfuse + Prometheus)
- [ ] Implement skill registry (PostgreSQL)
- [ ] Configure namespace structure

**Week 3-4**: SDLC Pipeline
- [ ] Create GitHub Actions CI templates
- [ ] Integrate DeepEval for LLM evaluation gates
- [ ] Set up Argo CD for GitOps
- [ ] Deploy first skill (ECM triage-and-assign)

**Week 5-6**: Multi-Tenancy
- [ ] Implement RBAC enforcement
- [ ] Configure NetworkPolicies per domain
- [ ] Deploy Agent Sandbox operator
- [ ] Test cross-domain isolation

**Week 7-8**: Feedback Loop
- [ ] Build curation pipeline (weekly batch job)
- [ ] Set up shadow deployment for fine-tuned models
- [ ] Create Grafana dashboards
- [ ] Document runbooks

**Result**: Production-grade agentic platform ready for 50+ skills across 6 domains.

---

## Sources

- [TrueFoundry AI Observability](https://www.truefoundry.com)
- [Langfuse Open Source](https://langfuse.com)
- [Braintrust Data Plane](https://www.braintrust.dev)
- [Opik vs Langfuse vs Phoenix Comparison](https://www.comet.com/site/blog/opik-vs-langfuse-vs-arize-phoenix/)
- [Google Agent Sandbox for Kubernetes](https://cloud.google.com/blog/products/containers-kubernetes/introducing-agent-sandbox-kubernetes)
- [Kubernetes Multi-Tenancy Best Practices](https://kubernetes.io/docs/concepts/security/multi-tenancy/)
- [Agentic SDLC 2026 Patterns](https://www.anthropic.com/research)
- [LLM Evaluation in CI/CD](https://www.braintrust.dev/docs/guides/ci-cd)
- [Dust.tt Platform Architecture](https://dust.tt/blog)
- [Nebuly Feedback Loop Platform](https://nebuly.com)
- [Fireworks AI Fine-Tuning](https://fireworks.ai)
