# CNR (Completed Not Received) Runbook

## Overview
A **Completed Not Received (CNR)** case is when the **Order Table** and **Falcon Table** both show **COMPLETED**, but the **beneficiary has not received the funds**. This runbook aligns with the CNR SOP for Customer Support/ORM and Operations.

**Scope:** All Aspora corridors — UAE, UK, EU, US.  
**SOP Reference:** CNR SOP (Objective, Definition & Validation, Next Action).

## Definition & Validation (SOP)

A case is CNR **only if all** of the following are true:
- **Order Table status:** COMPLETED  
- **Falcon Table status:** COMPLETED  
- **Customer reports non-receipt of funds**

**Validation rules:**
- Always **verify Falcon Table status** before classifying as CNR.
- **Order Table alone must not be used** for classification.
- If **Order = COMPLETED** but **Falcon = FAILED** → classify as **Refund**, not CNR.

| Order Table | Falcon Table | Customer | Classification |
|-------------|--------------|----------|----------------|
| COMPLETED   | COMPLETED    | Non-receipt | **CNR** |
| COMPLETED   | FAILED       | Non-receipt | **Refund** (not CNR) |

## Sub-Categories & CX Guidance (SOP)

### 1. Transferred to Correct Account
- Customer confirms transfer was to the **correct** account.
- Requires **beneficiary Statement of Account (SOA)** as proof of non-receipt.
- **CX:** Acknowledge, reassure case is logged, advise Ops will investigate and update within SLA.

### 2. Transferred to Incorrect Account
- Customer reports funds sent to **incorrect/unintended** account.
- **Beneficiary SOA** not required for verification.
- **CX (RDA):** Acknowledge, reassure, advise Ops will investigate; **no definite TAT**; manage expectations.
- **CX (VDA):** Inform that partner rails may **not process incorrect-account claims** without SOA; manage expectations.

## Next Action / Resolution Path (SOP)

1. **Create a BO ticket** under **CNR** category in Intercom.
2. **Route** to appropriate team (RDA or VDA) by rail and sub-category.
3. **VDA – Transferred to Incorrect Account:** Cannot be raised with partner banks without **beneficiary SOA** (per partner SOP).
4. **Intercom notes** must include: order ID, falcon ID, corridor, sub-category, SOA attachment if applicable.  
   **Absence of any of these fields/docs = invalid BO.**
5. Confirm **expected SLA for resolution** with the customer.
6. Follow up internally until Ops updates with settlement confirmation or closure.

## Responsible Teams & SLAs (SOP)

| BO Type | Responsible Team | FRT | SLA / TAT |
|---------|-------------------|-----|-----------|
| CNR – Transferred to Correct Account (RDA) | Payment Ops | Within 4 hours | 72 hours |
| CNR – Transferred to Incorrect Account (RDA) | Payment Ops | Within 4 hours | No definite TAT (best effort) |
| CNR – Transferred to Correct Account (VDA) | VDA Ops | Within 4 hours | 72 hours |
| CNR – Transferred to Incorrect Account (VDA) | VDA Ops | NA | NA |

## SLA Breach – Manual Payout (SOP)

If a CNR BO is not resolved within SLA (e.g. 72 hours for “Transferred to Correct Account”):

1. **CX Verification**
   - Confirm with customer that funds **still not received**; obtain **SOA till date** as proof (on date of manual payout initiation).
   - Obtain **double credit return confirmation** from customer (including agreement to return any future credits for that transaction).
   - Document in BO ticket notes.

2. **Ops Validation**
   - Verify with payout partner: no return/rejection; transaction remains unresolved.

3. **Finance Guardrail**
   - If manual payout > **$10,000** (or undefined upper limit), **Finance approval** required before execution.

4. **Tech Execution**
   - Ops requests Tech to initiate manual payout; Tech executes.

5. **Record-Keeping**
   - Log in **Emergency Payout Sheet – CNR SLA Breach Tab** (Original Transaction ID, Original UTR, Transaction Date, Manual Payout UTR, Manual Payout Date, Amount, CX Owner, Customer Confirmation, Finance Approval, Remarks).

6. **CX Recovery / Write-off**
   - CX owns **recovery** if **double credit** occurs. If recovery fails, CX documents **write-off** with supporting evidence.

*Manual payout decision is made by Ops based on ETA from payout partner when it looks unreliable for the customer (judgement call).*

## Escalation & Owners (SOP)

- **Operations Owner:** @Vishnu R  
- **CX Owner:** @Asaf Ali  
- **Tech Owner:** @Raj Vishwakarma  

See [ESCALATION.md](../ESCALATION.md) for contact summary.
