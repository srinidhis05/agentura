-- ECM Triage Query (FAST - Optimized for Agent Gateway)
-- Based on Metabase SOP logic but re-engineered for MCP 30s timeout
--
-- ARCHITECTURE: 3-stage pipeline (run separately, each < 10s)
--   Stage 1: ecm-pending-list.sql (orders_goms only, no JOINs) → candidate order_ids
--   Stage 2: THIS QUERY per order_id → stuck_reason + enrichment
--   Stage 3: Priority scoring computed in-agent (knowledge-graph.yaml formula)
--
-- WHY NOT analytics_orders_master_data?
--   - It's a VIEW (not a table) that joins 10+ tables internally
--   - When combined with our LEFT JOINs, it creates a 15-table join → 60s+ execution
--   - orders_goms IS the base table; analytics_orders_master_data wraps it
--
-- USAGE: Replace {order_id} with actual order ID (or comma-separated list for batch)

WITH order_base AS (
    SELECT
        og.order_id,
        og.owner_id,
        og.status AS goms_order_status,
        og.sub_state AS goms_sub_state,
        og.meta_postscript_pricing_info_send_currency AS currency_from,
        og.meta_postscript_pricing_info_send_amount AS send_amount,
        og.meta_postscript_pricing_info_receive_amount AS receive_amount,
        og.meta_postscript_acquirer AS payment_acquirer,
        og.created_at,
        og.updated_at,
        ROUND(EXTRACT(EPOCH FROM (GETDATE() - og.created_at::timestamp)) / 3600, 1) AS hours_diff,
        CASE
            WHEN EXTRACT(EPOCH FROM (GETDATE() - og.created_at::timestamp)) / 3600 BETWEEN 12 AND 24 THEN '12_hr_bucket'
            WHEN EXTRACT(EPOCH FROM (GETDATE() - og.created_at::timestamp)) / 3600 BETWEEN 24 AND 48 THEN '24_hr_bucket'
            WHEN EXTRACT(EPOCH FROM (GETDATE() - og.created_at::timestamp)) / 3600 > 48 THEN '48_hr_bucket'
            ELSE '0_bucket'
        END AS time_bucket
    FROM orders_goms og
    WHERE og.order_id = '{order_id}'
),

-- Payment status from GOMS payments (latest completed)
latest_payment_goms AS (
    SELECT reference_id, payment_status
    FROM (
        SELECT reference_id, payment_status,
               ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM payments_goms
        WHERE payment_status = 'COMPLETED'
          AND reference_id = '{order_id}'
    ) pg
    WHERE rn = 1
),

-- Falcon transaction
falcon AS (
    SELECT transaction_id, status AS falcon_status, client_txn_id
    FROM falcon_transactions_v2
    WHERE client_txn_id = '{order_id}'
),

-- Latest payout (uses falcon transaction_id)
latest_payout AS (
    SELECT transaction_id, status, payout_partner, updated_at
    FROM (
        SELECT transaction_id, status, payout_partner, updated_at,
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY COALESCE(updated_at, created_at) DESC) AS rn
        FROM transaction_payout
        WHERE transaction_id IN (SELECT transaction_id FROM falcon)
    ) tp
    WHERE rn = 1
),

-- Lulu data (AED orders only)
lulu AS (
    SELECT order_id, sub_status, lulu_client, status AS lulu_main_status
    FROM lulu_data
    WHERE order_id = '{order_id}'
),

-- RFI data
rfi AS (
    SELECT reference_id, status AS rfi_status, modified_at AS rfi_modified_at,
           created_at AS rfi_created_at, rfitype
    FROM transfer_rfi
    WHERE reference_id = '{order_id}'
),

-- UAE manual payment
uae_manual AS (
    SELECT order_id, status
    FROM uae_manual_payments
    WHERE order_id = '{order_id}'
),

-- Checkout payment
checkout AS (
    SELECT order_id, status
    FROM checkout_payment_data
    WHERE order_id = '{order_id}'
),

-- Fulfillment GOMS (for TRM time diff)
fulfillment AS (
    SELECT order_id,
           DATEDIFF(SECOND, created_at, updated_at) AS goms_trm_time_diff_sec
    FROM fulfillments_goms
    WHERE order_id = '{order_id}'
),

-- RDA fulfillment (uses falcon transaction_id)
rda AS (
    SELECT order_id, status
    FROM rda_fulfillments
    WHERE order_id IN (SELECT transaction_id FROM falcon)
),

-- Enriched (assemble all data)
enriched AS (
    SELECT
        ob.*,
        pg.payment_status AS payment_status_goms,
        f.falcon_status,
        f.transaction_id AS ftv_transaction_id,
        l.sub_status AS lulu_status,
        l.lulu_client,
        tp.status AS payout_status,
        tp.payout_partner AS current_payout_partner,
        r.rfi_status,
        r.rfi_modified_at,
        r.rfi_created_at,
        r.rfitype AS rfi_type,
        um.status AS uae_manual_payment_status,
        c.status AS checkout_status,
        fg.goms_trm_time_diff_sec,
        rd.status AS rda_status,
        -- Bulk partner classification
        CASE
            WHEN ob.receive_amount > 50000 AND tp.payout_partner IN ('SINGHAI_2025_V2', 'VELTOPAYZ_V4', 'VELTOPAYZ_V5', 'VELTOPAYZ_V6') THEN 'bulk_vda_partner'
            WHEN tp.payout_partner IN ('VELTOPAYZ_HVT_BULK', 'VELTOPAYZ_KPR_BULK', 'ARMSTRONG_PARTNER_DASHBOARD', 'TANGOPE_V3') THEN 'bulk_vda_partner'
            WHEN tp.payout_partner = 'VANCE_RDA' THEN 'rda_partner'
            WHEN tp.payout_partner IS NOT NULL THEN 'vda_api_partner'
            ELSE NULL
        END AS bulk_partner_exclusions,
        -- Data freshness indicator for RFI
        CASE
            WHEN r.rfi_modified_at IS NOT NULL
                 AND EXTRACT(EPOCH FROM (GETDATE() - r.rfi_modified_at::timestamp)) / 3600 > 4
            THEN true
            ELSE false
        END AS rfi_data_stale
    FROM order_base ob
    LEFT JOIN latest_payment_goms pg ON pg.reference_id = ob.order_id
    LEFT JOIN falcon f ON f.client_txn_id = ob.order_id
    LEFT JOIN lulu l ON l.order_id = ob.order_id
    LEFT JOIN latest_payout tp ON tp.transaction_id = f.transaction_id
    LEFT JOIN rfi r ON r.reference_id = ob.order_id
    LEFT JOIN uae_manual um ON um.order_id = ob.order_id
    LEFT JOIN checkout c ON c.order_id = ob.order_id
    LEFT JOIN fulfillment fg ON fg.order_id = ob.order_id
    LEFT JOIN rda rd ON rd.order_id = f.transaction_id
)

SELECT
    e.*,

    -- ========== RFI TIMELINE (hours-based, NULL when no RFI) ==========
    ROUND(EXTRACT(EPOCH FROM (GETDATE() - e.rfi_created_at::timestamp)) / 3600, 1) AS rfi_pending_hours,
    ROUND(EXTRACT(EPOCH FROM (e.rfi_created_at::timestamp - e.created_at::timestamp)) / 3600, 1) AS order_to_rfi_hours,
    ROUND(36 - EXTRACT(EPOCH FROM (GETDATE() - e.rfi_created_at::timestamp)) / 3600, 1) AS rfi_hours_to_rejection,
    ROUND(36 - e.hours_diff, 1) AS order_hours_to_rejection,

    -- ========== STUCK REASON (Metabase SOP logic — verified) ==========
    CASE
        -- AED-specific rules
        WHEN currency_from = 'AED' AND lulu_client = 'LULU' AND lulu_status = 'CREDITED' AND goms_order_status = 'PROCESSING_DEAL_IN' THEN 'status_sync_issue'
        WHEN goms_order_status = 'COMPLETED' AND falcon_status = 'FAILED' THEN 'falcon_failed_order_completed_issue'
        WHEN currency_from = 'AED' AND payment_acquirer = 'LEANTECH' AND lulu_status = 'PAYMENT_PENDING' THEN 'stuck_at_lean_recon'
        WHEN currency_from = 'AED' AND payment_acquirer = 'CHECKOUT' AND lulu_status = 'PAYMENT_PENDING' THEN 'brn_issue'
        WHEN currency_from = 'AED' AND payment_acquirer IN ('UAE_MANUAL', 'LEANTECH') AND uae_manual_payment_status = 'RECONCILED' AND lulu_status = 'PAYMENT_PENDING' THEN 'brn_issue'
        WHEN currency_from = 'AED' AND payment_acquirer IN ('UAE_MANUAL', 'LEANTECH') AND uae_manual_payment_status = 'RECONCILED' AND lulu_status IS NULL THEN 'brn_issue'
        WHEN currency_from = 'AED' AND payment_acquirer IN ('UAE_MANUAL', 'LEANTECH') AND uae_manual_payment_status = 'RECONCILED' AND lulu_status = 'CREATED' THEN 'brn_issue'
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

    -- ========== STUCK SUB-REASON (granular bifurcation within stuck_reason) ==========
    CASE
        -- Refund sub-reasons (when order qualifies as refund_pending)
        WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'CHECKOUT' AND checkout_status = 'CAPTURED' AND ftv_transaction_id IS NULL THEN 'refund_checkout_not_initiated'
        WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'CHECKOUT' AND checkout_status IN ('REFUND_INITIATED', 'REFUND_PENDING') THEN 'refund_checkout_pending'
        WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'LEANTECH' AND checkout_status IS NULL THEN 'refund_lean_not_initiated'
        WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'LEANTECH' AND checkout_status IS NOT NULL THEN 'refund_lean_pending'
        WHEN goms_order_status = 'FAILED' AND payment_acquirer = 'UAE_MANUAL' THEN 'refund_manual_pending'
        WHEN currency_from = 'AED' AND lulu_status = 'CANCELLATION_COMPLETED' AND ftv_transaction_id IS NOT NULL AND checkout_status = 'CAPTURED' THEN 'refund_lulu_cancellation'
        WHEN currency_from = 'AED' AND goms_order_status != 'FAILED' AND lulu_status = 'CANCELLATION_COMPLETED' THEN 'refund_lulu_cancellation'
        WHEN goms_order_status = 'FAILED' AND payment_status_goms = 'COMPLETED' AND ftv_transaction_id IS NULL AND lulu_status IS NULL THEN 'refund_order_failed'
        WHEN currency_from IN ('GBP', 'EUR') AND goms_order_status = 'FAILED' AND goms_sub_state = 'FAILED' THEN 'refund_order_failed'

        -- GBP payment sub-reasons (stuck_due_to_payment_issue_goms)
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND payment_status_goms = 'COMPLETED' AND goms_sub_state = 'AWAIT_RETRY_INTENT' THEN 'gbp_await_retry_intent'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NULL AND payment_status_goms = 'COMPLETED' AND goms_sub_state = 'PENDING' THEN 'gbp_pending_no_fulfillment'

        -- GBP TRM sub-reasons (stuck_due_trm)
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NULL THEN 'gbp_trm_compliance_hold'
        WHEN currency_from IN ('GBP', 'EUR') AND ftv_transaction_id IS NULL AND goms_trm_time_diff_sec IS NOT NULL AND rfi_status IS NOT NULL THEN 'gbp_trm_rfi_awaiting_customer'

        -- RDA partner sub-reasons
        WHEN bulk_partner_exclusions = 'rda_partner' AND payout_status = 'PROCESSING' AND rfi_status IS NULL AND rda_status != 'ONHOLD' THEN 'rda_processing_no_rfi'
        WHEN bulk_partner_exclusions = 'rda_partner' AND rda_status = 'ONHOLD' AND rfi_status IS NULL THEN 'rda_onhold_no_rfi'
        WHEN bulk_partner_exclusions = 'rda_partner' AND rda_status = 'ONHOLD' AND rfi_status IS NOT NULL THEN 'rda_onhold_rfi_pending'
        WHEN bulk_partner_exclusions = 'rda_partner' AND payout_status = 'FAILED' THEN 'rda_payout_failed'

        ELSE NULL
    END AS stuck_sub_reason,

    -- ========== TEAM DEPENDENCY ==========
    CASE
        WHEN currency_from = 'AED' AND lulu_client = 'LULU' AND lulu_status = 'CREDITED' AND goms_order_status = 'PROCESSING_DEAL_IN' THEN 'Ops'
        WHEN goms_order_status = 'COMPLETED' AND falcon_status = 'FAILED' THEN 'Ops'
        WHEN currency_from = 'AED' AND lulu_status = 'PAYMENT_PENDING' THEN 'Ops'
        WHEN currency_from = 'AED' AND uae_manual_payment_status = 'RECONCILED' THEN 'Ops'
        WHEN rfi_status IS NOT NULL THEN 'KYC_ops'
        WHEN rda_status = 'ONHOLD' AND rfi_status IS NULL THEN 'KYC_ops'
        WHEN goms_trm_time_diff_sec IS NOT NULL THEN 'KYC_ops'
        WHEN bulk_partner_exclusions = 'bulk_vda_partner' THEN 'VDA_ops'
        WHEN bulk_partner_exclusions = 'vda_api_partner' THEN 'VDA_ops'
        ELSE 'Ops'
    END AS team_dependency,

    -- ========== CATEGORY ==========
    CASE
        WHEN hours_diff < 12 THEN 'level_zero'
        WHEN hours_diff BETWEEN 12 AND 24 THEN 'warning'
        WHEN hours_diff BETWEEN 24 AND 36 THEN 'action_required'
        WHEN hours_diff > 36 THEN 'critical'
    END AS category,

    -- ========== ACTIONABILITY FLAG (disqualification check) ==========
    -- Orders that fail this check should NOT be assigned to agents
    CASE
        -- D1: Abandoned payment — never completed, no downstream progression
        WHEN payment_status_goms IN ('CREATED', 'INITIATED') AND ftv_transaction_id IS NULL THEN false
        WHEN payment_status_goms IS NULL AND ftv_transaction_id IS NULL AND lulu_status IS NULL THEN false
        -- D4: AWAIT_RETRY_INTENT but payment never completed
        WHEN goms_sub_state = 'AWAIT_RETRY_INTENT' AND payment_status_goms != 'COMPLETED' THEN false
        ELSE true
    END AS is_actionable,

    -- ========== DISQUALIFICATION REASON (for reporting) ==========
    CASE
        WHEN payment_status_goms IN ('CREATED', 'INITIATED') AND ftv_transaction_id IS NULL THEN 'abandoned_payment'
        WHEN payment_status_goms IS NULL AND ftv_transaction_id IS NULL AND lulu_status IS NULL THEN 'dead_order'
        WHEN goms_sub_state = 'AWAIT_RETRY_INTENT' AND payment_status_goms != 'COMPLETED' THEN 'abandoned_retry'
        ELSE NULL
    END AS disqualification_reason

FROM enriched e;
