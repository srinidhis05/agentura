# ECM Operations — Guardrails

> Anti-patterns learned from production. Every correction adds a guardrail.

---

## GRD-001: Never Invent Diagnoses

**Mistake**: Agent generated a plausible-sounding diagnosis for an unknown sub-state.
**Impact**: Ops agent acted on wrong diagnosis, escalated to wrong team, 4h wasted.
**Rule**: If sub-state is not in `diagnosis-mapping.yaml`, output "Unknown sub-state — escalate to L2."
**Detection**: Output contains diagnosis not present in config YAML.

---

## GRD-002: UAE Corridor CNR_RESERVED Needs LULU Escalation

**Mistake**: Applied standard escalation path for UAE corridor order stuck in CNR_RESERVED.
**Impact**: Order sat 8h longer than needed. LULU ops handles this, not standard path.
**Rule**: When corridor = UAE AND sub_state = CNR_RESERVED, ALWAYS check LULU escalation path first.
**Detection**: UAE + CNR_RESERVED in input, but LULU not mentioned in output.

---


---

## GRD-003: Auto-generated from correction

**Mistake**: Agent produced incorrect output.
**Impact**: User had to manually correct.
**Rule**: UAE corridor orders stuck in CNR_RESERVED need LULU escalation, not standard path. Always check LULU ops team first for UAE orders.
**Detection**: Auto-generated — review and refine this guardrail.


---

## GRD-004: Auto-generated from correction

**Mistake**: Agent produced incorrect output.
**Impact**: User had to manually correct.
**Rule**: UK corridor orders in COMPLIANCE_HOLD must be escalated to the FCA Regulatory Affairs team, not generic Compliance Operations. FCA holds require a specific SAR (Suspicious Activity Report) filing check within 4 hours. Standard compliance team cannot clear FCA holds — only the FCA liaison officer has authority.
**Detection**: Auto-generated — review and refine this guardrail.


---

## GRD-005: Auto-generated from correction

**Mistake**: Agent produced incorrect output.
**Impact**: User had to manually correct.
**Rule**: India inward remittances in RBI_HOLD MUST go through the Authorized Dealer (AD) bank route, not generic RBI Liaison. The AD bank is the only entity authorized to release RBI holds under FEMA Section 6. Always check FEMA purpose code (P0103 for family maintenance, P0107 for personal gifts) as wrong purpose code is the #1 reason for RBI holds on India corridors. Escalation goes to AD Bank compliance desk, not our internal team.
**Detection**: Auto-generated — review and refine this guardrail.


---

## GRD-006: Auto-generated from correction

**Mistake**: Agent produced incorrect output.
**Impact**: User had to manually correct.
**Rule**: Singapore MAS_REVIEW holds are governed by MAS Notice 626 (Prevention of Money Laundering). For amounts above SGD 20,000, the MAS-appointed compliance officer at our Singapore entity must file a CTR (Cash Transaction Report) BEFORE the hold can be released. Standard ops cannot bypass this — it requires the Singapore MLRO (Money Laundering Reporting Officer) sign-off. Typical clearance: 2-4 hours after CTR filing.
**Detection**: Auto-generated — review and refine this guardrail.

## When to Add New Guardrails

- User corrects an output → guardrail added automatically via `aspora correct`
- Ops manager flags a pattern → add manually here
- Max 20 guardrails per domain. If more, some belong in individual skill guardrails.
