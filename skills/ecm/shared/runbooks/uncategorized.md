# Uncategorized Order Runbook

## Overview
Order doesn't match any known stuck pattern — requires manual investigation.

**Team:** Ops  
**Stuck Reason:** `uncategorized`

## Resolution Steps

### Step 1: Gather Order Context
1. Note all available fields:
   - order_id, order_status, currency_from
   - payment_acquirer, payout_status
   - lulu_status (if AED), goms status (if GBP/EUR)
   - falcon_status, rfi_status
   - hours_diff (age of order)

### Step 2: Check Order Timeline
1. Review order creation timestamp
2. Check payment status and when it completed
3. Trace progression through each system
4. Identify where order stopped progressing

### Step 3: Investigate Each System
Check in order:
1. **Payment**: Is payment truly complete?
2. **Compliance/TRM**: Any holds or flags?
3. **Lulu/GOMS**: Order status in exchange system?
4. **Falcon**: Transaction created and status?
5. **Payout Partner**: Payout submitted and status?

### Step 4: Identify Root Cause
Common uncategorized scenarios:
- New edge case not yet in logic
- Data inconsistency across systems
- System integration failure
- Manual intervention previously attempted

### Step 5: Resolution
Based on investigation:
1. If matches known pattern: Apply relevant runbook
2. If new pattern: Document and resolve manually
3. If data issue: Correct data and retry
4. If system issue: Escalate to engineering

### Step 6: Report New Pattern
If this represents a new stuck pattern:
1. Document the scenario clearly
2. Report to ops lead for query logic update
3. Suggest addition to stuck_reasons.yaml

## Escalation
Escalate if:
- Cannot determine root cause
- Multiple uncategorized orders with same pattern
- Order > 36 hours
- Customer escalation

Contact: ops-lead@aspora.com or #ops-ecm Slack channel
