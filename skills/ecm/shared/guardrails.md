# ECM Operations Guardrails

**Apply these rules in every ECM skill.** They define what the agent must and must not do so outputs are accurate, safe, and trustworthy.

---

## 0. MCP Configuration (CRITICAL)

**ONLY use the `ecm-gateway` MCP server for all data queries.**

| Tool Name | Purpose |
|-----------|---------|
| `mcp__ecm-gateway__redshift_execute_sql_tool` | Execute Redshift SQL queries |
| `mcp__ecm-gateway__redshift_list_databases` | List Redshift databases |
| `mcp__ecm-gateway__sheets_get_sheet_data` | Read Google Sheets |
| `mcp__ecm-gateway__sheets_update_cells` | Update Google Sheets |
| `mcp__ecm-gateway__sheets_list_spreadsheets` | List spreadsheets |

**FORBIDDEN:**
- `awslabs.redshift-mcp-server` — NOT configured in this workspace
- Any standalone Redshift MCP — NOT available
- Hallucinated MCP tools — NEVER make up tool names

**If a tool call fails:** Report the exact error. Do NOT fabricate results.

---

## 1. No Hallucination — Data and Facts

- **Only use data that comes from executed queries or from runbooks.** Do not invent ticket IDs, order IDs, customer names, counts, dates, SLA values, or any other facts.
- **Do not guess or infer values** that are not explicitly returned by the data source (e.g. do not assume an order exists; do not invent a `stuck_reason` or priority).
- **Do not fabricate query results.** If you have not run the skill’s SQL (or the user has not), do not present rows, totals, or summaries as if they came from the database.
- **Do not make up resolution steps or runbook content.** Use only the steps defined in `runbooks/*.md`. Do not add “logical” steps that are not in the runbook.
- **In artifacts (e.g. JSX dashboards):** Visualizations and tables must use only the current data source — injected query results or user-provided spreadsheet (CSV). Do not invent rows or chart values; if there is no data, the UI should say so.

**When in doubt:** Say that you need to run the query or load the runbook, or that the information is not available from the current data.

---

## 2. Clear “No” on Unsupported or Unsafe Actions

- **Do not execute or suggest destructive actions** (e.g. bulk deletes, schema changes, or ad‑hoc `UPDATE`/`DELETE`) unless the skill explicitly defines them and the user has confirmed.
- **Do not expose raw PII** beyond what the artifact is designed to show (e.g. masking rules in the skill/artifact must be respected). Do not suggest copying full unmasked customer data unless the runbook or policy allows it.
- **Do not answer for other systems or teams** (e.g. “Finance will approve”) unless that is stated in runbooks or official docs. Prefer: “Escalate to Finance per runbook” without inventing outcomes.
- **Do not invent integrations.** Only use connectors and data sources declared in the plugin (e.g. Redshift, `operations` schema). Do not claim to call external APIs or tools that are not configured.

---

## 3. Scope and Honesty

- **Stay within ECM scope.** For questions outside tickets, orders, runbooks, and defined workflows, say so and point the user to the right team or tool instead of guessing.
- **If the query returns no rows,** say “No tickets/orders found” (or the appropriate message). Do not invent a single row or summary to “be helpful.”
- **If a runbook does not cover the situation,** say so. Do not invent a new runbook section. Suggest escalation or that the runbook may need to be updated.
- **If you do not know,** say “I don’t know” or “I’d need to run the query / check the runbook to confirm.” Do not fill gaps with plausible-sounding but unsourced statements.

---

## 4. Idempotency and Consistency

- **Use the exact queries and artifacts defined in the skill.** Do not rewrite SQL in a way that changes semantics (e.g. different filters or joins) unless the skill explicitly allows overrides.
- **Parameterized inputs only.** Use `{order_id}`, `{ticket_id}`, `{current_user}` etc. as defined. Do not substitute placeholder or fake IDs “for demonstration.”

---

## 5. What the Plugin Is Supposed to Give

- **Accurate, up-to-date views** of tickets and orders by running the plugin’s queries against the configured data source.
- **Step-by-step guidance** taken verbatim from the runbooks, mapped by `stuck_reason` (or equivalent) as defined in the skill.
- **Clear, actionable responses** for resolve/escalate/contact, using only defined actions and templates.
- **Explicit uncertainty** when data is missing or runbooks don’t apply, so users are not misled.

---

## 6. Summary: Must / Must Not

| Must | Must not |
|------|----------|
| Use only query results and runbook content | Invent IDs, numbers, or facts |
| Say “no data” or “run the query” when appropriate | Fabricate rows or summaries |
| Follow runbook steps as written | Add or invent resolution steps |
| Stay within defined data sources and connectors | Claim unsupported integrations or outcomes |
| Say “I don’t know” when unsure | Guess to sound helpful |
| Respect PII and masking rules | Expose or suggest exposing raw PII beyond policy |
| Use only skill-defined queries and parameters | Change query semantics or use fake IDs |

Every ECM skill should be executed with these guardrails in mind. When documenting or invoking a skill, agents should treat this file as mandatory context.

---

## 6.5. Slack Message Quality (MANDATORY for all Slack posts)

**Before posting ANY message to Slack, read and follow `config/slack-formatting.md`.**

Key rules:
- **Main message < 2000 chars** — summary only, details in thread
- **No markdown tables** — Slack does NOT render `| col | col |`. Use code blocks or bullet lists.
- **Numbers lead sentences** — `*397* orders stuck` not `The current backlog has 397 orders`
- **3-message pattern**: summary (main) → data detail (thread) → actions (thread)
- **Pre-send checklist** must pass before every `chat.postMessage` call

---

## 7. Valid Stuck Reasons and Team Dependencies

The following are the **only valid `stuck_reason` values** from the ECM query. Do not invent new stuck reasons.

### Ops Team
- `status_sync_issue` — Order/payout completed but status not synced
- `falcon_failed_order_completed_issue` — Order COMPLETED but Falcon FAILED
- `stuck_at_lean_recon` — LEANTECH payment with PAYMENT_PENDING (AED)
- `brn_issue` — BRN not pushed to Lulu (AED)
- `stuck_at_lulu` — No FTV but Lulu status exists (AED)
- `refund_pending` — Order failed/cancelled, refund needed
- `cancellation_pending` — Cancellation requested but not completed
- `stuck_at_rda_partner` — RDA partner processing without RFI
- `stuck_due_to_payment_issue_goms` — GOMS payment in AWAIT_RETRY_INTENT/PENDING (GBP/EUR)
- `uncategorized` — No matching pattern

### KYC Ops Team
- `rfi_order_within_24_hr` — RFI pending, < 24 hrs (AED)
- `rfi_order_grtr_than_24_hr` — RFI pending, > 24 hrs (AED)
- `stuck_at_rda_partner_rfi_within_24_hrs` — RDA + RFI, < 24 hrs
- `stuck_at_rda_partner_rfi_grtr_than_24_hrs` — RDA + RFI, > 24 hrs
- `no_rfi_created` — Payout needs docs but no RFI created
- `stuck_due_trm` — TRM hold without RFI (GBP/EUR)
- `stuck_due_trm_rfi_within_24_hrs` — TRM + RFI, < 24 hrs (GBP/EUR)
- `stuck_due_trm_rfi_grtr_than_24_hrs` — TRM + RFI, > 24 hrs (GBP/EUR)

### VDA Ops Team
- `bulk_vda_order_within_16_hrs` — Bulk partner, within window (excluded by default)
- `bulk_vda_order_grtr_than_16_hrs` — Bulk partner, exceeded window (excluded by default)
- `stuck_at_vda_partner` — VDA API partner payout not completed

### Valid Categories (based on hours_diff)
- `level_zero` — < 12 hours
- `warning` — 12-24 hours
- `action_required` — 24-36 hours
- `critical` — > 36 hours

### Valid Team Dependencies
- `Ops` — General operations
- `KYC_ops` — KYC/RFI operations
- `VDA_ops` — VDA partner operations

Runbooks for each stuck_reason are in `runbooks/`. See `stuck-reasons.yaml` for full configuration.

---

## 8. Dead Order Filtering (Knowledge Graph Rule)

**Source:** `config/knowledge-graph.yaml`

> "Order exists in GOMS but no downstream system has a record → Dead orders. Do NOT assign to ops agents — no action possible."

### Dead Order Definition

An order is **DEAD** if it has:
1. No Lulu record (`lulu_order_id IS NULL`)
2. No Falcon record (`falcon_order_id IS NULL`)
3. Payment status NOT COMPLETED (abandoned payment)

### Actionable Order Requirements

| Currency | Must Have |
|----------|-----------|
| AED | Lulu record (order_id in lulu_data table) |
| GBP, EUR | Payment COMPLETED (Falcon record may create during processing) |

### Sub-State Filtering

**ACTIONABLE sub_states only:**
```
FULFILLMENT_PENDING     - Normal processing, needs monitoring (SLA: 24h UAE, 1h UK)
REFUND_TRIGGERED        - CRITICAL: customer funds at risk (SLA: 2h)
TRIGGER_REFUND          - CRITICAL: refund needed (SLA: 2h)
FULFILLMENT_TRIGGER     - About to fulfill, may be stuck
MANUAL_REVIEW           - AlphaDesk ops action needed (SLA: 30min)
AWAIT_EXTERNAL_ACTION   - RFI / manual action (SLA: 24h)
```

**NON-ACTIONABLE sub_states (EXCLUDE):**
```
CNR_RESERVED_WAIT       - Auto-resolves, no agent action needed
INIT_PAYMENT            - Payment not started
CREATED                 - Initial state
PRE_ORDER               - Pre-order
PAYMENT_INITIATED       - Payment in progress
COMPLETED               - Terminal state
CANCELLED               - Terminal state
```

### Query Filter Pattern

Always use this pattern in ECM queries:

```sql
-- Payment must be COMPLETED
INNER JOIN paid_orders p ON p.reference_id = o.order_id

-- Sub_state must be actionable
AND o.sub_state IN (
    'FULFILLMENT_PENDING', 'REFUND_TRIGGERED', 'TRIGGER_REFUND',
    'FULFILLMENT_TRIGGER', 'MANUAL_REVIEW', 'AWAIT_EXTERNAL_ACTION'
)

-- AED orders MUST have Lulu record (not dead)
AND (
    o.meta_postscript_pricing_info_send_currency IN ('GBP', 'EUR')
    OR o.order_id IN (SELECT order_id FROM lulu_orders)
)
```

### Validation Before Assignment

**Expected order count:** 200-600 (typical)
**Red flag:** > 1,000 orders → check if dead order filter is applied
**Fail threshold:** > 2,000 orders → STOP, investigate filters

---

## 9. Operational Pre-Flight Checks (MANDATORY)

### 9a. Before Writing Ad-Hoc SQL
1. **READ the closest existing query** from `shared/queries/` first
2. **Copy table and column names** exactly — never guess
3. Reference table: `payments_goms` (reference_id, payment_status), `lulu_data` (order_id), `falcon_transactions_v2` (client_txn_id), `orders_goms` (meta_postscript_pricing_info_send_currency, meta_postscript_pricing_info_send_amount)

### 9b. Before Status Audits
1. **Check ALL non-actionable states** — not just COMPLETED
2. Use: `sub_state NOT IN ('FULFILLMENT_PENDING','REFUND_TRIGGERED','TRIGGER_REFUND','FULFILLMENT_TRIGGER','MANUAL_REVIEW','AWAIT_EXTERNAL_ACTION')`
3. This catches: CNR_RESERVED_WAIT, FAILED, COMPLETED, CANCELLED, INIT_PAYMENT, CREATED, etc.

### 9c. Before Slack Posts
1. **Validate token**: `curl -s https://slack.com/api/auth.test -H "Authorization: Bearer $SLACK_BOT_TOKEN"`
2. If `ok: false` → STOP, tell user
3. **Use file-based curl** for messages with special chars: write JSON to `/tmp/slack_*.json`, then `curl -d @file`
4. **Follow 3-message pattern**: summary (main) → data (thread) → actions (thread)

### 9d. After Bulk Mutations (>10 rows)
1. **Re-run the source query** to validate new state
2. **Re-present affected views** (charts, trends, summaries)
3. Never show stale snapshot data after mutations

---

## 10. Redshift Table Reference (Quick Lookup)

| Table | Key Columns | Join Key |
|-------|------------|----------|
| `orders_goms` | order_id, status, sub_state, created_at, meta_postscript_pricing_info_send_currency, meta_postscript_pricing_info_send_amount | order_id |
| `payments_goms` | reference_id, payment_status, payment_acquirer | reference_id = order_id |
| `lulu_data` | order_id, lulu_status, lulu_order_id | order_id |
| `falcon_transactions_v2` | client_txn_id, status | client_txn_id = order_id |
| `transfer_rfi` | reference_id, status, rfitype, created_at, modified_at | reference_id = order_id |
| `payouts_goms` | order_id, status, partner | order_id |

**NEVER use:** `payment_transactions_goms`, `lulu_order_details`, `analytics_orders_master_data`
