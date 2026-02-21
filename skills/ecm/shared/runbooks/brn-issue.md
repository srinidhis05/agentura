# BRN Issue Runbook

## Overview
Payment has been reconciled but Bank Reference Number (BRN) submission to Lulu is pending or failed.

**Team:** Ops  
**Stuck Reason:** `brn_issue`  
**Currency:** AED only

## Common Causes
- Checkout payment captured but BRN not pushed to Lulu
- UAE Manual payment reconciled but Lulu status is PAYMENT_PENDING or CREATED
- BRN submission job failed or delayed

## Resolution Steps

### Step 1: Verify Payment Status
1. Check `payment_acquirer` — should be CHECKOUT, UAE_MANUAL, or LEANTECH
2. Check `uae_manual_payment_status` — should be RECONCILED
3. Check `checkout_status` — should be CAPTURED

### Step 2: Check Lulu Status
1. Check `lulu_status`:
   - PAYMENT_PENDING → BRN not received
   - CREATED → Order created but BRN pending
   - NULL → Order not submitted to Lulu

### Step 3: Push BRN Manually
1. Access Lulu integration dashboard
2. Find order by order_id
3. Trigger manual BRN submission
4. Wait for Lulu acknowledgment

### Step 4: Verify Lulu Update
1. Refresh Lulu status after 5 minutes
2. Expected status: PAYMENT_CONFIRMED or TXN_TRANSMITTED
3. If still pending, check Lulu error logs

### Step 5: Document Resolution
1. Note BRN that was submitted
2. Update ECM with resolution
3. Monitor order progression

## Escalation
Escalate if:
- BRN submission fails repeatedly
- Lulu rejects the BRN
- Order value > 50,000 AED

**Lulu / BRN:** See [ESCALATION.md](../ESCALATION.md) — BRN Error–Checkout: raise to Lulu (agent.support@pearldatadirect.com per SOP); TechOps Level 1 for internal sync issues.
