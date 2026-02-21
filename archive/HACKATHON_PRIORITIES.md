# Hackathon Implementation Priorities

> **Goal:** Build an AI-first, skills-based trading platform with extensibility moat for future wealth integrations (gold, crypto, real estate).

---

## CEO Framework Validation (Pre-Build Check)

### Persist vs Pivot Criteria (Source: Aditya Agarwal)

Before investing 48-72 hours, validate against the 5 heuristics:

| Heuristic | Status | Evidence |
|-----------|--------|----------|
| **1. Motivation & Energy** | ✅ | Building for Aspora's NRI customers — real users, real pain |
| **2. Creative Flow** | ✅ | Novel angles: currency impact visualization, feedback-as-moat, cross-border intelligence |
| **3. Learning Velocity** | ✅ | NRI sentiment research revealed deep pain points (currency "invisible thief", scam victims) |
| **4. Confidence Trajectory** | ✅ | Each research phase increased conviction (Cleo's $250M ARR validates relationship AI) |
| **5. Smart Friend Feedback** | ⏳ | Validate with team before building |

**Verdict:** PERSIST — all 4 validated heuristics are green.

### First 10 Customers Strategy (Source: Stripe Atlas)

For hackathon demo, identify 10 NRI personas who would use this:

| # | Persona | Pain Point | How We Solve |
|---|---------|------------|--------------|
| 1 | Dubai techie, family in India | "My 12% returns are really 4% after currency" | Currency impact visualization |
| 2 | UK nurse, parents depend on remittances | "Am I sending money at the right time?" | FX timing alerts |
| 3 | US grad, education fund for siblings | "How much do I actually need in dollars?" | Goal-based multi-currency planning |
| 4 | Singapore banker, multiple goals | "I can't track progress across currencies" | Unified dashboard |
| 5 | Canada engineer, first-time investor | "I don't trust robo-advisors" | Transparent multi-agent reasoning |
| 6 | Australia doctor, retirement planning | "No one understands NRI tax complexity" | Tax-aware rebalancing |
| 7 | Germany scientist, parents' medical fund | "I'm paralyzed by choices" | AI-guided allocation |
| 8 | UAE businessman, property in India | "I need to time my big transfers" | Rate alert system |
| 9 | New Zealand developer, diversification | "I want exposure to both markets" | Cross-border portfolio view |
| 10 | Ireland teacher, emergency fund | "I need liquidity but also growth" | Goal-matched allocation |

**Hackathon Validation:** Build demo flow that resonates with persona #1 (Dubai techie).

---

## Core Architecture: AI-First with Feedback Loops

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WEALTH COPILOT CORE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    AI ORCHESTRATION LAYER                        │    │
│  │  • Conversation Engine (Claude/GPT-4)                            │    │
│  │  • Skill Router (matches intent → skill)                         │    │
│  │  • Feedback Collector (every interaction → training data)        │    │
│  │  • User Persona Engine (risk profile, goals, preferences)        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      SKILLS RUNTIME                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │    │
│  │  │  MARKET      │ │  TRADING     │ │  ANALYSIS    │             │    │
│  │  │  SKILLS      │ │  SKILLS      │ │  SKILLS      │             │    │
│  │  ├──────────────┤ ├──────────────┤ ├──────────────┤             │    │
│  │  │• get-quote   │ │• place-order │ │• fundamental │             │    │
│  │  │• get-history │ │• rebalance   │ │• technical   │             │    │
│  │  │• watchlist   │ │• stop-loss   │ │• sentiment   │             │    │
│  │  │• alerts      │ │• dca-execute │ │• news-intel  │             │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘             │    │
│  │                                                                  │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │    │
│  │  │  PERSONA     │ │  SAFETY      │ │  ONBOARDING  │             │    │
│  │  │  SKILLS      │ │  SKILLS      │ │  SKILLS      │             │    │
│  │  ├──────────────┤ ├──────────────┤ ├──────────────┤             │    │
│  │  │• risk-assess │ │• loss-limit  │ │• broker-link │             │    │
│  │  │• goal-match  │ │• position-cap│ │• kyc-verify  │             │    │
│  │  │• strategy-   │ │• volatility- │ │• tutorial    │             │    │
│  │  │  recommend   │ │  pause       │ │• first-trade │             │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  BROKER ADAPTER LAYER                            │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │    │
│  │  │ PAPER   │ │ INDIA   │ │   US    │ │  GOLD   │ │ CRYPTO  │   │    │
│  │  │ TRADING │ │ STOCKS  │ │ STOCKS  │ │ (future)│ │ (future)│   │    │
│  │  ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤   │    │
│  │  │ Mock    │ │ Zerodha │ │ Alpaca  │ │ GoldAPI │ │ Binance │   │    │
│  │  │ Engine  │ │ Groww   │ │ IBKR    │ │ Augmont │ │ Coinbase│   │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   FEEDBACK & LEARNING LOOP                       │    │
│  │  • Every skill execution logged with outcome                     │    │
│  │  • User corrections become test cases                            │    │
│  │  • Skill performance metrics (accuracy, latency, user approval)  │    │
│  │  • A/B test skill versions                                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Priority 1: Foundation (Hours 0-12)

### 1.1 AI Orchestration Core

```typescript
// packages/core/src/orchestrator.ts

interface Orchestrator {
  // Main entry point
  chat(userId: string, message: string): Promise<Response>;

  // Skill routing
  routeToSkill(intent: Intent): Skill;

  // Feedback loop
  recordOutcome(executionId: string, outcome: Outcome): void;

  // Persona engine
  getPersona(userId: string): UserPersona;
  updatePersona(userId: string, insights: Insight[]): void;
}

interface UserPersona {
  id: string;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  investmentHorizon: 'short' | 'medium' | 'long';
  goals: Goal[];
  preferredMarkets: Market[];
  tradingStyle: 'passive' | 'active' | 'day-trader';
  experienceLevel: 'beginner' | 'intermediate' | 'expert';

  // Learned from interactions
  behavioralInsights: {
    approvalRate: number;        // How often they approve suggestions
    riskActual: number;          // Observed vs stated risk tolerance
    preferredAssets: string[];   // What they actually trade
    activeHours: string[];       // When they engage
  };
}
```

### 1.2 Skills Runtime

```typescript
// packages/skills/src/runtime.ts

interface SkillDefinition {
  name: string;
  version: string;
  triggers: string[];
  inputs: InputSchema;
  outputs: OutputSchema;

  // Safety constraints
  guardrails: {
    maxPositionSize?: number;
    requiresApproval?: boolean;
    blockedDuring?: string[];    // e.g., ['market_closed', 'high_volatility']
    cooldownMs?: number;
  };

  // For feedback loop
  testCases: TestCase[];
}

interface SkillExecution {
  id: string;
  skillName: string;
  skillVersion: string;
  userId: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;

  // Feedback data
  startedAt: Date;
  completedAt: Date;
  userApproved: boolean | null;
  userFeedback?: string;
  outcome?: 'success' | 'failure' | 'partial';

  // For learning
  llmCalls: LLMCall[];
  confidence: number;
}
```

### 1.3 Broker Adapter Interface

```typescript
// packages/brokers/src/adapter.ts

interface BrokerAdapter {
  // Identity
  name: string;
  market: 'india' | 'us' | 'uk' | 'crypto' | 'gold';
  supportedAssets: AssetType[];

  // Connection
  connect(credentials: Credentials): Promise<void>;
  disconnect(): Promise<void>;
  isConnected(): boolean;

  // Portfolio
  getHoldings(): Promise<Holding[]>;
  getBalance(): Promise<Balance>;

  // Market Data
  getQuote(symbol: string): Promise<Quote>;
  getHistoricalData(symbol: string, range: DateRange): Promise<OHLCV[]>;

  // Trading
  placeOrder(order: Order): Promise<OrderResult>;
  cancelOrder(orderId: string): Promise<void>;
  getOrderStatus(orderId: string): Promise<OrderStatus>;

  // Safety
  getPositionLimits(): PositionLimits;
  validateOrder(order: Order): ValidationResult;
}

// Paper trading adapter (MVP)
class PaperTradingAdapter implements BrokerAdapter {
  name = 'paper';
  market = 'all';
  // ... implements all methods with simulated execution
}
```

---

## Priority 2: Safety & Trust (Hours 12-20)

### 2.1 Loss Prevention System (Configurable)

```yaml
# config/risk-profiles/default.yaml
---
# Risk profile presets - users can customize or create their own

profiles:
  conservative:
    name: "Capital Preservation"
    description: "Prioritize protecting your capital"
    limits:
      max_daily_loss_pct: 2
      max_position_pct: 5
      max_single_trade_pct: 1
      require_stop_loss: true
      stop_loss_default_pct: 5
      volatility_pause_multiplier: 2  # Pause if volatility > 2x normal
      max_open_positions: 10
      max_leverage: 1.0  # No leverage
    alerts:
      warn_at_loss_pct: 1
      notify_large_trade_above: 0.5  # % of portfolio

  moderate:
    name: "Balanced Growth"
    description: "Balance between growth and protection"
    limits:
      max_daily_loss_pct: 5
      max_position_pct: 10
      max_single_trade_pct: 2
      require_stop_loss: true
      stop_loss_default_pct: 8
      volatility_pause_multiplier: 3
      max_open_positions: 20
      max_leverage: 1.0
    alerts:
      warn_at_loss_pct: 3
      notify_large_trade_above: 1.5

  aggressive:
    name: "Maximum Growth"
    description: "Higher risk for potentially higher returns"
    limits:
      max_daily_loss_pct: 10
      max_position_pct: 20
      max_single_trade_pct: 5
      require_stop_loss: false  # Optional for aggressive
      stop_loss_default_pct: 15
      volatility_pause_multiplier: 5
      max_open_positions: 50
      max_leverage: 2.0
    alerts:
      warn_at_loss_pct: 5
      notify_large_trade_above: 3

  day_trader:
    name: "Active Day Trading"
    description: "For experienced traders with high activity"
    limits:
      max_daily_loss_pct: 8
      max_position_pct: 25
      max_single_trade_pct: 10
      require_stop_loss: true
      stop_loss_default_pct: 3  # Tighter stops
      volatility_pause_multiplier: null  # No auto-pause
      max_open_positions: 100
      max_leverage: 4.0
    alerts:
      warn_at_loss_pct: 4
      notify_large_trade_above: 5

  # Platform-enforced absolute limits (cannot be overridden)
  platform_limits:
    absolute_max_daily_loss_pct: 25
    absolute_max_position_pct: 50
    absolute_max_leverage: 10.0
    min_stop_loss_pct: 1  # If enabled, must be at least 1%
```

```yaml
# skills/safety/loss-prevention.skill.md
---
name: loss-prevention
version: 2.0.0
category: safety
triggers:
  - automatic (every trade)
  - "change my risk settings"
  - "update loss limits"
configurable: true
---

# Loss Prevention Agent (Configurable)

## Configuration Hierarchy

```
Platform Limits (absolute, non-negotiable)
    ↓
Risk Profile Defaults (conservative/moderate/aggressive/day_trader)
    ↓
User Customizations (within profile bounds)
    ↓
Per-Trade Overrides (with explicit acknowledgment)
```

## User Customization Options

Users can adjust within their profile's bounds:

```typescript
interface UserRiskConfig {
  // Inherit from profile, then override
  baseProfile: 'conservative' | 'moderate' | 'aggressive' | 'day_trader';

  // User customizations (must be within profile bounds)
  overrides: {
    max_daily_loss_pct?: number;
    max_position_pct?: number;
    max_single_trade_pct?: number;
    require_stop_loss?: boolean;
    stop_loss_default_pct?: number;
    volatility_pause_enabled?: boolean;
    volatility_pause_multiplier?: number;
  };

  // Per-asset overrides
  assetOverrides: {
    [symbol: string]: {
      max_position_pct?: number;
      stop_loss_pct?: number;
    };
  };

  // Notification preferences
  notifications: {
    email_on_limit_breach: boolean;
    push_on_large_trade: boolean;
    daily_risk_summary: boolean;
  };
}
```

## Validation Logic

```typescript
function validateRiskConfig(
  userConfig: UserRiskConfig,
  profileDefaults: RiskProfile,
  platformLimits: PlatformLimits
): ValidationResult {
  const errors = [];

  // Check against platform absolute limits
  if (userConfig.overrides.max_daily_loss_pct > platformLimits.absolute_max_daily_loss_pct) {
    errors.push(`Daily loss limit cannot exceed ${platformLimits.absolute_max_daily_loss_pct}%`);
  }

  // Check against profile bounds (profiles define reasonable ranges)
  const profileMax = profileDefaults.limits.max_daily_loss_pct * 1.5; // Allow 50% above profile default
  if (userConfig.overrides.max_daily_loss_pct > profileMax) {
    errors.push(`For ${profileDefaults.name} profile, daily loss limit should not exceed ${profileMax}%`);
  }

  return { valid: errors.length === 0, errors };
}
```

## Per-Trade Override Flow

```
User requests trade exceeding their limits
    ↓
AI explains: "This trade is 8% of your portfolio. Your limit is 5%."
    ↓
Options:
  1. [Reduce to 5%] - Adjust trade to fit limits
  2. [Override this once] - Explicit acknowledgment required
  3. [Update my limits] - Modify risk profile
  4. [Cancel] - Abort trade
    ↓
If override selected:
  - User confirms: "I understand this exceeds my 5% limit"
  - Override logged with timestamp, reason, acknowledgment
  - Trade executes
  - Risk team can review override patterns
```

## Enforcement Levels

| Level | Description | Overridable |
|-------|-------------|-------------|
| **HARD** | Platform absolute limits | Never |
| **FIRM** | Profile defaults | With acknowledgment |
| **SOFT** | User preferences | Freely adjustable |
| **ADVISORY** | AI recommendations | Suggestions only |
```

```typescript
// packages/core/src/safety/risk-config.ts

interface RiskConfigService {
  // Get effective config for user (merges profile + user overrides)
  getEffectiveConfig(userId: string): Promise<EffectiveRiskConfig>;

  // Update user's risk profile
  setBaseProfile(userId: string, profile: RiskProfileType): Promise<void>;

  // Update specific overrides
  updateOverrides(userId: string, overrides: Partial<RiskOverrides>): Promise<ValidationResult>;

  // Validate a trade against user's config
  validateTrade(userId: string, trade: ProposedTrade): Promise<TradeValidation>;

  // Request override for specific trade
  requestOverride(userId: string, tradeId: string, acknowledgment: string): Promise<OverrideResult>;

  // Get override history (for audit/learning)
  getOverrideHistory(userId: string): Promise<OverrideEvent[]>;
}

// Example usage
const config = await riskConfigService.getEffectiveConfig(userId);
console.log(config);
// {
//   baseProfile: 'moderate',
//   effectiveLimits: {
//     max_daily_loss_pct: 5,        // From profile
//     max_position_pct: 8,          // User reduced from 10
//     max_single_trade_pct: 2,      // From profile
//     require_stop_loss: true,      // From profile
//     stop_loss_default_pct: 10,    // User increased from 8
//   },
//   assetOverrides: {
//     'RELIANCE.NS': { max_position_pct: 15 }  // User allows more for this stock
//   }
// }
```

### 2.2 Position Sizing by Persona

```typescript
// packages/core/src/safety/position-sizing.ts

function calculatePositionSize(
  persona: UserPersona,
  trade: ProposedTrade,
  portfolio: Portfolio
): PositionSize {

  const riskMultiplier = {
    conservative: 0.5,
    moderate: 1.0,
    aggressive: 1.5,
  }[persona.riskTolerance];

  const experienceMultiplier = {
    beginner: 0.5,
    intermediate: 0.8,
    expert: 1.0,
  }[persona.experienceLevel];

  const baseSize = portfolio.totalValue * 0.02; // 2% base
  const adjustedSize = baseSize * riskMultiplier * experienceMultiplier;

  return {
    amount: Math.min(adjustedSize, trade.requestedAmount),
    reasoning: `Based on ${persona.riskTolerance} risk tolerance and ${persona.experienceLevel} experience`,
  };
}
```

### 2.3 Security Architecture

```typescript
// Security layers

interface SecurityConfig {
  // API Key encryption
  encryption: {
    algorithm: 'AES-256-GCM';
    keyDerivation: 'PBKDF2';
  };

  // Rate limiting
  rateLimits: {
    ordersPerMinute: 10;
    ordersPerDay: 100;
    apiCallsPerMinute: 60;
  };

  // Audit logging
  auditLog: {
    logAllTrades: true;
    logAllApprovals: true;
    retentionDays: 365;
  };

  // 2FA for sensitive operations
  requireMFA: {
    withdrawals: true;
    brokerConnection: true;
    riskLimitChange: true;
  };
}
```

---

## Priority 3: Persona & Strategy Engine (Hours 20-28)

### 3.1 User Persona Assessment

```yaml
# skills/onboarding/risk-assessment.skill.md
---
name: risk-assessment
version: 1.0.0
triggers:
  - "assess my risk"
  - new_user_signup
---

# Risk Assessment Skill

## Questions (Progressive Disclosure)

### Level 1: Basic (5 questions)
1. "What's your investment timeline?" (1-3 years / 3-10 years / 10+ years)
2. "How would you feel if your portfolio dropped 20%?" (Sell immediately / Hold and wait / Buy more)
3. "What's your primary goal?" (Preserve capital / Steady growth / Aggressive growth)
4. "How much investing experience do you have?" (New / Some / Expert)
5. "What percentage of your income are you investing?" (< 10% / 10-30% / > 30%)

### Level 2: Behavioral (observed, not asked)
- Approval rate on trade suggestions
- Time taken to approve trades
- How often they check portfolio
- Response to market volatility

### Output
{
  "riskTolerance": "moderate",
  "riskScore": 6.5,  // 1-10 scale
  "investmentHorizon": "medium",
  "tradingStyle": "passive",
  "confidenceLevel": 0.85,
  "suggestedStrategy": "balanced-growth"
}
```

### 3.2 Strategy Recommendation Engine

```typescript
// packages/core/src/strategy/recommender.ts

interface StrategyProfile {
  name: string;
  description: string;

  allocation: {
    equity: number;
    debt: number;
    gold: number;
    cash: number;
  };

  rebalanceFrequency: 'monthly' | 'quarterly' | 'yearly';

  suitableFor: {
    riskTolerance: ('conservative' | 'moderate' | 'aggressive')[];
    horizon: ('short' | 'medium' | 'long')[];
    goals: string[];
  };
}

const STRATEGIES: StrategyProfile[] = [
  {
    name: 'capital-preservation',
    description: 'Focus on protecting capital with minimal risk',
    allocation: { equity: 20, debt: 60, gold: 10, cash: 10 },
    rebalanceFrequency: 'yearly',
    suitableFor: {
      riskTolerance: ['conservative'],
      horizon: ['short', 'medium'],
      goals: ['emergency-fund', 'short-term-goal'],
    },
  },
  {
    name: 'balanced-growth',
    description: 'Balance between growth and stability',
    allocation: { equity: 50, debt: 30, gold: 10, cash: 10 },
    rebalanceFrequency: 'quarterly',
    suitableFor: {
      riskTolerance: ['moderate'],
      horizon: ['medium', 'long'],
      goals: ['house-deposit', 'education'],
    },
  },
  {
    name: 'aggressive-growth',
    description: 'Maximize growth for long-term goals',
    allocation: { equity: 80, debt: 10, gold: 5, cash: 5 },
    rebalanceFrequency: 'monthly',
    suitableFor: {
      riskTolerance: ['aggressive'],
      horizon: ['long'],
      goals: ['retirement', 'wealth-building'],
    },
  },
];

function recommendStrategy(persona: UserPersona): StrategyProfile {
  // Match persona to strategy
  return STRATEGIES.find(s =>
    s.suitableFor.riskTolerance.includes(persona.riskTolerance) &&
    s.suitableFor.horizon.includes(persona.investmentHorizon)
  ) || STRATEGIES[1]; // Default to balanced
}
```

---

## Priority 4: Multi-Market Configuration (Hours 28-36)

### 4.1 Market Configuration System

```yaml
# config/markets/india.yaml
---
market:
  id: india
  name: "Indian Stock Market"
  currency: INR
  timezone: "Asia/Kolkata"

trading_hours:
  pre_market: "09:00-09:15"
  regular: "09:15-15:30"
  post_market: "15:30-16:00"
  holidays_url: "https://api.nse.co.in/holidays"

brokers:
  - id: zerodha
    name: "Zerodha Kite"
    api_type: "kite_connect"
    supported_assets: ["equity", "mutual_fund", "etf"]
    requires_2fa: true

  - id: groww
    name: "Groww"
    api_type: "groww_api"
    supported_assets: ["equity", "mutual_fund"]

indices:
  - symbol: "NIFTY50"
    name: "Nifty 50"

  - symbol: "SENSEX"
    name: "BSE Sensex"

default_assets:
  - symbol: "NIFTYBEES"
    type: "etf"
    description: "Nifty 50 ETF"

  - symbol: "GOLDBEES"
    type: "etf"
    description: "Gold ETF"

tax_rules:
  stcg_rate: 0.15  # 15% for < 1 year
  ltcg_rate: 0.10  # 10% for > 1 year, above 1L
  ltcg_exemption: 100000
```

```yaml
# config/markets/us.yaml
---
market:
  id: us
  name: "US Stock Market"
  currency: USD
  timezone: "America/New_York"

trading_hours:
  pre_market: "04:00-09:30"
  regular: "09:30-16:00"
  post_market: "16:00-20:00"

brokers:
  - id: alpaca
    name: "Alpaca"
    api_type: "alpaca_v2"
    supported_assets: ["equity", "etf"]
    paper_trading: true

  - id: ibkr
    name: "Interactive Brokers"
    api_type: "ibkr_api"
    supported_assets: ["equity", "etf", "options", "futures"]

indices:
  - symbol: "SPY"
    name: "S&P 500 ETF"

  - symbol: "QQQ"
    name: "Nasdaq 100 ETF"

default_assets:
  - symbol: "VTI"
    type: "etf"
    description: "Total Stock Market"

  - symbol: "VXUS"
    type: "etf"
    description: "International Stock"
```

### 4.2 Broker Onboarding Skills

```yaml
# skills/onboarding/broker-connect.skill.md
---
name: broker-connect
version: 1.0.0
triggers:
  - "connect my broker"
  - "link Zerodha"
  - "add Alpaca account"
---

# Broker Connection Skill

## Supported Brokers

### India
1. **Zerodha Kite**
   - Requires: Kite Connect API key + secret
   - Auth: OAuth redirect flow
   - Setup time: ~5 minutes

2. **Groww**
   - Requires: API credentials from developer portal
   - Setup time: ~3 minutes

### US
1. **Alpaca (Recommended for paper trading)**
   - Requires: API key + secret
   - Paper trading: Built-in
   - Setup time: ~2 minutes

2. **Interactive Brokers**
   - Requires: IB Gateway setup
   - Setup time: ~15 minutes

## Connection Flow

1. User selects broker from list
2. Show step-by-step credentials guide (with screenshots)
3. Validate credentials with test API call
4. Fetch initial portfolio snapshot
5. Set up webhook for real-time updates
6. Confirm connection + show holdings

## Error Handling

- Invalid credentials → Clear error + retry guide
- Rate limited → Queue and retry with backoff
- Broker maintenance → Show status page link
```

---

## Priority 5: Feedback Loop & Learning (Hours 36-42)

### 5.1 Feedback Collection System

```typescript
// packages/core/src/feedback/collector.ts

interface FeedbackEvent {
  type: 'skill_execution' | 'trade_outcome' | 'user_correction' | 'approval_decision';
  timestamp: Date;
  userId: string;
  sessionId: string;

  // Skill context
  skillName: string;
  skillVersion: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;

  // User feedback
  userAction: 'approved' | 'rejected' | 'modified';
  userModifications?: Record<string, any>;
  userComment?: string;

  // Outcome (for trades)
  tradeOutcome?: {
    entryPrice: number;
    exitPrice?: number;
    pnl?: number;
    holdingPeriod?: number;
  };
}

class FeedbackCollector {
  async record(event: FeedbackEvent): Promise<void> {
    // Store in database
    await this.db.insert('feedback_events', event);

    // If this is a correction, create test case
    if (event.userAction === 'modified') {
      await this.createTestCase(event);
    }

    // Update skill performance metrics
    await this.updateSkillMetrics(event);
  }

  async createTestCase(event: FeedbackEvent): Promise<void> {
    const testCase = {
      skillName: event.skillName,
      input: event.inputs,
      expectedOutput: event.userModifications || event.outputs,
      source: 'user_correction',
      createdAt: new Date(),
    };
    await this.db.insert('skill_test_cases', testCase);
  }

  async getSkillMetrics(skillName: string): Promise<SkillMetrics> {
    const events = await this.db.query('feedback_events', { skillName });
    return {
      totalExecutions: events.length,
      approvalRate: events.filter(e => e.userAction === 'approved').length / events.length,
      avgConfidence: average(events.map(e => e.confidence)),
      avgLatencyMs: average(events.map(e => e.latencyMs)),
      profitableTradeRate: this.calculateProfitableRate(events),
    };
  }
}
```

### 5.2 Test Generation from Feedback

```typescript
// packages/skills/src/testing/generator.ts

interface GeneratedTest {
  name: string;
  skillName: string;
  input: Record<string, any>;
  expectedOutput: Record<string, any>;
  source: 'user_correction' | 'manual' | 'auto_generated';
  confidence: number;
}

class TestGenerator {
  async generateFromCorrections(skillName: string): Promise<GeneratedTest[]> {
    const corrections = await this.db.query('feedback_events', {
      skillName,
      userAction: 'modified',
    });

    return corrections.map(c => ({
      name: `correction_${c.id}`,
      skillName,
      input: c.inputs,
      expectedOutput: c.userModifications,
      source: 'user_correction',
      confidence: 0.9, // User corrections are high confidence
    }));
  }

  async generateFromSuccessfulTrades(skillName: string): Promise<GeneratedTest[]> {
    const successfulTrades = await this.db.query('feedback_events', {
      skillName,
      'tradeOutcome.pnl': { $gt: 0 },
    });

    return successfulTrades.map(t => ({
      name: `profitable_trade_${t.id}`,
      skillName,
      input: t.inputs,
      expectedOutput: t.outputs,
      source: 'auto_generated',
      confidence: 0.7,
    }));
  }
}
```

---

## Priority 6: Demo-Ready UI (Hours 42-48)

### 6.1 Key Screens for Hackathon Demo

```
1. ONBOARDING FLOW (2 screens)
   ├── Risk Assessment Chat
   └── Broker Connection Wizard

2. DASHBOARD (1 screen)
   ├── Portfolio Overview
   ├── Goal Progress Cards
   └── AI Insight Banner

3. CHAT INTERFACE (1 screen)
   ├── Conversation Thread
   ├── Skill Execution Indicators
   └── Trade Approval Cards

4. TRADE APPROVAL (1 modal)
   ├── Trade Details
   ├── AI Reasoning
   └── Approve/Modify/Reject

5. AGENT DASHBOARD (1 screen)
   ├── Active Agents Status
   ├── Skill Execution Log
   └── Feedback Metrics
```

### 6.2 Component Priority

| Component | Demo Impact | Build Time | Priority |
|-----------|-------------|------------|----------|
| Chat Interface | HIGH | 4h | P0 |
| Trade Approval Modal | HIGH | 2h | P0 |
| Dashboard Overview | HIGH | 3h | P0 |
| Agent Status Panel | HIGH | 2h | P0 |
| Broker Connection | MEDIUM | 3h | P1 |
| Goal Progress | MEDIUM | 2h | P1 |
| Skill Metrics | LOW | 2h | P2 |

---

## Extensibility for Future Assets

### Gold Integration (Post-Hackathon)

```yaml
# config/markets/gold.yaml
---
market:
  id: gold
  name: "Gold"
  currency: INR

brokers:
  - id: augmont
    name: "Augmont Gold"
    api_type: "augmont_api"

  - id: goldrush
    name: "Gold Rush"

assets:
  - symbol: "GOLD_24K"
    type: "physical"
    unit: "gram"

  - symbol: "GOLDBEES"
    type: "etf"
    exchange: "NSE"

  - symbol: "SGB"
    type: "sovereign_gold_bond"
    issuer: "RBI"
```

### Crypto Integration (Post-Hackathon)

```yaml
# config/markets/crypto.yaml
---
market:
  id: crypto
  name: "Cryptocurrency"
  currency: USD
  trading_hours: "24/7"

brokers:
  - id: binance
    name: "Binance"
    api_type: "binance_v3"

  - id: coinbase
    name: "Coinbase"
    api_type: "coinbase_pro"
```

---

## Hackathon Demo Script (3 minutes)

```
0:00-0:30 | THE HOOK
"NRIs lose billions to currency risk and bad advice.
We built an AI that finally understands cross-border wealth."

0:30-1:00 | ONBOARDING
- Show risk assessment chat (3 questions)
- AI creates persona: "Moderate risk, 10-year horizon"
- AI recommends strategy: "Balanced Growth"

1:00-1:30 | AI IN ACTION
- User asks: "Should I buy Reliance?"
- Show multi-agent analysis (Research → Risk → Strategy)
- Trade proposal with reasoning

1:30-2:00 | SAFETY DEMO
- Show loss prevention rules
- Demo position sizing by persona
- "You wanted 10%, I recommend 5% based on your profile"

2:00-2:30 | FEEDBACK LOOP
- User modifies trade → becomes test case
- Show skill metrics dashboard
- "Every interaction makes us smarter"

2:30-3:00 | EXTENSIBILITY
- Show market configuration files
- "Gold, crypto, real estate—same architecture"
- "Skills are our moat. Tests are our training data."
```

---

## Success Metrics for Hackathon

| Metric | Target |
|--------|--------|
| Working skills | 10+ |
| Test cases | 50+ |
| Broker adapters | 2 (Paper + Alpaca) |
| Market configs | 2 (India + US) |
| Safety rules | 5+ |
| Demo polish | Smooth 3-min flow |

---

*Implementation plan ready. Build sequence: Foundation → Safety → Persona → Markets → Feedback → UI*
