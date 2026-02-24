---
name: resolve-ticket
role: field
domain: ecm
trigger: manual
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.08"
timeout: "30s"
---

# Resolve Ticket Skill

## Trigger
- "resolve {order_id} {notes}"
- "fixed {order_id} {notes}"
- "done {order_id} {notes}"
- "close {order_id} {notes}"

## Google Sheet
**Spreadsheet ID:** `1r50OEZlFVSUmU1tkLBqx2_BzlilZ3s0pArNHV83tRks`

## Description
Marks a ticket as resolved by updating **Google Sheets** (Assignments + Resolutions tabs). Redshift is read-only.

## Input
- `order_id` - The order to resolve
- `notes` - Resolution notes (what was done to fix it) — **REQUIRED**

## Data Flow

### Step 1: Find assignment in Sheet
Read **Assignments** tab:
- Find row where `Order ID = {order_id}` and `Status IN ('OPEN', 'IN_PROGRESS')`
- Get `Assigned At` timestamp

### Step 2: Get order details from Redshift (read-only)
```sql
SELECT order_id,
       meta_postscript_pricing_info_send_currency AS currency_from,
       meta_postscript_pricing_info_send_amount AS send_amount,
       status AS order_status
FROM orders_goms
WHERE order_id = '{order_id}'
```

> **DO NOT use `analytics_orders_master_data`** — it is a slow view. Use `orders_goms` directly.

### Step 3: Calculate metrics
- Resolution Time = Now - Assigned At
- SLA Target = from `../shared/config/stuck-reasons.yaml`
- SLA Status = MET if Resolution Time < SLA Target, else MISSED

### Step 4: Collect Sentinel Feedback (3 quick questions)

```
Quick feedback (helps Sentinel improve):

1. Was the diagnosis correct?
   [CORRECT] — the stuck_reason matched reality
   [PARTIAL] — partially right, but needed adjustment
   [WRONG] — completely different issue than diagnosed

2. Did you follow the prescribed action?
   [YES] — followed the action in Notes exactly
   [MODIFIED] — adapted the steps
   [IGNORED] — used a completely different approach

3. Resolution type?
   [AGENT_RESOLVED] — you fixed it manually
   [SELF_HEALED] — order resolved itself before you acted
   [ESCALATED_RESOLVED] — escalated, then resolved by L2/partner
   [FALSE_POSITIVE] — not actually stuck / no action needed
```

**Default values** (if agent skips): CORRECT, YES, AGENT_RESOLVED

### Step 5: Write to Resolutions tab
Append row with ALL 13 columns:
```
Timestamp | Order ID | Agent | Notes | Assigned At | Time (min) | SLA Target | SLA Status | Stuck Reason | Amount | Currency | Diagnosis Match | Action Followed | Resolution Type
```

### Step 6: Update Assignments tab
Update the row: `Status` = "RESOLVED"

### Step 7: Get remaining queue
Read **Assignments** tab for remaining OPEN/IN_PROGRESS tickets.

## Output Format

```
✅ Ticket Resolved: {order_id}

┌─────────────────────────────────────────┐
│ Metric          │ Value                 │
├─────────────────┼───────────────────────┤
│ Resolution Time │ 6 minutes             │
│ SLA Target      │ 2 hours               │
│ SLA Status      │ ✅ MET                │
└─────────────────────────────────────────┘

📝 Logged to ECM Operations Sheet:
   Resolution: "{notes}"
   Agent: @{agent}
   Feedback: {diagnosis_match} | {action_followed} | {resolution_type}

---

🎫 @{agent}'s Queue: {remaining_count} remaining

📊 Your Stats Today:
│ Resolved: {today_resolved}
│ Avg Time: {avg_resolution_time}
│ SLA Met: {sla_met_percent}%

Next: `order {next_urgent_order_id}` (SLA in {sla_remaining} ⚠️)
```

## Error Cases

### Order not found in Assignments
```
❌ Order {order_id} not found in your queue.
Run `my tickets` to see your current queue.
```

### Empty notes
```
❌ Resolution notes are required.
Example: resolve {order_id} "Replayed webhook, LULU confirmed"
```

## Guardrails
- Only resolve orders that exist in Assignments tab
- Notes are required (reject empty)
- Never write to Redshift (read-only)
- All writes go to Google Sheets
