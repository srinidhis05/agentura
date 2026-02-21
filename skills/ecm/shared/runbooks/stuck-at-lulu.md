# Stuck at Lulu Runbook

## Overview
AED order is stuck at Lulu — no Falcon transaction ID created but Lulu status exists.

**Team:** Ops  
**Stuck Reason:** `stuck_at_lulu`  
**Currency:** AED only

## Common Causes
- Lulu processing delay
- Lulu compliance hold
- BRN mismatch or validation failure
- Lulu system issues

## Resolution Steps

### Step 1: Verify Order State
1. Check `ftv_transaction_id` — should be NULL (no Falcon txn)
2. Check `order_status` — should NOT be FAILED
3. Check `lulu_status` — should have a value

### Step 2: Check Lulu Status Details
Common Lulu statuses when stuck:
- **CREATED**: Order received, not yet processed
- **PAYMENT_PENDING**: Waiting for BRN
- **PAYMENT_CONFIRMED**: BRN received, processing
- **TXN_TRANSMITTED**: Sent to beneficiary bank

### Step 3: Investigate Lulu Hold
1. Access Lulu dashboard
2. Search for order by order_id
3. Check for any compliance flags or holds
4. Note specific status and sub-status

### Step 4: Resolution by Status
**If CREATED/PAYMENT_PENDING:**
- Check if BRN was submitted (see brn-issue.md)
- May need manual BRN push

**If PAYMENT_CONFIRMED (stuck):**
- Check Lulu processing queue
- May need Lulu support ticket

**If TXN_TRANSMITTED (stuck):**
- Order should progress to CREDITED
- Check for banking delays
- Contact Lulu if > 4 hours

### Step 5: Escalate to Lulu Support
If stuck > 4 hours:
1. Raise ticket with Lulu support
2. Provide order_id and current status
3. Request status update or resolution

### Step 6: Document
1. Record Lulu status and support ticket
2. Update ECM with resolution
3. Monitor for completion

## Escalation
Escalate if:
- Lulu support unresponsive
- Order stuck > 24 hours
- High-value order (> 50,000 AED)
- Customer complaint

Contact: ops-lead@aspora.com or #ops-ecm Slack channel
