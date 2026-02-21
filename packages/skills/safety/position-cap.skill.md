---
name: position-cap
description: Enforce position sizing limits using Kelly Criterion
triggers:
  - "position size"
  - "how much to buy"
  - "quantity"
  - "allocation"
---

# Position Cap Skill

> You calculate safe position sizes. Max 2% per position, always.

## Hard Limits

| Rule | Limit | Reason |
|------|-------|--------|
| Max Single Position | 2% of portfolio | Diversification |
| Max Sector Exposure | 25% | Concentration risk |
| Max Positions per Sector | 5 | Avoid over-betting |

## Position Sizing Algorithm

Use **Half-Kelly Criterion** with volatility adjustment:

```typescript
function calculatePositionSize(
  price: number,
  portfolioValue: number,
  winRate: number = 0.5,
  avgWin: number = 0.08,
  avgLoss: number = 0.04,
  volatility: number = 0.2
): number {
  // Kelly Criterion
  const kellyPct = (winRate * avgWin - (1 - winRate) * avgLoss) / avgWin;

  // Half-Kelly for safety
  const halfKelly = Math.max(0, kellyPct / 2);

  // Volatility adjustment
  const volAdjusted = halfKelly * (1 / (1 + volatility));

  // Cap at 2%
  const cappedPct = Math.min(volAdjusted, 0.02);

  return Math.floor((portfolioValue * cappedPct) / price);
}
```

## Checking Before Trade

```json
{
  "symbol": "RELIANCE.NS",
  "requested_quantity": 50,
  "price": 2450,
  "position_value": 122500,
  "portfolio_value": 1000000,
  "position_pct": 12.25,
  "max_allowed_pct": 2.0,
  "max_allowed_quantity": 8,
  "decision": "REDUCE",
  "message": "Position 12.25% exceeds 2% limit. Reducing to 8 shares."
}
```

## User Communication

When position too large:

```
📊 Position Size Adjusted

You requested: 50 shares of RELIANCE (₹1,22,500)
This would be: 12.25% of your portfolio

Maximum allowed: 2% (₹20,000)
Adjusted quantity: 8 shares

Why? Keeping any single position under 2% ensures:
- No single loss can significantly hurt you
- Better diversification across opportunities
- Emotional discipline in volatile markets

Should I proceed with 8 shares?
```

## Sector Concentration Check

```typescript
function checkSectorConcentration(
  symbol: string,
  newPositionValue: number,
  portfolio: Portfolio
): { allowed: boolean; message: string } {
  const sector = getSector(symbol);
  const currentSectorExposure = portfolio.sectorExposure[sector] || 0;
  const newExposure = currentSectorExposure + (newPositionValue / portfolio.totalValue) * 100;

  if (newExposure > 25) {
    return {
      allowed: false,
      message: `Adding this would put ${sector} at ${newExposure.toFixed(1)}% (max 25%)`
    };
  }

  return { allowed: true, message: '' };
}
```

## Guardrails

1. **NEVER** allow positions > 2% regardless of user confidence
2. **ALWAYS** check sector concentration before approving
3. **ALWAYS** suggest the safe quantity when rejecting
4. **NEVER** average down into losing positions beyond limit
5. **ALWAYS** consider existing positions when calculating new exposure
