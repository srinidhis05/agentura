# Transaction Request Not Received (Digit9) Runbook – Lulu

## Overview
AML/RFI check or **missing payment from Vance to Lulu** → transaction not forwarded to **Digit9**. KYC contacts user for documents and reverts to Lulu; Lulu SG approves or rejects. If rejected, follow Excess Credit flow.

**Team:** Ops / KYC_ops  
**SOP Reference:** Lulu SOP § 3.2 Transaction Request Not Received (Digit9)  
**Frequency:** ~10–20 cases/day

## Trigger
- AML/RFI check **or** missing payment from Vance to Lulu → transaction not sent to Digit9.

## Happy Flow (SOP)

1. **User** initiates transfer → **Vance** → **Lulu** → **Digit9** → **Falcon**.
2. AML/RFI triggers → **Lulu SG** emails Vance.
3. **KYC** contacts the user for documents and reverts to Lulu.
4. **Lulu SG** verifies and **approves/rejects**:
   - **Approved** → Digit9 pushes to Falcon.
   - **Rejected** → follow **Excess Credit** flow ([excess-credit.md](excess-credit.md)).

## Alternate Flow – Funds Not Received
- Lulu requests **payment confirmation**:
  - **Lean/Checkout:** Check match type in Recon.
  - **Manual:** Check Vance reconciliation and confirm.

## Exception Flow (SOP)
- If the transaction is **rejected** → Vance informs Lulu to **cancel** and add to **pending action sheet**.

## Resolution Steps

### Step 1: Confirm Cause
1. Check whether cause is AML/RFI or **missing payment** (Vance → Lulu).
2. If payment missing: reconcile (Lean/Checkout match type or Manual reconciliation).

### Step 2: RFI / Documents (if AML/RFI)
1. KYC contacts user for required documents.
2. Revert to Lulu SG with documents.
3. Track Lulu decision (approve → Digit9/Falcon; reject → Excess Credit).

### Step 3: If Rejected
1. Inform Lulu to cancel the transaction.
2. Add to **pending action sheet**.
3. Follow [excess-credit.md](excess-credit.md) for refund once excess credit sheet is received.

## Escalation
- Rejected / excess credit → [excess-credit.md](excess-credit.md) and [ESCALATION.md](../ESCALATION.md).
- Payment recon issues → internal recon/Ops escalation per SOP.
