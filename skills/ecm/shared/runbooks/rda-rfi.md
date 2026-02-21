# RDA Partner with RFI Runbook

## Overview
Order is stuck at RDA partner with an active RFI (Request for Information) — partner is on hold waiting for customer documents.

**Team:** KYC_ops
**Stuck Reasons:**
- `stuck_at_rda_partner_rfi_within_24_hrs` — RFI active, within 24 hours
- `stuck_at_rda_partner_rfi_grtr_than_24_hrs` — RFI active, exceeded 24 hours

## Data freshness
If **modified_at** in the `transfer_rfi` table is **more than 4 hours** ago, check **AlphaDesk** for the latest RFI status before acting on this runbook. The Redshift data may be stale.

## Resolution Steps

### Step 1: Check RFI Status
1. Query `transfer_rfi` table by `reference_id` = order_id
2. Verify `rfi_status` is not NULL (RFI exists)
3. Note: `status`, `previous_status`, `requested_items`, `modified_at`
4. Check `rda_status` = ONHOLD (partner waiting)
5. If `modified_at` > 4 hours ago → check AlphaDesk for real-time status before proceeding

### Step 2: Determine Action Based on RFI Age

#### RFI status = REQUESTED (customer has NOT responded)

**Within 24 hours** (`stuck_at_rda_partner_rfi_within_24_hrs`):
- **DO NOT nudge the user.** No action required.
- Customer has time to respond — monitoring only.
- Confirm notification was sent.
- Outcome: **Wait. No outreach.**

**Exceeded 24 hours** (`stuck_at_rda_partner_rfi_grtr_than_24_hrs`):
- **Nudge the user** — send follow-up reminder (email/SMS/push).
- Escalate to customer support for direct outreach.
- If no response after 48 hours, consider cancellation.
- Outcome: **Send reminder. Escalate if needed.**

#### RFI status = SUBMITTED (customer HAS responded)
- Documents submitted — awaiting partner review.
- If `modified_at` > 4 hours with no status change → check AlphaDesk.
- Once partner releases hold, submit documents if needed.
- Outcome: **Monitor partner review. No customer action needed.**

#### RFI status = REJECTED
- Customer's documents were rejected (check `rejection_message`).
- Customer must resubmit correct documents.
- If rejection is > 24 hours old with no resubmission → nudge the user.
- Outcome: **Notify customer of rejection reason. Request resubmission.**

### Step 3: Submit Documents to Partner
Once documents received and accepted:
1. Verify documents meet requirements
2. Submit to RDA partner via their portal
3. Update RFI status to SUBMITTED
4. Monitor partner for release from hold

### Step 4: Document Resolution
1. Record customer response and documents provided
2. Note partner reference for submission
3. Update ECM ticket

## Escalation
Escalate if:
- Documents rejected by partner
- Customer disputes RFI requirements
- Order > 48 hours with no customer response
- High-value order (> 50,000)

Contact: kyc-lead@aspora.com or #kyc-ops Slack channel
