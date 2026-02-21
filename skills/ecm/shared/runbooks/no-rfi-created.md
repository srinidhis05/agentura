# No RFI Created Runbook

## Overview
Payout partner requires additional documents (ADDITIONAL_DOCUMENTS_REQUIRED) but no RFI was created in our system.

**Team:** KYC_ops  
**Stuck Reason:** `no_rfi_created`

## Common Causes
- RFI automation failed or didn't trigger
- Partner flagged order after initial submission
- Webhook from partner not received
- Manual RFI creation missed

## Resolution Steps

### Step 1: Verify Partner Status
1. Check `payout_status` = ADDITIONAL_DOCUMENTS_REQUIRED
2. Check `rfi_status` — should be NULL
3. Check `rda_status` — may be ONHOLD

### Step 2: Check Partner Dashboard
1. Access payout partner dashboard
2. Find order by ftv_transaction_id
3. Get specific document requirements from partner
4. Note partner's hold reason

### Step 3: Create RFI Manually
1. Access RFI creation tool
2. Create RFI for order_id
3. Specify documents needed (from partner requirements)
4. Set RFI type and urgency

### Step 4: Notify Customer
1. Trigger RFI notification to customer
2. Include clear instructions on what's needed
3. Set deadline (typically 24-48 hours)

### Step 5: Investigate Automation Failure
1. Check RFI automation logs
2. Identify why RFI wasn't auto-created
3. Report to engineering if systemic issue

### Step 6: Document
1. Record manual RFI creation
2. Note automation failure reason
3. Update ECM ticket

## Escalation
Escalate if:
- Cannot create RFI manually
- Unclear what documents partner needs
- Order > 24 hours without RFI
- High-value order

Contact: kyc-lead@aspora.com or #kyc-ops Slack channel
