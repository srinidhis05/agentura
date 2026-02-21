# Falcon Failed - Order Completed Runbook

## Overview
Order is marked COMPLETED but Falcon transaction status is FAILED — status mismatch.

**Team:** Ops  
**Stuck Reason:** `falcon_failed_order_completed_issue`

## Common Causes
- Falcon failure not properly propagated
- Status sync race condition
- Manual order completion without checking Falcon
- Webhook processing error

## Resolution Steps

### Step 1: Verify Status Mismatch
1. Check `order_status` = COMPLETED
2. Check `falcon_status` = FAILED
3. This is an inconsistent state that needs correction

### Step 2: Investigate Falcon Failure
1. Access Falcon dashboard
2. Find transaction by ftv_transaction_id
3. Get failure reason and timestamp
4. Check if payout actually failed

### Step 3: Determine Correct State
**If Falcon truly failed (payout not sent):**
1. Order status should be FAILED, not COMPLETED
2. Customer did NOT receive funds
3. Refund may be needed

**If Falcon actually succeeded (status wrong):**
1. Falcon status needs correction
2. Verify with payout partner
3. Update Falcon status

### Step 4: Correct Order Status
Based on investigation:
1. If payout failed: Change order_status to FAILED, trigger refund
2. If payout succeeded: Correct Falcon status to COMPLETED
3. Update all related systems

### Step 5: Customer Impact
1. Check if customer was incorrectly notified of completion
2. If refund needed, prioritize communication
3. If payout succeeded, confirm with customer

### Step 6: Root Cause
1. Investigate how mismatch occurred
2. Report to engineering if systemic
3. Document in ECM

## Escalation
Escalate immediately if:
- Cannot determine true status
- Customer claims non-receipt
- High-value order (> 10,000)

Contact: ops-lead@aspora.com AND engineering-on-call
