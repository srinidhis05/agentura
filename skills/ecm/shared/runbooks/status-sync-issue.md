# Status Sync Issue Runbook

## Overview
Order or payout is completed but the status is not synced across systems.

**Team:** Ops  
**Stuck Reason:** `status_sync_issue`

## Common Scenarios
1. Lulu status = CREDITED but order_status = PROCESSING_DEAL_IN
2. Payout status = COMPLETED and Lulu status = CREDITED but order not marked complete
3. All downstream systems show success but order stuck

## Resolution Steps

### Step 1: Verify Downstream Status
1. Check `falcon_status` — should be COMPLETED
2. Check `lulu_status` — should be CREDITED (for AED)
3. Check `payout_status` — should be COMPLETED
4. All should align for a completed order

### Step 2: Identify Sync Failure Point
1. Compare order_status with downstream statuses
2. Check status sync job logs for errors
3. Look for webhook delivery failures

### Step 3: Trigger Manual Sync
1. Access order management dashboard
2. Find order by order_id
3. Trigger status refresh/sync
4. Wait for status update (usually < 1 minute)

### Step 4: Force Status Update (if needed)
If manual sync fails:
1. Verify all downstream truly completed
2. Submit status correction request
3. Update order_status to COMPLETED

### Step 5: Root Cause
1. Note why sync failed (webhook, job, timeout)
2. Report to engineering if pattern emerges
3. Update ECM ticket

## Escalation
Escalate if:
- Manual sync doesn't work
- Conflicting statuses in downstream systems
- Customer has complained about order

**SOP:** Status sync error (e.g. transaction incorrectly marked Processing Deal In) → raise **internally to TechOps** (see [ESCALATION.md](../ESCALATION.md) — TechOps Level 1).
