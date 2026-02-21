-- ECM Bifurcation Summary (Aggregate stuck_reason + stuck_sub_reason)
-- Returns counts grouped by stuck_reason, stuck_sub_reason, and currency.
-- Used by: manager/skills/ecm-daily-flow.md (Phase 3.5: Bifurcation Breakdown)
--
-- Design: Reuses pending-list base filters (DEC-004, DEC-008) + triage-fast
-- stuck_reason/stuck_sub_reason CASE logic, applied in batch across all orders.
-- LEFT JOINs limited to 500 pre-filtered orders for MCP 30s timeout safety.
--
-- Expected: <20s, returns ~20-40 rows
-- Guardrail: If SUM(order_count) > 1000, dead order filter may be broken (DEC-010)

WITH paid_orders AS (
    SELECT DISTINCT reference_id
    FROM payments_goms
    WHERE payment_status = 'COMPLETED'
      AND created_at >= CURRENT_DATE - 30
),
lulu_orders AS (
    SELECT order_id, sub_status, lulu_client, status AS lulu_main_status
    FROM lulu_data
    WHERE created_at >= CURRENT_DATE - 30
),
candidates AS (
    SELECT o.order_id,
           o.status AS goms_order_status,
           o.sub_state AS goms_sub_state,
           o.meta_postscript_pricing_info_send_currency AS currency_from,
           o.meta_postscript_pricing_info_send_amount AS send_amount,
           o.meta_postscript_acquirer AS payment_acquirer,
           o.created_at,
           ROUND(EXTRACT(EPOCH FROM (GETDATE() - o.created_at::timestamp)) / 3600, 1) AS hours_diff,
           CASE
               WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at::timestamp)) / 3600 BETWEEN 12 AND 24 THEN '12_hr_bucket'
               WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at::timestamp)) / 3600 BETWEEN 24 AND 48 THEN '24_hr_bucket'
               WHEN EXTRACT(EPOCH FROM (GETDATE() - o.created_at::timestamp)) / 3600 > 48 THEN '48_hr_bucket'
               ELSE '0_bucket'
           END AS time_bucket,
           l.sub_status AS lulu_status,
           l.lulu_client
    FROM orders_goms o
    INNER JOIN paid_orders p ON p.reference_id = o.order_id
    LEFT JOIN lulu_orders l ON l.order_id = o.order_id
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
    ORDER BY o.created_at ASC
    LIMIT 500
),
-- Enrich with payment, falcon, payout, RFI, checkout, fulfillment, RDA
latest_payment_goms AS (
    SELECT reference_id, payment_status
    FROM (
        SELECT reference_id, payment_status,
               ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM payments_goms
        WHERE payment_status = 'COMPLETED'
          AND reference_id IN (SELECT order_id FROM candidates)
    ) pg WHERE rn = 1
),
falcon AS (
    SELECT transaction_id, status AS falcon_status, client_txn_id
    FROM falcon_transactions_v2
    WHERE client_txn_id IN (SELECT order_id FROM candidates)
),
latest_payout AS (
    SELECT transaction_id, status AS payout_status, payout_partner
    FROM (
        SELECT transaction_id, status, payout_partner,
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM transaction_payout
        WHERE transaction_id IN (SELECT transaction_id FROM falcon)
    ) tp WHERE rn = 1
),
rfi AS (
    SELECT reference_id, status AS rfi_status, created_at AS rfi_created_at
    FROM transfer_rfi
    WHERE reference_id IN (SELECT order_id FROM candidates)
),
checkout AS (
    SELECT order_id, status
    FROM checkout_payment_data
    WHERE order_id IN (SELECT order_id FROM candidates)
),
fulfillment AS (
    SELECT order_id,
           DATEDIFF(SECOND, created_at, updated_at) AS goms_trm_time_diff_sec
    FROM fulfillments_goms
    WHERE order_id IN (SELECT order_id FROM candidates)
),
rda AS (
    SELECT order_id, status
    FROM rda_fulfillments
    WHERE order_id IN (SELECT transaction_id FROM falcon)
),
uae_manual AS (
    SELECT order_id, status
    FROM uae_manual_payments
    WHERE order_id IN (SELECT order_id FROM candidates)
),
enriched AS (
    SELECT
        c.*,
        pg.payment_status AS payment_status_goms,
        f.falcon_status,
        f.transaction_id AS ftv_transaction_id,
        tp.payout_status,
        tp.payout_partner AS current_payout_partner,
        r.rfi_status,
        r.rfi_created_at,
        co.status AS checkout_status,
        fg.goms_trm_time_diff_sec,
        rd.status AS rda_status,
        um.status AS uae_manual_payment_status,
        CASE
            WHEN c.send_amount > 50000 AND tp.payout_partner IN ('SINGHAI_2025_V2', 'VELTOPAYZ_V4', 'VELTOPAYZ_V5', 'VELTOPAYZ_V6') THEN 'bulk_vda_partner'
            WHEN tp.payout_partner IN ('VELTOPAYZ_HVT_BULK', 'VELTOPAYZ_KPR_BULK', 'ARMSTRONG_PARTNER_DASHBOARD', 'TANGOPE_V3') THEN 'bulk_vda_partner'
            WHEN tp.payout_partner = 'VANCE_RDA' THEN 'rda_partner'
            WHEN tp.payout_partner IS NOT NULL THEN 'vda_api_partner'
            ELSE NULL
        END AS bulk_partner_exclusions
    FROM candidates c
    LEFT JOIN latest_payment_goms pg ON pg.reference_id = c.order_id
    LEFT JOIN falcon f ON f.client_txn_id = c.order_id
    LEFT JOIN latest_payout tp ON tp.transaction_id = f.transaction_id
    LEFT JOIN rfi r ON r.reference_id = c.order_id
    LEFT JOIN checkout co ON co.order_id = c.order_id
    LEFT JOIN fulfillment fg ON fg.order_id = c.order_id
    LEFT JOIN rda rd ON rd.order_id = f.transaction_id
    LEFT JOIN uae_manual um ON um.order_id = c.order_id
),
classified AS (
    SELECT
        e.*,
        -- stuck_reason (same logic as ecm-triage-fast.sql)
        CASE
            WHEN currency_from = 'AED' AND lulu_client = 'LULU' AND lulu_status = 'CREDITED' AND goms_order_status = 'PROCESSING_DEAL_IN' THEN 'status_sync_issue'
            WHEN goms_order_status = 'COMPLETED' AND falcon_status = 'FAILED' THEN 'falcon_failed_order_completed_issue'
            WHEN currency_from = 'AED' AND payment_acquirer = 'LEANTECH' AND lulu_status = 'PAYMENT_PENDING' THEN 'stuck_at_lean_recon'
            WHEN currency_from = 'AED' AND payment_acquirer = 'CHECKOUT' AND lulu_status = 'PAYMENT_PENDING' THEN 'brn_issue'
            WHEN currency_from = 'AED' AND payment_acquirer IN ('UAE_MANUAL', 'LEANTECH') AND uae_manual_payment_status = 'RECONCILED' AND lulu_status IN ('PAYMENT_PENDING', 'CREATED') THEN 'brn_issue'
            WHEN currency_from = 'AED' AND payment_acquirer IN ('UAE_MANUAL', 'LEANTECH') AND uae_manual_payment_status = 'RECONCILED' AND lulu_status IS NULL THEN 'brn_issue'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND rfi_status IS NOT NULL AND time_bucket = '12_hr_bucket' THEN 'rfi_order_within_24_hr'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND rfi_status IS NOT NULL AND rda_status = 'ONHOLD' AND time_bucket = '12_hr_bucket' THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND rfi_status IS NOT NULL AND rda_status = 'ONHOLD' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND rfi_status IS NOT NULL AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'rfi_order_grtr_than_24_hr'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND goms_order_status != 'FAILED' AND lulu_status IS NOT NULL THEN 'stuck_at_lulu'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NULL AND goms_order_status = 'FAILED' AND lulu_status IS NOT NULL THEN 'refund_pending'
            WHEN currency_from = 'AED' AND payment_acquirer = 'CHECKOUT' AND lulu_status = 'CANCELLATION_COMPLETED' AND ftv_transaction_id IS NOT NULL AND current_payout_partner = 'VANCE_RDA' AND checkout_status = 'CAPTURED' THEN 'refund_pending'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'bulk_vda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'bulk_vda_order_within_16_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'bulk_vda_partner' AND time_bucket = '12_hr_bucket' THEN 'bulk_vda_order_grtr_than_16_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status != 'COMPLETED' AND bulk_partner_exclusions = 'vda_api_partner' THEN 'stuck_at_vda_partner'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'ADDITIONAL_DOCUMENTS_REQUIRED' AND rfi_status IS NULL AND bulk_partner_exclusions = 'rda_partner' THEN 'no_rfi_created'
            WHEN currency_from = 'AED' AND payment_acquirer = 'CHECKOUT' AND lulu_status = 'TXN_TRANSMITTED' AND ftv_transaction_id IS NOT NULL AND current_payout_partner = 'VANCE_RDA' AND checkout_status = 'CAPTURED' THEN 'stuck_at_rda_partner'
            WHEN currency_from = 'AED' AND payment_acquirer IN ('LEANTECH', 'UAE_MANUAL') AND lulu_status = 'TXN_TRANSMITTED' AND ftv_transaction_id IS NOT NULL AND current_payout_partner = 'VANCE_RDA' AND payout_status = 'FAILED' AND lulu_status != 'CANCELLATION_COMPLETED' THEN 'cancellation_pending'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NULL AND bulk_partner_exclusions = 'rda_partner' THEN 'stuck_at_rda_partner'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_within_24_hrs'
            WHEN currency_from = 'AED' AND ftv_transaction_id IS NOT NULL AND goms_order_status != 'FAILED' AND payout_status = 'PROCESSING' AND rfi_status IS NOT NULL AND bulk_partner_exclusions = 'rda_partner' AND time_bucket NOT IN ('12_hr_bucket', '0_bucket') THEN 'stuck_at_rda_partner_rfi_grtr_than_24_hrs'
            WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND payout_status = 'COMPLETED' AND lulu_status = 'CREDITED' THEN 'status_sync_issue'
            WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'CANCELLATION_REQUEST_CREATED' THEN 'cancellation_pending'
            WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'CANCELLATION_COMPLETED' THEN 'refund_pending'
            WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'TXN_TRANSMITTED' AND falcon_status = 'FAILED' THEN 'cancellation_pending'
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
        -- stuck_sub_reason (same logic as ecm-triage-fast.sql)
        CASE
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'CHECKOUT' AND checkout_status = 'CAPTURED' AND ftv_transaction_id IS NULL THEN 'refund_checkout_not_initiated'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'CHECKOUT' AND checkout_status IN ('REFUND_INITIATED', 'REFUND_PENDING') THEN 'refund_checkout_pending'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'LEANTECH' AND checkout_status IS NULL THEN 'refund_lean_not_initiated'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'LEANTECH' AND checkout_status IS NOT NULL THEN 'refund_lean_pending'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'UAE_MANUAL' THEN 'refund_manual_pending'
            WHEN currency_from = 'AED' AND lulu_status = 'CANCELLATION_COMPLETED' AND ftv_transaction_id IS NOT NULL AND checkout_status = 'CAPTURED' THEN 'refund_lulu_cancellation'
            WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'CANCELLATION_COMPLETED' THEN 'refund_lulu_cancellation'
            WHEN goms_order_status = 'FAILED' AND payment_status_goms = 'COMPLETED' AND ftv_transaction_id IS NULL AND lulu_status IS NULL THEN 'refund_order_failed'
            WHEN currency_from IN ('GBP', 'EUR') AND goms_order_status = 'FAILED' AND goms_sub_state = 'FAILED' THEN 'refund_order_failed'
            WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND payment_status_goms = 'COMPLETED' AND goms_sub_state = 'AWAIT_RETRY_INTENT' THEN 'gbp_await_retry_intent'
            WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND payment_status_goms = 'COMPLETED' AND goms_sub_state = 'PENDING' THEN 'gbp_pending_no_fulfillment'
            WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NULL THEN 'gbp_trm_compliance_hold'
            WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NOT NULL THEN 'gbp_trm_rfi_awaiting_customer'
            WHEN bulk_partner_exclusions = 'rda_partner' AND payout_status = 'PROCESSING' AND rfi_status IS NULL AND rda_status != 'ONHOLD' THEN 'rda_processing_no_rfi'
            WHEN bulk_partner_exclusions = 'rda_partner' AND rda_status = 'ONHOLD' AND rfi_status IS NULL THEN 'rda_onhold_no_rfi'
            WHEN bulk_partner_exclusions = 'rda_partner' AND rda_status = 'ONHOLD' AND rfi_status IS NOT NULL THEN 'rda_onhold_rfi_pending'
            WHEN bulk_partner_exclusions = 'rda_partner' AND payout_status = 'FAILED' THEN 'rda_payout_failed'
            ELSE NULL
        END AS stuck_sub_reason,
        -- RFI lifecycle timeline
        ROUND(EXTRACT(EPOCH FROM (GETDATE() - rfi_created_at::timestamp)) / 3600, 1) AS rfi_pending_hours,
        ROUND(EXTRACT(EPOCH FROM (rfi_created_at::timestamp - created_at::timestamp)) / 3600, 1) AS order_to_rfi_hours,
        ROUND(36 - EXTRACT(EPOCH FROM (GETDATE() - rfi_created_at::timestamp)) / 3600, 1) AS rfi_hours_to_rejection,

        -- Control point: who owns the blocker for refunds
        CASE
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'CHECKOUT' AND checkout_status = 'CAPTURED' AND ftv_transaction_id IS NULL THEN 'ops_initiate_checkout'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'CHECKOUT' AND checkout_status IN ('REFUND_INITIATED', 'REFUND_PENDING') THEN 'acquirer_checkout'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'LEANTECH' AND checkout_status IS NULL THEN 'ops_initiate_lean'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'LEANTECH' AND checkout_status IS NOT NULL THEN 'acquirer_lean'
            WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'UAE_MANUAL' THEN 'finops_manual'
            WHEN currency_from = 'AED' AND lulu_status = 'CANCELLATION_COMPLETED' THEN 'ops_lulu_excess'
            WHEN goms_order_status = 'FAILED' AND payment_status_goms = 'COMPLETED' AND ftv_transaction_id IS NULL THEN 'ops_no_downstream'
            WHEN currency_from IN ('GBP', 'EUR') AND goms_order_status = 'FAILED' THEN 'ops_gbp_failed'
            ELSE NULL
        END AS refund_control_point,

        -- Infra layer: which system layer is blocking (GBP pipeline)
        CASE
            WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND goms_sub_state = 'AWAIT_RETRY_INTENT' THEN 'L1_gateway_retry'
            WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND goms_sub_state = 'PENDING' THEN 'L1_gateway_fulfillment'
            WHEN currency_from IN ('GBP', 'EUR') AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NULL THEN 'L2_trm_review'
            WHEN currency_from IN ('GBP', 'EUR') AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NOT NULL THEN 'L2_trm_rfi'
            WHEN bulk_partner_exclusions = 'rda_partner' THEN 'L3_partner_rda'
            WHEN bulk_partner_exclusions = 'vda_api_partner' THEN 'L3_partner_vda'
            WHEN bulk_partner_exclusions = 'bulk_vda_partner' THEN 'L3_partner_bulk'
            ELSE NULL
        END AS gbp_infra_layer
    FROM enriched e
)
SELECT
    stuck_reason,
    COALESCE(stuck_sub_reason, 'none') AS stuck_sub_reason,
    COALESCE(refund_control_point, 'n/a') AS refund_control_point,
    COALESCE(gbp_infra_layer, 'n/a') AS gbp_infra_layer,
    currency_from AS currency,
    COUNT(*) AS order_count,
    ROUND(SUM(send_amount), 0) AS total_amount,
    ROUND(AVG(hours_diff), 1) AS avg_hours,
    SUM(CASE WHEN hours_diff > 36 THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN send_amount >= 5000 THEN 1 ELSE 0 END) AS high_value_count,
    -- RFI lifecycle (meaningful for RFI-related stuck_reasons)
    ROUND(AVG(rfi_pending_hours), 1) AS avg_rfi_pending_hours,
    SUM(CASE WHEN rfi_pending_hours IS NOT NULL AND rfi_pending_hours < 24 THEN 1 ELSE 0 END) AS rfi_under_24h,
    SUM(CASE WHEN rfi_pending_hours IS NOT NULL AND rfi_pending_hours BETWEEN 24 AND 36 THEN 1 ELSE 0 END) AS rfi_24_to_36h,
    SUM(CASE WHEN rfi_pending_hours IS NOT NULL AND rfi_pending_hours > 36 THEN 1 ELSE 0 END) AS rfi_over_36h,
    -- RFI creation delay (how long before ops/system created the RFI after order)
    ROUND(AVG(order_to_rfi_hours), 1) AS avg_order_to_rfi_delay,
    -- Auto-reject eligibility (from RFI creation, 36h window)
    SUM(CASE WHEN rfi_hours_to_rejection IS NOT NULL AND rfi_hours_to_rejection <= 0 THEN 1 ELSE 0 END) AS auto_reject_eligible_now,
    SUM(CASE WHEN rfi_hours_to_rejection IS NOT NULL AND rfi_hours_to_rejection BETWEEN 0 AND 6 THEN 1 ELSE 0 END) AS auto_reject_in_6h
FROM classified
GROUP BY 1, 2, 3, 4, 5
ORDER BY order_count DESC;
