# GOMS Payment Issue Runbook

## Overview
GBP/EUR order is stuck due to GOMS payment processing issue.

**Team:** Ops  
**Stuck Reason:** `stuck_due_to_payment_issue_goms`  
**Currency:** GBP, EUR only

## Common Causes
- Payment in AWAIT_RETRY_INTENT state
- Payment stuck in PENDING state
- Payment processor issue
- Retry mechanism not working

## Resolution Steps

### Step 1: Verify GOMS State
1. Check `payment_status_goms` = COMPLETED
2. Check `goms_sub_state`:
   - AWAIT_RETRY_INTENT → Retry pending
   - PENDING → Initial processing stuck
3. Check `goms_trm_time_diff_sec` — should be NULL (not in TRM)

### Step 2: Check GOMS Dashboard
1. Access GOMS order dashboard
2. Find order by order_id
3. Check payment processing logs
4. Identify specific failure or hold reason

### Step 3: Handle AWAIT_RETRY_INTENT
If stuck in retry:
1. Check retry count and last attempt time
2. Check payment processor status
3. Consider manual retry trigger
4. If processor issue, wait or escalate

### Step 4: Handle PENDING
If stuck in pending:
1. Check if initial payment submission failed
2. Check for validation errors
3. May need manual push or data correction

### Step 5: Trigger Resolution
1. If retriable: Trigger manual payment retry
2. If data issue: Correct data and resubmit
3. If processor down: Monitor processor status, escalate if prolonged

### Step 6: Document
1. Record GOMS status and action taken
2. Note any processor issues
3. Update ECM ticket

## Escalation
Escalate if:
- Multiple retry failures
- Payment processor issue > 2 hours
- Order > 12 hours stuck
- Customer complaint

Contact: ops-lead@aspora.com or #ops-ecm Slack channel
