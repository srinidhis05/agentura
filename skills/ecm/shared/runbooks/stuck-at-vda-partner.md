# Stuck at VDA Partner Runbook

## Overview
Order is stuck at a VDA (Virtual Dollar Account) API partner with payout not completed.

**Team:** VDA_ops  
**Stuck Reason:** `stuck_at_vda_partner`

## Applicable Partners
All VDA API partners (non-bulk), identified when:
- `bulk_partner_exclusions` = 'vda_api_partner'
- `payout_status` != 'COMPLETED'

## Common Causes
- Partner API timeout or error
- Partner processing queue backlog
- Beneficiary validation failure
- Compliance check at partner

## Resolution Steps

### Step 1: Check Partner Status
1. Verify `current_payout_partner` value
2. Check `payout_status`:
   - PROCESSING → May be normal delay
   - FAILED → Needs retry
   - PENDING → Not yet picked up
3. Check `ftv_transaction_id` for partner lookup

### Step 2: Check Partner Dashboard
1. Access VDA partner portal
2. Search by transaction_id
3. Get partner-side status and any errors
4. Note partner reference number

### Step 3: Diagnose Issue
**If Processing (slow):**
- Check partner's current SLA
- May need to wait, set reminder

**If Failed:**
- Get failure reason from partner
- Common: beneficiary details wrong, daily limit exceeded
- Fix issue and retry

**If Pending:**
- Check if transaction was submitted
- May need to resubmit

### Step 4: Retry or Route
1. If retriable: Submit retry request
2. If partner-side issue: Escalate to partner support
3. If our data issue: Fix data and retry
4. Consider routing to alternate partner if available

### Step 5: Document
1. Record partner status and response
2. Note any data corrections made
3. Update ECM ticket

## Escalation
Escalate if:
- Partner support unresponsive
- Multiple retry failures
- Order > 24 hours stuck
- High-value order (> 10,000)

Contact: vda-lead@aspora.com or #vda-ops Slack channel
