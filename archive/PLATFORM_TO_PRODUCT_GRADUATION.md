# Platform to Product Graduation Guide

**Question**: How do I start Wealth on the Aspora platform, validate it, then extract it to a standalone product without breaking everything?

**Answer**: Design for portability from day 1. Use the "Strangler Fig" migration pattern. Extract in phases over 3-6 months.

---

## The Graduation Journey

```
Phase 1: Platform-Native (Months 0-6)
┌─────────────────────────────────┐
│  Aspora Platform                │
│  ├── ECM Domain                 │
│  ├── FinCrime Domain            │
│  └── Wealth Domain (NEW)        │
│      └── 3 skills               │
│          - portfolio-check      │
│          - position-cap         │
│          - loss-limit           │
└─────────────────────────────────┘
Users: 100-1K (early adopters)
Team: 2 people (1 frontend, 1 skill dev)
Cost: Marginal (shared infra)

Phase 2: Hybrid Architecture (Months 7-12)
┌─────────────────────────────────┐
│  Aspora Platform                │
│  ├── ECM Domain                 │
│  ├── FinCrime Domain            │
│  └── Wealth Domain (LITE)       │
│      └── Facade skills          │◄──┐
└─────────────────────────────────┘   │
                                      │ API calls
┌─────────────────────────────────┐   │
│  Wealth Backend (NEW)           │◄──┘
│  ├── Portfolio Service          │
│  ├── Trading Engine             │
│  ├── Risk Management            │
│  └── Broker Gateway             │
└─────────────────────────────────┘
Users: 1K-10K (growing)
Team: 5 people (2 FE, 2 BE, 1 DevOps)
Cost: +$50K/mo infra

Phase 3: Standalone Product (Months 13-18)
┌─────────────────────────────────┐
│  Aspora Platform                │
│  ├── ECM Domain                 │
│  └── FinCrime Domain            │
│  (Wealth removed)               │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  Wealth Product (Standalone)    │
│  ├── React/Next.js Frontend     │
│  ├── FastAPI/Go Backend         │
│  ├── PostgreSQL Database        │
│  ├── Redis Cache                │
│  └── Mobile App (iOS/Android)   │
└─────────────────────────────────┘
Users: 10K-100K (product-market fit)
Team: 10 people (3 FE, 3 BE, 1 mobile, 1 DevOps, 1 QA, 1 PM)
Cost: ~$150K/mo infra + team
```

---

## Reusable Components (What You Keep)

### 1. Business Logic (95% Reusable)

**What's in Platform Today**:

```markdown
# domains/wealth/skills/portfolio-check.md
---
name: portfolio-check
description: Show multi-currency portfolio
---

# Portfolio Check Skill

## Calculation Logic
1. Calculate position value: `quantity × current_price`
2. Calculate P&L: `(current_price - avg_price) × quantity`
3. Convert all to user's preferred currency
4. Calculate sector concentration
5. Check goals progress

## Risk Calculations
- Daily P&L percentage
- Sector concentration (max 25% per sector)
- Position sizes (max 2% per holding)

## Output Format
[structured portfolio display]
```

**How to Extract**:

```python
# wealth-product/services/portfolio_service.py
# Copy logic directly from skill markdown

from decimal import Decimal
from typing import Dict, List
import pandas as pd

class PortfolioService:
    """
    Extracted from domains/wealth/skills/portfolio-check.md
    All calculation logic is IDENTICAL to platform version
    """

    def calculate_portfolio_value(
        self,
        holdings: List[Dict],
        currency: str = 'INR'
    ) -> Dict:
        """
        Same logic as skill, now as Python service
        """
        df = pd.DataFrame(holdings)

        # Step 1: Position values (copied from skill)
        df['position_value'] = df['quantity'] * df['current_price']

        # Step 2: P&L calculation (copied from skill)
        df['unrealized_pnl'] = (df['current_price'] - df['avg_price']) * df['quantity']
        df['pnl_pct'] = (df['current_price'] / df['avg_price'] - 1) * 100

        # Step 3: Currency conversion (copied from skill)
        df['position_value_converted'] = df.apply(
            lambda row: self._convert_currency(
                row['position_value'],
                row['currency'],
                currency
            ),
            axis=1
        )

        total_value = df['position_value_converted'].sum()

        # Step 4: Sector concentration (copied from skill)
        sector_concentration = df.groupby('sector')['position_value_converted'].sum() / total_value

        return {
            'total_value': total_value,
            'holdings': df.to_dict('records'),
            'sector_concentration': sector_concentration.to_dict(),
            'currency': currency
        }

    def check_risk_limits(self, portfolio: Dict) -> Dict:
        """
        Extracted from domains/wealth/skills/safety/position-cap.md
        """
        total_value = portfolio['total_value']
        violations = []

        for holding in portfolio['holdings']:
            position_pct = holding['position_value_converted'] / total_value

            # Max 2% per position (from position-cap skill)
            if position_pct > 0.02:
                violations.append({
                    'type': 'position_size',
                    'symbol': holding['symbol'],
                    'current': position_pct,
                    'limit': 0.02
                })

        # Max 25% per sector (from position-cap skill)
        for sector, pct in portfolio['sector_concentration'].items():
            if pct > 0.25:
                violations.append({
                    'type': 'sector_concentration',
                    'sector': sector,
                    'current': pct,
                    'limit': 0.25
                })

        return {
            'status': 'GREEN' if not violations else 'RED',
            'violations': violations
        }
```

**Reusability**: 95%+
- All math, formulas, business rules copy directly
- Just change from "LLM prompt instructions" to "Python functions"
- **NO logic changes** (avoid regression risk)

### 2. Data Models (90% Reusable)

**What's in Platform Today**:

```csv
# domains/wealth/data/portfolios.csv
user_id,symbol,quantity,avg_price,current_price,currency,sector
demo_user,RELIANCE.NS,15,2450,2530,INR,Energy
demo_user,BTC,0.05,45000,52000,USD,Crypto
```

**How to Extract**:

```python
# wealth-product/models/portfolio.py

from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Holding(Base):
    """
    Same schema as platform CSV, now in Postgres
    """
    __tablename__ = 'holdings'

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)
    avg_price = Column(Numeric(18, 2), nullable=False)
    current_price = Column(Numeric(18, 2), nullable=False)  # Updated periodically
    currency = Column(String(3), nullable=False)
    sector = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Add indexes for queries
    __table_args__ = (
        Index('idx_user_symbol', 'user_id', 'symbol'),
    )
```

**Migration Script**:

```python
# migrations/001_import_platform_data.py

import pandas as pd
from sqlalchemy import create_engine
from models.portfolio import Holding

def migrate_from_platform():
    """
    One-time migration from platform CSV to standalone DB
    """
    engine = create_engine('postgresql://wealth-db:5432/wealth_prod')

    # Read platform data
    df = pd.read_csv('/path/to/aspora-platform/domains/wealth/data/portfolios.csv')

    # Convert to database rows
    df['id'] = df.apply(lambda row: f"{row['user_id']}_{row['symbol']}", axis=1)
    df['created_at'] = pd.Timestamp.now()
    df['updated_at'] = pd.Timestamp.now()

    # Bulk insert
    df.to_sql('holdings', engine, if_exists='append', index=False)

    print(f"Migrated {len(df)} holdings from platform")
```

**Reusability**: 90%
- Schema is identical (CSV → SQL)
- Add indexes, constraints for production
- Data migrates cleanly (one-time script)

### 3. Risk Algorithms (100% Reusable)

**What's in Platform Today**:

```typescript
// domains/wealth/skills/safety/position-cap.skill.md (TypeScript in markdown)

function calculatePositionSize(
  price: number,
  portfolioValue: number,
  winRate: number = 0.5,
  avgWin: number = 0.08,
  avgLoss: number = 0.04,
  volatility: number = 0.2
): number {
  // Half-Kelly Criterion
  const kellyPct = (winRate * avgWin - (1 - winRate) * avgLoss) / avgWin;
  const halfKelly = Math.max(0, kellyPct / 2);

  // Volatility adjustment
  const volAdjusted = halfKelly * (1 / (1 + volatility));

  // Cap at 2%
  const cappedPct = Math.min(volAdjusted, 0.02);

  return Math.floor((portfolioValue * cappedPct) / price);
}
```

**How to Extract**:

```python
# wealth-product/services/risk_service.py

class RiskService:
    """
    Extracted from domains/wealth/skills/safety/position-cap.skill.md
    Algorithm is IDENTICAL (Kelly Criterion math doesn't change)
    """

    MAX_POSITION_SIZE = 0.02  # 2%
    MAX_SECTOR_EXPOSURE = 0.25  # 25%
    MAX_DAILY_LOSS = 0.05  # 5%

    def calculate_position_size(
        self,
        price: float,
        portfolio_value: float,
        win_rate: float = 0.5,
        avg_win: float = 0.08,
        avg_loss: float = 0.04,
        volatility: float = 0.2
    ) -> int:
        """
        Half-Kelly Criterion (copy from platform skill)
        """
        # Kelly percentage
        kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        half_kelly = max(0, kelly_pct / 2)

        # Volatility adjustment
        vol_adjusted = half_kelly * (1 / (1 + volatility))

        # Cap at 2%
        capped_pct = min(vol_adjusted, self.MAX_POSITION_SIZE)

        # Return quantity
        return int((portfolio_value * capped_pct) / price)

    def check_daily_loss_limit(self, user_id: str) -> Dict:
        """
        Extracted from domains/wealth/skills/safety/loss-limit.skill.md
        """
        # Get today's P&L
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        positions = self.portfolio_service.get_holdings(user_id)

        # Calculate daily P&L
        daily_pnl = sum(p['unrealized_pnl'] for p in positions if p['updated_at'] >= today_start)
        portfolio_value = sum(p['position_value'] for p in positions)
        daily_pnl_pct = daily_pnl / portfolio_value if portfolio_value > 0 else 0

        # Check against limit
        if daily_pnl_pct <= -self.MAX_DAILY_LOSS:
            return {
                'breached': True,
                'current': daily_pnl_pct,
                'limit': -self.MAX_DAILY_LOSS,
                'action': 'Circuit breaker activated. Trading disabled until tomorrow.'
            }

        return {
            'breached': False,
            'current': daily_pnl_pct,
            'limit': -self.MAX_DAILY_LOSS,
            'remaining': -self.MAX_DAILY_LOSS - daily_pnl_pct
        }
```

**Reusability**: 100%
- Math is math (Kelly Criterion doesn't change)
- Constants are the same (2%, 5%, 25%)
- Just copy-paste and add tests

### 4. API Contracts (80% Reusable)

**What's in Platform Today** (implicit in skill execution):

```python
# Platform executor call
result = await executor.execute(
    skill_id="wealth/portfolio-check",
    context={
        "user_id": "priya@aspora.com",
        "currency": "INR"
    }
)

# Result format
{
    "skill": "wealth/portfolio-check",
    "output": "📊 Your Portfolio (₹15,45,000)...",  # Markdown text
    "cost": 0.02,
    "latency": 1.2,
    "user_id": "priya@aspora.com"
}
```

**Standalone Product API**:

```python
# wealth-product/api/portfolio.py

from fastapi import APIRouter, Depends
from services.portfolio_service import PortfolioService
from services.risk_service import RiskService

router = APIRouter()

@router.get("/api/v1/portfolio")
async def get_portfolio(
    user_id: str = Depends(get_current_user),
    currency: str = 'INR',
    portfolio_service: PortfolioService = Depends()
):
    """
    Same inputs as platform skill (user_id, currency)
    More structured output (JSON instead of markdown)
    """
    holdings = await portfolio_service.get_holdings(user_id)
    portfolio = portfolio_service.calculate_portfolio_value(holdings, currency)

    # Risk checks (from platform skills)
    risk_status = RiskService().check_risk_limits(portfolio)

    # Goals (from platform data)
    goals = await portfolio_service.get_goals(user_id)

    return {
        "portfolio": {
            "total_value": portfolio['total_value'],
            "currency": currency,
            "holdings": portfolio['holdings'],
            "sector_concentration": portfolio['sector_concentration']
        },
        "risk": risk_status,
        "goals": goals,
        "metadata": {
            "calculated_at": datetime.now().isoformat(),
            "latency_ms": 150  # Much faster than LLM call
        }
    }
```

**Backward Compatibility**: Keep platform facade

```python
# Platform skill becomes API wrapper
# domains/wealth/skills/portfolio-check.md becomes:

# Portfolio Check Skill (FACADE)

> This skill now calls the Wealth Product API

## Implementation

```python
import httpx

async def execute_skill(context: dict) -> str:
    """
    Call standalone Wealth API instead of local calculation
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://wealth-api.aspora.com/api/v1/portfolio",
            params={
                "user_id": context['user_id'],
                "currency": context.get('currency', 'INR')
            },
            headers={"Authorization": f"Bearer {WEALTH_API_KEY}"}
        )
        data = response.json()

    # Format as markdown (same output format as before)
    return f"""
📊 Your Portfolio ({data['portfolio']['currency']} {data['portfolio']['total_value']:,.0f})

Top Holdings:
{format_holdings(data['portfolio']['holdings'])}

🎯 Goals:
{format_goals(data['goals'])}

⚠️ Risk Status: {data['risk']['status']}
"""
```

**Reusability**: 80%
- Inputs are identical (user_id, currency)
- Outputs need reformatting (JSON → Markdown for platform)
- Business logic is the same

### 5. Configuration (100% Reusable)

**What's in Platform Today**:

```yaml
# domains/wealth/aspora.config.yaml

domain:
  name: wealth
  scope: user
  data_isolation: strict

risk_limits:
  max_position_size: 0.02
  max_sector_exposure: 0.25
  max_daily_loss: 0.05
  max_weekly_loss: 0.10
  max_drawdown: 0.15

currency_pairs:
  INR_USD: 83.2
  INR_AED: 22.6
  USD_INR: 0.012
  # etc.

supported_brokers:
  - zerodha
  - alpaca
  - interactive_brokers
```

**How to Extract**:

```python
# wealth-product/config/risk_config.yaml
# EXACT SAME FILE, just copy it

risk_limits:
  max_position_size: 0.02
  max_sector_exposure: 0.25
  max_daily_loss: 0.05
  max_weekly_loss: 0.10
  max_drawdown: 0.15

# Load in code
from yaml import safe_load

class Config:
    def __init__(self):
        with open('config/risk_config.yaml') as f:
            config = safe_load(f)
            self.max_position_size = config['risk_limits']['max_position_size']
            # etc.
```

**Reusability**: 100%
- Copy YAML file verbatim
- Zero changes needed

---

## What You CANNOT Reuse (Need to Rebuild)

### 1. Skill Execution Layer (0% Reusable)

**Platform Dependency**:

```python
# This is platform-specific, CANNOT reuse in standalone product

class SkillExecutor:
    async def execute(self, skill_id: str, context: dict):
        skill = self.registry[skill_id]

        # Load skill markdown
        skill_prompt = self._load_skill(skill['path'])

        # Call OpenRouter with LLM
        response = await self.client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": skill_prompt}]
        )

        return {"output": response.choices[0].message.content}
```

**What You Build Instead**:

```python
# wealth-product/api/main.py
# Traditional REST API (FastAPI)

from fastapi import FastAPI
from api.portfolio import router as portfolio_router
from api.trading import router as trading_router
from api.goals import router as goals_router

app = FastAPI(title="Wealth Product API")

app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(trading_router, prefix="/api/v1")
app.include_router(goals_router, prefix="/api/v1")

# Service layer (replaces skill execution)
@app.get("/api/v1/portfolio")
async def get_portfolio(user_id: str, currency: str = 'INR'):
    # Direct Python service call (no LLM)
    service = PortfolioService()
    portfolio = service.calculate_portfolio_value(user_id, currency)
    return portfolio
```

**Effort**: 2-3 weeks to build REST API layer

### 2. Channel Adapters (20% Reusable)

**Platform Version** (Slack bot with skill routing):

```python
# Aspora platform Slack adapter
@app.message(/portfolio/)
async def handle_portfolio_request(message, say):
    # Platform-specific: Route to skill executor
    result = await executor.execute(
        skill_id="wealth/portfolio-check",
        context={"user_id": get_user_id(message['user'])}
    )
    await say(result['output'])  # Already formatted markdown
```

**Standalone Version** (new Slack bot):

```python
# wealth-product/channels/slack_bot.py
# Similar structure, but calls REST API instead of executor

from slack_bolt.async_app import AsyncApp
import httpx

app = AsyncApp(token=SLACK_BOT_TOKEN)

@app.message(/portfolio/)
async def handle_portfolio_request(message, say):
    user_id = get_user_id(message['user'])

    # Call Wealth API (not platform executor)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/portfolio",
            params={"user_id": user_id, "currency": "INR"}
        )
        data = response.json()

    # Format response (need to rebuild markdown formatting)
    formatted = format_portfolio_for_slack(data)

    await say(formatted)

def format_portfolio_for_slack(data: dict) -> str:
    """
    Rebuild formatting that LLM did automatically on platform
    """
    holdings_text = "\n".join([
        f"- {h['symbol']} ({h['pct']:.1f}%) — {h['value']:,.0f}"
        for h in data['portfolio']['holdings'][:5]
    ])

    goals_text = "\n".join([
        f"- {g['name']}: {g['progress']}% → {g['current']} saved (target {g['target']})"
        for g in data['goals']
    ])

    return f"""
📊 Your Portfolio ({data['portfolio']['currency']} {data['portfolio']['total_value']:,.0f})

Top Holdings:
{holdings_text}

🎯 Goals:
{goals_text}

⚠️ Risk Status: {data['risk']['status']}
"""
```

**Reusability**: 20%
- Slack SDK usage is same (Bolt framework)
- Message handling patterns are same
- BUT: Formatting logic needs to be rebuilt (LLM did this automatically on platform)

**Effort**: 1-2 weeks to rebuild channel adapters + formatting

### 3. Frontend (0% Reusable if Platform Has No Web UI)

**Platform**: Likely has no dedicated Wealth UI (just Slack/WhatsApp)

**Standalone**: Need to build from scratch

```typescript
// wealth-product/frontend/src/App.tsx
// Full React/Next.js app

import { PortfolioView } from './components/PortfolioView';
import { TradingPanel } from './components/TradingPanel';
import { GoalsTracker } from './components/GoalsTracker';

export default function App() {
  return (
    <div className="wealth-app">
      <Sidebar />
      <main>
        <PortfolioView />
        <TradingPanel />
        <GoalsTracker />
      </main>
    </div>
  );
}
```

**Effort**: 3-4 months for production-grade web + mobile UI

### 4. Authentication & Authorization (30% Reusable)

**Platform**: Uses context injection + user database

```python
# Platform approach
user = db.get_by_slack_id(slack_user_id)
result = await executor.execute(
    skill_id="wealth/portfolio-check",
    context={"user_id": user.id}
)
```

**Standalone**: Need OAuth, JWT, session management

```python
# wealth-product/auth/jwt.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Replace platform context injection with JWT validation
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    """
    New: Need to implement login flow (didn't exist on platform)
    """
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT
    token = jwt.encode(
        {"sub": user.id, "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256"
    )

    return {"access_token": token, "token_type": "bearer"}
```

**Reusability**: 30%
- User database schema can be reused
- User identification logic is same
- BUT: Need to add OAuth, JWT, password hashing (platform didn't need this)

**Effort**: 1-2 weeks for auth system

---

## Migration Strategy: The Strangler Fig Pattern

### Timeline: 6-Month Gradual Migration

```
Month 1-2: Backend Extraction (Dual-Write Phase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────┐
│  Platform Skills │  ← Still serves users
│  (wealth domain) │
└────────┬─────────┘
         │ Writes to BOTH:
         ├──────────────┐
         │              │
         ▼              ▼
┌───────────────┐  ┌────────────────┐
│ Platform DB   │  │ New Wealth DB  │  ← Build this
│ (portfolios/) │  │ (PostgreSQL)   │
└───────────────┘  └────────────────┘
                           │
                           ▼
                   ┌────────────────┐
                   │ Wealth Backend │  ← Build this (no traffic yet)
                   │ (FastAPI/Go)   │
                   └────────────────┘

Actions:
1. Build Wealth backend (FastAPI/Go)
2. Migrate data model (CSV → PostgreSQL schema)
3. Copy business logic (skills → Python services)
4. Set up dual-write (platform writes to both DBs)
5. Verify data consistency (automated checks)

Risk: ZERO user impact (platform still serves 100% traffic)


Month 3-4: API Migration (Traffic Shift Phase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────┐
│  Platform Skills │  ← Now FACADE (calls Wealth API)
└────────┬─────────┘
         │ API calls
         ▼
┌────────────────────────┐
│  Wealth Backend (API)  │  ← Now serves traffic
└───────┬────────────────┘
        │ Reads/Writes
        ▼
┌────────────────┐
│ Wealth DB      │  ← Single source of truth
└────────────────┘

┌───────────────┐
│ Platform DB   │  ← STOP writing here (mark deprecated)
└───────────────┘

Actions:
1. Convert platform skills to API wrappers:
   ```python
   # domains/wealth/skills/portfolio-check.md
   # OLD: Direct calculation in skill
   # NEW: Call Wealth API

   async def execute_skill(context):
       response = await httpx.get("https://wealth-api/portfolio")
       return format_as_markdown(response.json())
   ```

2. Shift traffic gradually:
   - Week 1: 10% of requests go to Wealth API
   - Week 2: 25%
   - Week 3: 50%
   - Week 4: 100%

3. Monitor error rates, latency, data consistency

Risk: User-facing (monitor closely, rollback plan ready)


Month 5: Frontend Buildout (New UI Phase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Users still access via:                     New web UI launches:
┌──────────┐  ┌──────────┐                ┌─────────────────┐
│  Slack   │  │ WhatsApp │                │ wealth.aspora   │
└────┬─────┘  └─────┬────┘                │ (React/Next.js) │
     │              │                      └────────┬────────┘
     └──────┬───────┘                              │
            ▼                                      │
   ┌─────────────────┐                             │
   │ Platform Facade │                             │
   │ (API wrapper)   │                             │
   └────────┬────────┘                             │
            │                                      │
            └──────────────┬───────────────────────┘
                           ▼
                  ┌─────────────────┐
                  │  Wealth Backend │
                  │  (REST API)     │
                  └─────────────────┘

Actions:
1. Build web UI (React/Next.js)
2. Build mobile app (React Native)
3. Migrate users gradually:
   - Email existing users: "New web UI available"
   - Keep Slack/WhatsApp working (for now)

Risk: LOW (additive, doesn't break existing channels)


Month 6: Full Extraction (Decommission Platform Hooks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Users access via:                           Platform no longer involved:
┌─────────────────┐  ┌──────────┐         ╳ ┌──────────────────┐
│ wealth.aspora   │  │  Slack*  │         ╳ │ Platform Facade  │
│ (web + mobile)  │  │ WhatsApp*│         ╳ │ (REMOVED)        │
└────────┬────────┘  └─────┬────┘         ╳ └──────────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌──────────────────┐
         │ Wealth Slack Bot │  ← NEW (standalone, not platform)
         │ (separate bot)   │
         └────────┬─────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Wealth Backend │
         └─────────────────┘

Actions:
1. Deploy standalone Slack/WhatsApp bots (wealth-specific)
2. Remove wealth domain from platform
   ```bash
   rm -rf aspora-platform/domains/wealth/
   ```
3. Update platform docs to remove wealth references
4. Decommission platform's wealth database

Risk: ZERO (all users migrated to standalone product)
```

---

## Detailed Migration Checklist

### Phase 1: Backend Extraction (Months 1-2)

```bash
# Week 1-2: Project setup
□ Create new repo: wealth-product
□ Set up FastAPI/Go project structure
□ Set up PostgreSQL database
□ Set up Redis for caching
□ Set up CI/CD pipeline

# Week 3-4: Data model migration
□ Convert CSV schema to PostgreSQL
  - portfolios.csv → holdings table
  - goals.csv → goals table
  - Add indexes, constraints

□ Write migration scripts
  - One-time bulk import from platform
  - Ongoing sync (dual-write) during transition

□ Verify data consistency
  - Automated comparison tests (platform DB vs wealth DB)
  - Alert if data diverges

# Week 5-6: Business logic migration
□ Extract portfolio calculation logic
  - Copy from skills/portfolio-check.md
  - Implement as PortfolioService
  - Add unit tests (copy test cases from platform)

□ Extract risk management logic
  - Copy from skills/safety/position-cap.md
  - Implement as RiskService
  - Add unit tests

□ Extract trading logic (if exists)
  - Copy from skills/execute-trade.md
  - Implement as TradingService
  - Add integration tests

# Week 7-8: API layer
□ Build REST API endpoints
  - GET /api/v1/portfolio
  - POST /api/v1/trades
  - GET /api/v1/goals
  - PATCH /api/v1/goals/:id

□ Add authentication (JWT)
□ Add rate limiting
□ Add request validation (Pydantic)
□ Load testing (simulate platform traffic)
□ Document API (OpenAPI/Swagger)
```

### Phase 2: API Migration (Months 3-4)

```bash
# Week 1: Platform facade
□ Convert platform skills to API wrappers
  - Modify skills/*.md to call Wealth API HTTP
  - Keep response format identical (markdown)
  - Add error handling (if API down, return cached result)

# Week 2: Canary deployment (10% traffic)
□ Deploy canary config
  ```python
  # Platform skill executor
  WEALTH_API_TRAFFIC_PCT = 0.10  # 10% of requests

  async def execute_wealth_skill(skill_id, context):
      if random.random() < WEALTH_API_TRAFFIC_PCT:
          # Call new API
          return await call_wealth_api(skill_id, context)
      else:
          # Old path (direct calculation)
          return await execute_local_skill(skill_id, context)
  ```

□ Monitor metrics:
  - Error rate (new API vs old path)
  - Latency (new API vs old path)
  - Response diff (should be identical)

□ Alert on anomalies

# Week 3-4: Gradual rollout
□ Increase traffic: 10% → 25% → 50% → 100%
  - Increase by 15% each day if error rate < 0.1%
  - Rollback if error rate > 1%
  - Monitor Slack for user complaints

□ Update observability
  - Datadog dashboard: platform vs wealth API metrics
  - Alerts: wealth API error rate, latency p95

□ Decommission dual-write
  - Platform stops writing to platform DB
  - Wealth DB is now source of truth
```

### Phase 3: Frontend Buildout (Month 5)

```bash
# Week 1-2: Web UI
□ Bootstrap Next.js project
□ Build core pages:
  - Dashboard (portfolio overview)
  - Holdings (detailed table)
  - Goals (progress tracker)
  - Trading (buy/sell interface)
  - Settings (preferences)

□ Implement authentication UI
  - Login/signup forms
  - OAuth providers (Google, Apple)
  - Session management

□ Connect to Wealth API
  - Axios/fetch wrappers
  - Error handling
  - Loading states

# Week 3-4: Mobile UI
□ Bootstrap React Native project
□ Build core screens (same as web)
□ Test on iOS + Android
□ Submit to app stores (beta)

# Throughout: User migration
□ Email campaign: "New web UI available"
□ In-Slack message: "Try our new dashboard at wealth.aspora.com"
□ Offer migration incentive (free month, extra features)
```

### Phase 4: Full Extraction (Month 6)

```bash
# Week 1: Standalone channel bots
□ Build new Slack bot (wealth-specific)
  - Copy structure from platform adapter
  - Calls Wealth API directly (not platform)
  - Deploy as separate Slack app

□ Build new WhatsApp bot (if needed)

# Week 2: User migration
□ Notify users: "Wealth is moving to new bot"
  - Platform bot: "Invite @WealthBot for portfolio features"
  - Auto-invite WealthBot to user DMs
  - Gradual deprecation (platform bot returns "Use @WealthBot")

# Week 3: Decommission platform hooks
□ Remove wealth domain from platform
  ```bash
  cd aspora-platform
  rm -rf domains/wealth/
  git commit -m "Extract wealth domain to standalone product"
  ```

□ Update platform documentation
  - Remove wealth from README
  - Add link: "For wealth management, see wealth.aspora.com"

□ Shut down platform's wealth database
  ```bash
  # Final backup
  pg_dump platform_wealth_db > wealth_final_backup.sql

  # Drop tables
  DROP TABLE portfolios;
  DROP TABLE goals;
  ```

# Week 4: Post-migration monitoring
□ Verify NO users still using platform for wealth
□ Monitor standalone product metrics
□ Celebrate 🎉
```

---

## Hurdles and Mitigation

### Hurdle 1: Data Consistency During Dual-Write

**Problem**: Platform and Wealth DB can diverge during dual-write phase

**Mitigation**:

```python
# Automated consistency checker (run hourly)

import pandas as pd
from sqlalchemy import create_engine

def check_data_consistency():
    """
    Compare platform DB vs wealth DB, alert on mismatches
    """
    # Platform data
    platform_df = pd.read_csv('/platform/domains/wealth/data/portfolios.csv')

    # Wealth DB data
    wealth_engine = create_engine('postgresql://wealth-db/wealth_prod')
    wealth_df = pd.read_sql('SELECT * FROM holdings', wealth_engine)

    # Compare
    mismatches = []

    for user_id in platform_df['user_id'].unique():
        platform_user = platform_df[platform_df['user_id'] == user_id]
        wealth_user = wealth_df[wealth_df['user_id'] == user_id]

        # Check row counts
        if len(platform_user) != len(wealth_user):
            mismatches.append({
                'user_id': user_id,
                'issue': 'row_count_mismatch',
                'platform': len(platform_user),
                'wealth': len(wealth_user)
            })

        # Check values
        for symbol in platform_user['symbol']:
            platform_qty = platform_user[platform_user['symbol'] == symbol]['quantity'].values[0]
            wealth_qty = wealth_user[wealth_user['symbol'] == symbol]['quantity'].values

            if len(wealth_qty) == 0 or wealth_qty[0] != platform_qty:
                mismatches.append({
                    'user_id': user_id,
                    'symbol': symbol,
                    'issue': 'quantity_mismatch',
                    'platform': platform_qty,
                    'wealth': wealth_qty[0] if len(wealth_qty) > 0 else None
                })

    if mismatches:
        # Alert via Slack
        send_slack_alert(f"⚠️ Data consistency issues: {len(mismatches)} mismatches found")
        # Log details
        logger.error(f"Consistency check failed: {mismatches}")
    else:
        logger.info("✅ Data consistency check passed")

# Run hourly
schedule.every(1).hours.do(check_data_consistency)
```

### Hurdle 2: Response Format Changes (Markdown → JSON)

**Problem**: Platform returns markdown, Standalone returns JSON. Facades need formatting logic.

**Mitigation**: Build shared formatting library

```python
# wealth-common/formatters.py
# Used by BOTH platform facade AND standalone bots

def format_portfolio_markdown(portfolio_data: dict) -> str:
    """
    Shared formatter: JSON → Markdown
    Used by platform skills and standalone Slack bot
    """
    holdings_text = "\n".join([
        f"- {h['symbol']} ({h['sector']}) — {h['currency']} {h['position_value']:,.2f} ({h['pnl_pct']:+.1f}%)"
        for h in portfolio_data['holdings'][:10]
    ])

    sector_text = "\n".join([
        f"- {sector}: {pct:.1%}"
        for sector, pct in portfolio_data['sector_concentration'].items()
    ])

    goals_text = "\n".join([
        f"- {g['name']}: {g['progress']:.0%} → {g['currency']} {g['current_amount']:,.0f} / {g['target_amount']:,.0f}"
        for g in portfolio_data['goals']
    ])

    risk_emoji = "🟢" if portfolio_data['risk']['status'] == 'GREEN' else "🔴"

    return f"""
📊 Your Portfolio ({portfolio_data['currency']} {portfolio_data['total_value']:,.0f})

Top Holdings:
{holdings_text}

Sector Allocation:
{sector_text}

🎯 Goals:
{goals_text}

{risk_emoji} Risk Status: {portfolio_data['risk']['status']}
Daily P&L: {portfolio_data['risk']['daily_pnl_pct']:+.2%} (limit: {portfolio_data['risk']['daily_loss_limit']:.0%})
"""

# Platform skill uses it:
# domains/wealth/skills/portfolio-check.md
async def execute_skill(context):
    data = await call_wealth_api(context)
    return format_portfolio_markdown(data)

# Standalone Slack bot uses it:
# wealth-product/channels/slack_bot.py
@app.message(/portfolio/)
async def portfolio_command(message, say):
    data = await get_portfolio_api(user_id)
    await say(format_portfolio_markdown(data))
```

### Hurdle 3: Authentication Differences

**Problem**: Platform uses context injection, Standalone needs OAuth/JWT

**Mitigation**: User identity mapping during transition

```python
# During migration: support BOTH auth methods

class AuthService:
    def get_user_from_request(self, request):
        """
        Support both platform context and JWT
        """
        # Check for JWT (standalone auth)
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
            try:
                payload = jwt.decode(token, SECRET_KEY)
                return payload['sub']  # user_id
            except JWTError:
                pass

        # Check for platform context header (during migration)
        if 'X-Platform-User-ID' in request.headers:
            # Platform is calling on behalf of user
            platform_api_key = request.headers.get('X-Platform-API-Key')
            if platform_api_key == PLATFORM_TRUSTED_KEY:
                return request.headers['X-Platform-User-ID']

        raise HTTPException(status_code=401, detail="Unauthorized")

# Platform facade adds context header:
async def call_wealth_api(context):
    return await httpx.get(
        "https://wealth-api/portfolio",
        headers={
            "X-Platform-User-ID": context['user_id'],
            "X-Platform-API-Key": PLATFORM_TRUSTED_KEY
        }
    )
```

### Hurdle 4: Breaking Changes to Business Logic

**Problem**: Need to fix bug in risk algorithm. Platform and Standalone must stay in sync.

**Mitigation**: Extract to shared library FIRST, then both consume it

```python
# wealth-common/ (shared Python package)
# Used by BOTH platform and standalone

# wealth-common/risk.py
class RiskCalculator:
    """
    Shared risk calculation logic
    Platform and standalone both depend on this package
    """
    MAX_POSITION_SIZE = 0.02

    def calculate_position_size(self, price, portfolio_value, **kwargs):
        # Logic here
        pass

# Install in platform:
# aspora-platform/requirements.txt
wealth-common==1.2.3  # Pin version

# Install in standalone:
# wealth-product/requirements.txt
wealth-common==1.2.3  # Same version

# On fix/bugfix:
1. Update wealth-common to 1.2.4
2. Deploy to PyPI (private)
3. Update BOTH platform and standalone to 1.2.4
4. Deploy platform first (test)
5. Deploy standalone (test)
```

### Hurdle 5: Database Migration Without Downtime

**Problem**: How to migrate 100K users' data from platform DB to wealth DB?

**Mitigation**: Blue-green migration with verification

```python
# Step 1: Snapshot platform data
pg_dump platform_wealth_db > snapshot_2026_02_17.sql

# Step 2: Import to wealth DB
psql wealth_db < snapshot_2026_02_17.sql

# Step 3: Enable dual-write (platform writes to both DBs)
class PortfolioRepository:
    def update_position(self, user_id, symbol, quantity, price):
        # Write to platform DB
        platform_db.execute(
            "UPDATE portfolios SET quantity = ?, current_price = ? WHERE user_id = ? AND symbol = ?",
            quantity, price, user_id, symbol
        )

        # ALSO write to wealth DB (async, fire-and-forget)
        try:
            wealth_db.execute(
                "UPDATE holdings SET quantity = ?, current_price = ?, updated_at = NOW() WHERE user_id = ? AND symbol = ?",
                quantity, price, user_id, symbol
            )
        except Exception as e:
            # Log but don't fail (platform DB is still source of truth)
            logger.error(f"Dual-write to wealth DB failed: {e}")

# Step 4: Verify consistency (run for 1 week)
# See Hurdle 1 consistency checker

# Step 5: Flip source of truth (wealth DB becomes primary)
# Platform reads from wealth DB, writes to wealth DB only

# Step 6: Decommission platform DB
DROP TABLE portfolios;
```

### Hurdle 6: Testing During Migration

**Problem**: How to test standalone product before full migration?

**Mitigation**: Shadow mode testing

```python
# Platform skill runs BOTH old and new path, compares results

async def execute_portfolio_skill(context):
    # Old path (direct calculation)
    old_result = await calculate_portfolio_local(context)

    # New path (call wealth API) - SHADOW MODE
    try:
        new_result = await call_wealth_api(context)

        # Compare results
        if old_result != new_result:
            logger.warning(f"Shadow mode mismatch for user {context['user_id']}: old={old_result}, new={new_result}")
            # Alert engineering team
    except Exception as e:
        logger.error(f"Shadow mode API call failed: {e}")

    # ALWAYS return old result (new path doesn't affect users yet)
    return old_result
```

---

## Summary: Graduation Roadmap

### Reusable (80%+ of work)
✅ Business logic (portfolio calc, risk algorithms)
✅ Data models (CSV → SQL, same schema)
✅ Configuration (YAML files copy directly)
✅ Domain knowledge (sector limits, Kelly Criterion math)
✅ Test cases (copy to new codebase)

### Rebuild (20% of work)
❌ Execution layer (skills → REST API)
❌ Authentication (context injection → OAuth/JWT)
❌ Channel adapters (skill routing → API calls + formatting)
❌ Frontend (build from scratch if platform has no UI)
❌ Observability (Datadog setup, alerts, dashboards)

### Migration Duration
- **Fast path**: 3 months (team of 5, focus mode)
- **Safe path**: 6 months (gradual migration, extensive testing)
- **Complex**: 9 months (mobile app + multi-broker integration)

### Biggest Risks
1. **Data consistency** during dual-write (mitigate: automated checks)
2. **User disruption** during traffic shift (mitigate: canary deployment)
3. **Feature parity** before full migration (mitigate: shadow mode testing)
4. **Cost spike** during dual operation (mitigate: time-box migration, kill old system fast)

### Decision Framework

**Extract Wealth IF**:
- Wealth has >10K active users
- Wealth needs dedicated frontend (web + mobile)
- Wealth team can be 5+ people
- Regulatory/compliance requires separation
- Platform shared fate is unacceptable risk

**Keep Wealth on Platform IF**:
- Wealth has <1K users (not worth extraction cost)
- Wealth is primarily Slack/WhatsApp (no need for frontend)
- Team is <10 people total (can't afford separate product team)
- Cross-domain workflows are valuable (ECM → Wealth integration)
- Cost efficiency is critical (startup burn rate)

For your hackathon: Start on platform, validate for 6-12 months, extract when traction is clear.
