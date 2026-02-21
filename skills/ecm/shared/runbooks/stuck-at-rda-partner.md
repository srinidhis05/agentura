# Stuck at RDA Partner Runbook

## Overview
Order is stuck at RDA (Remittance Distribution Agent) partner during payout processing, without an active RFI.

**Team:** Ops  
**Stuck Reason:** `stuck_at_rda_partner`

## Applicable Partners
- VANCE_RDA

## Common Causes
- Partner processing delays
- Partner system downtime
- Missing or incorrect beneficiary details
- Compliance hold at partner level

## Resolution Steps

### Step 1: Check Payout Status
1. Verify `current_payout_partner` = VANCE_RDA (or other RDA partner)
2. Check `payout_status`:
   - PROCESSING → Normal processing, may just be slow
   - FAILED → Needs retry or investigation
3. Check `rfi_status` — should be NULL (no RFI) for this stuck reason

### Step 2: Check Partner Dashboard
1. Access RDA partner dashboard (VANCE portal)
2. Search for order by ftv_transaction_id
3. Check partner-side status and any error messages

### Step 3: Investigate Delay
If partner shows:
- **Processing**: Check expected SLA, may need to wait
- **On Hold**: Check hold reason, may need docs or correction
- **Failed**: Get failure reason, may need retry

### Step 4: Retry or Escalate
1. If simple delay: Monitor for 2-4 hours
2. If on hold: Address hold reason, provide missing info
3. If failed: Retry payout or route to different partner

### Step 5: Document
1. Record partner status and action taken
2. Update ECM with partner reference if any
3. Set follow-up reminder

## Escalation
Escalate if:
- Partner unresponsive
- Repeated failures
- Order > 36 hours old
- Customer escalation

Contact: ops-lead@aspora.com or #ops-ecm Slack channel
