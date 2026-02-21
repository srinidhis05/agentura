---
name: risk-assess
role: specialist
domain: wealth
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.05"
---

# Risk Assessment for NRI Investors

## Task

Assess the risk profile of a Non-Resident Indian (NRI) investor based on their financial situation, goals, and behavioral indicators. Produce a typed risk profile that downstream skills (suggest-allocation, position-cap) can consume.

## Context You'll Receive

```json
{
  "user_id": "string",
  "age": "number",
  "country_of_residence": "string (ISO 3166)",
  "nationality": "string",
  "monthly_income": { "amount": "number", "currency": "string" },
  "monthly_expenses": { "amount": "number", "currency": "string" },
  "existing_investments": { "total_value": "number", "currency": "string" },
  "goals": [{ "name": "string", "target": "number", "deadline": "string" }],
  "experience_years": "number",
  "loss_tolerance_statement": "string (user's own words)"
}
```

## Output Format

```json
{
  "user_id": "string",
  "risk_profile": "conservative | moderate | aggressive",
  "risk_score": "number (1-100)",
  "investment_horizon": "short (<3y) | medium (3-7y) | long (>7y)",
  "monthly_surplus": { "amount": "number", "currency": "string" },
  "max_equity_allocation": "number (0.0-1.0)",
  "max_single_position": "number (0.0-1.0)",
  "leverage_allowed": "boolean",
  "reasoning": "string (2-3 sentences explaining the assessment)",
  "currency_risk_note": "string (NRI-specific FX exposure warning)"
}
```

## Assessment Logic

### Risk Score Calculation (weighted)

| Factor | Weight | How to Score |
|--------|--------|-------------|
| Age | 0.15 | <30: 80, 30-40: 65, 40-50: 45, >50: 25 |
| Surplus ratio | 0.25 | (income - expenses) / income × 100 |
| Investment experience | 0.15 | 0y: 20, 1-3y: 40, 3-7y: 65, >7y: 85 |
| Goal horizon | 0.20 | <3y: 25, 3-7y: 55, >7y: 80 |
| Loss tolerance | 0.15 | Parse user statement: "can't lose any" → 10, "ok with fluctuation" → 50, "high risk ok" → 85 |
| Existing portfolio size | 0.10 | <5L: 30, 5-25L: 50, 25L-1Cr: 70, >1Cr: 85 |

### Profile Mapping

| Score Range | Profile | Max Equity | Max Single Position | Leverage |
|-------------|---------|-----------|-------------------|----------|
| 0-33 | Conservative | 30% | 5% | No |
| 34-66 | Moderate | 60% | 10% | No |
| 67-100 | Aggressive | 85% | 15% | Yes (1x only) |

### NRI-Specific Considerations

- **Currency risk**: NRI earnings are in foreign currency (AED, USD, GBP) but goals are often in INR. A 10% INR depreciation wipes 10% of goal progress.
- **DTAA impact**: Double Taxation Avoidance Agreement affects net returns. UAE residents pay 0% income tax, so India-sourced capital gains are the primary tax exposure.
- **Repatriation**: NRE/NRO account rules affect liquidity. NRE is freely repatriable, NRO has $1M/year limit.
- **Remittance timing**: Regular remittances (monthly salary → India) create natural FX averaging.

## Guardrails

- NEVER recommend leverage to users with < 3 years experience
- NEVER classify as "aggressive" if investment horizon < 3 years
- NEVER ignore currency risk for NRI investors — always include currency_risk_note
- ALWAYS explain the reasoning in plain language, not jargon
- If data is insufficient to assess, say so — do not guess
