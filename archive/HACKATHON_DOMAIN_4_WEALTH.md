# Domain 4: Wealth Copilot — Trading Bot Extension

**Strategic Assessment**: Should we add Wealth domain to the 36-hour hackathon?

---

## Executive Summary

**RECOMMENDATION**: ✅ **YES** — Add as Domain 4 (Stretch Goal) with LIMITED scope

**Why Add It**:
1. **Narrative Diversity** — Shows platform handles DIFFERENT persona (retail investors vs operations teams)
2. **Visual Demo Impact** — Trading bots are VISCERAL (portfolio charts, risk alerts, order execution)
3. **Already Built** — 2 safety skills exist, Fincept features documented
4. **Market Appeal** — Judges/audience likely have personal investment accounts (relatable)

**Why Limit Scope**:
1. ⏰ **Time Constraint** — 36 hours already packed with 3 domains
2. 🎯 **Focus Risk** — Don't dilute core demo (ECM multi-agent workflow)
3. 🧪 **Complexity** — Trading involves real-time data, broker APIs (fragile in demo)

---

## What You Already Have (Wealth Domain)

### Existing Skills (2)
| Skill | Status | Lines | Complexity |
|-------|--------|-------|------------|
| **position-cap** | ✅ READY | 120 | LOW (Kelly Criterion math) |
| **loss-limit** | ✅ READY | 109 | LOW (circuit breaker logic) |

### Available Features (from FinceptTerminal)
| Feature | Effort | Demo Impact | Risk |
|---------|--------|-------------|------|
| Portfolio Service | 2h | HIGH (tracking across brokers) | LOW |
| Notification Service | 2h | MEDIUM (alerts) | LOW |
| Grid/DCA Engine | 4h | HIGH (systematic investing) | MEDIUM |
| Visual Workflow Builder | 8h | VERY HIGH (drag-drop strategies) | HIGH (UI complexity) |
| Multi-Broker | 8h | HIGH (real trading) | VERY HIGH (API failures) |
| Backtesting | 6h | MEDIUM (validation) | MEDIUM |

### Wealth Domain Skills Gap Analysis
**Currently**: 2 safety skills (position-cap, loss-limit)
**Need for Demo**: 2-3 execution skills (portfolio-check, execute-trade, goal-progress)

**Effort to Add**:
- `portfolio-check` skill: 2 hours (read portfolio, calculate P&L, show goals)
- `execute-trade` skill: 3 hours (place order with safety checks)
- `goal-progress` skill: 2 hours (track "House in Mumbai" goal)

**Total**: ~7 hours to make wealth domain DEMO-READY

---

## Two Strategies: Conservative vs Aggressive

### Strategy A: Conservative (RECOMMENDED)
**Time**: 7 hours total
**Team**: 1 person (Person B during Hours 18-25)
**Scope**: Static portfolio demo + safety skills

**What to Build**:
1. **Static portfolio data** (CSV)
   - 10 holdings (mix of Indian stocks, crypto, US ETFs)
   - Multi-currency (INR, USD, AED)
   - Goal: "House in Mumbai" at 45% completion

2. **Skills** (3 total):
   ```yaml
   # domains/wealth/aspora.config.yaml
   domain:
     name: wealth
     description: AI wealth manager for cross-border investors
     owner: wealth-team

   skills:
     - name: portfolio-check
       path: skills/portfolio-check.md
       model: anthropic/claude-haiku-4.5  # Fast lookup

     - name: position-cap
       path: skills/safety/position-cap.md
       model: anthropic/claude-haiku-4.5

     - name: loss-limit
       path: skills/safety/loss-limit.md
       model: anthropic/claude-haiku-4.5
   ```

3. **Demo Flow** (30 seconds in pitch):
   ```
   User (Slack): "check my portfolio"
   Bot:
   📊 Your Portfolio (₹15,45,000 | $18,500 | AED 68,000)

   Top Holdings:
   - RELIANCE.NS (12.3%) — ₹1,89,950
   - Bitcoin (8.5%) — $1,572
   - VOO (US S&P 500) — $3,200

   🎯 Goals:
   - House in Mumbai: 45% → ₹22L saved (target ₹50L)

   ⚠️ Risk Status: Green
   - Daily loss: -0.8% (limit: 5%)
   - Sector concentration: 23% Tech (limit: 25%)

   Cost: $0.01 (Haiku)

   User: "buy 50 shares of RELIANCE"
   Bot:
   🚫 Position Size Adjusted

   You requested: 50 shares (₹1,22,500)
   This would be: 8% of portfolio

   Maximum allowed: 2% (₹30,900)
   Adjusted quantity: 12 shares

   Should I proceed with 12 shares?
   ```

**Demo Impact**:
- ✅ Shows 4th domain (wealth) onboarded
- ✅ Multi-currency support
- ✅ Risk guardrails (differentiator)
- ✅ Goal tracking (relatable)

**Risk**: LOW (static data, no external APIs)

---

### Strategy B: Aggressive (NOT RECOMMENDED)
**Time**: 16+ hours
**Team**: 2 people
**Scope**: Live trading with Hummingbot/Fincept integration

**What to Build**:
1. Real broker integration (Zerodha Kite API or Alpaca)
2. Live market data streaming
3. Visual workflow builder (drag-drop strategies)
4. Backtesting engine

**Why NOT Recommended**:
- ❌ **High Failure Risk** — Broker APIs fail during demos (auth, rate limits, market hours)
- ❌ **Time Sink** — 16 hours = half your hackathon
- ❌ **No Incremental Value** — Static demo tells the same story (platform works for wealth)

**Only Do This If**:
- You have > 48 hours (not 36)
- All 3 core domains (ECM, FinCrime, Fraud) are 100% polished by Hour 18
- You want a "wow factor" but risk losing core demo
---

## Integration Plan: Strategy A (Conservative)

### Hour 18-25: Wealth Domain Onboarding (1 Person)

**Person B** (after completing all 3 domain configs):

**Hour 18-20**: Create wealth domain structure
```bash
# Create domain directory
mkdir -p domains/wealth/skills/safety

# Copy existing skills
cp /Users/apple/code/experimentation/wealth-copilot/packages/skills/safety/*.md \
   domains/wealth/skills/safety/

# Create aspora.config.yaml (see above)
```

**Hour 20-22**: Build portfolio-check skill
```markdown
# domains/wealth/skills/portfolio-check.md
---
name: portfolio-check
description: Show multi-currency portfolio with goals and risk status
triggers:
  - "check portfolio"
  - "show my holdings"
  - "portfolio status"
---

# Portfolio Check Skill

> You show the user's portfolio across all accounts and currencies.

## Input
- User ID (from context)
- Currency preference (default: INR)

## Data Source
Read from `portfolios.csv`:
```csv
user_id,symbol,quantity,avg_price,current_price,currency
user123,RELIANCE.NS,15,2450,2530,INR
user123,BTC,0.05,45000,52000,USD
user123,VOO,10,420,435,USD
```

## Calculation
1. Calculate position value: `quantity × current_price`
2. Calculate P&L: `(current_price - avg_price) × quantity`
3. Convert all to user's preferred currency
4. Calculate sector concentration
5. Check goals progress (from `goals.csv`)

## Output Format
```
📊 Your Portfolio (₹15,45,000 | $18,500 | AED 68,000)

Top Holdings:
- RELIANCE.NS (12.3%) — ₹1,89,950 (+3.2%)
- Bitcoin (8.5%) — $1,572 (+15.6%)
- VOO (10.2%) — $4,350 (+3.6%)

🎯 Goals:
- House in Mumbai: 45% → ₹22L saved (target ₹50L)
- Kid's Education: 12% → $3K saved (target $25K)

⚠️ Risk Status: Green
- Daily P&L: +₹12,340 (+0.8%)
- Daily loss limit: 5% (4.2% remaining)
- Sector concentration: Tech 23% (limit 25%)
```

## Guardrails
- ALWAYS show all currencies (user may have cross-border assets)
- ALWAYS check risk limits (daily loss, sector concentration)
- NEVER show fake returns (use real calculations)
```

**Hour 22-23**: Create static data files
```csv
# domains/wealth/data/portfolios.csv
user_id,symbol,quantity,avg_price,current_price,currency,sector
demo_user,RELIANCE.NS,15,2450,2530,INR,Energy
demo_user,INFY.NS,8,1450,1480,INR,Technology
demo_user,HDFCBANK.NS,12,1650,1680,INR,Finance
demo_user,BTC,0.05,45000,52000,USD,Crypto
demo_user,ETH,0.8,2800,3100,USD,Crypto
demo_user,VOO,10,420,435,USD,Equity
demo_user,AAPL,5,180,185,USD,Technology
demo_user,GOOGL,3,140,145,USD,Technology
demo_user,TSLA,4,220,210,USD,Technology
demo_user,GLD,15,185,190,USD,Commodities
```

```csv
# domains/wealth/data/goals.csv
goal_id,user_id,goal_name,target_amount,current_amount,currency,target_date
1,demo_user,House in Mumbai,5000000,2200000,INR,2028-12-31
2,demo_user,Kid's Education,25000,3000,USD,2030-06-30
3,demo_user,Retirement Corpus,100000,12000,USD,2050-01-01
```

**Hour 23-24**: Test wealth skills locally
```bash
# Test portfolio-check
aspora execute wealth/portfolio-check \
  --context '{"user_id": "demo_user", "currency": "INR"}'

# Test position-cap
aspora execute wealth/position-cap \
  --context '{"symbol": "RELIANCE.NS", "quantity": 50, "price": 2530}'

# Expected: Position size adjusted from 50 → 12 shares
```

**Hour 24-25**: Add to Slack bot
```typescript
// Add to demo-bot.ts
app.message(/check portfolio|portfolio status/, async ({ message, say }) => {
  const result = await executor.execute({
    skill: "wealth/portfolio-check",
    context: { user_id: message.user, currency: "INR" }
  });

  await say({
    text: result.output,
    blocks: [
      {
        type: "section",
        text: { type: "mrkdwn", text: result.output }
      },
      {
        type: "actions",
        elements: [
          {
            type: "button",
            text: { type: "plain_text", text: "Trade" },
            action_id: "open_trade_modal"
          },
          {
            type: "button",
            text: { type: "plain_text", text: "Adjust Goals" },
            action_id: "adjust_goals"
          }
        ]
      },
      {
        type: "context",
        elements: [
          { type: "mrkdwn", text: `💰 Cost: $${result.cost.toFixed(4)} | ⚡ ${result.latency.toFixed(2)}s` }
        ]
      }
    ]
  });
});

app.message(/buy (\d+) shares of (.+)/, async ({ message, context, say }) => {
  const quantity = parseInt(context.matches[1]);
  const symbol = context.matches[2];

  // Check position cap first
  const checkResult = await executor.execute({
    skill: "wealth/position-cap",
    context: { symbol, quantity, price: 2530 }  // Mock price for demo
  });

  await say(checkResult.output);
});
```

---

## Revised Hackathon Timeline (with Wealth Domain)

### Hours 0-8: Foundation (No Change)
T1-T5 build core platform components

### Hours 8-18: Core Demo (No Change)
ECM multi-agent + FinCrime + Fraud Guardian integration

### **Hours 18-25: Wealth Domain Addition (NEW)**
**Person B**: Onboard wealth domain (7 hours)
- Hour 18-20: Setup domain structure, copy safety skills
- Hour 20-22: Build portfolio-check skill
- Hour 22-23: Create static data (portfolios, goals)
- Hour 23-24: Test skills locally
- Hour 24-25: Integrate with Slack bot

**Everyone Else**: Continue polish (dashboard, test generation, rehearsal)

### Hours 25-30: Final Rehearsal (Adjusted)
**NEW DEMO SCRIPT** (add 30 seconds for wealth):

```
Act 1 (30s): "4 production domains"  [CHANGED from 3]
  → ecm/ fincrime/ fraud-guardian/ wealth/

Act 2 (60s): Multi-agent ECM workflow [NO CHANGE]

Act 3 (60s): Auto-learning moat [NO CHANGE]

Act 4 (30s): Cross-domain power [SPLIT]
  → FinCrime investigation (15s)
  → Wealth portfolio + risk guardrails (15s)  [NEW]

  [Slack: "check portfolio"]
  Bot: [shows multi-currency portfolio]
  📊 Your Portfolio (₹15,45,000)
  🎯 House in Mumbai: 45%
  ⚠️ Risk: Green (all limits OK)

  [Slack: "buy 50 shares of RELIANCE"]
  Bot: 🚫 Position Size Adjusted
       50 shares = 8% of portfolio
       Maximum allowed: 2%
       Adjusted: 12 shares

  "Risk guardrails prevent emotional decisions. Even when YOU want to over-bet."
```

### Hours 30-36: Final Prep (No Change)

---

## Comparison: 3 Domains vs 4 Domains

| Aspect | 3 Domains (ECM/FinCrime/Fraud) | 4 Domains (+Wealth) |
|--------|-------------------------------|---------------------|
| **Total Skills** | 14 | 17 (+3 wealth skills) |
| **Narrative Diversity** | Operations + Compliance + Analytics | Operations + Compliance + Analytics + **Personal Finance** |
| **Demo Time** | 3 min | 3.5 min (still OK) |
| **Judge Relatability** | Medium (B2B focus) | **HIGH** (everyone invests) |
| **Risk of Failure** | LOW | MEDIUM (7 hours for new domain) |
| **Differentiator** | Multi-domain platform | Multi-domain platform + **Personal Use Case** |
| **Team Capacity** | Good (all 5 people busy) | Tight (Person B stretched) |

---

## Risk Assessment: Adding Wealth Domain

### Risks
1. **Time Pressure on Person B** — 7 hours is tight for new domain
   - Mitigation: Pre-build portfolio-check skill NOW (save 2 hours)

2. **Demo Complexity** — 4 domains harder to explain in 3 min
   - Mitigation: Keep wealth demo to 15 seconds (portfolio + 1 risk check)

3. **Data Quality** — Static CSV might look fake
   - Mitigation: Use realistic data (mix of gains/losses, reasonable holdings)

4. **Integration Bugs** — Slack bot with 4 domains = more edge cases
   - Mitigation: Test each domain separately, have fallback (show CLI if Slack breaks)

### Upsides
1. **Judge Appeal** — Personal finance is universally relatable
2. **Differentiation** — Shows platform isn't just "operations tools"
3. **Risk Guardrails** — Unique feature (competitors don't have Kelly Criterion)
4. **Visual Impact** — Portfolio charts, currency conversions are VISCERAL

---

## Decision Framework

### Add Wealth Domain IF:
- ✅ By Hour 18, all 3 core domains are 100% working
- ✅ Multi-agent workflow executes cleanly
- ✅ Auto-learning demo is polished
- ✅ Person B has bandwidth (not debugging ECM configs)
- ✅ You want max "wow factor" (4 domains > 3)

### Skip Wealth Domain IF:
- ❌ Core 3 domains have bugs at Hour 18
- ❌ Team is exhausted, needs sleep buffer
- ❌ Demo already > 3 minutes (can't add more)
- ❌ Conservative approach preferred (better to nail 3 than rush 4)

---

## Alternative: Hummingbot vs Custom Build

### Option A: Custom Build (RECOMMENDED)
**Approach**: Use your existing Wealth Copilot skills (position-cap, loss-limit) + static portfolio demo
**Effort**: 7 hours
**Risk**: LOW
**Demo Impact**: HIGH (risk guardrails are unique)

**Why Better**:
- ✅ Full control over demo flow
- ✅ No external dependencies
- ✅ Integrates with platform story (skills-first architecture)
- ✅ Shows YOUR code, not third-party tool

### Option B: Hummingbot Integration
**Approach**: Use Hummingbot's market-making strategies, wrap as Aspora skills
**Effort**: 12+ hours
**Risk**: VERY HIGH
**Demo Impact**: MEDIUM (cool but complex)

**Why NOT Recommended**:
- ❌ Hummingbot is CRYPTO-FOCUSED (market making, arbitrage) — not wealth management
- ❌ Requires running Hummingbot gateway (another service to manage)
- ❌ Complex setup (exchanges, API keys, strategies)
- ❌ Demo failure risk (live crypto prices, order failures)

**When to Use Hummingbot**:
- You're building a crypto trading platform (not wealth management)
- You have > 3 days (not 36 hours)
- You want to show LIVE trading (high risk, high reward)

### Option C: FinceptTerminal Features
**Approach**: Port Grid Trading, Backtesting, Multi-Broker from FinceptTerminal
**Effort**: 8-16 hours
**Risk**: MEDIUM-HIGH
**Demo Impact**: VERY HIGH (if it works)

**Recommended Subset** (if you choose this):
1. **Grid Trading** (4 hours) — "Systematic DCA for NRIs"
   - Demo: "Invest ₹10K every month in Nifty 50, rebalance quarterly"
2. **Portfolio Service** (2 hours) — Multi-broker tracking
   - Demo: "Holdings from Zerodha + Alpaca in one view"

**Skip**:
- Visual Workflow Builder (8 hours, too complex)
- Multi-Broker (8 hours, API failures)
- Backtesting (6 hours, not core value prop)

---

## FINAL RECOMMENDATION

### Recommended Approach: **Strategy A + Pre-Work**

**Pre-Work** (Do NOW, before hackathon):
1. Build `portfolio-check` skill (2 hours) → Save time during hackathon
2. Prepare static data CSVs (portfolios, goals) → Copy-paste ready
3. Test skills locally → Debug before event

**During Hackathon**:
- **ONLY add Wealth IF** core 3 domains are solid by Hour 18
- **LIMIT to 7 hours** (Person B, Hours 18-25)
- **FALLBACK**: If running behind, skip wealth, stick with 3 domains

**Why This Works**:
- Low-risk addition (static demo, no APIs)
- High-impact differentiator (risk guardrails, multi-currency)
- Doesn't compromise core demo (ECM multi-agent)
- Shows platform versatility (B2B operations + B2C wealth)

---

## Revised Success Metrics

### Minimum Viable Demo (3 Domains)
- ✅ ECM multi-agent workflow
- ✅ FinCrime investigation
- ✅ Fraud Guardian rule analysis
- ✅ Auto-learning (correction → test)
- ✅ Cost comparison

### Stretch Goal (4 Domains) — **NEW**
- 🎯 Wealth portfolio check (multi-currency)
- 🎯 Risk guardrails (position-cap blocks bad trade)
- 🎯 Goal tracking (House in Mumbai 45%)
- 🎯 4-domain narrative ("Solves operations AND personal finance")

### Gold Standard (All of Above + Polish)
- 🏆 All 4 domains execute flawlessly
- 🏆 Judges relate to wealth demo ("I have this problem!")
- 🏆 Risk guardrails get questions ("How does Kelly Criterion work?")
- 🏆 Someone asks "Can I use this for my portfolio?"

---

## Appendix: File Structure with Wealth Domain

```
aspora-platform/
├── domains/
│   ├── ecm/
│   ├── fincrime/
│   ├── fraud-guardian/
│   └── wealth/                          # NEW
│       ├── aspora.config.yaml
│       ├── skills/
│       │   ├── portfolio-check.md       # NEW (2h to build)
│       │   └── safety/
│       │       ├── position-cap.md      # EXISTING (copy)
│       │       └── loss-limit.md        # EXISTING (copy)
│       └── data/
│           ├── portfolios.csv           # NEW (static demo data)
│           └── goals.csv                # NEW (static demo data)
├── packages/
├── workflows/
├── tests/
└── demo-bot.ts                          # UPDATE (add wealth commands)
```

**Total New Files**: 5
**Total New Code**: ~400 lines (portfolio-check skill + data + Slack integration)

---

## Final Answer to Your Question

**Q: Can I onboard the wealth bot that we initially discussed or build a trading bot using Hummingbot/FinceptTerminal?**

**A: YES to Wealth Bot (Strategy A), NO to Hummingbot, MAYBE to select FinceptTerminal features**

### What to Do:
1. **Before Hackathon**: Build `portfolio-check` skill + prepare data CSVs (4 hours of pre-work)
2. **During Hackathon**:
   - Focus on 3 core domains (ECM, FinCrime, Fraud) for first 18 hours
   - **CHECKPOINT Hour 18**: If all working, add Wealth domain (7 hours)
   - If behind schedule, skip Wealth, stick with 3 domains
3. **Demo**: Add 30 seconds showing portfolio + risk guardrails (if time allows)

### What NOT to Do:
- ❌ Don't integrate Hummingbot (crypto-focused, complex, high failure risk)
- ❌ Don't build live trading (broker APIs fragile during demos)
- ❌ Don't port 100+ node system (16+ hours, too ambitious)

### Conservative Fallback:
If you want 4 domains but low risk, just copy the 2 existing safety skills:
- `position-cap` (exists, 120 lines)
- `loss-limit` (exists, 109 lines)

Demo them as "Risk Guardrails Domain" without portfolio tracking. Still shows platform versatility in 30 seconds.

**TL;DR**: Add Wealth domain as stretch goal if Hour 18 checkpoint is green. Use static demo (no live APIs). Pre-build `portfolio-check` skill NOW to save 2 hours during hackathon.
