---
name: order-details
role: field
domain: ecm
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.12"
timeout: "30s"
---

# Order Details & Diagnosis

## Trigger
- "order {order_id}"
- "lookup {order_id}"

## Files Used
```
../shared/queries/ecm-triage-fast.sql  → Order facts + stuck_reason
../shared/config/stuck-reasons.yaml    → Action, team, SLA, runbook
../shared/config/diagnosis-mapping.yaml → Sub-state diagnoses
../shared/config/knowledge-graph.yaml  → State machines, partner playbook, scoring
```

---

## Flow

### 1. Run Order Query
Execute `../shared/queries/ecm-triage-fast.sql` with `{order_id}` replaced.

### 2. Check Actionability
If `is_actionable = false`:
```
⛔ Order not actionable: {disqualification_reason}
```
Stop here — no resolution steps.

### 3. Lookup stuck_reason
From `../shared/config/stuck-reasons.yaml`, get the entry for the `stuck_reason` returned by query.

### 4. Compute Priority
```
score = 0.25 × age_score + 0.20 × amount_score + 0.25 × severity + 0.15 × rfi_score + 0.10 × payment_score

age_score:    >72h=1.0, >36h=0.9, >24h=0.7, >12h=0.5, else=0.1
amount_score: >15K=1.0, >5K=0.8, >2K=0.7, >500=0.5, else=0.1
rfi_score:    REQUESTED>24h=0.7, EXPIRED=0.9, else=0.0
payment_score: COMPLETED=0.0, PENDING=0.3, null=0.5

priority: ≥0.7=P1🔴, ≥0.5=P2🟠, ≥0.3=P3🟡, else=P4🟢
```

---

## Output Format

```
## {order_id} | {priority} | {team}

### What's Wrong
{Plain English explanation of the stuck state based on stuck_reason}
- Explain what happened (payment status, where it's stuck)
- Explain why it's blocked (TRM, RFI, partner issue, etc.)
- Mention how long it's been stuck

### What To Do
{Numbered steps from ../shared/config/stuck-reasons.yaml action, expanded into clear instructions}
1. First step (be specific - mention AlphaDesk, dashboards, etc.)
2. Second step
3. What to verify after

### Order Facts
| Field | Value |
|-------|-------|
| Status | {goms_order_status} / {goms_sub_state} |
| Amount | {send_amount} {currency_from} → {receive_amount} INR |
| Age | {hours_diff}h ({X} days) |
| Payment | {✅/❌} {payment_status_goms} via {payment_acquirer} |
| Falcon | {✅/❌} {falcon_status or "No transaction"} |
| Lulu | {✅/❌/—} {lulu_status or "N/A for GBP/EUR"} |
| Payout | {✅/❌/—} {payout_status or "Not initiated"} |
| RFI | {rfi_status or "None"} |

### Customer
| Field | Value |
|-------|-------|
| User ID | {owner_id} |
| Email | {masked_email or "—"} |
| Phone | {masked_phone or "—"} |
| KYC Status | {kyc_status or "—"} |

**Note:** The query returns `owner_id` from `orders_goms`. Email, phone, and KYC are only shown when the query (or a joined user table) returns them; otherwise show "—". Do not invent customer PII.

### Priority
**{P1/P2/P3/P4} ({label})** — {Brief explanation of why this priority}

**SLA:** {sla_hours}h | **Escalation:** {escalation} | **Runbook:** `{runbook}`
```

---

## What's Wrong Templates

Use these based on `stuck_reason`:

### stuck_due_trm
> {currency} order stuck in **TRM (Transaction Risk Monitoring)** for {hours}h. Payment completed via {acquirer} but order never progressed to Falcon — blocked at compliance check.

### stuck_due_trm_rfi_*
> {currency} order stuck in **TRM** with pending RFI. Customer {has/hasn't} responded to document request. TRM cannot release until docs verified.

### brn_issue
> AED order payment reconciled but **BRN (Bank Reference Number) not pushed to Lulu**. Lulu is waiting for payment confirmation to start processing.

### stuck_at_lulu
> AED order sent to Lulu but **stuck in Lulu processing**. No Falcon transaction created. Need to check Lulu dashboard for sub-status.

### refund_pending
> Order failed/cancelled but **customer funds not refunded**. Payment was captured via {acquirer}. Refund must be initiated urgently.

### cancellation_pending
> Cancellation requested but **not completed at Lulu**. If already transmitted, may need recall request.

### status_sync_issue
> Order **completed at partner but GOMS not updated**. Lulu shows CREDITED but order still shows PROCESSING_DEAL_IN. Webhook may have been missed.

### rfi_order_within_24_hr
> RFI created, **waiting for customer response**. Within 24h window — do NOT nudge customer yet.

### rfi_order_grtr_than_24_hr
> RFI pending **over 24 hours**. Customer has not responded. Time to send reminder.

### no_rfi_created
> Payout partner requires documents but **no RFI was created** in the system. Bug — need to create manually.

### stuck_at_vda_partner
> Order sent to VDA partner but **payout not completed**. Check partner dashboard for status.

### uncategorized
> Order doesn't match known stuck patterns. **Manual investigation required** — check full system chain.

---

## What To Do Templates

Expand the action one-liner into numbered steps:

### stuck_due_trm
1. Open **AlphaDesk** → Search `{order_id}`
2. Go to **ComplianceReview** section
3. Check TRM flag reason
4. If documents needed → Create RFI for customer
5. If clearable → Release the TRM hold
6. After release → Verify Falcon transaction gets created

### brn_issue
1. Open **{acquirer} Dashboard** (Checkout/Lean/UAE Manual)
2. Find transaction for `{order_id}`, copy BRN/reference number
3. Open **AlphaDesk** → Push BRN to Lulu
4. Verify Lulu status changes from PAYMENT_PENDING → TXN_TRANSMITTED

### refund_pending
1. Open **{acquirer} Dashboard**
2. Check if refund already initiated
3. If no refund exists → Initiate refund for {amount} {currency}
4. Note refund reference number
5. Update order notes with refund details

### status_sync_issue
1. Open **AlphaDesk** → Search `{order_id}`
2. Verify Lulu shows CREDITED/COMPLETED
3. Trigger **webhook replay** / force sync
4. Verify GOMS status updates to COMPLETED

### rfi_order_grtr_than_24_hr
1. Check RFI status in **AlphaDesk**
2. Verify customer was notified
3. Send **reminder** via email/SMS
4. If no response after 48h → Consider escalation or cancellation

---

## Guardrails
- Do NOT load knowledge-graph.yaml unless stuck_reason = uncategorized
- Do NOT invent actions — use ../shared/config/stuck-reasons.yaml + templates above
- Do NOT nudge customer if RFI < 24h (check `no_action: true` flag)
- If query fails, report error — do not fabricate data
- Mask customer PII (show only last 4 digits of phone, partial email)
- NEVER invent a diagnosis not in `diagnosis-mapping.yaml`. Say "Unknown sub-state — escalate to L2."
- NEVER skip SLA check — every order must show hours_in_state vs SLA threshold.
- ALWAYS include reasoning_trace — ops managers audit these.
