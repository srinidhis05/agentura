# Cancellation Pending Runbook

## Overview
Order cancellation has been requested but not yet completed.

**Team:** Ops  
**Stuck Reason:** `cancellation_pending`

## Common Scenarios
- `lulu_status` = CANCELLATION_REQUEST_CREATED (request submitted)
- `lulu_status` = TXN_TRANSMITTED but falcon_status = FAILED (needs cancel)
- Payout failed but Lulu cancellation not initiated

## Resolution Steps

### Step 1: Verify Cancellation Status
1. Check `lulu_status`:
   - CANCELLATION_REQUEST_CREATED → Request submitted, waiting
   - TXN_TRANSMITTED → May need cancellation
2. Check `falcon_status` — if FAILED, cancellation needed
3. Check `payout_status` — if FAILED, confirms need to cancel

### Step 2: Check Lulu Cancellation Queue
1. Access Lulu dashboard
2. Find order in cancellation queue
3. Check if cancellation is processing or stuck
4. Note any error messages

### Step 3: Trigger Cancellation (if not started)
If cancellation not yet requested:
1. Verify order should be cancelled
2. Submit cancellation request to Lulu
3. Wait for acknowledgment

### Step 4: Monitor Cancellation
1. Cancellation typically completes within 1-4 hours
2. Expected final status: CANCELLATION_COMPLETED
3. If stuck > 4 hours, escalate to Lulu support

### Step 5: Post-Cancellation
Once cancelled:
1. Order should auto-update to FAILED
2. Refund process should trigger (see refund-pending.md)
3. Update ECM ticket

## Escalation
Escalate if:
- Cancellation stuck > 4 hours
- Lulu rejects cancellation
- Funds already credited to beneficiary (may need recall)
- Customer dispute

Contact: ops-lead@aspora.com or #ops-ecm Slack channel
