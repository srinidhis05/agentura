# Bulk VDA Partner Runbook

## Overview
High-value orders routed to bulk VDA partners for manual/batch processing.

**Team:** VDA_ops  
**Stuck Reasons:**
- `bulk_vda_order_within_16_hrs` — Within processing window (monitoring only)
- `bulk_vda_order_grtr_than_16_hrs` — Exceeded processing window

**Note:** These are typically filtered out of the main ECM dashboard as they have longer expected processing times.

## Applicable Partners
High-value (receive_amount > 50,000):
- SINGHAI_2025_V2
- VELTOPAYZ_V4, V5, V6

Always bulk:
- VELTOPAYZ_HVT_BULK
- VELTOPAYZ_KPR_BULK
- ARMSTRONG_PARTNER_DASHBOARD
- TANGOPE_V3

## Resolution Steps

### Step 1: Verify Bulk Classification
1. Check `receive_amount` — if > 50,000, bulk classification applies
2. Check `current_payout_partner` — should be a bulk partner
3. Check `bulk_partner_exclusions` = 'bulk_vda_partner'

### Step 2: Within 16 Hours (Monitoring)
If `bulk_vda_order_within_16_hrs`:
1. No action required — normal processing time
2. Bulk partners typically process in batches (1-2x daily)
3. Set reminder to check at 16-hour mark

### Step 3: Exceeded 16 Hours
If `bulk_vda_order_grtr_than_16_hrs`:
1. Check partner dashboard for batch status
2. Verify order is in partner's queue
3. Check for any partner-side issues

### Step 4: Escalate to Partner
If stuck > 24 hours:
1. Contact partner operations team
2. Provide transaction_id and order details
3. Request status update and ETA

### Step 5: Consider Re-routing
If partner consistently delayed:
1. Discuss with VDA ops lead
2. Consider routing to alternate partner
3. Update routing rules if systemic

### Step 6: Document
1. Record partner batch processing times
2. Note any delays and causes
3. Update ECM ticket

## Escalation
Escalate if:
- Order > 24 hours
- Partner unresponsive
- Customer escalation
- Batch processing failure

Contact: vda-lead@aspora.com or #vda-ops Slack channel
