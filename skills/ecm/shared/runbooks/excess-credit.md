# Excess Credit Runbook (Lulu)

## Overview
Lulu holds a transaction for AML/RFI checks; if the user doesn’t respond within **2 working days**, Lulu **auto-cancels** and **blocks** the user. Unclaimed/untraceable credits land as excess credit. Ops must map Lulu ref → Order ID and process refunds via UAE FTS.

**Team:** Ops (Vance Operations + KYC)  
**SOP Reference:** Lulu SOP § 3.1 Excess Credit Flow  
**Frequency:** ~25–30 cases/day

## Triggers / Reasons for Excess Credit
- AML/RFI check → user did not respond within 2 days
- Beneficiary account doesn’t exist
- Beneficiary account returned funds
- Beneficiary bank server issue
- Operations suspended
- Delay in recon / amount mismatch / failed txns on NT

## How It Works (SOP)

1. **Lulu** holds the transaction for **2 working days** for AML/RFI checks.
2. **KYC** creates an RFI request on AD and sends an email.
3. If no response for 2 days → Lulu **auto-cancels** and **blocks** the user.
4. **Lulu Accounts Team** sends a daily **excess credit sheet** (**T+1**).
5. Ops maps **Luluref → Order ID** using Alphadesk.
6. Once Lulu sends cancellation webhook, AD notifies users in-app to add refund details.
7. Ops requests the user’s **UAE bank account details** wherever AD can’t run using webhook.
8. On receiving details, Ops updates the **pending action sheet**.

## Timeline (SOP)

| Day | Action |
|-----|--------|
| **T+1** | Lulu shares the excess credit sheet |
| **T+2** | Vance contacts the user for details |
| **T+3** | Refund processed |

## Refund TAT
- Refunds are processed via **UAE FTS** (similar to NEFT) within **2 working days** of receiving user details.

## Resolution Steps

### Step 1: Receive Excess Credit Sheet
1. Confirm daily excess credit sheet from Lulu (T+1).
2. Dependencies: Timely sheet from Lulu.

### Step 2: Map Lulu Ref → Order ID
1. Use **Alphadesk** to map Luluref → Order ID.
2. Confirm order_id and amount.

### Step 3: User Refund Details
1. Where AD webhook ran: user gets in-app notification to add refund details.
2. Where AD didn’t run: Ops requests user’s **UAE bank account details** (email/phone).
3. Update **pending action sheet** on receiving details.

### Step 4: Process Refund
1. Initiate refund via **UAE FTS**.
2. Target: within **2 working days** of receiving user details.
3. Note refund reference and update tracking.

### Step 5: Update Pending Action Sheet
1. Mark case as refund initiated / completed.
2. Update ECM / Incident Log as per Edge Case process if applicable.

## Dependencies (SOP)
- Timely sheet from Lulu
- Prompt user response
- UAE FTS processing

## Escalation
- If sheet is delayed or missing → FinOps / Lulu Accounts (see [ESCALATION.md](../ESCALATION.md)).
- If refund fails or user disputes → follow Refund Pending runbook and escalate per ESCALATION.md.

**Contacts:** See [ESCALATION.md](../ESCALATION.md) — FinOps / Lulu: accounts.uae@ae.luluexchange.com, shehin.abdul@ae.luluexchange.com, gokul.gopikumar@ae.luluexchange.com.
