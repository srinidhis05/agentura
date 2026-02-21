# Txn Released (AML/RFI) Runbook – Lulu

## Overview
Transaction is in **Txn Released** status because Lulu initiated an **AML (Anti-Money Laundering)** or **RFI (Request for Information)** check. The transfer **will not be forwarded to Digit9** until this is cleared.

**Team:** Ops / KYC_ops  
**SOP Reference:** Lulu SOP § 3.5 Process: Handling Transactions in "Txn Released" Status Due to AML/RFI Checks  
**Frequency:** ~10–20 cases/day

## Trigger
- Transaction enters **Txn Released** due to AML/RFI check by Lulu.
- Trf will not go to Digit9 until cleared.

## Happy Flow (SOP)

1. User initiates transfer → **Vance** → **Lulu** → **Digit9** → **Falcon**.
2. If AML/RFI is triggered, Lulu conducts checks internally; if additional documents are needed, **LuLu Money Singapore (LuLu SG)** emails Vance.
3. **Normal RFI process:** Obtain required documents from user and respond.
4. **LuLu SG** reviews and either:
   - **Approved** → Transaction proceeds to **Digit9** → pushed to **Falcon**.
   - **Rejected** → Initiate **Excess Credit** process (see [excess-credit.md](excess-credit.md)).

## Timeline (SOP)
- Validity of this RFI: **2 working days** (same as general Lulu RFI).

## Exception Flow (SOP)

- **User not willing to send documents:**
  - Vance informs Lulu to **cancel** the transaction.
  - Add the case to the **Pending Action Sheet** for further resolution.
- **Peak (>10 transactions in Txn Released):**
  - Share the output with Lulu via email to **agent.support@pearldatadirect.com**.

## Resolution Steps

### Step 1: Confirm Txn Released
1. Identify order in Lulu with status Txn Released (AML/RFI).
2. Confirm RFI/email from Lulu SG if applicable.

### Step 2: RFI Response
1. Follow normal RFI process: collect documents from user, submit to Lulu.
2. Ensure response within **2 working days** to avoid auto-cancel and excess credit.

### Step 3: Post Lulu Decision
- **Approved:** Monitor for progression to Digit9 → Falcon; no further action except tracking.
- **Rejected:** Follow [excess-credit.md](excess-credit.md) (map Luluref → Order ID, user details, refund via UAE FTS).

### Step 4: Peak Handling
- If **>10** such cases: prepare list and email to **agent.support@pearldatadirect.com** for Lulu attention.

## Escalation
- Rejected cases → Excess Credit runbook and [ESCALATION.md](../ESCALATION.md) (FinOps/Lulu).
- No response from Lulu within SLA → escalate per [ESCALATION.md](../ESCALATION.md).
