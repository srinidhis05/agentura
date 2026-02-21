-- ECM Pattern Clusters (Step 1: Lightweight aggregation)
-- Groups actionable stuck orders by failure signature to surface systemic issues.
-- Reuses pending-list filters (DEC-004, DEC-008) + adds classification joins.
--
-- Design: 5 LEFT JOINs (lighter than triage-fast's 9).
-- All CTEs filter created_at >= CURRENT_DATE - 30.
-- Pre-filtered to ~200-600 actionable orders via INNER JOIN paid_orders + sub_state whitelist.
-- No stuck_reason CASE logic — the LLM maps state combinations via stuck-reasons.yaml.
--
-- Expected: <15s, returns ~10-25 pattern rows (HAVING COUNT(*) >= 3)
-- Guardrail: If SUM(order_count) > 1000, dead order filter may be broken (DEC-010)

WITH paid_orders AS (
    SELECT DISTINCT reference_id
    FROM payments_goms
    WHERE payment_status = 'COMPLETED'
      AND created_at >= CURRENT_DATE - 30
),
lulu_orders AS (
    SELECT order_id, sub_status, lulu_client
    FROM lulu_data
    WHERE created_at >= CURRENT_DATE - 30
),
falcon_orders AS (
    SELECT client_txn_id, transaction_id, status AS falcon_status
    FROM falcon_transactions_v2
    WHERE created_at >= CURRENT_DATE - 30
),
payout_latest AS (
    SELECT transaction_id, status AS payout_status, payout_partner
    FROM (
        SELECT transaction_id, status, payout_partner,
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM transaction_payout
        WHERE created_at >= CURRENT_DATE - 30
    ) WHERE rn = 1
),
rfi_orders AS (
    SELECT reference_id, status AS rfi_status
    FROM transfer_rfi
    WHERE created_at >= CURRENT_DATE - 30
),
base AS (
    SELECT
        o.order_id,
        o.status AS goms_status,
        o.sub_state,
        o.meta_postscript_pricing_info_send_currency AS currency_from,
        o.meta_postscript_pricing_info_send_amount AS send_amount,
        ROUND(EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600, 1) AS hours_diff,
        l.sub_status AS lulu_status,
        l.lulu_client,
        f.transaction_id AS ftv_transaction_id,
        f.falcon_status,
        tp.payout_status,
        tp.payout_partner,
        r.rfi_status
    FROM orders_goms o
    INNER JOIN paid_orders p ON p.reference_id = o.order_id
    LEFT JOIN lulu_orders l ON l.order_id = o.order_id
    LEFT JOIN falcon_orders f ON f.client_txn_id = o.order_id
    LEFT JOIN payout_latest tp ON tp.transaction_id = f.transaction_id
    LEFT JOIN rfi_orders r ON r.reference_id = o.order_id
    WHERE o.status IN ('PROCESSING_DEAL_IN', 'PENDING', 'FAILED', 'IN_PROGRESS')
      AND o.sub_state IN (
          'FULFILLMENT_PENDING', 'REFUND_TRIGGERED', 'TRIGGER_REFUND',
          'FULFILLMENT_TRIGGER', 'MANUAL_REVIEW', 'AWAIT_EXTERNAL_ACTION'
      )
      AND o.meta_postscript_pricing_info_send_currency IN ('AED', 'GBP', 'EUR')
      AND o.created_at >= CURRENT_DATE - 30
      AND o.created_at < GETDATE() - INTERVAL '12 hours'
      AND (
          o.meta_postscript_pricing_info_send_currency IN ('GBP', 'EUR')
          OR o.order_id IN (SELECT order_id FROM lulu_orders)
      )
)
SELECT
    currency_from,
    goms_status,
    sub_state,
    COALESCE(lulu_status, 'N/A') AS lulu_status,
    CASE WHEN ftv_transaction_id IS NOT NULL THEN 'yes' ELSE 'no' END AS has_falcon,
    COALESCE(falcon_status, 'N/A') AS falcon_status,
    COALESCE(payout_status, 'N/A') AS payout_status,
    COALESCE(payout_partner, 'N/A') AS payout_partner,
    COALESCE(rfi_status, 'none') AS rfi_status,
    COUNT(*) AS order_count,
    ROUND(SUM(send_amount), 0) AS total_amount,
    ROUND(AVG(send_amount), 0) AS avg_amount,
    ROUND(AVG(hours_diff), 1) AS avg_hours_stuck,
    ROUND(MAX(hours_diff), 1) AS max_hours_stuck,
    SUM(CASE WHEN send_amount >= 5000 THEN 1 ELSE 0 END) AS high_value_count,
    SUM(CASE WHEN hours_diff > 36 THEN 1 ELSE 0 END) AS critical_count
FROM base
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
HAVING COUNT(*) >= 3
ORDER BY SUM(send_amount) DESC
LIMIT 25;
