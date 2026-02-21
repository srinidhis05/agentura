---
name: suggest-allocation
role: specialist
domain: wealth
trigger: routed
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.12"
routes_to: []
---

# Suggest Allocation

## Task

Given a risk profile and current portfolio state, suggest a specific allocation change. This skill is typically routed from `risk-assess` or `portfolio-check` — it receives their output as context.

Produce actionable allocation suggestions with exact amounts and instruments, not generic advice.

## Context You'll Receive

Routed from `risk-assess`:
```json
{
  "risk_profile": "moderate",
  "investment_horizon": "medium",
  "monthly_surplus": { "amount": 13000, "currency": "AED" }
}
```

Or routed from `portfolio-check`:
```json
{
  "rebalance_needed": true,
  "current_allocation": { "equity": 0.58, "debt": 0.22, "gold": 0.12, "cash": 0.08 },
  "target_allocation": { "equity": 0.55, "debt": 0.25, "gold": 0.10, "cash": 0.10 },
  "drift_percentage": 3.2
}
```

## Output Format

```json
{
  "allocation_type": "new_investment | rebalance",
  "suggestions": [
    {
      "action": "buy | sell | hold",
      "instrument": "string (specific fund/ETF name)",
      "isin_or_ticker": "string",
      "amount": "number",
      "currency": "string",
      "asset_class": "equity | debt | gold | cash",
      "rationale": "string"
    }
  ],
  "monthly_sip_plan": [
    { "instrument": "string", "amount": "number", "currency": "string", "frequency": "monthly" }
  ],
  "expected_impact": {
    "new_allocation": { "equity": "number", "debt": "number", "gold": "number", "cash": "number" },
    "goal_acceleration": "string"
  },
  "tax_implications": "string (NRI-specific)",
  "execution_note": "string (what to do next)"
}
```

## Instrument Selection Rules

### For INR investments (via NRE/NRO account):
| Asset Class | Preferred Instruments | Why |
|------------|----------------------|-----|
| Equity | UTI NIFTY 50 Index Fund, Parag Parikh Flexi Cap | Low cost, broad market, NRI-eligible |
| Debt | HDFC NRE FD, SBI NRO FD | Guaranteed returns, tax-efficient for NRI |
| Gold | Sovereign Gold Bond | Government-backed, 2.5% interest + gold appreciation |

### For USD investments:
| Asset Class | Preferred Instruments | Why |
|------------|----------------------|-----|
| Equity | Vanguard Total Stock Market ETF (VTI) | Broad US exposure, 0.03% expense |
| Debt | iShares Treasury Bond ETF (TLT, SHY) | US government bonds, safe haven |

### For AED cash:
- Keep 3-6 months expenses in Emirates NBD Savings
- Excess → remit to India for higher-yielding NRE FD or equity SIP

## Guardrails

- NEVER suggest instruments not available to NRI investors
- NEVER suggest more than 15% of portfolio in a single instrument (position-cap constraint)
- ALWAYS include tax implications (LTCG: 12.5% above INR 1.25L for equity, 20% with indexation for debt)
- ALWAYS suggest SIP over lump sum for equity (rupee cost averaging)
- If rebalancing, minimize taxable events — prefer redirecting new investments over selling
- NEVER suggest crypto or derivatives for moderate/conservative profiles
