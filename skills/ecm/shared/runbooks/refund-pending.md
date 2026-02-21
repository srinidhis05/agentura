# Refund Pending Runbook

## Overview
Order failed or was cancelled and customer refund has not been processed. For **Lulu excess credit** (auto-cancel after 2 days no RFI response), use [excess-credit.md](excess-credit.md). For **CNR** (Order + Falcon COMPLETED but beneficiary not received), use [cnr-completed-not-received.md](cnr-completed-not-received.md).

**Team:** Ops  
**Stuck Reason:** `refund_pending`

## Common Causes
- Order failed after payment captured
- Lulu cancellation completed but refund not triggered (see [excess-credit.md](excess-credit.md) for Lulu flow)
- Checkout payment captured but order cancelled
- GOMS order failed but refund not initiated

## Resolution Steps

### Step 1: Identify Payment Source
1. Check `payment_acquirer` (CHECKOUT, LEANTECH, UAE_MANUAL)
2. Check `checkout_status` — if CAPTURED, refund needed via Checkout
3. Check `truelayer_status` — if not EXECUTED, TrueLayer refund may be needed

### Step 2: Verify Cancellation Complete
1. For AED: Check `lulu_status` = CANCELLATION_COMPLETED
2. For GBP/EUR: Check `goms_order_status` = FAILED and `goms_sub_state` = FAILED

### Step 3: Initiate Refund
For **Checkout**:
1. Access Checkout dashboard
2. Find transaction by order_id
3. Initiate full refund
4. Note refund reference number

For **TrueLayer** (GBP/EUR):
1. Access TrueLayer dashboard
2. Initiate refund payment
3. Verify payment_reference = 'refund_payment'

For **UAE Manual**:
1. Contact finance team for manual refund
2. Provide order details and amount

### Step 4: Update Status
1. Mark refund as initiated in tracking
2. Update ECM ticket with refund reference
3. Monitor for refund completion (usually 3-5 business days)

## Refund TAT (SOP alignment)
- **UAE FTS (Lulu excess credit):** Within **2 working days** of receiving user details (see [excess-credit.md](excess-credit.md)).
- **Checkout / TrueLayer / UAE Manual:** Per payment rail; typically 3–5 business days.

## Escalation
Escalate if:
- Refund fails or is rejected
- Customer claims refund not received after 7 days
- High-value refund (> $10,000 — Finance approval per CNR SOP)

See [ESCALATION.md](../ESCALATION.md) for TechOps/FinOps/Lulu contacts.
