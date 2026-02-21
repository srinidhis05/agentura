---
name: my-tickets
role: field
domain: ecm
trigger: manual
model: anthropic/claude-sonnet-4-5-20250929
cost_budget_per_execution: "$0.10"
timeout: "30s"
---

# My Tickets Skill (Agent Persona)

## Trigger
- "my tickets"
- "my queue"
- "show my tickets"
- "what should I work on"
- "next task"

## Persona: Agent
This skill is for the **agent persona** (individual contributor).
Shows their assigned tickets with **clear actionables** — not just data.

For the **manager persona** (triage & assign), see `../triage-and-assign/SKILL.md`.

---

## Google Sheet
**Spreadsheet ID:** `1r50OEZlFVSUmU1tkLBqx2_BzlilZ3s0pArNHV83tRks`

### Assignments Tab Schema (10 columns)
```
A: Order ID | B: Assigned Agent | C: Assigned At | D: Status | E: Priority
F: Currency | G: Amount         | H: Hours Stuck | I: Diagnosis | J: Notes
```

---

## Description
Shows the agent's assigned ticket queue from Google Sheets, enriched with live Redshift data and **specific actionable instructions** per ticket.

The agent sees:
1. Their tickets sorted by priority (P1 first)
2. Live hours_stuck from Redshift (not stale Sheet value)
3. The **Diagnosis** (stuck_reason) from the Sheet
4. The **Notes** column with the one-liner action from the manager
5. A full action block per ticket from triage-and-assign Action Generation Rules

---

## Data Flow

### Step 1: Get agent identity
Get agent email from session context or ask once.

### Step 2: Get assignments from Google Sheet
Read **Assignments** tab:
- Filter: `Assigned Agent = {agent_email}` AND `Status IN ('OPEN', 'IN_PROGRESS')`

### Step 3: Refresh order data from Redshift
For each order_id from Sheet, get **live** status:
```sql
SELECT
    order_id, status AS order_status, sub_state,
    meta_postscript_pricing_info_send_currency AS currency_from,
    meta_postscript_pricing_info_send_amount AS send_amount,
    ROUND(EXTRACT(EPOCH FROM (GETDATE() - created_at)) / 3600, 1) AS hours_diff
FROM orders_goms
WHERE order_id IN ({order_ids_from_sheet})
```

> **DO NOT use `analytics_orders_master_data`** — it is a slow view. Use `orders_goms` directly.

**Auto-resolve check:** If Redshift shows `status = 'COMPLETED'`, flag it:
- Tell agent: "Order {id} has been completed — you can resolve it"
- Do NOT auto-update the Sheet

### Step 4: Enrich with stuck_reason
If Diagnosis column (I) is empty, run `../shared/queries/ecm-triage-fast.sql` per order.

### Step 5: Generate actionables
For each ticket, look up the `Diagnosis` value in Action Generation Rules from `../triage-and-assign/SKILL.md`.

### Step 6: Calculate SLA
- SLA hours from `../shared/config/stuck-reasons.yaml`
- SLA remaining = SLA hours - live hours_diff
- `🔴 BREACHED` | `⚠️ CRITICAL` (<25%) | `🟡 WARNING` (25-50%) | `🟢 OK` (>50%)

### Step 7: Sort and display
Sort by: Priority (P1 first) → SLA breached first → SLA remaining ascending

---

## Output Format

```
🎫 @{agent}'s Queue — {count} tickets

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🔴 P1 | {order_id} | {send_amount} {currency} | {hours_stuck}h | SLA: BREACHED
   Diagnosis: {diagnosis_display}
   ┌─────────────────────────────────────────────┐
   │ WHAT TO DO:                                 │
   │ {specific_action_from_stuck_reason}         │
   │ CHECK: {what_to_verify}                     │
   │ DONE? → resolve {order_id} "{notes}"        │
   │ STUCK? → stuck {order_id} "{reason}"        │
   └─────────────────────────────────────────────┘

2. 🟠 P2 | {order_id} | {amount} {currency} | {hours}h | SLA: ⚠️ 2h
   → {one_line_action_from_notes}
   → Type `order {order_id}` for full details

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Start with #1 — {brief_reason_why_most_urgent}

📊 Your Stats Today:
│ Queue: {current} / {max} tickets
│ Resolved today: {today_count}
│ Avg resolution: {avg_time} min
│ SLA met: {sla_pct}%
```

---

## Guardrails
- Only show tickets from Google Sheet (Assignments tab)
- Order data from Redshift (read-only via `orders_goms`)
- Do not invent tickets, SLA times, or resolution steps
- Action text from triage-and-assign Action Generation Rules only
- If Diagnosis is empty or `uncategorized`, say so — do not guess
- RFI < 24h: NEVER suggest nudging the customer
- Do NOT auto-resolve tickets in Sheet — agent must confirm
