---
name: escalate-ticket
role: field
domain: ecm
trigger: manual
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.15"
timeout: "45s"
---

# Escalate Ticket Skill

## Trigger
- "stuck {order_id} {reason}"
- "escalate {order_id} {reason}"
- "can't fix {order_id} {reason}"

## Google Sheet
**Spreadsheet ID:** `1r50OEZlFVSUmU1tkLBqx2_BzlilZ3s0pArNHV83tRks`

## Description
Escalates a ticket by writing to **Google Sheets** (Escalations tab) and updating Assignments. Optionally notifies Slack.

## Input
- `order_id` - The order to escalate
- `reason` - Why escalation is needed — **REQUIRED**

## Data Flow

### Step 1: Find assignment in Sheet
Read **Assignments** tab:
- Find row where `Order ID = {order_id}` and `Status IN ('OPEN', 'IN_PROGRESS')`

### Step 2: Get order details from Redshift (read-only)
```sql
SELECT order_id, status AS order_status,
       meta_postscript_pricing_info_send_currency AS currency_from,
       meta_postscript_pricing_info_send_amount AS send_amount,
       ROUND(EXTRACT(EPOCH FROM (GETDATE() - created_at)) / 3600, 1) AS hours_diff
FROM orders_goms
WHERE order_id = '{order_id}'
```

Or use `../shared/queries/ecm-triage-fast.sql` for full details including `stuck_reason` and `team_dependency`.

> **DO NOT use `analytics_orders_master_data`** — it is a slow view. Use `orders_goms` directly.

### Step 3: Write to Escalations tab
Append row to **Escalations** tab:
```
Timestamp | Order ID | Escalated By | Reason | Order Status | Stuck Hours | Amount | Currency | Priority | Assigned To | Resolved At | Resolution Notes
```
(Last 3 columns left blank — filled when resolved)

### Step 4: Update Assignments tab
Update the row: `Status` = "ESCALATED"

### Step 5: Notify (optional)
If Slack MCP is configured:
```
🚨 ECM Escalation: {order_id}

Agent: @{agent}
Reason: {reason}

Order: {send_amount} {currency}
Stuck: {hours_diff}h | Status: {order_status}

@dinesh @tech-ops please review
```

### Step 6: Get remaining queue
Read **Assignments** tab for remaining OPEN/IN_PROGRESS tickets.

## Output Format

```
🚨 Escalated: {order_id}

┌─────────────────────────────────────────┐
│ Escalation Details                      │
├─────────────────────────────────────────┤
│ Reason: {reason}                        │
│ Logged to: ECM Operations Sheet         │
│ Notified: @dinesh, @tech-ops (if Slack) │
└─────────────────────────────────────────┘

📋 Order Summary:
│ Status: {order_status}
│ Amount: {send_amount} {currency}
│ Stuck: {hours_diff} hours

---

Ticket removed from your queue.

🎫 @{agent}'s Queue: {remaining_count} remaining
Next: `order {next_order_id}`
```

## Escalation Contacts
- **L1**: albert.roshan@pearldatadirect.com, sreejith.parameswaran@pearldatadirect.com
- **L2**: @dinesh (Slack)
- **L3**: Tech-ops team lead

## Guardrails
- Only escalate orders in Assignments tab
- Reason is required (reject empty)
- Never write to Redshift
- All writes go to Google Sheets
- ALWAYS include the full timeline — incomplete escalations get rejected by L2
- If Redshift data is unavailable, flag it — don't fabricate timelines
