# Lulu Pending Transactions – Non-Terminal States Runbook

## Overview
Identify and resolve Lulu transactions that are **not** in **COMPLETED** or **REJECTED** status. These are raised with Lulu using a defined SQL output; if there is a **peak (>50 transactions)**, the output is shared with Lulu via email.

**Team:** Ops  
**SOP Reference:** Lulu SOP § 3.4 Pending Transactions – Non-Terminal States

## Purpose
- Surface transactions stuck in non-terminal Lulu statuses.
- Enable batch follow-up with Lulu (agent.support@pearldatadirect.com).

## How to Identify (SOP)

Run the query in `queries/lulu-pending-non-terminal.sql` with the desired date range. Replace `{start_date}` and `{end_date}` (e.g. `'2025-01-01'` and `'2025-02-17'`). The query filters:

- `lulu_data.status` **NOT IN** ('COMPLETED', 'REJECTED')
- `lulu_client` = 'LULU'
- `payment_acquirer` != 'UAE_MANUAL'
- Leantech: `ld.status` = 'ACCEPTED_BY_BANK' **OR** Checkout: `order_status` = 'PROCESSING_DEAL_IN'

## Action Taken (SOP)

1. Run the query for the relevant period (e.g. `created_at` between start and end date).
2. **Check for peak:** If result set has **>50 transactions**, treat as peak.
3. **Share with Lulu:** Email the output to **agent.support@pearldatadirect.com**.
4. Follow up per Lulu SLA / internal pending action process.

## Query Reference

The SQL is stored in this plugin as `queries/lulu-pending-non-terminal.sql` so it can be run from Redshift/MCP or copied into Metabase. Date range is parameterized.

## Escalation
- Normal volume: handle via pending action sheet and Lulu follow-up.
- Peak (>50): send output to Lulu as above; escalate internally if no response within agreed SLA (see [ESCALATION.md](../ESCALATION.md)).
