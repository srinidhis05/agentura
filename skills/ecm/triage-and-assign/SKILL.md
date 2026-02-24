---
name: triage-and-assign
role: manager
domain: ecm
trigger: always
model: anthropic/claude-haiku-4.5
cost_budget_per_execution: "$0.05"
timeout: "30s"
---

# ECM Triage & Assignment Manager

## Guardrails
- **Always apply** the rules in `../shared/guardrails.md`. Use only data from executed queries and runbooks; never invent order IDs, counts, or resolution steps.

## Trigger
- "triage"
- "triage and assign"
- "analyse and assign"
- "prioritize tickets"
- "daily briefing"

## Persona: Manager
This skill is for the **manager persona** who coordinates the entire ECM operation.
The manager analyses all stuck orders, scores them by priority, and assigns them to agents.

For the **agent persona** (individual contributor), see `../my-tickets/SKILL.md`.

---

## Google Sheet
**Spreadsheet ID:** `1r50OEZlFVSUmU1tkLBqx2_BzlilZ3s0pArNHV83tRks`

### Assignments Tab Schema (10 columns)
```
A: Order ID      | B: Assigned Agent | C: Assigned At | D: Status | E: Priority
F: Currency      | G: Amount         | H: Hours Stuck | I: Diagnosis | J: Notes
```
Status values: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `ESCALATED`

### Agents Tab Schema (6 columns)
```
A: Email | B: Name | C: Team | D: Slack Handle | E: Active | F: Max Tickets
```
Teams: `Ops`, `KYC_ops`, `VDA_ops`

---

## Philosophy
> "Agents should never scout for data or problems. The manager-agent analyses, prioritizes, and assigns. Human agents execute with clear instructions."

---

## Data Flow

### Step 1: Get actionable stuck orders (FAST — < 5 seconds)

**Time range is configurable:**
- Default: 30 days
- Override: Manager can say `triage last 14 days` or `triage last 60 days`
- Minimum age filter: **12 hours** (orders younger than 12h are still in normal processing)

```sql
SELECT
    og.order_id, og.created_at::date AS order_date,
    og.status AS goms_order_status, og.sub_state,
    og.meta_postscript_pricing_info_send_currency AS currency_from,
    og.meta_postscript_pricing_info_send_amount AS send_amount,
    og.meta_postscript_pricing_info_receive_amount AS receive_amount,
    og.meta_postscript_acquirer AS payment_acquirer,
    ROUND(EXTRACT(EPOCH FROM (GETDATE() - og.created_at)) / 3600, 1) AS hours_diff
FROM orders_goms og
WHERE og.status IN ('PROCESSING_DEAL_IN', 'PENDING', 'FAILED')
  AND og.meta_postscript_pricing_info_send_currency IN ('AED', 'GBP', 'EUR')
  AND og.created_at >= CURRENT_DATE - {time_range_days}
  AND og.created_at < GETDATE() - INTERVAL '12 hours'
  AND og.sub_state IN (
      'PENDING', 'FULFILLMENT_PENDING', 'AWAIT_RETRY_INTENT',
      'REFUND_TRIGGERED', 'PAYMENT_SUCCESS', 'AWAIT_EXTERNAL_ACTION',
      'MANUAL_REVIEW', 'FAILED'
  )
ORDER BY
    CASE og.sub_state
        WHEN 'REFUND_TRIGGERED' THEN 1
        WHEN 'AWAIT_RETRY_INTENT' THEN 2
        WHEN 'MANUAL_REVIEW' THEN 3
        WHEN 'AWAIT_EXTERNAL_ACTION' THEN 4
        WHEN 'FULFILLMENT_PENDING' THEN 5
        WHEN 'PENDING' THEN 6
        WHEN 'FAILED' THEN 7
        ELSE 8
    END,
    og.meta_postscript_pricing_info_send_amount DESC,
    og.created_at ASC
LIMIT 100;
```

> **Exclude** `CNR_RESERVED_WAIT` (normal 10-day monitoring) and `INIT_PAYMENT` / `CREATED` / `PRE_ORDER` (transient states).

### Step 2: Get already-assigned orders from Google Sheet
- Filter where `Status IN ('OPEN', 'IN_PROGRESS', 'ESCALATED')`
- Build a set of already-assigned `order_id`s
- Exclude these from new assignment

### Step 3: Enrich top candidates (sequential queries — each < 10s)
For the top ~20 unassigned orders (by amount * age), run `../shared/queries/ecm-triage-fast.sql` with `{order_id}` replaced.

**Batch optimization:** Use `IN ('{id1}', '{id2}', ...)` for up to 10 order_ids per query.

### Step 3.5: DISQUALIFY non-actionable orders (MANDATORY — before scoring)

**CRITICAL: A wrong assignment means a real stuck customer gets skipped.**

#### Disqualification Rules

| # | Condition | Reason |
|---|-----------|--------|
| D1 | `payment_status_goms` IN (`CREATED`, `INITIATED`, NULL) AND `falcon_status` IS NULL | Abandoned payment |
| D2 | `stuck_reason` = `uncategorized` AND `payment_status_goms` != `COMPLETED` | No completed payment + no known pattern |
| D3 | `stuck_reason` = `uncategorized` AND all downstream systems are NULL | Dead order |
| D4 | `goms_sub_state` = `AWAIT_RETRY_INTENT` AND `payment_status_goms` != `COMPLETED` | Payment retry pending but never paid |
| D5 | Order age > 30 days AND `stuck_reason` = `uncategorized` | Stale uncategorized |

**NEVER assign an `uncategorized` order without first verifying that payment was completed AND at least one downstream system has a record.**

### Step 4: Compute Priority Score

```
PRIORITY_SCORE = (
  0.25 * age_score +
  0.20 * amount_score +
  0.25 * stuck_severity_score +
  0.15 * rfi_urgency_score +
  0.10 * payment_risk_score +
  0.05 * attempt_score
)
```

| Factor | Weight | Key thresholds |
|--------|--------|----------------|
| Age | 0.25 | >72h=1.0, 36-72h=0.9, 24-36h=0.7, 12-24h=0.5 |
| Amount | 0.20 | >15K=1.0, 5-15K=0.8, 2-5K=0.7, 500-2K=0.5 |
| Severity | 0.25 | refund_pending=1.0, falcon_failed=0.9, no_rfi=0.8, sync=0.6, brn=0.5 |
| RFI | 0.15 | EXPIRED=0.9, REJECTED>24h=0.8, REQUESTED>24h=0.7 |
| Payment | 0.10 | FAILED no refund=0.9, PENDING=0.3 |
| Attempts | 0.05 | 3+=0.9, 2=0.5, 1=0.1 |

**Priority mapping:**
- Score > 0.7 → **P1** (Critical)
- Score 0.5-0.7 → **P2** (High)
- Score 0.3-0.5 → **P3** (Medium)
- Score < 0.3 → **P4** (Low/Monitor)

### Step 5: Check agent capacity
Read **Agents** tab — get all active agents, count current tickets, calculate available slots.

### Step 6: Assign and write to Sheet
For each available agent slot, pick highest-priority unassigned order matching agent's team.

### Step 7: Update ECM Dashboard tab

---

## Action Generation Rules

For each `stuck_reason`, generate the **exact next step**. These are baked into the Notes column.

### Ops Team Actions
- `status_sync_issue` → `Status sync: Force-sync via AlphaDesk, verify LULU=CREDITED`
- `falcon_failed_order_completed_issue` → `Falcon sync: Verify payout at partner, force GOMS update via AlphaDesk`
- `brn_issue` → `BRN push: Get ref from {acquirer}, push to Lulu via AlphaDesk`
- `stuck_at_lean_recon` → `Lean recon: Check Lean Admin queue, escalate to Ahsan if stuck`
- `stuck_at_lulu` → `Lulu stuck: Check Lulu dashboard, escalate to Binoy if >48h`
- `refund_pending` → `REFUND {amount} {currency}: Check {acquirer} refund queue, initiate if missing`
- `cancellation_pending` → `Cancel pending: Check Lulu status, request cancellation or recall`
- `stuck_at_rda_partner` → `RDA stuck: Check partner dashboard, escalate if >24h`
- `stuck_due_to_payment_issue_goms` → `GOMS payment: Check acquirer for capture status, manual recon if needed`
- `uncategorized` → `INVESTIGATE: Full system review needed — GOMS/Falcon/Lulu/Payout`

### KYC Ops Team Actions
- `rfi_order_within_24_hr` → `RFI <24h: MONITOR ONLY — do NOT nudge customer`
- `rfi_order_grtr_than_24_hr` → `RFI >24h: Nudge customer via email/SMS, check AlphaDesk if data >4h stale`
- `no_rfi_created` → `BUG: Create RFI manually in AlphaDesk, flag for engineering`
- `stuck_due_trm` → `TRM hold: Check ComplianceReview in AlphaDesk, release or create RFI`
- `stuck_due_trm_rfi_within_24_hrs` → `TRM+RFI <24h: Monitor, TRM release pending docs`
- `stuck_due_trm_rfi_grtr_than_24_hrs` → `TRM+RFI >24h: Nudge customer for docs, TRM waiting`

### VDA Ops Team Actions
- `stuck_at_vda_partner` → `VDA stuck: Check partner dashboard, force sync if completed`
- `bulk_vda_order_within_16_hrs` / `bulk_vda_order_grtr_than_16_hrs` → `Bulk VDA: Monitor (<16h) or escalate (>16h)`

---

## Output Format

### Manager Briefing
```
🎯 Sentinel Triage Report — {date}
📅 Time range: Last {time_range_days} days (orders 12h+ old)

📊 Overview:
│ Actionable stuck orders: {actionable_count}
│ Already assigned: {assigned_count} (across {agent_count} agents)
│ New to assign: {new_count}
│ Critical (> 36h): {critical_count} 🔴
│ High-value (> 5K): {high_value_count} 💰
│ Disqualified (not real edge cases): {disqualified_count} ⛔

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Top Priority Orders (unassigned):

# | Order ID      | Amount       | Stuck  | Diagnosis            | Priority | Action
--|---------------|-------------|--------|----------------------|----------|--------
1 | {order_id}    | {amt} {cur} | {hrs}h | {stuck_reason}       | P1 🔴    | {one_liner}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 Agent Capacity: {dynamically from Agents tab}

📈 Recommended Assignments:
→ Assign {order_id} (P1, {stuck_reason}) → @{agent} ({team})

Shall I proceed with these assignments? (confirm to write to Sheet)
```

---

## Guardrails

### Assignment Safety (HIGHEST PRIORITY)
- **NEVER assign an order without running Step 3.5 disqualification first**
- **NEVER assign `uncategorized` orders** unless payment_status = COMPLETED AND at least one downstream system has a record
- **NEVER assign abandoned payments** (payment_status IN CREATED/INITIATED/NULL with no falcon)
- Only assign orders that match a known `stuck_reason` from the runbooks
- If in doubt, **do not assign** — add to disqualified summary

### Data Integrity
- Only assign orders verified in Redshift
- Respect agent capacity limits from Agents tab
- Never write to Redshift (read-only)
- All writes go to Google Sheets
- Priority scores from `../shared/config/knowledge-graph.yaml`
- Action text from Action Generation Rules — do not invent steps
- RFI < 24h: NEVER suggest nudging customer
- **Manager must confirm** before writing assignments to Sheet
