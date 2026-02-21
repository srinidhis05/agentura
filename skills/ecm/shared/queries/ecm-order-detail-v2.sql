-- ECM Order Detail Query V2
-- Based on Metabase SOP - DO NOT use analytics_orders_master_data (not optimized)
-- Replace {order_id} with the specific order ID

-- Optimized: explicit columns + restrict by order_id so CTEs scan minimal rows
WITH latest_payments_goms AS (
    SELECT reference_id, created_at, updated_at, payment_status
    FROM (
        SELECT reference_id, created_at, updated_at, payment_status,
               ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM payments_goms
        WHERE payment_status = 'COMPLETED'
          AND reference_id = '{order_id}'
    ) pg
    WHERE rn = 1
),
latest_payout AS (
    SELECT transaction_id, status, payout_partner, updated_at
    FROM (
        SELECT transaction_id, status, payout_partner, updated_at,
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM transaction_payout
        WHERE transaction_id IN (SELECT transaction_id FROM falcon_transactions_v2 WHERE client_txn_id = '{order_id}')
    ) tp
    WHERE rn = 1
),
order_base AS (
    SELECT
        og.order_id,
        og.status AS goms_order_status,
        og.sub_state AS goms_sub_state,
        og.meta_postscript_pricing_info_send_currency AS currency_from,
        og.meta_postscript_pricing_info_send_amount AS send_amount,
        og.meta_postscript_pricing_info_receive_amount AS receive_amount,
        og.created_at,
        og.updated_at,
        ROUND(EXTRACT(EPOCH FROM (GETDATE() - og.created_at)) / 3600, 1) AS hours_diff,
        -- Time bucket
        CASE
            WHEN EXTRACT(EPOCH FROM (GETDATE() - og.created_at)) / 3600 BETWEEN 12 AND 24 THEN '12_hr_bucket'
            WHEN EXTRACT(EPOCH FROM (GETDATE() - og.created_at)) / 3600 BETWEEN 24 AND 48 THEN '24_hr_bucket'
            WHEN EXTRACT(EPOCH FROM (GETDATE() - og.created_at)) / 3600 > 48 THEN '48_hr_bucket'
            ELSE '0_bucket'
        END AS time_bucket
    FROM orders_goms og
    WHERE og.order_id = '{order_id}'
),
enriched_data AS (
    SELECT
        ob.*,
        -- Payment data
        pg.payment_status AS payment_status_goms,
        -- Falcon data
        fal.status AS falcon_status,
        fal.transaction_id AS ftv_transaction_id,
        -- Lulu data (AED orders)
        l.sub_status AS lulu_status,
        l.lulu_client,
        l.status AS lulu_main_status,
        -- Payout data
        tp.status AS payout_status,
        tp.payout_partner AS current_payout_partner,
        -- RFI data
        t.status AS rfi_status,
        -- UAE Manual Payment
        ump.status AS uae_manual_payment_status,
        -- Checkout data
        cpd.status AS checkout_status,
        -- Fulfillments (TRM time)
        DATE_DIFF('seconds', fg.created_at::timestamp, fg.updated_at::timestamp) AS goms_trm_time_diff_sec,
        -- RDA status
        rf.status AS rda_status,
        -- Bulk partner classification
        CASE
            WHEN ob.receive_amount > 50000 AND tp.payout_partner IN ('SINGHAI_2025_V2', 'VELTOPAYZ_V4', 'VELTOPAYZ_V5', 'VELTOPAYZ_V6') THEN 'bulk_vda_partner'
            WHEN tp.payout_partner IN ('VELTOPAYZ_HVT_BULK', 'VELTOPAYZ_KPR_BULK', 'ARMSTRONG_PARTNER_DASHBOARD', 'TANGOPE_V3') THEN 'bulk_vda_partner'
            WHEN tp.payout_partner = 'VANCE_RDA' THEN 'rda_partner'
            WHEN tp.payout_partner IS NOT NULL THEN 'vda_api_partner'
            ELSE NULL
        END AS bulk_partner_exclusions
    FROM order_base ob
    LEFT JOIN latest_payments_goms pg ON pg.reference_id = ob.order_id
    LEFT JOIN falcon_transactions_v2 fal ON fal.client_txn_id = ob.order_id
    LEFT JOIN lulu_data l ON l.order_id = ob.order_id
    LEFT JOIN latest_payout tp ON tp.transaction_id = fal.transaction_id
    LEFT JOIN transfer_rfi t ON t.reference_id = ob.order_id
    LEFT JOIN uae_manual_payments ump ON ump.order_id = ob.order_id
    LEFT JOIN checkout_payment_data cpd ON cpd.order_id = ob.order_id
    LEFT JOIN fulfillments_goms fg ON fg.order_id = ob.order_id
    LEFT JOIN rda_fulfillments rf ON rf.order_id = fal.transaction_id
)
SELECT
    ed.*,
    -- Derive stuck_reason based on Metabase SOP logic
    CASE
        -- AED-specific rules
        WHEN currency_from = 'AED' AND lulu_client = 'LULU' AND lulu_status = 'CREDITED' AND goms_order_status = 'PROCESSING_DEAL_IN' THEN 'status_sync_issue'
        WHEN goms_order_status = 'COMPLETED' AND falcon_status = 'FAILED' THEN 'falcon_failed_order_completed_issue'
        WHEN currency_from = 'AED' AND lulu_status = 'PAYMENT_PENDING' THEN 'brn_issue'
        WHEN currency_from = 'AED' AND uae_manual_payment_status = 'RECONCILED' AND lulu_status = 'PAYMENT_PENDING' THEN 'brn_issue'
        WHEN currency_from = 'AED' AND uae_manual_payment_status = 'RECONCILED' AND lulu_status IS NULL THEN 'brn_issue'
        WHEN currency_from = 'AED' AND uae_manual_payment_status = 'RECONCILED' AND lulu_status = 'CREATED' THEN 'brn_issue'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND rfi_status IS NOT NULL AND time_bucket = '12_hr_bucket' THEN 'rfi_order_within_24_hr'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND rfi_status IS NOT NULL AND rda_status = 'ONHOLD' AND time_bucket = '12_hr_bucket' THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND rfi_status IS NOT NULL AND rda_status = 'ONHOLD' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND rfi_status IS NOT NULL AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'rfi_order_grtr_than_24_hr'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND goms_order_status != 'FAILED' AND lulu_status IS NOT NULL THEN 'stuck_at_lulu'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND goms_order_status = 'FAILED' AND lulu_status IS NOT NULL THEN 'refund_pending'
        WHEN currency_from = 'AED' AND lulu_status = 'CANCELLATION_COMPLETED' AND ftv_transaction_id IS NOT NULL AND current_payout_partner = 'VANCE_RDA' AND checkout_status = 'CAPTURED' THEN 'refund_pending'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'bulk_vda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'bulk_vda_order_within_16_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'bulk_vda_partner' AND time_bucket = '12_hr_bucket' THEN 'bulk_vda_order_grtr_than_16_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'vda_api_partner' THEN 'stuck_at_vda_partner'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NULL AND bulk_partner_exclusions = 'rda_partner' THEN 'no_rfi_created'
        WHEN currency_from = 'AED' AND lulu_status = 'TXN_TRANSMITTED' AND ftv_transaction_id IS NOT NULL AND current_payout_partner = 'VANCE_RDA' AND checkout_status = 'CAPTURED' THEN 'stuck_at_rda_partner'
        WHEN currency_from = 'AED' AND lulu_status = 'TXN_TRANSMITTED' AND ftv_transaction_id IS NOT NULL AND current_payout_partner = 'VANCE_RDA' AND payout_status = 'FAILED' AND lulu_status != 'CANCELLATION_COMPLETED' THEN 'cancellation_pending'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NULL AND bulk_partner_exclusions = 'rda_partner' THEN 'stuck_at_rda_partner'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
        WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
        WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND payout_status = 'COMPLETED' AND lulu_status = 'CREDITED' THEN 'status_sync_issue'
        WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'CANCELLATION_REQUEST_CREATED' THEN 'cancellation_pending'
        WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'CANCELLATION_COMPLETED' THEN 'refund_pending'
        WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'TXN_TRANSMITTED' AND falcon_status = 'FAILED' THEN 'cancellation_pending'

        -- GBP/EUR-specific rules
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND rfi_status IS NULL AND rda_status = 'ONHOLD' THEN 'no_rfi_created'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND rfi_status IS NOT NULL AND rda_status = 'ONHOLD' AND time_bucket = '12_hr_bucket' THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND rfi_status IS NOT NULL AND rda_status = 'ONHOLD' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND payment_status_goms = 'COMPLETED' AND goms_sub_state = 'AWAIT_RETRY_INTENT' THEN 'stuck_due_to_payment_issue_goms'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND payment_status_goms = 'COMPLETED' AND goms_sub_state = 'PENDING' THEN 'stuck_due_to_payment_issue_goms'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NULL THEN 'stuck_due_trm'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NOT NULL AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_due_trm_rfi_grtr_than_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NOT NULL AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_due_trm_rfi_within_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'bulk_vda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'bulk_vda_order_within_16_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'bulk_vda_partner' AND time_bucket = '12_hr_bucket' THEN 'bulk_vda_order_grtr_than_16_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'vda_api_partner' THEN 'stuck_at_vda_partner'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NULL AND bulk_partner_exclusions = 'rda_partner' THEN 'no_rfi_created'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NULL AND bulk_partner_exclusions = 'rda_partner' AND rda_status != 'ONHOLD' THEN 'stuck_at_rda_partner'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_order_status = 'FAILED' AND goms_sub_state = 'FAILED' THEN 'refund_pending'
        WHEN currency_from IN ('GBP', 'EUR') AND goms_order_status != 'FAILED' AND payout_status = 'COMPLETED' THEN 'status_sync_issue'

        ELSE 'uncategorized'
    END AS stuck_reason,

    -- Team dependency
    CASE
        WHEN currency_from = 'AED' AND lulu_client = 'LULU' AND lulu_status = 'CREDITED' AND goms_order_status = 'PROCESSING_DEAL_IN' THEN 'Ops'
        WHEN goms_order_status = 'COMPLETED' AND falcon_status = 'FAILED' THEN 'Ops'
        -- ... (simplified - full logic would repeat the stuck_reason CASE and map to teams)
        ELSE 'Ops'
    END AS team_dependency,

    -- Category
    CASE
        WHEN hours_diff < 12 THEN 'level_zero'
        WHEN hours_diff BETWEEN 12 AND 24 THEN 'warning'
        WHEN hours_diff BETWEEN 24 AND 36 THEN 'action_required'
        WHEN hours_diff > 36 THEN 'critical'
    END AS category
FROM enriched_data ed;
