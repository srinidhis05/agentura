# Stuck Due to TRM Runbook

## Overview
GBP/EUR order is stuck in TRM (Transaction Risk Monitoring) processing.

**Team:** KYC_ops  
**Stuck Reasons:**
- `stuck_due_trm` — Stuck in TRM without RFI
- `stuck_due_trm_rfi_within_24_hrs` — TRM with RFI, < 24 hours
- `stuck_due_trm_rfi_grtr_than_24_hrs` — TRM with RFI, > 24 hours

**Currency:** GBP, EUR only

## Common Causes
- TRM compliance flag triggered
- Manual review required
- RFI pending customer response
- TRM system processing delay

## Resolution Steps

### Step 1: Verify TRM Status
1. Check `goms_trm_time_diff_sec` — should be NOT NULL (TRM triggered)
2. Check `ftv_transaction_id` — should be NULL (not yet passed TRM)
3. Check `rfi_status`:
   - NULL → `stuck_due_trm` (no RFI)
   - NOT NULL → `stuck_due_trm_rfi_*` (has RFI)

### Step 2: Without RFI (stuck_due_trm)
If no RFI exists:
1. Access TRM dashboard
2. Check TRM flag/hold reason
3. If documents needed, create RFI (see no-rfi-created.md)
4. If clearance possible, approve manually

### Step 3: With RFI (Within 24 Hours)
If `stuck_due_trm_rfi_within_24_hrs`:
1. Verify customer was notified
2. Monitor for customer response
3. No immediate action — within SLA

### Step 4: With RFI (Exceeded 24 Hours)
If `stuck_due_trm_rfi_grtr_than_24_hrs`:
1. Send reminder to customer
2. Escalate to customer support for outreach
3. If documents received, submit and clear TRM
4. Consider cancellation if no response after 48 hours

### Step 5: Clear TRM
Once resolved:
1. Submit TRM clearance with documents/justification
2. Order should proceed to Falcon/payout
3. Monitor for ftv_transaction_id creation

### Step 6: Document
1. Record TRM flag reason and resolution
2. Note any documents received
3. Update ECM ticket

## Escalation
Escalate if:
- TRM flag unclear
- Cannot clear despite valid documents
- Customer disputes TRM requirements
- Order > 48 hours

Contact: kyc-lead@aspora.com or #kyc-ops Slack channel
