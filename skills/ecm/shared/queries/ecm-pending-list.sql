-- ECM Pending List Query (FAST - Step 1)
-- Returns TRULY ACTIONABLE stuck orders
-- Target: < 10 seconds, returns candidate order_ids for Step 2 (ecm-triage-fast.sql)
--
-- CRITICAL FILTERS (from knowledge-graph.yaml):
-- 1. Payment COMPLETED (not abandoned)
-- 2. Actionable sub_states only (FULFILLMENT_PENDING, REFUND_TRIGGERED, etc.)
-- 3. Has downstream system record (Falcon OR Lulu) - NOT dead orders
--
-- GUARDRAIL: Dead orders (no downstream record) are EXCLUDED
-- Per knowledge graph: "Order exists in GOMS but no downstream system has a record →
--                       Dead orders. Do NOT assign to ops agents — no action possible."

WITH paid_orders AS (
    SELECT DISTINCT reference_id
    FROM payments_goms
    WHERE payment_status = 'COMPLETED'
      AND created_at >= CURRENT_DATE - 30
),
-- Downstream system records (proof order is not dead)
lulu_orders AS (
    SELECT DISTINCT order_id FROM lulu_data WHERE created_at >= CURRENT_DATE - 30
),
falcon_orders AS (
    SELECT DISTINCT client_txn_id FROM falcon_transactions_v2 WHERE created_at >= CURRENT_DATE - 30
)
SELECT
    o.order_id,
    o.created_at::date AS order_date,
    o.status AS order_status,
    o.sub_state,
    o.meta_postscript_pricing_info_send_currency AS currency_from,
    o.meta_postscript_pricing_info_send_amount AS send_amount,
    o.meta_postscript_pricing_info_receive_amount AS receive_amount,
    ROUND(EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600, 1) AS hours_diff,
    CASE
        WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600 > 36 THEN 'critical'
        WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600 > 24 THEN 'action_required'
        WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600 > 12 THEN 'warning'
        ELSE 'level_zero'
    END AS category
FROM orders_goms o
INNER JOIN paid_orders p ON p.reference_id = o.order_id
WHERE
    -- Status filter (non-terminal)
    o.status IN ('PROCESSING_DEAL_IN', 'PENDING', 'FAILED', 'IN_PROGRESS')

    -- ACTIONABLE sub_states ONLY (from knowledge-graph.yaml goms_uae_states/goms_uk_states)
    AND o.sub_state IN (
        'FULFILLMENT_PENDING',     -- Normal processing, needs monitoring (SLA: 24h UAE, 1h UK)
        'REFUND_TRIGGERED',        -- CRITICAL: customer funds at risk (SLA: 2h)
        'TRIGGER_REFUND',          -- CRITICAL: refund needed (SLA: 2h)
        'FULFILLMENT_TRIGGER',     -- About to fulfill, may be stuck
        'MANUAL_REVIEW',           -- AlphaDesk ops action needed (SLA: 30min)
        'AWAIT_EXTERNAL_ACTION'    -- RFI / manual action (SLA: 24h)
    )

    -- Currency filter
    AND o.meta_postscript_pricing_info_send_currency IN ('AED', 'GBP', 'EUR')

    -- Time window: last 30 days, at least 12 hours old
    AND o.created_at >= CURRENT_DATE - 30
    AND o.created_at < GETDATE() - INTERVAL '12 hours'

    -- GUARDRAIL: Must have downstream system record (NOT a dead order)
    -- AED orders must have Lulu record, GBP/EUR can proceed without (Falcon creates later)
    AND (
        o.meta_postscript_pricing_info_send_currency IN ('GBP', 'EUR')
        OR o.order_id IN (SELECT order_id FROM lulu_orders)
    )
ORDER BY
    -- Priority: critical first, then by amount (high value first)
    CASE
        WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600 > 36 THEN 1
        WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600 > 24 THEN 2
        WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600 > 12 THEN 3
        ELSE 4
    END,
    o.meta_postscript_pricing_info_send_amount DESC,
    o.created_at ASC
LIMIT 500;
