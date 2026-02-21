# Wealth Copilot — Product & Technical Specification

> **One-liner:** Your personal AI wealth manager that understands your cross-border life and optimizes your financial life across countries and goals.

**Author:** Wealth Copilot Team
**Date:** 2026-02-14
**Status:** Draft v1.0

---

## Working Backwards (Amazon Methodology)

> **Start with the customer. Write the press release first. Build backwards.**

See [PRESS_RELEASE.md](./PRESS_RELEASE.md) for:
- **Press Release** — The launch announcement we're building towards
- **Customer FAQ** — Questions real users will ask
- **Internal FAQ** — Stakeholder questions with honest answers
- **Customer Letter** — A delighted user's testimonial (our north star)
- **Persist vs. Pivot Checkpoints** — 6-month evaluation criteria

**The one-liner we're building towards:**
> "Aspora Launches Wealth Copilot: The First AI Wealth Manager Built for Cross-Border Lives"

---

## Strategic Frameworks (from CTO Knowledge Engine)

### Decision Framework: Persist vs. Pivot (6-month checkpoints)

| Checkpoint | Measurement | Threshold |
|------------|-------------|-----------|
| Motivation & Energy | Team enthusiasm | >80% excited |
| Creative Flow | New skill ideas/month | >5 substantive |
| Learning Velocity | "Aha moments" about cross-border | >2/month |
| Confidence Trajectory | "Is this working?" | Increasing |
| External Validation | NPS, investor interest | NPS >50 |

### First 10 Customers (Stripe Atlas Framework)

**Priority matrix for customer acquisition:**
1. Warm network (Aspora remittance users)
2. Early adopter profile + intrinsically reachable
3. Single decision maker + discretionary budget
4. Active online presence (LinkedIn, NRI forums)

**Qualification criteria:**
- Cross-border (UAE/UK/US ↔ India)
- Investable assets > $25K
- Trades monthly (active investor)
- Technical early adopter

### Executive Leverage (Keith Rabois Framework)

> Output = (your team + neighboring teams) / team size

- **Hire only if** they increase output/people ratio
- **Judge inputs** (quality of strategy), not outputs (quarterly metrics)
- **High-leverage activities**: All-hands, dashboards, performance feedback

### Investor Psychology (Sam Altman Framework)

Investors bet on:
1. Market size and timing (cross-border = 280M+ people)
2. Team's unique ability to execute (fintech + AI)
3. Solution's fundamental advantage (skills-based architecture)
4. Founder's improvement rate (show progress across meetings)

---

## Executive Summary

Wealth Copilot is an AI-first, skills-based personal wealth management platform designed for cross-border individuals (NRIs, global citizens, expats). It combines:

1. **Conversational AI** — Cleo-style relationship building that drives retention
2. **Goal-Based Planning** — House deposits, education, retirement with currency-aware allocation
3. **Autonomous Trading** — Multi-agent system that executes strategies on user's behalf
4. **Skills Architecture** — Trainable, testable skills that become the competitive moat

**Key Insight (from Cleo):** Users spend extended time discussing finances with AI. This builds trust, brand association, and 80%+ retention. The AI relationship IS the product.

---

## Table of Contents

- [Working Backwards](#working-backwards-amazon-methodology)
- [Strategic Frameworks](#strategic-frameworks-from-cto-knowledge-engine)
1. [Problem Statement](#1-problem-statement)
2. [Target User](#2-target-user)
3. [Core Value Propositions](#3-core-value-propositions)
4. [System Architecture](#4-system-architecture)
5. [Agent System Design](#5-agent-system-design)
6. [Skills Catalog](#6-skills-catalog)
7. [Data Model](#7-data-model)
8. [Cross-Border Intelligence](#8-cross-border-intelligence)
9. [Trading Engine](#9-trading-engine)
10. [Testing Strategy (The Moat)](#10-testing-strategy-the-moat)
11. [UI/UX Philosophy](#11-uiux-philosophy)
12. [Aspora Integration Points](#12-aspora-integration-points)
13. [Tech Stack](#13-tech-stack)
14. [MVP Scope (Hackathon)](#14-mvp-scope-hackathon)
15. [Future Roadmap](#15-future-roadmap)
16. [Research Sources](#16-research-sources)

---

## 1. Problem Statement

**Cross-border individuals face fragmented wealth management:**

| Pain Point | Current State |
|------------|---------------|
| Multi-currency confusion | Assets in INR, USD, AED, GBP — no unified view |
| FX risk eroding returns | 10% India returns wiped out by 8% INR depreciation |
| Goal planning across borders | "How much in India vs abroad for my kid's US education?" |
| Tax complexity | DTAA, FBAR, NRE/NRO — manual compliance |
| Trust deficit | Robo-advisors feel impersonal; human advisors are expensive |
| Execution friction | Multiple broker accounts, manual rebalancing |

**The gap:** No platform combines relationship-driven AI, cross-border intelligence, goal-based planning, AND autonomous execution.

---

## 2. Target User

### Primary Persona: "Global Raj"

- **Demographics:** 32-45, working in UAE/UK/US, family in India
- **Income:** $80K-300K annually
- **Assets:** $50K-500K across multiple countries
- **Goals:**
  - House deposit in India (₹50L in 3 years)
  - Kids' international education ($200K in 15 years)
  - Retirement split between countries
- **Behavior:**
  - Checks portfolio 2-3x/week
  - Sends money home monthly
  - Anxious about FX timing
  - Wants to invest but paralyzed by complexity
- **Trust:** Will share financial data with AI after 3-4 positive interactions

### Secondary Personas

1. **"Tech-Savvy Priya"** — 28, single, aggressive growth, wants autonomous trading
2. **"Conservative Uncle"** — 55, near retirement, wants capital preservation + income
3. **"Busy Founder"** — 40, no time for finance, "just make it work"

---

## 3. Core Value Propositions

### 3.1 Relationship-First AI (Cleo Model)

```
Week 1:  "Hey! I noticed you transferred ₹2L to India. Planning something big?"
Week 2:  "Your USD investments are up 8%, but INR weakened 3%. Net gain: 5%. Want me to explain?"
Week 4:  "Based on our chats, I think you're more conservative than your portfolio suggests. Adjust?"
Month 2: "You mentioned your daughter's education. I've modeled 3 scenarios. Which resonates?"
Month 6: "Happy 6 months! Here's your wealth journey so far. You're 23% closer to your house goal."
```

**Key metrics:**
- Session length > 3 minutes (Cleo benchmark)
- Return visits > 3x/week
- Trust score (derived from data shared, questions asked)

### 3.2 Goal-Based Allocation Engine

```
┌─────────────────────────────────────────────────────────┐
│  GOAL: House Deposit in Mumbai                          │
│  Target: ₹50,00,000 | Timeline: 36 months               │
├─────────────────────────────────────────────────────────┤
│  Currency Mix:        │  Asset Allocation:              │
│  ├─ INR: 70%          │  ├─ Indian Debt MF: 40%         │
│  └─ USD: 30% (hedge)  │  ├─ Indian Equity MF: 30%       │
│                       │  ├─ US Treasury ETF: 20%        │
│  Monthly Target:      │  └─ Gold ETF: 10%               │
│  ₹1,20,000 (~$1,400)  │                                 │
├─────────────────────────────────────────────────────────┤
│  Progress: ████████░░░░░░░░░░ 42% ($21,000 / $50,000)   │
│  On Track: ✅ Ahead by 2 months                          │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Autonomous Trading with Human Oversight

```
┌─────────────────────────────────────────────────────────┐
│  TRADE PROPOSAL #247                                    │
├─────────────────────────────────────────────────────────┤
│  Action: REBALANCE                                      │
│  Sell: 50 units NIFTYBEES @ ₹245 (₹12,250)             │
│  Buy: 15 units GOLDBEES @ ₹52 (₹780)                   │
│  Buy: $90 VTI @ $280                                    │
├─────────────────────────────────────────────────────────┤
│  Reasoning:                                             │
│  • India equity overweight by 8% vs target              │
│  • Gold underweight — adding inflation hedge            │
│  • USD allocation low — INR weakening trend             │
│                                                         │
│  Risk Assessment: LOW (within normal rebalancing)       │
│  Tax Impact: ₹450 STCG (minimal)                        │
├─────────────────────────────────────────────────────────┤
│  [✅ Approve]  [✏️ Modify]  [❌ Reject]  [🤖 Auto-approve similar]  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WEALTH COPILOT                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Mobile    │  │    Web      │  │   Voice     │  │   WhatsApp  │ │
│  │    App      │  │   Portal    │  │  (Future)   │  │   (Future)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         └─────────────────┴─────────────────┴─────────────────┘     │
│                                   │                                  │
│  ┌────────────────────────────────▼────────────────────────────────┐│
│  │                    CONVERSATION LAYER                           ││
│  │  ┌─────────────────────────────────────────────────────────┐   ││
│  │  │  Copilot Agent (Orchestrator)                            │   ││
│  │  │  • Maintains conversation state & memory                  │   ││
│  │  │  • Routes to specialized agents                           │   ││
│  │  │  • Builds relationship over time                          │   ││
│  │  └─────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                   │                                  │
│  ┌────────────────────────────────▼────────────────────────────────┐│
│  │                    AGENT COLLECTIVE                             ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           ││
│  │  │ Research │ │ Trading  │ │   Risk   │ │  Goals   │           ││
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │           ││
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           ││
│  │       │            │            │            │                  ││
│  │  ┌────▼────────────▼────────────▼────────────▼────┐            ││
│  │  │              SKILLS RUNTIME                     │            ││
│  │  │  • Skill discovery & loading                    │            ││
│  │  │  • Skill execution & caching                    │            ││
│  │  │  • Skill testing & validation                   │            ││
│  │  └────────────────────────────────────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                   │                                  │
│  ┌────────────────────────────────▼────────────────────────────────┐│
│  │                    DATA & EXECUTION LAYER                       ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           ││
│  │  │ Market   │ │ Broker   │ │ Currency │ │ User     │           ││
│  │  │  Data    │ │ Gateway  │ │ Service  │ │ Store    │           ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Skills-Based Architecture (Core Innovation)

```
skills/
├── research/
│   ├── fundamental-analysis.skill.md
│   ├── technical-analysis.skill.md
│   ├── sentiment-analysis.skill.md
│   └── macro-analysis.skill.md
├── trading/
│   ├── place-order.skill.md
│   ├── rebalance-portfolio.skill.md
│   ├── tax-loss-harvest.skill.md
│   └── dca-execute.skill.md
├── goals/
│   ├── create-goal.skill.md
│   ├── track-progress.skill.md
│   ├── suggest-allocation.skill.md
│   └── adjust-timeline.skill.md
├── cross-border/
│   ├── fx-analysis.skill.md
│   ├── currency-hedge.skill.md
│   ├── remittance-optimize.skill.md
│   └── tax-implications.skill.md
├── relationship/
│   ├── onboarding.skill.md
│   ├── weekly-checkin.skill.md
│   ├── milestone-celebrate.skill.md
│   └── concern-address.skill.md
└── aspora/
    ├── product-recommend.skill.md
    ├── cross-sell.skill.md
    └── referral-program.skill.md
```

**Why Skills?**
1. **Trainable** — Each skill has test cases; improve by adding examples
2. **Composable** — Complex actions = skill chains
3. **Auditable** — Every decision traced to skill execution
4. **Versionable** — A/B test skill versions
5. **Explainable** — Users can ask "why" and get skill reasoning

---

## 5. Agent System Design

### 5.1 Agent Roles (Inspired by TradingAgents Framework)

```
┌─────────────────────────────────────────────────────────────────┐
│                    COPILOT (ORCHESTRATOR)                        │
│  • Maintains conversation context & user memory                  │
│  • Routes queries to specialized agents                          │
│  • Synthesizes multi-agent outputs for user                      │
│  • Builds trust through consistent personality                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ RESEARCH TEAM   │ │ TRADING TEAM    │ │ PLANNING TEAM   │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ • Fundamental   │ │ • Strategist    │ │ • Goals Advisor │
│   Analyst       │ │ • Executor      │ │ • Tax Planner   │
│ • Technical     │ │ • Risk Manager  │ │ • FX Specialist │
│   Analyst       │ │                 │ │                 │
│ • Sentiment     │ │                 │ │                 │
│   Analyst       │ │                 │ │                 │
│ • Macro         │ │                 │ │                 │
│   Analyst       │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 5.2 Agent Communication Protocol

```yaml
# Message format between agents
message:
  id: "msg_12345"
  from: "research.fundamental"
  to: "trading.strategist"
  type: "analysis_complete"
  payload:
    ticker: "RELIANCE.NS"
    recommendation: "BUY"
    confidence: 0.78
    reasoning: "Strong Q3 results, Jio growth trajectory"
    data_sources:
      - "quarterly_earnings"
      - "analyst_consensus"
      - "peer_comparison"
  metadata:
    timestamp: "2026-02-14T10:30:00Z"
    skill_used: "fundamental-analysis.skill.md"
    execution_time_ms: 1250
```

### 5.3 Decision Flow (Multi-Agent Collaboration)

```
User: "Should I buy Reliance?"
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ COPILOT: Parse intent → Route to Research Team              │
└─────────────────────────────────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┬──────────────┐
         ▼                  ▼                  ▼              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐   ┌─────────────┐
│ Fundamental │    │ Technical   │    │ Sentiment   │   │ Macro       │
│ Analysis    │    │ Analysis    │    │ Analysis    │   │ Analysis    │
│ ────────────│    │ ────────────│    │ ────────────│   │ ────────────│
│ P/E: 25x    │    │ RSI: 62     │    │ News: +0.7  │   │ Sector: +   │
│ Growth: 18% │    │ Trend: UP   │    │ Social: +0.4│   │ INR: Weak   │
│ Score: 7/10 │    │ Score: 7/10 │    │ Score: 6/10 │   │ Score: 6/10 │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘   └──────┬──────┘
       │                  │                  │                 │
       └──────────────────┴──────────────────┴─────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│ BULL-BEAR DEBATE (Researcher Agents)                        │
│ ────────────────────────────────────────────────────────────│
│ BULL: "Strong fundamentals, Jio monetization, retail play"  │
│ BEAR: "Valuation stretched, debt concerns, oil volatility"  │
│ SYNTHESIS: "Cautious BUY with 5% position size"             │
└─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│ RISK MANAGER: Check against user profile                    │
│ • Risk tolerance: MODERATE                                  │
│ • Current India allocation: 45% (target: 40%)               │
│ • Reliance already held: 3%                                 │
│ VERDICT: "Approve small addition (2%), reduces to DCA"      │
└─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│ COPILOT → USER:                                             │
│ "Based on analysis, Reliance looks decent but you're        │
│  already overweight India. I'd suggest:                     │
│  • Add ₹20,000 now (2% of portfolio)                        │
│  • Set up monthly SIP of ₹5,000                             │
│  • This aligns with your retirement goal (India exposure)   │
│                                                             │
│  Want me to set this up? Or shall we discuss alternatives?" │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Skills Catalog

### 6.1 Skill Definition Format

```yaml
# skills/trading/rebalance-portfolio.skill.md
---
name: rebalance-portfolio
version: 1.2.0
category: trading
triggers:
  - "rebalance my portfolio"
  - "my allocation is off"
  - "auto-rebalance"
  - regex: "rebalance.*goal"
inputs:
  - name: goal_id
    type: string
    required: false
    description: "Specific goal to rebalance for"
  - name: threshold
    type: number
    default: 5
    description: "Rebalance if drift > threshold %"
outputs:
  - name: trades
    type: array<Trade>
    description: "Proposed trades to execute"
  - name: reasoning
    type: string
    description: "Why these trades"
dependencies:
  - get-current-allocation
  - get-target-allocation
  - calculate-drift
  - generate-trades
  - estimate-tax-impact
connectors:
  - broker-gateway
  - market-data
guardrails:
  - max_single_trade_pct: 10
  - require_approval_above: 50000
  - blocked_during: ["market_closed", "high_volatility"]
tests:
  - test_basic_rebalance
  - test_tax_aware_rebalance
  - test_multi_currency_rebalance
  - test_no_action_within_threshold
---

# Rebalance Portfolio

## Purpose
Automatically generate trades to bring portfolio back to target allocation.

## Algorithm
1. Fetch current holdings across all brokers
2. Calculate current allocation percentages
3. Compare against target allocation (from goal or profile)
4. If drift > threshold:
   a. Identify overweight assets (sell candidates)
   b. Identify underweight assets (buy candidates)
   c. Generate trades to minimize drift
   d. Apply tax-loss harvesting if beneficial
   e. Estimate tax impact
5. Return trade proposals with reasoning

## Execution
Requires user approval unless auto-approve is enabled for rebalancing.
```

### 6.2 Core Skills (MVP)

| Category | Skill | Priority | Complexity |
|----------|-------|----------|------------|
| **Onboarding** | `collect-profile` | P0 | Low |
| | `risk-assessment` | P0 | Medium |
| | `link-accounts` | P0 | High |
| **Goals** | `create-goal` | P0 | Medium |
| | `track-goal-progress` | P0 | Low |
| | `suggest-allocation` | P0 | High |
| **Research** | `fundamental-analysis` | P1 | High |
| | `technical-indicators` | P1 | Medium |
| | `news-sentiment` | P1 | Medium |
| **Trading** | `place-order` | P1 | High |
| | `rebalance-portfolio` | P1 | High |
| | `dca-setup` | P1 | Medium |
| **Cross-Border** | `fx-rate-analysis` | P0 | Medium |
| | `remittance-timing` | P1 | High |
| | `currency-allocation` | P0 | Medium |
| **Relationship** | `weekly-summary` | P0 | Low |
| | `milestone-notification` | P1 | Low |
| | `proactive-insight` | P1 | Medium |

### 6.3 Skill Composition Example

```
User: "Set up my daughter's education fund"

Skill Chain:
1. create-goal.skill.md
   → Collect: name, target amount, timeline, currency
   → Output: goal_id: "edu_001"

2. suggest-allocation.skill.md
   → Input: goal_id, timeline (15 years), risk (moderate-aggressive)
   → Output: { "US_EQUITY": 50%, "INDIA_EQUITY": 30%, "BONDS": 20% }

3. currency-allocation.skill.md
   → Input: goal (education in US), current_location (UAE)
   → Output: { "USD": 70%, "INR": 30% }
   → Reasoning: "Education in US, hedge INR exposure"

4. dca-setup.skill.md
   → Input: monthly_contribution, allocation
   → Output: Scheduled monthly investments

5. weekly-checkin.skill.md (scheduled)
   → "Your education fund grew 2.3% this month. On track for 2041!"
```

---

## 7. Data Model

### 7.1 Core Entities

```typescript
// User & Profile
interface User {
  id: string;
  email: string;
  phone: string;
  created_at: Date;
  kyc_status: 'pending' | 'verified' | 'rejected';
}

interface UserProfile {
  user_id: string;
  name: string;
  date_of_birth: Date;
  residency: {
    current: CountryCode;    // UAE
    tax_residencies: CountryCode[];  // [UAE, India]
    citizenships: CountryCode[];     // [India]
  };
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  investment_experience: 'beginner' | 'intermediate' | 'expert';
  income_bracket: string;
  employment_type: 'salaried' | 'self_employed' | 'business_owner';
  preferences: {
    communication_frequency: 'daily' | 'weekly' | 'monthly';
    auto_approve_threshold: number;  // USD
    excluded_sectors: string[];      // e.g., ['tobacco', 'gambling']
  };
}

// Goals
interface Goal {
  id: string;
  user_id: string;
  name: string;
  type: 'house' | 'education' | 'retirement' | 'emergency' | 'custom';
  target_amount: Money;
  target_date: Date;
  priority: number;
  target_allocation: Allocation;
  currency_mix: CurrencyAllocation;
  status: 'active' | 'paused' | 'achieved' | 'abandoned';
  progress: GoalProgress;
}

interface GoalProgress {
  current_value: Money;
  percentage: number;
  projected_completion_date: Date;
  monthly_required: Money;
  on_track: boolean;
}

// Portfolio
interface Portfolio {
  user_id: string;
  holdings: Holding[];
  total_value: Money;
  allocation: Allocation;
  currency_exposure: CurrencyAllocation;
  last_updated: Date;
}

interface Holding {
  id: string;
  asset: Asset;
  quantity: number;
  average_cost: Money;
  current_value: Money;
  unrealized_pnl: Money;
  unrealized_pnl_pct: number;
  broker_id: string;
  goal_tags: string[];  // Which goals this holding serves
}

// Trading
interface Trade {
  id: string;
  user_id: string;
  type: 'BUY' | 'SELL';
  asset: Asset;
  quantity: number;
  price: Money;
  status: 'proposed' | 'approved' | 'executing' | 'completed' | 'failed' | 'rejected';
  proposed_by: string;  // agent_id
  reasoning: string;
  skill_trace: SkillExecution[];
  approval: {
    required: boolean;
    approved_at?: Date;
    approved_by?: 'user' | 'auto';
  };
  execution: {
    broker_id: string;
    order_id: string;
    executed_at: Date;
    executed_price: Money;
    fees: Money;
  };
}

// Conversation & Memory
interface Conversation {
  id: string;
  user_id: string;
  started_at: Date;
  messages: Message[];
  context: ConversationContext;
}

interface UserMemory {
  user_id: string;
  facts: Fact[];           // "Has daughter named Ananya, age 5"
  preferences: Preference[]; // "Prefers weekly updates on Sunday"
  concerns: Concern[];      // "Worried about INR depreciation"
  milestones: Milestone[];  // "Celebrated 1 year anniversary"
  trust_score: number;      // 0-100, increases over time
}

// Cross-Border Specific
interface CurrencyAllocation {
  [currency: string]: {
    percentage: number;
    reason: string;
  };
}

interface RemittancePlan {
  user_id: string;
  from_currency: CurrencyCode;
  to_currency: CurrencyCode;
  monthly_amount: Money;
  preferred_rate_threshold?: number;
  auto_execute: boolean;
  history: RemittanceExecution[];
}
```

### 7.2 Skill Execution Trace (For Testing & Debugging)

```typescript
interface SkillExecution {
  id: string;
  skill_name: string;
  skill_version: string;
  started_at: Date;
  completed_at: Date;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  llm_calls: LLMCall[];
  connector_calls: ConnectorCall[];
  sub_skills: SkillExecution[];  // Nested skill calls
  error?: SkillError;
}

interface LLMCall {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  prompt_hash: string;  // For test reproducibility
}
```

---

## 8. Cross-Border Intelligence

### 8.1 Currency Risk Engine

```
┌─────────────────────────────────────────────────────────────┐
│                  CURRENCY RISK DASHBOARD                     │
├─────────────────────────────────────────────────────────────┤
│  Your Exposure:                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  INR ████████████████░░░░ 65%  │ At Risk: HIGH      │    │
│  │  USD ████████░░░░░░░░░░░░ 25%  │ Stable             │    │
│  │  AED ████░░░░░░░░░░░░░░░░ 10%  │ Pegged to USD      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  INR Trend (vs USD): -4.2% YTD                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │     85 ─┐                                           │    │
│  │     84 ─┤    ╭───╮                      ╭──         │    │
│  │     83 ─┤───╯    ╰──────────╮    ╭─────╯           │    │
│  │     82 ─┤                    ╰──╯                   │    │
│  │         Jan  Feb  Mar  Apr  May  Jun  Jul          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ⚠️ Alert: Your India returns (12%) are offset by INR       │
│     depreciation (4.2%). Real return: 7.8%                  │
│                                                              │
│  💡 Suggestion: Consider hedging 20% of INR exposure        │
│     via USD-denominated India ETFs                          │
│                                                              │
│  [Explain More]  [Apply Hedge]  [Dismiss]                   │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Remittance Optimizer

```typescript
interface RemittanceOptimization {
  // When user needs to send money home
  analyze(request: {
    amount: Money;
    from: CurrencyCode;
    to: CurrencyCode;
    urgency: 'immediate' | 'this_week' | 'this_month' | 'flexible';
    purpose: 'family' | 'investment' | 'property' | 'other';
  }): RemittanceRecommendation;
}

// Example output
{
  "recommendation": "WAIT",
  "current_rate": 83.45,
  "predicted_rate_7d": 83.12,
  "potential_savings": "$45 on $10,000",
  "confidence": 0.72,
  "reasoning": "INR showing short-term strength due to RBI intervention. Suggest waiting 3-5 days.",
  "alternatives": [
    {
      "action": "SPLIT",
      "description": "Send 50% now, 50% in 7 days",
      "benefit": "Reduces timing risk"
    },
    {
      "action": "USE_ASPORA",
      "description": "Aspora offers 83.52 rate (better than market)",
      "benefit": "Save $70 on fees"
    }
  ]
}
```

### 8.3 Tax-Aware Decisions

```yaml
# Cross-border tax considerations baked into every decision
tax_awareness:
  scenarios:
    - name: "NRI selling India mutual funds"
      considerations:
        - LTCG > 1L taxed at 10% (equity) / 20% with indexation (debt)
        - TDS applicable, can claim refund
        - No DTAA benefit for capital gains (India-UAE)
      skill_action: "Flag tax impact before execution"

    - name: "US ETF dividends for UAE resident"
      considerations:
        - 30% US withholding tax (no DTAA)
        - Consider Ireland-domiciled ETFs (15% withholding)
      skill_action: "Recommend UCITS ETFs over US ETFs"

    - name: "Repatriating funds from India"
      considerations:
        - NRO → overseas: Subject to TDS, limits apply
        - NRE: Freely repatriable
      skill_action: "Suggest NRE routing for investments"
```

---

## 9. Trading Engine

### 9.1 Broker Integrations (Adapter Pattern)

```typescript
// Base adapter interface
interface BrokerAdapter {
  // Connection
  connect(credentials: BrokerCredentials): Promise<void>;
  disconnect(): Promise<void>;
  isConnected(): boolean;

  // Portfolio
  getHoldings(): Promise<Holding[]>;
  getBalance(): Promise<Balance>;

  // Trading
  placeOrder(order: Order): Promise<OrderResult>;
  cancelOrder(orderId: string): Promise<void>;
  getOrderStatus(orderId: string): Promise<OrderStatus>;

  // Market Data
  getQuote(symbol: string): Promise<Quote>;
  getHistoricalData(symbol: string, range: DateRange): Promise<OHLCV[]>;
}

// Implementations
class ZerodhaAdapter implements BrokerAdapter { ... }
class UpstoxAdapter implements BrokerAdapter { ... }
class GrowwAdapter implements BrokerAdapter { ... }
class AlpacaAdapter implements BrokerAdapter { ... }  // US
class InteractiveBrokersAdapter implements BrokerAdapter { ... }  // Global
```

### 9.2 Execution Engine

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Trade Queue                    Execution Status             │
│  ┌─────────────────────┐       ┌─────────────────────┐      │
│  │ 1. BUY NIFTYBEES    │──────▶│ ✅ Completed        │      │
│  │ 2. SELL RELIANCE    │──────▶│ ⏳ Pending approval │      │
│  │ 3. BUY VTI          │──────▶│ 🔄 Executing...    │      │
│  │ 4. BUY GOLDBEES     │       │ ⏸️ Queued          │      │
│  └─────────────────────┘       └─────────────────────┘      │
│                                                              │
│  Safety Controls:                                            │
│  ├─ ✅ Market hours check                                   │
│  ├─ ✅ Position size limits                                 │
│  ├─ ✅ Daily loss limits                                    │
│  ├─ ✅ Duplicate order detection                            │
│  └─ ✅ Approval workflow                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 Paper Trading Mode

```typescript
class PaperTradingEngine {
  // Simulated portfolio with real market data
  private virtualPortfolio: Portfolio;
  private tradeHistory: Trade[];

  // Uses real market data, simulated execution
  async executeOrder(order: Order): Promise<OrderResult> {
    const quote = await this.marketData.getQuote(order.symbol);
    // Simulate slippage
    const executedPrice = this.applySlippage(quote.price, order.type);
    // Update virtual portfolio
    this.updatePortfolio(order, executedPrice);
    return { status: 'FILLED', price: executedPrice };
  }

  // Performance tracking
  getPerformanceMetrics(): PerformanceMetrics {
    return {
      totalReturn: this.calculateReturn(),
      sharpeRatio: this.calculateSharpe(),
      maxDrawdown: this.calculateMaxDrawdown(),
      winRate: this.calculateWinRate(),
    };
  }
}
```

---

## 10. Testing Strategy (The Moat)

### 10.1 Testing Philosophy

> "Tests are training data for skills. The more tests, the better the skill performs."

```
┌─────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ╱ E2E Tests ╲                            │
│                   ╱  (10 tests) ╲         User journeys     │
│                  ╱───────────────╲                          │
│                 ╱ Integration     ╲                         │
│                ╱  (50 tests)       ╲      Agent + Skills    │
│               ╱─────────────────────╲                       │
│              ╱    Skill Tests        ╲                      │
│             ╱     (200 tests)         ╲   Per-skill         │
│            ╱───────────────────────────╲                    │
│           ╱       Unit Tests            ╲                   │
│          ╱        (500 tests)            ╲  Core logic      │
│         ╱─────────────────────────────────╲                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Skill Testing Framework

```typescript
// skills/__tests__/rebalance-portfolio.test.ts

describe('rebalance-portfolio skill', () => {
  // Table-driven tests
  const testCases: SkillTestCase[] = [
    {
      name: 'basic_rebalance_equity_overweight',
      input: {
        current_allocation: { equity: 70, debt: 20, gold: 10 },
        target_allocation: { equity: 60, debt: 30, gold: 10 },
        portfolio_value: 100000,
      },
      expected: {
        trades: [
          { type: 'SELL', asset_class: 'equity', amount: 10000 },
          { type: 'BUY', asset_class: 'debt', amount: 10000 },
        ],
        reasoning: expect.stringContaining('equity overweight'),
      },
    },
    {
      name: 'no_rebalance_within_threshold',
      input: {
        current_allocation: { equity: 62, debt: 28, gold: 10 },
        target_allocation: { equity: 60, debt: 30, gold: 10 },
        threshold: 5,
      },
      expected: {
        trades: [],
        reasoning: expect.stringContaining('within threshold'),
      },
    },
    {
      name: 'multi_currency_rebalance',
      input: {
        holdings: [
          { symbol: 'NIFTYBEES', currency: 'INR', value: 50000 },
          { symbol: 'VTI', currency: 'USD', value: 30000 },
        ],
        target_currency_mix: { INR: 40, USD: 60 },
      },
      expected: {
        trades: expect.arrayContaining([
          expect.objectContaining({ type: 'SELL', currency: 'INR' }),
          expect.objectContaining({ type: 'BUY', currency: 'USD' }),
        ]),
      },
    },
    {
      name: 'tax_loss_harvesting_opportunity',
      input: {
        holdings: [
          { symbol: 'INFY', cost: 1500, current: 1200, unrealized_loss: -300 },
        ],
        rebalance_needed: true,
      },
      expected: {
        trades: expect.arrayContaining([
          expect.objectContaining({
            type: 'SELL',
            symbol: 'INFY',
            reasoning: expect.stringContaining('tax loss'),
          }),
        ]),
      },
    },
  ];

  testCases.forEach(({ name, input, expected }) => {
    it(name, async () => {
      const result = await executeSkill('rebalance-portfolio', input);
      expect(result).toMatchObject(expected);
    });
  });
});
```

### 10.3 Agent Conversation Tests

```typescript
// agents/__tests__/copilot-conversations.test.ts

describe('Copilot conversation flows', () => {
  const conversationTests = [
    {
      name: 'new_user_onboarding',
      conversation: [
        { user: "Hi, I'm new here", expect_skill: 'onboarding' },
        { user: "I'm 35, work in Dubai", expect_memory: { age: 35, location: 'UAE' } },
        { user: "I want to save for a house in India", expect_skill: 'create-goal' },
        { user: "Around 50 lakhs in 3 years", expect_goal: { type: 'house', amount: 5000000, currency: 'INR' } },
      ],
    },
    {
      name: 'returning_user_goal_check',
      setup: { user_id: 'test_user_1', goals: [{ name: 'House', progress: 42 }] },
      conversation: [
        { user: "How's my house goal?", expect_response: /42%|on track/ },
        { user: "Can I speed it up?", expect_skill: 'adjust-timeline' },
      ],
    },
    {
      name: 'cross_border_concern',
      conversation: [
        { user: "I'm worried about the rupee falling", expect_skill: 'fx-analysis' },
        { user: "Should I move money to USD?", expect_response: /currency.*allocation|hedge/ },
      ],
    },
  ];

  conversationTests.forEach(({ name, conversation, setup }) => {
    it(name, async () => {
      const copilot = await createCopilot(setup);
      for (const turn of conversation) {
        const response = await copilot.chat(turn.user);
        if (turn.expect_skill) {
          expect(response.skills_used).toContain(turn.expect_skill);
        }
        if (turn.expect_response) {
          expect(response.text).toMatch(turn.expect_response);
        }
        if (turn.expect_memory) {
          expect(copilot.memory).toMatchObject(turn.expect_memory);
        }
      }
    });
  });
});
```

### 10.4 Financial Accuracy Tests

```typescript
// core/__tests__/financial-calculations.test.ts

describe('Financial calculations', () => {
  describe('Goal projection', () => {
    it('calculates future value with monthly SIP', () => {
      const result = calculateFutureValue({
        principal: 100000,
        monthlyContribution: 10000,
        annualReturn: 0.12,
        years: 10,
      });
      expect(result).toBeCloseTo(3300386, -2);  // ~33L
    });

    it('calculates required SIP for goal', () => {
      const result = calculateRequiredSIP({
        targetAmount: 5000000,  // 50L
        currentSavings: 500000,  // 5L
        annualReturn: 0.10,
        years: 5,
      });
      expect(result).toBeCloseTo(55000, -3);  // ~55K/month
    });
  });

  describe('Currency conversion', () => {
    it('handles multi-hop conversion', () => {
      // AED → USD → INR
      const result = convertCurrency({
        amount: 10000,
        from: 'AED',
        to: 'INR',
        rates: { 'AED/USD': 0.27, 'USD/INR': 83.5 },
      });
      expect(result).toBeCloseTo(225450, -1);
    });
  });

  describe('Tax calculations', () => {
    it('calculates India LTCG correctly', () => {
      const result = calculateIndiaLTCG({
        gains: 200000,
        holdingPeriod: 400,  // days
        assetType: 'equity_mf',
      });
      // First 1L exempt, 10% on rest
      expect(result.tax).toBe(10000);
    });
  });
});
```

### 10.5 Backtesting Framework

```typescript
// backtesting/strategy-backtest.ts

interface BacktestConfig {
  strategy: string;         // Skill or strategy name
  startDate: Date;
  endDate: Date;
  initialCapital: number;
  benchmark: string;        // e.g., 'NIFTY50'
}

interface BacktestResult {
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  benchmarkReturn: number;
  alpha: number;
  trades: Trade[];
  equityCurve: TimeSeries;
}

// Example: Backtest goal-based rebalancing
const result = await backtest({
  strategy: 'goal-based-rebalancing',
  startDate: new Date('2020-01-01'),
  endDate: new Date('2025-12-31'),
  initialCapital: 1000000,
  benchmark: 'NIFTY50',
  config: {
    target_allocation: { equity: 60, debt: 30, gold: 10 },
    rebalance_threshold: 5,
    rebalance_frequency: 'quarterly',
  },
});

console.log(result);
// {
//   totalReturn: 0.89,          // 89% over 5 years
//   annualizedReturn: 0.136,    // 13.6% CAGR
//   sharpeRatio: 1.2,
//   maxDrawdown: -0.18,         // 18% max drawdown
//   benchmarkReturn: 0.72,      // Nifty: 72%
//   alpha: 0.034,               // 3.4% alpha
// }
```

### 10.6 Test Coverage Requirements

| Component | Min Coverage | Critical Paths |
|-----------|-------------|----------------|
| Skills | 90% | All triggers, edge cases |
| Agents | 85% | Decision flows, error handling |
| Trading Engine | 95% | Order execution, risk checks |
| Financial Calcs | 100% | All formulas, edge cases |
| Cross-Border | 90% | Currency, tax, compliance |

---

## 11. UI/UX Philosophy

### 11.1 Design Principles

1. **Conversation-First** — Chat is primary interface, not buried in a corner
2. **Progressive Disclosure** — Show summary, reveal detail on demand
3. **Confidence Through Transparency** — Always show reasoning, never magic
4. **Celebrate Progress** — Milestones, streaks, goal progress front and center
5. **Minimal Anxiety** — Green/positive framing, gentle notifications

### 11.2 Key Screens

```
┌─────────────────────────────────────────────────────────────┐
│                      HOME SCREEN                             │
├─────────────────────────────────────────────────────────────┤
│  Good morning, Raj! ☀️                                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Net Worth: $124,500                    ↑ 2.3% MTD  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Goals Progress                                              │
│  ┌─────────────────────┐ ┌─────────────────────┐            │
│  │ 🏠 House Deposit    │ │ 🎓 Ananya's Education│            │
│  │ ████████░░ 72%      │ │ ██░░░░░░░░ 15%      │            │
│  │ ₹36L / ₹50L        │ │ $30K / $200K        │            │
│  │ On track ✅         │ │ 14 years to go      │            │
│  └─────────────────────┘ └─────────────────────┘            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  💬 "Your INR investments outperformed this week.   │    │
│  │      Want me to explain the currency impact?"       │    │
│  │                                                     │    │
│  │  [Yes, explain]  [Show portfolio]  [Later]          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│  │  💬  Chat with Copilot                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 11.3 Chat Interface

```
┌─────────────────────────────────────────────────────────────┐
│  CHAT WITH COPILOT                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 🤖 Based on your goals and risk profile, I've    │        │
│  │    generated 3 trade suggestions for this month: │        │
│  │                                                   │        │
│  │    1. Buy ₹15,000 NIFTYBEES (equity allocation)  │        │
│  │    2. Buy $200 VTI (US exposure)                 │        │
│  │    3. Add ₹5,000 to SGB (gold hedge)             │        │
│  │                                                   │        │
│  │    Total: ₹28,500 (~$340)                        │        │
│  │                                                   │        │
│  │    [✅ Approve All] [Review Each] [Skip]          │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│        ┌─────────────────────────────────────────┐          │
│        │ Why VTI instead of VOO?                 │ You      │
│        └─────────────────────────────────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 🤖 Great question! VTI gives you total US market │        │
│  │    exposure (3,500+ stocks) vs VOO's S&P 500.   │        │
│  │                                                   │        │
│  │    For your 15-year education goal, the small-   │        │
│  │    cap exposure in VTI historically adds ~0.5%   │        │
│  │    annual return.                                │        │
│  │                                                   │        │
│  │    That said, VOO is fine too. Prefer VOO?       │        │
│  │                                                   │        │
│  │    [Keep VTI] [Switch to VOO] [Compare more]     │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Type a message...                              📎 🎤│    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Aspora Integration Points

### 12.1 Natural Cross-Sell Opportunities

| User Signal | Aspora Product | Skill Trigger |
|-------------|---------------|---------------|
| "Sending money to India" | Remittance service | `remittance-optimize` |
| High INR exposure | FX hedging products | `currency-hedge` |
| New goal created | Savings account | `product-recommend` |
| Large idle cash | Fixed deposits | `suggest-parking` |
| International travel | Travel card | `travel-prep` |

### 12.2 Integration Architecture

```typescript
interface AsporaConnector {
  // Remittance
  getRemittanceRates(): Promise<RemittanceRate[]>;
  initiateTransfer(request: TransferRequest): Promise<TransferResult>;

  // Products
  getEligibleProducts(userId: string): Promise<Product[]>;
  applyForProduct(userId: string, productId: string): Promise<ApplicationResult>;

  // Account linking
  linkAsporaAccount(userId: string): Promise<void>;
  getAccountBalance(): Promise<Balance>;
}
```

### 12.3 Cross-Sell Skill

```yaml
# skills/aspora/cross-sell.skill.md
---
name: aspora-cross-sell
triggers:
  - goal_created
  - remittance_initiated
  - high_cash_balance
  - currency_concern
guardrails:
  - max_frequency: once_per_week
  - relevance_threshold: 0.7
  - user_opt_out: respected
---

# Natural Product Recommendation

## Principles
1. Only recommend when genuinely beneficial
2. Explain WHY this product helps their goal
3. Never pushy — offer, don't insist
4. Track acceptance rate, optimize for user value

## Example Flow
User: "I need to send ₹5L to India for my property payment"

Copilot: "I can help with that! A few options:

1. **Aspora Remittance** — Current rate: 83.52 (0.08% better than market)
   - Fee: $0 for transfers > $5,000
   - Arrives in 24 hours

2. **Your bank** — Rate: ~83.20, Fee: ~$40

The Aspora route saves you ~$85 on this transfer.

[Use Aspora] [Use my bank] [Compare more options]"
```

---

## 13. Tech Stack

### 13.1 Recommended Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React + TypeScript | Industry standard, component ecosystem |
| **Mobile** | React Native or Expo | Code sharing with web |
| **Backend** | Node.js + TypeScript | Skill system, fast iteration |
| **Agent Framework** | LangGraph | Multi-agent orchestration (proven in TradingAgents) |
| **LLM** | Claude 3.5 (primary), GPT-4 (fallback) | Quality reasoning, function calling |
| **Database** | PostgreSQL | Relational, JSONB for flexibility |
| **Cache** | Redis | Session, rate limiting, real-time |
| **Queue** | Bull (Redis-based) | Trade execution, async jobs |
| **Market Data** | Alpha Vantage, Yahoo Finance, NSE APIs | Cost-effective, sufficient for MVP |
| **Broker SDKs** | Zerodha Kite, Alpaca | India + US coverage |
| **Testing** | Jest, Playwright | Unit + E2E |
| **Infra** | Vercel (web), Railway/Render (API) | Fast deployment, low ops |

### 13.2 Project Structure

```
wealth-copilot/
├── SPEC.md                    # This file
├── README.md
├── apps/
│   ├── web/                   # React web app
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   └── stores/
│   │   └── package.json
│   └── mobile/                # React Native (future)
├── packages/
│   ├── core/                  # Shared business logic
│   │   ├── src/
│   │   │   ├── entities/      # Domain models
│   │   │   ├── services/      # Business logic
│   │   │   └── utils/         # Financial calculations
│   │   └── package.json
│   ├── agents/                # Agent system
│   │   ├── src/
│   │   │   ├── copilot/       # Main orchestrator
│   │   │   ├── research/      # Research agents
│   │   │   ├── trading/       # Trading agents
│   │   │   └── planning/      # Goal planning agents
│   │   └── package.json
│   └── skills/                # Skill definitions
│       ├── research/
│       ├── trading/
│       ├── goals/
│       ├── cross-border/
│       ├── relationship/
│       └── aspora/
├── services/
│   └── api/                   # Backend API
│       ├── src/
│       │   ├── routes/
│       │   ├── middleware/
│       │   ├── connectors/    # Broker, market data
│       │   └── jobs/          # Background jobs
│       └── package.json
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── backtests/
├── docs/
│   └── adr/                   # Architecture decisions
├── scripts/
├── turbo.json                 # Monorepo config
└── package.json
```

---

## 14. MVP Scope (Hackathon)

### 14.1 What's IN for MVP (48-72 hours)

| Feature | Priority | Effort |
|---------|----------|--------|
| Chat interface with Copilot | P0 | 4h |
| User onboarding flow | P0 | 3h |
| Goal creation & tracking | P0 | 4h |
| Portfolio view (manual entry) | P0 | 3h |
| 3-5 core skills working | P0 | 8h |
| Basic allocation suggestions | P0 | 4h |
| Currency exposure view | P1 | 3h |
| Paper trading mode | P1 | 4h |
| Skill test suite (20+ tests) | P0 | 4h |
| Demo data & scenarios | P0 | 2h |

**Total: ~40 hours of focused work**

### 14.2 What's OUT for MVP

- Real broker integration (use paper trading)
- Mobile app (web only)
- Advanced tax calculations
- Real-time market data (use delayed)
- Voice interface
- Full Aspora integration
- Backtesting UI

### 14.3 MVP Demo Script

```
SCENE 1: Onboarding (2 min)
- New user signs up
- Copilot asks about location, goals, risk
- User creates "House in India" goal

SCENE 2: Portfolio Setup (2 min)
- User adds existing holdings manually
- Copilot analyzes allocation, currency mix
- Shows gap vs goal target

SCENE 3: Conversation & Trust (3 min)
- User asks "Am I on track?"
- Copilot shows progress, suggests adjustments
- User asks "Why are you suggesting more USD?"
- Copilot explains currency risk, shows INR trend

SCENE 4: Trade Suggestion (2 min)
- Copilot proposes monthly rebalancing trades
- User reviews reasoning
- Approves trades (paper mode executes)

SCENE 5: Cross-Border Insight (1 min)
- Copilot: "You mentioned sending money home. Want me to track rates?"
- Natural Aspora mention
```

---

## 15. Future Roadmap

### Phase 2 (Post-Hackathon, 1-2 months)

- [ ] Real broker integration (Zerodha, Alpaca)
- [ ] Automated DCA execution
- [ ] Tax report generation
- [ ] Mobile app (React Native)
- [ ] Voice interface (Cleo 3.0 style)

### Phase 3 (3-6 months)

- [ ] Advanced research agents (sentiment, technical)
- [ ] Backtesting UI for strategies
- [ ] Social features (anonymous benchmarking)
- [ ] Full Aspora product suite integration
- [ ] Regulatory compliance (RIA registration?)

### Phase 4 (6-12 months)

- [ ] WhatsApp integration
- [ ] Family accounts (joint goals)
- [ ] Estate planning module
- [ ] B2B white-label for banks/fintechs

---

## 16. Hackathon-Winning Features (From Research)

> **Full research synthesis:** See [RESEARCH_SYNTHESIS.md](./RESEARCH_SYNTHESIS.md)

### What Wins AI Trading Hackathons

Based on analysis of Agent Arena, OpenBB, Microsoft AI Agents, and YC Demo Day winners:

| Pattern | Why It Wins | Our Implementation |
|---------|-------------|-------------------|
| **Multi-Agent Dashboard** | Shows sophistication | 5+ agents visible, real-time status |
| **30+ Data Sources** | Demonstrates depth | News, social, market, geopolitical |
| **News Intelligence** | Novel, impressive | RSS → GPT-4 → trading signals |
| **Live Execution** | Proves production-ready | Paper trading with real prices |
| **Explainable AI** | Builds trust | Show reasoning for every decision |
| **Social Impact Angle** | Judges love this | "Financial inclusion for global citizens" |

### News Intelligence Skill (High Demo Impact)

```yaml
# skills/research/news-intelligence.skill.md
sources:
  - google_news_rss
  - economic_times_rss
  - rbi_announcements
  - fed_announcements

classification:
  - NOISE: Ignore
  - FUD: Potential sell signal
  - ALPHA: Potential buy signal
  - CROSS_BORDER: INR/USD impact

output:
  - sentiment_score: -1.0 to +1.0
  - goal_impact: Which goals affected
  - action_recommendation: What to do
  - explanation: Why (for user trust)
```

### "Vibe Watcher" (Inspired by OpenClaw)

Monitor high-impact accounts and events:
- **Political**: RBI Governor, Finance Minister, Fed Chair
- **Economic**: CPI releases, GDP announcements, rate decisions
- **Geopolitical**: Tariffs, sanctions, conflicts affecting INR/USD

Automatically adjust risk parameters when volatility detected.

### Demo Script (Updated for Hackathon Win)

```
SCENE 1: The Hook (30 sec)
"280 million people live cross-border lives.
Every finance app treats them like single-country investors.
Wealth Copilot is the first AI that understands cross-border wealth."

SCENE 2: News Intelligence (45 sec)
[LIVE DEMO]
- News feed processing in real-time
- "RBI announcement detected" → shows sentiment classification
- "Impact on your ₹50L house goal: -2.3%"
- One-tap hedge recommendation

SCENE 3: Multi-Agent Collaboration (45 sec)
[DASHBOARD VIEW]
- 5 agents: News, Sentiment, Technical, Risk, Execution
- Watch them "think" in real-time
- Show message passing between agents
- Final recommendation synthesis

SCENE 4: The Trade (30 sec)
- Agent proposes: "Reduce INR exposure by 10%"
- Shows reasoning chain (3 data sources cited)
- User approves → Paper trade executes
- Portfolio updates instantly

SCENE 5: The Moat (30 sec)
"Our architecture is skills-based.
Every conversation becomes a test case.
We've written 200+ tests in 48 hours.
That's not just code—that's a learning system."
```

### Agent Arena Winner Pattern (Rogue - $3,000 1st Place)

```
What Rogue had:
├── 10+ specialized agents coordinating
├── 30+ data sources
├── Social sentiment from Twitter/X
├── Whale movement tracking
├── React dashboard + Voice AI
└── 24/7 autonomous execution

What we adapt:
├── 5+ specialized agents (Research, Trading, Planning teams)
├── 15+ data sources (news, market, FX, geopolitical)
├── News sentiment classification
├── Currency volatility tracking ("INR Index")
├── React dashboard + goal visualization
└── Paper trading with approval workflow
```

---

## 17. Research Sources

### Hackathon Winners
- [Agent Arena Winners](https://blog.iqai.com/agent-arena-hackathon-winners-announced/) — Rogue ($3K), Athenea ($2K), CryptoInsight AI ($1K)
- [OpenBB Hackathon](https://openbb.co/blog/highlights-from-the-openbb-sponsored-fintech-ai-hackathon) — Financial Analysis Bot, Fin-RWKV
- [Microsoft AI Agents Hackathon](https://microsoft.github.io/AI_Agents_Hackathon/winners/)

### Technical References
- [OpenClaw Trading Assistant](https://github.com/molt-bot/openclaw-trading-assistant) — Multi-agent trading architecture
- [MarketBot](https://github.com/EthanAlgoX/MarketBot) — Finance-focused AI agent
- [TradingAgents Framework](https://github.com/TauricResearch/TradingAgents) — Multi-agent LLM trading
- [News Trading Bot Learnings](https://profitview.net/blog/what-i-learned-when-building-an-ai-news-trading-bot) — RSS → GPT → signals

### Architecture & Patterns
- [TradingAgents Framework](https://github.com/TauricResearch/TradingAgents) — Multi-agent LLM trading architecture
- [AWS: Agentic AI Patterns for Financial Services](https://aws.amazon.com/blogs/industries/agentic-ai-in-financial-services-choosing-the-right-pattern-for-multi-agent-systems/)
- [FinceptTerminal](https://github.com/Fincept-Corporation/FinceptTerminal) — Comprehensive financial terminal architecture

### Product Inspiration
- [VibeTrader](https://vibetrader.markets/portfolio) — Natural language trading strategies
- [Cleo AI](https://web.meetcleo.com/) — Relationship-driven fintech AI
- [Cleo 3.0 Launch](https://techintelpro.com/news/finance/financial-services/cleo-30-launches-as-ai-financial-coach-with-voice-and-memory) — Voice & memory features

### Cross-Border Wealth Management
- [WealthMunshi NRI Guide](https://wealthmunshi.com/ai-powered-personalized-financial-strategies-nris-2026-guide/) — AI strategies for NRIs
- [Green Portfolio: Currency Risk](https://greenportfolio.co/blog/currency-risk-killing-india-returns/) — FX impact on India returns
- [iNRI Platform](https://www.goinri.com/) — NRI financial super-app
- [Belong: NRI Asset Allocation](https://getbelong.com/blog/asset-allocation-investing-india/) — India allocation strategies

### Goal-Based Investing
- [InvestSuite: Goal-Based Robo-Advisors](https://www.investsuite.com/insights/blogs/what-are-the-best-robo-advisor-apps-for-goal-based-personalized-investing-key-features-and-considerations)
- [Britannica: AI for Retirement Planning](https://www.britannica.com/money/ai-for-retirement-financial-planning)

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **NRI** | Non-Resident Indian |
| **NRE/NRO** | NRI bank account types (External/Ordinary) |
| **DTAA** | Double Tax Avoidance Agreement |
| **LTCG** | Long-Term Capital Gains |
| **SIP** | Systematic Investment Plan |
| **DCA** | Dollar Cost Averaging |
| **FX** | Foreign Exchange |
| **AUM** | Assets Under Management |

---

## Appendix B: Competitive Landscape

| Competitor | Strengths | Gaps |
|------------|-----------|------|
| **Cleo** | Relationship AI, retention | No investing, US-only |
| **Wealthfront** | Goal-based, tax-loss harvest | No cross-border, no chat |
| **INDmoney** | India NRI focus | Limited AI, no autonomous trading |
| **Groww** | Great UX, India | No cross-border intelligence |
| **VibeTrader** | NL trading strategies | No goal planning, US-only |

**Wealth Copilot's Unique Position:** Cross-border intelligence + Relationship AI + Goal-based + Autonomous execution. No one does all four.

---

*Document generated: 2026-02-14*
*Ready for hackathon build.*
