# Intelligence Layer Architecture — ReAct + Reflexion + Vector Search

**Purpose**: Transform CRUD skills into intelligent reasoning agents that detect patterns, perform root cause analysis, and learn from corrections.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION LAYER                             │
│  Slack / WhatsApp / CLI                                                      │
│  "Why are 50% of tickets stuck >24h?" | "What's causing alert spike?"       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ASPORA SKILLS EXECUTOR                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  ROUTER LAYER (Context Injection)                                    │   │
│  │  - Extract user_id, team_id, domain                                  │   │
│  │  - Route to appropriate skill                                        │   │
│  │  - Inject context into skill execution                               │   │
│  └───────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                           │
│                                  ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              INTELLIGENCE LAYER (NEW)                                │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐     │   │
│  │  │  1. PATTERN RECOGNITION (Vector Search)                    │     │   │
│  │  │     - Query pgvector for similar past cases                │     │   │
│  │  │     - Find: "Stuck tickets with same symptoms"             │     │   │
│  │  │     - Return: Top 5 similar executions + outcomes          │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  │                           ▼                                           │   │
│  │  ┌────────────────────────────────────────────────────────────┐     │   │
│  │  │  2. REACT REASONING LOOP                                   │     │   │
│  │  │     ┌──────────────────────────────────────────┐           │     │   │
│  │  │     │ Thought: "Need to analyze ticket data"   │           │     │   │
│  │  │     │ Action: query_tickets(status=stuck)      │           │     │   │
│  │  │     │ Observation: 150 tickets, 75 >24h old    │           │     │   │
│  │  │     └──────────────┬───────────────────────────┘           │     │   │
│  │  │                    ▼                                        │     │   │
│  │  │     ┌──────────────────────────────────────────┐           │     │   │
│  │  │     │ Thought: "Check assignment patterns"     │           │     │   │
│  │  │     │ Action: analyze_assignments()            │           │     │   │
│  │  │     │ Observation: 50% stuck at "awaiting mgr" │           │     │   │
│  │  │     └──────────────┬───────────────────────────┘           │     │   │
│  │  │                    ▼                                        │     │   │
│  │  │     ┌──────────────────────────────────────────┐           │     │   │
│  │  │     │ Thought: "Compare to precedents"         │           │     │   │
│  │  │     │ Action: search_similar_patterns()        │           │     │   │
│  │  │     │ Observation: 3 past cases, all resolved  │           │     │   │
│  │  │     │              by routing rule change      │           │     │   │
│  │  │     └──────────────┬───────────────────────────┘           │     │   │
│  │  │                    ▼                                        │     │   │
│  │  │     ┌──────────────────────────────────────────┐           │     │   │
│  │  │     │ Thought: "Enough info for diagnosis"     │           │     │   │
│  │  │     │ Action: ANSWER                           │           │     │   │
│  │  │     │ Root Cause: Manager capacity bottleneck  │           │     │   │
│  │  │     │ Fix: Update routing rules (based on Case │           │     │   │
│  │  │     │      #1234 from 2 weeks ago)             │           │     │   │
│  │  │     └──────────────────────────────────────────┘           │     │   │
│  │  │                                                             │     │   │
│  │  │     [Max 5 iterations, then force answer]                  │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  │                           ▼                                           │   │
│  │  ┌────────────────────────────────────────────────────────────┐     │   │
│  │  │  3. RESPONSE GENERATION                                    │     │   │
│  │  │     - Format diagnosis with evidence                       │     │   │
│  │  │     - Include precedent citations                          │     │   │
│  │  │     - Provide actionable recommendations                   │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  │                                                                       │   │
│  └───────────────────────────────┬───────────────────────────────────────┘   │
│                                  │                                           │
│                                  ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  EXECUTION LOGGER                                                    │   │
│  │  - Log reasoning trace to pgvector (for future pattern matching)    │   │
│  │  - Track cost, latency, tool calls                                  │   │
│  │  - Send to Langfuse for observability                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  USER RECEIVES ANSWER        │
                    │                              │
                    │  🔍 Root Cause Analysis      │
                    │  ├─ Manager capacity issue   │
                    │  ├─ 50% of tickets stuck at  │
                    │  │   "awaiting manager"      │
                    │  └─ 2 managers, 300 tickets  │
                    │                              │
                    │  💡 Recommendation           │
                    │  Update routing rule:        │
                    │  IF priority=LOW →           │
                    │     route to team-B         │
                    │  (Based on Case #1234)       │
                    └──────────────┬───────────────┘
                                   │
                     USER PROVIDES FEEDBACK
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REFLEXION LEARNING LOOP                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  SCENARIO A: User Approves                                          │   │
│  │  ───────────────────────────────────────────────────────────────────│   │
│  │  User: "✓ Fixed! Routing rule worked."                             │   │
│  │                                                                      │   │
│  │  System:                                                             │   │
│  │  1. Mark execution as SUCCESSFUL in pgvector                        │   │
│  │  2. Strengthen pattern: "Manager capacity → routing rule fix"       │   │
│  │  3. Future similar cases: Confidence score ↑                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  SCENARIO B: User Corrects                                          │   │
│  │  ───────────────────────────────────────────────────────────────────│   │
│  │  User: "✗ Wrong. We already updated routing. Real issue is that     │   │
│  │         tickets from source=API + priority=NORMAL need to skip       │   │
│  │         manager approval entirely."                                  │   │
│  │                                                                      │   │
│  │  System (Reflexion Agent):                                          │   │
│  │  1. Create episodic memory entry:                                   │   │
│  │     ┌────────────────────────────────────────────────────────────┐  │   │
│  │     │ <mistake>                                                  │  │   │
│  │     │   Assumed manager capacity issue. Recommended routing rule │  │   │
│  │     │   change (priority=LOW → team-B).                          │  │   │
│  │     │ </mistake>                                                 │  │   │
│  │     │                                                             │  │   │
│  │     │ <correction>                                               │  │   │
│  │     │   Real issue: Tickets from source=API + priority=NORMAL    │  │   │
│  │     │   should skip manager approval entirely.                   │  │   │
│  │     │ </correction>                                              │  │   │
│  │     │                                                             │  │   │
│  │     │ <revised_approach>                                         │  │   │
│  │     │   When analyzing stuck tickets:                            │  │   │
│  │     │   1. ALWAYS check ticket source (API vs Manual)            │  │   │
│  │     │   2. IF source=API, consider approval bypass rules first   │  │   │
│  │     │   3. THEN check manager capacity                           │  │   │
│  │     │                                                             │  │   │
│  │     │   New rule: source=API + priority=NORMAL → auto-approve    │  │   │
│  │     │ </revised_approach>                                        │  │   │
│  │     └────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │  2. Store in PostgreSQL:                                             │   │
│  │     INSERT INTO reflexion_memory (                                  │   │
│  │       execution_id,                                                 │   │
│  │       mistake,                                                      │   │
│  │       correction,                                                   │   │
│  │       revised_approach,                                             │   │
│  │       embedding  -- pgvector for semantic search                    │   │
│  │     )                                                               │   │
│  │                                                                      │   │
│  │  3. Next execution: ReAct agent loads this memory BEFORE reasoning  │   │
│  │     - Searches reflexion_memory for similar context                │   │
│  │     - Finds: "When stuck tickets + source=API, check bypass rules" │   │
│  │     - Applies learned heuristic                                     │   │
│  │     - Avoids repeating same mistake                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LEARNING METRICS (Tracked Over Time)                               │   │
│  │                                                                      │   │
│  │  Day 1:   Accuracy 60% (many corrections needed)                    │   │
│  │  Week 1:  Accuracy 75% (learning from 50+ corrections)              │   │
│  │  Month 1: Accuracy 92% (precedent DB has 500+ cases)                │   │
│  │  Month 3: Accuracy 95% (handles edge cases from 2000+ executions)   │   │
│  │                                                                      │   │
│  │  Competitive Moat: After 6 months, you have 10,000+ case precedents │   │
│  │                    Competitor starting from zero cannot catch up    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL + PGVECTOR                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  TABLE: skill_executions                                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  id               UUID PRIMARY KEY                                  │   │
│  │  skill_id         TEXT  -- "ecm/manager/analyze-stuck-tickets"      │   │
│  │  user_id          TEXT                                              │   │
│  │  team_id          TEXT                                              │   │
│  │  input_context    JSONB -- User question + params                   │   │
│  │  reasoning_trace  JSONB -- Full ReAct loop (thoughts + actions)     │   │
│  │  tool_calls       JSONB -- All tools executed                       │   │
│  │  output           TEXT  -- Final answer                             │   │
│  │  user_feedback    TEXT  -- NULL | "approved" | "corrected"          │   │
│  │  correction_text  TEXT  -- User's correction if provided            │   │
│  │  embedding        VECTOR(1536)  -- pgvector for similarity search   │   │
│  │  cost_usd         DECIMAL                                           │   │
│  │  latency_ms       INTEGER                                           │   │
│  │  created_at       TIMESTAMP                                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  TABLE: reflexion_memory                                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  id                UUID PRIMARY KEY                                 │   │
│  │  execution_id      UUID REFERENCES skill_executions(id)             │   │
│  │  mistake           TEXT  -- What the agent got wrong                │   │
│  │  correction        TEXT  -- What user said was actually right       │   │
│  │  revised_approach  TEXT  -- How to handle this in future            │   │
│  │  embedding         VECTOR(1536)  -- For semantic search             │   │
│  │  application_count INTEGER DEFAULT 0  -- Times this learning used   │   │
│  │  success_rate      DECIMAL  -- % of times this fix worked           │   │
│  │  created_at        TIMESTAMP                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  TABLE: pattern_library                                             │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  id               UUID PRIMARY KEY                                  │   │
│  │  domain           TEXT  -- "ecm" | "fincrime" | "fraud"             │   │
│  │  pattern_name     TEXT  -- "manager_capacity_bottleneck"            │   │
│  │  symptoms         JSONB -- {"stuck_pct": ">40%", "location": ...}   │   │
│  │  root_causes      JSONB -- ["capacity", "routing", "approval"]      │   │
│  │  solutions        JSONB -- Ranked by success rate                   │   │
│  │  precedent_ids    UUID[] -- Links to successful executions          │   │
│  │  confidence       DECIMAL -- Based on # of successful cases         │   │
│  │  last_seen        TIMESTAMP                                         │   │
│  │  embedding        VECTOR(1536)                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  INDEXES:                                                                    │
│  - CREATE INDEX ON skill_executions USING ivfflat (embedding vector_cosine) │
│  - CREATE INDEX ON reflexion_memory USING ivfflat (embedding vector_cosine) │
│  - CREATE INDEX ON pattern_library USING ivfflat (embedding vector_cosine)  │
│  - CREATE INDEX ON skill_executions(skill_id, created_at DESC)              │
│  - CREATE INDEX ON skill_executions(user_feedback) WHERE user_feedback IS   │
│    NOT NULL                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ReAct Agent Implementation

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
import asyncpg
import numpy as np

@dataclass
class ReActContext:
    """Context passed through ReAct reasoning loop"""
    user_id: str
    team_id: str
    domain: str
    question: str
    db_pool: asyncpg.Pool
    max_iterations: int = 5

    # Populated during execution
    reasoning_trace: list = None
    tool_calls: list = None
    precedents: list = None
    reflexion_memories: list = None

# Define tools available to the agent
async def query_tickets(ctx: RunContext[ReActContext], filters: dict) -> dict:
    """Query ECM tickets database"""
    # Implementation queries actual ticket data
    return {"tickets": [...], "count": 150}

async def analyze_assignments(ctx: RunContext[ReActContext]) -> dict:
    """Analyze ticket assignment patterns"""
    return {"stuck_at": "awaiting_manager", "percentage": 50}

async def search_similar_patterns(ctx: RunContext[ReActContext], symptoms: dict) -> list:
    """Search vector DB for similar past cases"""
    # Convert symptoms to embedding
    embedding = await get_embedding(str(symptoms))

    # Query pgvector for similar executions
    query = """
        SELECT
            id,
            input_context,
            output,
            user_feedback,
            1 - (embedding <=> $1) as similarity
        FROM skill_executions
        WHERE user_feedback = 'approved'
          AND (embedding <=> $1) < 0.3
        ORDER BY similarity DESC
        LIMIT 5
    """

    results = await ctx.deps.db_pool.fetch(query, embedding)
    return [dict(r) for r in results]

async def load_reflexion_memories(ctx: RunContext[ReActContext]) -> list:
    """Load relevant past corrections"""
    # Get embedding of current context
    embedding = await get_embedding(ctx.deps.question)

    query = """
        SELECT
            mistake,
            correction,
            revised_approach,
            success_rate,
            1 - (embedding <=> $1) as relevance
        FROM reflexion_memory
        WHERE (embedding <=> $1) < 0.4
        ORDER BY relevance DESC
        LIMIT 3
    """

    results = await ctx.deps.db_pool.fetch(query, embedding)
    return [dict(r) for r in results]

# Create ReAct agent
intelligence_agent = Agent(
    'openai:gpt-4',  # Or anthropic/claude-sonnet-4.5 via OpenRouter
    deps_type=ReActContext,
    system_prompt="""
You are an intelligent diagnostic agent using ReAct (Reasoning + Acting) approach.

BEFORE answering, you MUST:
1. Load reflexion memories (past mistakes to avoid)
2. Search for similar precedents
3. Reason step-by-step using Thought → Action → Observation pattern
4. Continue until you have sufficient evidence for diagnosis

FORMAT for each iteration:
Thought: [Your reasoning about what to do next]
Action: [Tool to call with parameters]
Observation: [Result from tool execution]

After 3-5 iterations, provide:
- Root Cause Analysis (with evidence)
- Recommendation (citing precedents if available)
- Confidence level

CRITICAL: If reflexion memories show you made this mistake before,
          apply the revised_approach IMMEDIATELY.
""",
    tools=[
        query_tickets,
        analyze_assignments,
        search_similar_patterns,
        load_reflexion_memories
    ]
)

async def execute_with_intelligence(
    skill_id: str,
    context: dict,
    db_pool: asyncpg.Pool
) -> dict:
    """Execute skill with intelligence layer"""

    # Create context
    react_context = ReActContext(
        user_id=context['user_id'],
        team_id=context['team_id'],
        domain=context['domain'],
        question=context['question'],
        db_pool=db_pool,
        reasoning_trace=[],
        tool_calls=[]
    )

    # Execute ReAct agent
    result = await intelligence_agent.run(
        context['question'],
        deps=react_context
    )

    # Extract reasoning trace for logging
    reasoning_trace = result.all_messages()  # Full Thought→Action→Observation chain

    # Store execution in pgvector
    execution_id = await store_execution(
        skill_id=skill_id,
        context=context,
        reasoning_trace=reasoning_trace,
        output=result.data,
        db_pool=db_pool
    )

    return {
        "execution_id": execution_id,
        "output": result.data,
        "reasoning_trace": reasoning_trace,
        "cost": result.cost(),
        "iterations": len([m for m in reasoning_trace if "Thought:" in m])
    }
```

---

## Reflexion Learning Loop

```python
async def handle_user_feedback(
    execution_id: str,
    feedback_type: str,  # "approved" | "corrected"
    correction_text: str | None,
    db_pool: asyncpg.Pool
):
    """Process user feedback and create reflexion memory if corrected"""

    if feedback_type == "approved":
        # Simply mark as successful
        await db_pool.execute(
            "UPDATE skill_executions SET user_feedback = 'approved' WHERE id = $1",
            execution_id
        )
        return

    # User provided correction - create reflexion memory

    # 1. Get original execution
    execution = await db_pool.fetchrow(
        "SELECT * FROM skill_executions WHERE id = $1",
        execution_id
    )

    # 2. Use LLM to extract structured learning
    reflexion_prompt = f"""
ORIGINAL QUESTION: {execution['input_context']['question']}

MY ANSWER: {execution['output']}

USER CORRECTION: {correction_text}

Extract a structured learning entry:
1. What mistake did I make in my reasoning?
2. What was the actual correct answer/approach?
3. How should I revise my approach for similar future cases?

Format:
<mistake>
[Detailed description of the error in reasoning]
</mistake>

<correction>
[What the user said was actually correct]
</correction>

<revised_approach>
[Specific steps to take in future similar situations]
Include: WHEN [conditions], THEN [approach]
</revised_approach>
"""

    reflection_result = await intelligence_agent.run(reflexion_prompt)

    # 3. Parse and store
    mistake = extract_tag(reflection_result.data, "mistake")
    correction = extract_tag(reflection_result.data, "correction")
    revised_approach = extract_tag(reflection_result.data, "revised_approach")

    # 4. Create embedding for semantic search
    learning_text = f"{mistake}\n{correction}\n{revised_approach}"
    embedding = await get_embedding(learning_text)

    # 5. Store reflexion memory
    await db_pool.execute("""
        INSERT INTO reflexion_memory (
            execution_id,
            mistake,
            correction,
            revised_approach,
            embedding
        ) VALUES ($1, $2, $3, $4, $5)
    """, execution_id, mistake, correction, revised_approach, embedding)

    # 6. Mark execution as corrected
    await db_pool.execute("""
        UPDATE skill_executions
        SET user_feedback = 'corrected',
            correction_text = $2
        WHERE id = $1
    """, execution_id, correction_text)

    print(f"✓ Reflexion memory created. Agent will learn from this correction.")
```

---

## Observability Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LANGFUSE OBSERVABILITY                            │
│                                                                              │
│  Trace Hierarchy:                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  EXECUTION                                                           │   │
│  │  ├─ SPAN: load_reflexion_memories (50ms)                            │   │
│  │  │  └─ Retrieved 2 relevant past corrections                        │   │
│  │  ├─ SPAN: search_similar_patterns (120ms)                           │   │
│  │  │  └─ Found 5 precedents with 85% avg confidence                   │   │
│  │  ├─ SPAN: react_iteration_1 (800ms)                                 │   │
│  │  │  ├─ Thought: "Need ticket data"                                  │   │
│  │  │  ├─ Action: query_tickets(status=stuck)                          │   │
│  │  │  └─ Observation: 150 tickets                                     │   │
│  │  ├─ SPAN: react_iteration_2 (600ms)                                 │   │
│  │  │  ├─ Thought: "Analyze assignment patterns"                       │   │
│  │  │  ├─ Action: analyze_assignments()                                │   │
│  │  │  └─ Observation: 50% stuck at manager                            │   │
│  │  ├─ SPAN: react_iteration_3 (400ms)                                 │   │
│  │  │  ├─ Thought: "Check precedents"                                  │   │
│  │  │  ├─ Action: search_similar_patterns(...)                         │   │
│  │  │  └─ Observation: 3 cases, routing fix worked                     │   │
│  │  ├─ SPAN: generate_answer (200ms)                                   │   │
│  │  └─ TOTAL: 2.17s, $0.08, 4 tool calls                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Metrics Tracked:                                                            │
│  - Reasoning iterations per execution (avg: 3.2)                             │
│  - Precedent utilization rate (% of answers citing past cases)               │
│  - Reflexion memory hit rate (% of executions using past corrections)        │
│  - User approval rate (Day 1: 60% → Month 1: 92%)                            │
│  - Cost per execution (with intelligence: $0.08 vs simple CRUD: $0.01)       │
│                                                                              │
│  DeepEval Custom Metrics:                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  @deepeval.metric                                                    │   │
│  │  class ReasoningQualityMetric(Metric):                               │   │
│  │      def measure(self, test_case):                                   │   │
│  │          # Check if reasoning trace is logical                       │   │
│  │          # Verify tool calls were necessary                          │   │
│  │          # Ensure precedents were cited when available               │   │
│  │          return score                                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Example Execution Flow (ECM Domain)

```
USER QUESTION:
"Why are so many tickets stuck for >24 hours?"

════════════════════════════════════════════════════════════════════════════

PHASE 1: Load Context
────────────────────────────────────────────────────────────────────────────
[REFLEXION MEMORY SEARCH]
Found 2 relevant past corrections:

Memory #1 (Relevance: 0.87):
  - Mistake: "Assumed manager capacity issue, recommended hiring"
  - Correction: "Real issue was routing rule for API tickets"
  - Revised: "ALWAYS check ticket source before capacity analysis"

Memory #2 (Relevance: 0.74):
  - Mistake: "Suggested increasing manager headcount"
  - Correction: "Need to check if tickets require manual approval"
  - Revised: "IF automated tickets → check approval bypass rules first"

════════════════════════════════════════════════════════════════════════════

PHASE 2: ReAct Reasoning Loop
────────────────────────────────────────────────────────────────────────────
ITERATION 1:
  Thought: "Based on reflexion memory, I should check ticket source FIRST
            before analyzing capacity. Let me get ticket data with source."

  Action: query_tickets(status="stuck", min_age_hours=24, include_source=True)

  Observation:
    Total: 150 tickets
    Breakdown:
      - source=API: 112 tickets (75%)
      - source=MANUAL: 38 tickets (25%)

────────────────────────────────────────────────────────────────────────────
ITERATION 2:
  Thought: "75% are API-originated. Memory #1 says check routing rules for
            API tickets. Let me analyze where they're stuck."

  Action: analyze_ticket_status(source="API")

  Observation:
    API tickets stuck at:
      - awaiting_manager_approval: 95 tickets (85% of API tickets)
      - awaiting_assignment: 17 tickets (15%)

────────────────────────────────────────────────────────────────────────────
ITERATION 3:
  Thought: "85% stuck at manager approval. But reflexion memory says check
            approval bypass rules. Let me search for similar past cases."

  Action: search_similar_patterns({
            "symptom": "stuck_tickets",
            "source": "API",
            "stage": "awaiting_approval"
          })

  Observation: Found 3 precedents

    Case #1234 (2 weeks ago, confidence: 0.92):
      - Same symptoms: API tickets stuck at approval
      - Root cause: Tickets with priority=NORMAL required manual approval
      - Solution: Added bypass rule "source=API AND priority=NORMAL → auto-approve"
      - Outcome: 90% reduction in stuck tickets

    Case #987 (1 month ago, confidence: 0.85):
      - Symptoms: Manual tickets stuck
      - Root cause: Manager capacity (2 managers, 300 tickets)
      - Solution: Hired temp reviewer
      - Outcome: 60% improvement

────────────────────────────────────────────────────────────────────────────
ITERATION 4:
  Thought: "Case #1234 is more relevant (API tickets, same symptom, higher
            confidence). Let me check if we have the same approval rule issue."

  Action: check_approval_rules(source="API", priority="NORMAL")

  Observation:
    Current rule: ALL API tickets require manager approval
    Exception rules: priority=CRITICAL → auto-escalate to director

    No bypass rule exists for priority=NORMAL API tickets

────────────────────────────────────────────────────────────────────────────
ITERATION 5:
  Thought: "I have enough evidence. The issue matches Case #1234 exactly.
            Time to provide diagnosis."

  Action: ANSWER

════════════════════════════════════════════════════════════════════════════

FINAL RESPONSE:
────────────────────────────────────────────────────────────────────────────
🔍 ROOT CAUSE ANALYSIS

Pattern Detected: API Ticket Approval Bottleneck
Confidence: 92% (based on precedent Case #1234)

Evidence:
├─ 150 tickets stuck >24 hours
├─ 112 (75%) are API-originated
├─ 95 (85% of API tickets) stuck at "awaiting_manager_approval"
└─ Current rules require ALL API tickets to get manual approval

Root Cause:
API tickets with priority=NORMAL are unnecessarily requiring manual manager
approval, creating a bottleneck.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDATION

Update approval workflow:
```yaml
approval_rules:
  - condition:
      source: API
      priority: NORMAL
    action: auto_approve
    reasoning: Low-risk automated tickets don't need manual review
```

Expected Impact:
- 90% reduction in stuck tickets (based on Case #1234 - implemented 2 weeks ago)
- Frees manager capacity for high-priority manual tickets
- Processing time: <1 hour instead of >24 hours

Similar Successful Resolutions:
• Case #1234 (2 weeks ago) - Same fix, 90% improvement ✓

Cost: $0.08 | Latency: 2.17s | Iterations: 5
────────────────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════════

USER FEEDBACK OPTIONS:
[Approve] [Correct] [Need More Info]
```

---

## Key Differentiators

| Feature | Traditional CRUD Skill | Intelligence Layer (ReAct + Reflexion) |
|---------|----------------------|----------------------------------------|
| **Query** | "show stuck tickets" | "WHY are tickets stuck?" |
| **Output** | List of 150 tickets | Root cause + precedent-based fix |
| **Learning** | None | Improves from every correction |
| **Precedents** | N/A | Cites past successful resolutions |
| **Cost** | $0.01 (Haiku) | $0.08 (Sonnet with reasoning) |
| **Latency** | 0.4s | 2-3s (multi-step reasoning) |
| **Value** | Data retrieval | Diagnostic + actionable insight |
| **Competitive Moat** | Replicable in 1 day | Requires 6+ months of precedent accumulation |

---

## Implementation Timeline (12-16 Hours)

**Phase 1 (0-4h): Foundation**
- Set up PostgreSQL with pgvector extension
- Create tables (skill_executions, reflexion_memory, pattern_library)
- Implement embedding generation (OpenAI text-embedding-3-small)
- Build basic vector search queries

**Phase 2 (4-8h): ReAct Agent**
- Implement ReAct agent with Pydantic AI
- Define tools (query_tickets, analyze_assignments, search_patterns)
- Build reasoning loop (max 5 iterations with force-answer)
- Test with 3-5 sample ECM scenarios

**Phase 3 (8-12h): Reflexion Loop**
- Implement feedback capture UI (Slack buttons: Approve/Correct)
- Build reflexion memory creation (LLM extracts structured learning)
- Integrate memory loading into ReAct agent pre-execution
- Test correction → learning → improved answer flow

**Phase 4 (12-16h): Observability**
- Integrate Langfuse for trace visualization
- Build DeepEval custom metrics (reasoning quality, precedent usage)
- Create Grafana dashboard (approval rate, memory hit rate, cost trends)
- Seed initial 100 executions for pattern library

---

## Success Metrics (After 1 Month)

1. **Approval Rate**: 60% (Day 1) → 92% (Month 1)
2. **Reflexion Memory Size**: 0 → 150+ corrections
3. **Precedent Library**: 0 → 500+ successful cases
4. **Average Iterations**: 4.5 → 3.2 (more efficient reasoning)
5. **Cost per Execution**: $0.08 → $0.06 (fewer wasted iterations)
6. **Time to Answer**: 3s → 2s (better tool selection)

**Competitive Moat**: Cannot be replicated without 6+ months of production usage and user corrections.
