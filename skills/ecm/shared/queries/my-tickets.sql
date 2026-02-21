-- My Tickets Query (optimized: orders_goms base, no analytics_orders_master_data view)
-- Returns tickets assigned to a specific agent with SLA status.
-- Replace {agent_email} with the agent's email/username.
-- Output columns unchanged for compatibility with skills/my-tickets.md.

WITH latest_payout AS (
    SELECT transaction_id, status, payout_partner
    FROM (
        SELECT transaction_id, status, payout_partner,
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM transaction_payout
    ) tp
    WHERE rn = 1
),
latest_payment_goms AS (
    SELECT reference_id, payment_status
    FROM (
        SELECT reference_id, payment_status,
               ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM payments_goms
        WHERE payment_status = 'COMPLETED'
    ) pg
    WHERE rn = 1
),
order_base AS (
    SELECT
        og.order_id,
        og.owner_id AS user_id,
        og.created_at,
        og.status AS order_status,
        og.meta_postscript_pricing_info_send_currency AS currency_from,
        og.meta_postscript_acquirer AS payment_acquirer,
        og.meta_postscript_pricing_info_send_amount AS send_amount,
        og.meta_postscript_pricing_info_receive_amount AS receive_amount,
        og.sub_state,
        og.assigned_agent
    FROM orders_goms og
    WHERE og.assigned_agent = '{agent_email}'
      AND og.created_at::date >= CURRENT_DATE - 7
      AND og.status IN ('PROCESSING_DEAL_IN', 'PENDING', 'FAILED')
      AND og.meta_postscript_pricing_info_send_currency IN ('AED', 'GBP', 'EUR')
),
order_data AS (
    SELECT
        ob.order_id,
        ob.user_id,
        ob.created_at,
        ob.order_status,
        ob.currency_from,
        ob.payment_acquirer,
        ob.send_amount,
        ob.receive_amount,
        ob.sub_state,
        ob.assigned_agent,
        l.sub_status AS lulu_status,
        l.lulu_client,
        tp.status AS payout_status,
        EXTRACT(EPOCH FROM (GETDATE() - ob.created_at)) / 3600 AS hours_diff,
        CASE
            WHEN ob.order_status = 'FAILED' THEN 2
            WHEN ob.sub_state LIKE '%CNR%' THEN 4
            WHEN ob.sub_state LIKE '%RFI%' THEN 24
            WHEN l.sub_status = 'PAYMENT_PENDING' THEN 4
            ELSE 8
        END AS sla_hours,
        CASE
            WHEN ob.order_status = 'FAILED' AND ob.payment_acquirer = 'CHECKOUT' THEN 'Payment failed'
            WHEN ob.order_status = 'FAILED' THEN 'Payment failed'
            WHEN ob.sub_state = 'CNR_RESERVED_WAIT' THEN 'Waiting confirmation'
            WHEN ob.sub_state LIKE '%CNR%' THEN 'CNR processing'
            WHEN ob.sub_state LIKE '%RFI%' THEN 'RFI pending'
            WHEN l.sub_status = 'PAYMENT_PENDING' THEN 'BRN pending'
            WHEN l.sub_status = 'CREDITED' AND ob.order_status = 'PROCESSING_DEAL_IN' THEN 'Status sync issue'
            WHEN tp.status = 'ADDITIONAL_DOCUMENTS_REQUIRED' THEN 'Docs required'
            WHEN ob.order_status = 'PENDING' THEN 'Waiting confirmation'
            ELSE 'Under review'
        END AS diagnosis_short
    FROM order_base ob
    INNER JOIN latest_payment_goms pg ON pg.reference_id = ob.order_id AND pg.payment_status = 'COMPLETED'
    LEFT JOIN lulu_data l ON l.order_id = ob.order_id
    LEFT JOIN falcon_transactions_v2 f ON f.client_txn_id = ob.order_id
    LEFT JOIN latest_payout tp ON tp.transaction_id = f.transaction_id
)
SELECT
    order_id,
    order_status,
    currency_from,
    send_amount,
    ROUND(hours_diff, 0) AS hours_stuck,
    diagnosis_short,
    sla_hours,
    ROUND(GREATEST(sla_hours - hours_diff, 0) * 60, 0) AS sla_minutes_remaining,
    CASE
        WHEN hours_diff > sla_hours THEN 'BREACHED'
        WHEN hours_diff > sla_hours * 0.75 THEN 'CRITICAL'
        WHEN hours_diff > sla_hours * 0.5 THEN 'WARNING'
        ELSE 'OK'
    END AS sla_status,
    created_at,
    sub_state,
    lulu_status,
    payout_status
FROM order_data
ORDER BY
    CASE WHEN hours_diff > sla_hours THEN 0 ELSE 1 END,
    sla_minutes_remaining ASC
LIMIT 20;
