# FRM — Guardrails

> Anti-patterns learned from production. Every correction adds a guardrail.

---

## GRD-001: Always Cross-Check Beneficiary Across Users

**Mistake**: Classified alert as Quick Approve based on low amount and repeat beneficiary, without checking if beneficiary was receiving from multiple users.
**Impact**: Potential money mule network missed. Beneficiary BEN-7832 receiving from 3+ unique users.
**Rule**: ALWAYS check beneficiary_id across all users in batch and recent history before any Quick Approve. Beneficiary receiving from 3+ unique users in 7 days MUST go to Needs Investigation.
**Detection**: Quick Approve classification without cross-user beneficiary analysis in reasoning.

---

## GRD-002: Never Dismiss Based Solely on Low Amount

**Mistake**: Low amount (AED 1,200) used as primary reason for Quick Approve.
**Impact**: Structuring uses many small transactions below reporting thresholds.
**Rule**: Amount alone is never sufficient for Quick Approve. Always combine with behavioral signals.
**Detection**: Reasoning mentions "low amount" as primary justification.

---


---

## GRD-003: Auto-generated from correction

**Mistake**: Agent produced incorrect output.
**Impact**: User had to manually correct.
**Rule**: For UAE corporate KYC reviews, ALWAYS check DFSA (Dubai Financial Services Authority) sanctions list before proceeding. UAE corporates require mandatory DFSA screening plus UBO verification for any shareholder with >25% ownership. Missing DFSA check is a compliance violation.
**Detection**: Auto-generated — review and refine this guardrail.

## When to Add New Guardrails

- Analyst corrects a classification → guardrail added automatically via `aspora correct`
- Compliance review flags pattern → add manually here
