-- Lulu Pending Transactions – Non-Terminal States
-- SOP Reference: Lulu SOP § 3.4 Pending Transactions – Non-Terminal States
-- Use: Identify transactions not in COMPLETED or REJECTED; share with Lulu if peak (>50).
-- Recipient: agent.support@pearldatadirect.com

-- Parameters: replace date range as needed (e.g. created_at BETWEEN '2025-01-01' AND '2025-02-17')

-- Explicit columns (no lulu_data.*) for better Redshift scan performance
SELECT
    l.order_id,
    l.status,
    l.sub_status,
    l.lulu_client,
    l.created_at AS lulu_created_at,
    l.updated_at AS lulu_updated_at,
    o.payment_acquirer,
    DATE(o.created_at) AS created_date
FROM lulu_data l
LEFT JOIN orders o ON o.order_id = l.order_id
LEFT JOIN leantech_data ld ON o.id = ld.order_id
WHERE o.created_at BETWEEN '{start_date}' AND '{end_date}'
  AND l.status NOT IN ('COMPLETED', 'REJECTED')
  AND l.lulu_client = 'LULU'
  AND o.payment_acquirer != 'UAE_MANUAL'
  AND (
    (ld.status = 'ACCEPTED_BY_BANK')
    OR (o.payment_acquirer = 'CHECKOUT' AND o.order_status = 'PROCESSING_DEAL_IN')
  )
ORDER BY o.created_at DESC;
