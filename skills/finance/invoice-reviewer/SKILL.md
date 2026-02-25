---
name: invoice-reviewer
role: specialist
domain: finance
trigger: manual
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.10"
timeout: "45s"
---

# Invoice Reviewer

## Trigger
- "review invoice"
- "check invoice {invoice_id}"
- "validate invoice"
- "is this invoice correct"

## Task

Review an invoice for completeness, accuracy, and compliance. Verify line items match PO terms, check math, flag missing fields, and detect common fraud indicators (altered dates, mismatched bank details, round amounts).

## Input Format

```json
{
  "invoice": {
    "invoice_id": "INV-2026-0042",
    "vendor": "Acme Cloud Services",
    "vendor_tax_id": "XX-1234567",
    "date": "2026-01-20",
    "due_date": "2026-02-19",
    "currency": "USD",
    "line_items": [
      {
        "description": "Cloud hosting - January 2026",
        "quantity": 1,
        "unit_price": 3500.00,
        "total": 3500.00
      }
    ],
    "subtotal": 3500.00,
    "tax_rate": 0.08,
    "tax_amount": 280.00,
    "total": 3780.00,
    "bank_details": {
      "bank_name": "First National Bank",
      "account": "****4567",
      "routing": "021000021"
    }
  },
  "purchase_order": {
    "po_number": "PO-2025-118",
    "agreed_amount": 3500.00,
    "vendor": "Acme Cloud Services",
    "terms": "Net 30"
  }
}
```

## Output Format

```json
{
  "invoice_id": "INV-2026-0042",
  "verdict": "approved | needs_review | rejected",
  "math_check": {
    "line_items_correct": true,
    "subtotal_correct": true,
    "tax_correct": true,
    "total_correct": true
  },
  "po_match": {
    "vendor_match": true,
    "amount_within_tolerance": true,
    "variance": 0.00,
    "tolerance_pct": 5
  },
  "completeness": {
    "missing_fields": [],
    "warnings": []
  },
  "fraud_indicators": [
    {
      "indicator": "string",
      "severity": "high | medium | low",
      "detail": "string"
    }
  ],
  "recommendation": "Approve — all checks passed, matches PO-2025-118."
}
```

## Guardrails

1. Never approve invoices — only recommend. Final approval is always human.
2. Check math independently: sum line items, verify tax calculation, verify total.
3. PO variance tolerance is 5% unless specified otherwise.
4. Flag bank detail changes from previous invoices for the same vendor.
5. Weekend-dated or holiday-dated invoices get a medium fraud flag.
6. Always verify tax_id format matches the vendor's jurisdiction.
