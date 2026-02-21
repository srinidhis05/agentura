-- DEPRECATED: Use ecm-order-detail-v2.sql instead (no analytics_orders_master_data view).
-- This file is kept for reference only. All call paths should use ecm-order-detail-v2.sql.
--
-- Order Details Query
-- Fetch single order with all relevant statuses for ECM investigation
-- Parameter: {order_id} - The order ID to look up

SELECT 
    a.order_id, 
    a.created_at,
    a.created_at::date AS order_date,
    a.receive_amount,
    a.send_amount,
    a.order_status, 
    a.currency_from, 
    a.payment_acquirer, 
    a.payment_status AS order_payment_status, 
    a.ftv_transaction_id,
    fal.status as falcon_status,
    pg.payment_status AS payment_status_goms, 
    t.status AS rfi_status,
    tp.status AS payout_status,
    tp.payout_partner AS current_payout_partner,
    l.sub_status AS lulu_status,
    l.lulu_client,
    ump.status AS uae_manual_payment_status,
    cpd.status AS checkout_status,
    td.status AS truelayer_status,
    og.sub_state as goms_sub_state,
    og.status as goms_order_status,
    rf.status as rda_status,
    EXTRACT(EPOCH FROM (GETDATE() - a.created_at)) / 3600 AS hours_diff,
    -- Derived category based on hours
    CASE 
        WHEN EXTRACT(EPOCH FROM (GETDATE() - a.created_at)) / 3600 < 12 THEN 'level_zero'
        WHEN EXTRACT(EPOCH FROM (GETDATE() - a.created_at)) / 3600 BETWEEN 12 AND 24 THEN 'warning'
        WHEN EXTRACT(EPOCH FROM (GETDATE() - a.created_at)) / 3600 BETWEEN 24 AND 36 THEN 'action_required'
        ELSE 'critical'
    END AS category
FROM analytics_orders_master_data a
LEFT JOIN (
    SELECT reference_id, payment_status
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM payments_goms WHERE payment_status = 'COMPLETED'
    ) pg WHERE rn = 1
) pg ON pg.reference_id = a.order_id
LEFT JOIN falcon_transactions_v2 fal ON fal.transaction_id = a.ftv_transaction_id
LEFT JOIN transfer_rfi t ON t.reference_id = a.order_id
LEFT JOIN (
    SELECT transaction_id, status, payout_partner
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM transaction_payout
    ) tp WHERE rn = 1
) tp ON tp.transaction_id = a.ftv_transaction_id
LEFT JOIN lulu_data l ON l.order_id = a.order_id
LEFT JOIN uae_manual_payments ump ON ump.order_id = a.order_id
LEFT JOIN checkout_payment_data cpd ON cpd.order_id = a.order_id
LEFT JOIN truelayer_data td ON td.order_id = a.order_id AND td.payment_reference = 'refund_payment'
LEFT JOIN orders_goms og ON og.order_id = a.order_id
LEFT JOIN rda_fulfillments rf ON rf.order_id = a.ftv_transaction_id
WHERE a.order_id = '{order_id}';
