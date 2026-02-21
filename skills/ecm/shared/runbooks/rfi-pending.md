# RFI Pending Runbook

## Overview
Order has a Request for Information (RFI) pending customer response. Applies to:
- `rfi_order_within_24_hr` — RFI created, within 24 hour window
- `rfi_order_grtr_than_24_hr` — RFI created, exceeded 24 hours

**Team:** KYC_ops

## Data freshness
If **modified_at** in the `transfer_rfi` table is **more than 4 hours** ago, check **AlphaDesk** for the latest RFI status before acting on this runbook. The Redshift data may be stale.

## Resolution Steps

### Step 1: Check RFI Status
1. Query `transfer_rfi` table by `reference_id` = order_id
2. Note: `status`, `previous_status`, `rfitype`, `requested_items`, `modified_at`
3. Determine if customer has responded (status = SUBMITTED) or not (status = REQUESTED)
4. If `modified_at` > 4 hours ago → check AlphaDesk for real-time status before proceeding

### Step 2: Determine Action Based on RFI Age

#### RFI status = REQUESTED (customer has NOT responded)

**Within 24 hours** (`rfi_order_within_24_hr`):
- **DO NOT nudge the user.** No action required.
- Customer has time to respond — monitoring only.
- Confirm notification was sent (check `source_tenant`).
- Outcome: **Wait. No outreach.**

**Exceeded 24 hours** (`rfi_order_grtr_than_24_hr`):
- **Nudge the user** — send a follow-up reminder via email/SMS/push.
- Escalate to customer support for direct outreach if no response.
- If no response after 48 hours, consider cancellation.
- Outcome: **Send reminder. Escalate if needed.**

#### RFI status = SUBMITTED (customer HAS responded)
- Documents submitted — check if they are under review or already processed.
- If `modified_at` > 4 hours with no status change → check AlphaDesk.
- Outcome: **Monitor provider review. No customer action needed.**

#### RFI status = REJECTED
- Customer's submission was rejected (check `rejection_message`).
- Customer needs to resubmit correct documents.
- If rejection is > 24 hours old with no resubmission → nudge the user.
- Outcome: **Notify customer of rejection reason. Request resubmission.**

### Step 3: Document Resolution
1. Record customer response or lack thereof
2. If documents received and accepted, mark RFI as resolved
3. Update order to proceed or cancel

## Lulu RFI Validity (SOP)
- **2 working days** for Lulu AML/RFI. If no response → Lulu auto-cancels and blocks user; follow [excess-credit.md](excess-credit.md) for refund. For **Txn Released** AML/RFI, see [txn-released-aml-rfi.md](txn-released-aml-rfi.md).

## Escalation
Escalate if:
- Customer unreachable after multiple attempts
- Documents provided but still flagged
- High-value transaction (> 50,000)

See [ESCALATION.md](../ESCALATION.md) for TechOps/KYC and Lulu contacts.
