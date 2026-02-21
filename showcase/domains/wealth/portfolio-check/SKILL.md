---
name: portfolio-check
role: specialist
domain: wealth
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.08"
---

# Portfolio Health Check

## Task

Analyze an NRI investor's multi-currency portfolio and produce a health report covering: current allocation vs target, goal progress, currency exposure, and whether rebalancing is needed.

## Context You'll Receive

```json
{
  "user_id": "string",
  "risk_profile": "conservative | moderate | aggressive",
  "holdings": [{ "asset": "string", "value": "number", "currency": "string", "asset_class": "string" }],
  "goals": [{ "name": "string", "target": "number", "current": "number", "deadline": "string" }],
  "fx_rates": { "USD_INR": "number", "AED_INR": "number", "GBP_INR": "number" }
}
```

## Output Format

```json
{
  "user_id": "string",
  "total_portfolio_value_inr": "number",
  "currency_breakdown": { "INR": "number", "USD": "number", "AED": "number" },
  "asset_class_allocation": {
    "equity": { "current": "number", "target": "number", "drift": "number" },
    "debt": { "current": "number", "target": "number", "drift": "number" },
    "gold": { "current": "number", "target": "number", "drift": "number" },
    "cash": { "current": "number", "target": "number", "drift": "number" }
  },
  "goal_progress": [
    { "name": "string", "progress_pct": "number", "on_track": "boolean", "monthly_needed": "number" }
  ],
  "rebalance_needed": "boolean",
  "drift_percentage": "number",
  "currency_risk_assessment": "string",
  "recommendations": ["string"]
}
```

## Rebalancing Rules

| Risk Profile | Target: Equity | Target: Debt | Target: Gold | Target: Cash | Drift Threshold |
|-------------|---------------|-------------|-------------|-------------|-----------------|
| Conservative | 30% | 50% | 10% | 10% | 5% |
| Moderate | 55% | 25% | 10% | 10% | 7% |
| Aggressive | 75% | 10% | 10% | 5% | 10% |

If any asset class drifts beyond threshold → `rebalance_needed: true`.

## Goal Progress Calculation

For each goal:
```
months_remaining = months between now and deadline
monthly_needed = (target - current) / months_remaining
on_track = (current / target) >= (elapsed_months / total_months)
```

## Guardrails

- NEVER recommend selling assets without explaining tax implications (LTCG/STCG for NRI)
- ALWAYS convert all values to INR for comparison using provided fx_rates
- ALWAYS flag if > 40% of portfolio is in a single currency (concentration risk)
- ALWAYS flag if a goal's monthly_needed exceeds 50% of known monthly surplus
- If fx_rates are missing, state that currency risk cannot be assessed — do not use stale rates
