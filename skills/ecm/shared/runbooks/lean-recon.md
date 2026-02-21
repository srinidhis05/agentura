# Stuck at Lean Recon Runbook

## Overview
AED order with LEANTECH payment is stuck at Lean reconciliation stage.

**Team:** Ops  
**Stuck Reason:** `stuck_at_lean_recon`  
**Currency:** AED only

## Common Causes
- Lean payment not yet reconciled
- Reconciliation job delayed
- Payment amount mismatch
- Lean webhook not received

## Resolution Steps

### Step 1: Verify Status
1. Check `payment_acquirer` = LEANTECH
2. Check `lulu_status` = PAYMENT_PENDING
3. This indicates payment received but BRN not generated

### Step 2: Check Lean Dashboard
1. Access Lean Tech dashboard
2. Find payment by order_id or customer reference
3. Verify payment was received
4. Check reconciliation status

### Step 3: Investigate Recon Delay
Common issues:
- **Not reconciled**: Check recon job logs
- **Amount mismatch**: Verify payment amount matches order
- **Missing webhook**: Check webhook delivery logs

### Step 4: Trigger Reconciliation
1. If payment exists in Lean but not reconciled:
   - Check recon job schedule
   - Trigger manual reconciliation if available
2. If webhook missing:
   - Request webhook replay from Lean
   - Or manually update payment status

### Step 5: Post-Reconciliation
1. Once reconciled, BRN should generate
2. BRN pushed to Lulu (see brn-issue.md if stuck)
3. Order should progress

### Step 6: Document
1. Record Lean payment reference
2. Note reconciliation issue and fix
3. Update ECM ticket

## Escalation
Escalate if:
- Payment not found in Lean
- Reconciliation repeatedly fails
- Order > 12 hours stuck
- Customer complaint

Contact: ops-lead@aspora.com or #ops-ecm Slack channel
