-- ECM Flow Analysis: Backlog vs Yesterday vs Today
-- Purpose: Analyst view of order flow for ECM operations
-- Shows: How much backlog existed, what came in yesterday, what came in today

WITH paid_orders AS (
    SELECT DISTINCT reference_id
    FROM payments_goms
    WHERE payment_status = 'COMPLETED'
      AND created_at >= CURRENT_DATE - 30
),
lulu_orders AS (
    SELECT DISTINCT order_id FROM lulu_data WHERE created_at >= CURRENT_DATE - 30
),
stuck_orders AS (
    SELECT
        o.order_id,
        o.created_at,
        o.created_at::date AS order_date,
        o.sub_state,
        o.meta_postscript_pricing_info_send_currency AS currency,
        o.meta_postscript_pricing_info_send_amount AS send_amount,
        ROUND(EXTRACT(EPOCH FROM (GETDATE() - o.created_at)) / 3600, 1) AS hours_diff,
        CASE
            WHEN o.created_at::date = CURRENT_DATE THEN 'today'
            WHEN o.created_at::date = CURRENT_DATE - 1 THEN 'yesterday'
            ELSE 'backlog'
        END AS inflow_segment
    FROM orders_goms o
    INNER JOIN paid_orders p ON p.reference_id = o.order_id
    WHERE
        o.status IN ('PROCESSING_DEAL_IN', 'PENDING', 'FAILED', 'IN_PROGRESS')
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

-- Summary by segment and currency
SELECT
    inflow_segment,
    currency,
    COUNT(*) AS order_count,
    ROUND(SUM(send_amount), 2) AS total_amount,
    ROUND(AVG(hours_diff), 1) AS avg_hours_stuck,
    ROUND(MIN(hours_diff), 1) AS min_hours,
    ROUND(MAX(hours_diff), 1) AS max_hours
FROM stuck_orders
GROUP BY inflow_segment, currency
ORDER BY
    CASE inflow_segment
        WHEN 'backlog' THEN 1
        WHEN 'yesterday' THEN 2
        WHEN 'today' THEN 3
    END,
    currency;

-- Totals only (for chart)
-- SELECT
--     inflow_segment,
--     COUNT(*) AS total_orders,
--     ROUND(SUM(send_amount), 2) AS total_amount
-- FROM stuck_orders
-- GROUP BY inflow_segment
-- ORDER BY CASE inflow_segment WHEN 'backlog' THEN 1 WHEN 'yesterday' THEN 2 WHEN 'today' THEN 3 END;
