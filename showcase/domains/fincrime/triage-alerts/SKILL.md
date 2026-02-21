---
name: triage-alerts
role: specialist
domain: fincrime
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.15"
---

# FinCrime Alert Triage

## Task

Triage a batch of TRM (Transaction Risk Management) alerts. For each alert, classify as Quick Approve, Quick Hold, or Needs Investigation based on rule pattern knowledge and composite risk scoring.

This skill handles the first-pass triage. Deep investigation is a separate Phase 2 workflow.

## Context You'll Receive

```json
{
  "alerts": [
    {
      "event_id": "string",
      "order_id": "string",
      "user_id": "string",
      "amount": "number",
      "currency": "string",
      "beneficiary_id": "string",
      "trm_rule_tag": "string (one of 22 production rules)",
      "severity": "Critical | Warning",
      "composite_risk_score": "number (0-100)",
      "status": "on_hold",
      "user_kyc_status": "string",
      "order_count_30d": "number",
      "distinct_bene_count_30d": "number",
      "previous_alerts_count": "number",
      "has_prior_rejection": "boolean",
      "created_at": "string (ISO 8601)"
    }
  ]
}
```

## Quick Classification Rules

| Pattern | Classify As | Rationale |
|---------|-------------|-----------|
| SOURCE_ACCOUNT_NAME_MISMATCH + user has 5+ successful orders + same source account | Quick Approve | Established pattern, nickname mismatch |
| WATCHLIST_SCREENING_HIT + any severity | Needs Investigation | Watchlist requires documented review always |
| MONEY_LAUNDERING + HIGH_RISK_GENERAL + velocity spike + new beneficiary | Quick Hold | Multiple critical signals |
| LARGE_AMOUNT + amount within user's historical p95 + verified beneficiary | Quick Approve | Normal for this user |
| STRUCTURING_SUSPECTED + 3+ transactions just below threshold | Needs Investigation | Classic structuring pattern |
| BENEFICIARY_FLAGGED_FOR_AML + repeat beneficiary across multiple users | Quick Hold | Potential money mule network |

## Output Format

```json
{
  "triage_date": "string (ISO 8601)",
  "total_alerts": "number",
  "summary": {
    "quick_approve": "number",
    "quick_hold": "number",
    "needs_investigation": "number"
  },
  "quick_approvals": [
    {
      "event_id": "string",
      "order_id": "string",
      "rule_tag": "string",
      "reason": "string (specific, not generic)",
      "risk_score": "number"
    }
  ],
  "quick_holds": [
    {
      "event_id": "string",
      "order_id": "string",
      "rule_tags": ["string"],
      "red_flags": ["string"],
      "risk_score": "number",
      "recommended_action": "string"
    }
  ],
  "investigation_queue": [
    {
      "event_id": "string",
      "order_id": "string",
      "rule_tag": "string",
      "priority": "P1 | P2 | P3",
      "reason_for_investigation": "string",
      "risk_score": "number"
    }
  ]
}
```

## Guardrails

- NEVER approve a Critical severity alert without documented rationale
- NEVER copy-paste rationale between alerts — each must reflect specific facts
- NEVER dismiss based solely on "low amount" — structuring uses many small transactions
- NEVER assume a watchlist hit is a false positive without evidence
- ALWAYS check prior alert history — repeat patterns compound risk
- ALWAYS document what you checked, even if you found nothing
- Critical severity alerts approaching 24h SLA get P1 priority regardless of risk score
