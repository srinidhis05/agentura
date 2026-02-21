# Quick Diagnosis Lookup

Use this instead of parsing the full YAML. Copy-paste the diagnosis block.

## By sub_state / status

| Sub-state | Icon | Diagnosis | Fix |
|-----------|------|-----------|-----|
| `CNR_RESERVED_WAIT` | ⏳ | Checkout OK, LULU waiting | Check LULU portal, replay webhook |
| `PAYMENT_PENDING` | 🔄 | BRN not pushed | Push BRN manually |
| `PENDING` (order) | ⏳ | Waiting confirmation | Check payment + fulfillment status |
| `FAILED` (order) | ❌ | Payment failed | Check gateway, contact customer |
| `CREDITED` + `PROCESSING` | 🔄 | Status sync issue | Force sync |
| `CANCELLATION_REQUEST_CREATED` | 🔄 | Cancellation pending | Complete cancellation |
| `CANCELLATION_COMPLETED` | 💰 | Refund pending | Process refund |
| `ADDITIONAL_DOCUMENTS_REQUIRED` | 📄 | Docs needed | Create/check RFI |
| `ONHOLD` (RDA) | 📋 | RFI pending | Check KYC portal |
| `TXN_TRANSMITTED` | 🚚 | At partner | Check partner status |

## By stuck_reason

| stuck_reason | Team | Quick fix |
|--------------|------|-----------|
| `brn_issue` | Ops | Push BRN to LULU |
| `status_sync_issue` | Ops | Force status sync |
| `refund_pending` | Ops | Process refund |
| `cancellation_pending` | Ops | Complete cancellation |
| `stuck_at_lulu` | Ops | Check LULU portal |
| `stuck_at_lean_recon` | Ops | Check Leantech recon |
| `rfi_pending` / `rfi_order_*` | KYC | Check/send RFI |
| `no_rfi_created` | KYC | Create RFI |
| `stuck_at_rda_partner*` | KYC | Check RDA + RFI |
| `stuck_due_trm*` | KYC | Check TRM hold |
| `stuck_at_vda_partner` | VDA | Check VDA partner |
| `falcon_failed*` | Ops | Check Falcon, retry |
| `uncategorized` | Ops | Manual investigation |

## SLA by type

| Type | SLA |
|------|-----|
| Payment failed | 2h |
| CNR / BRN | 4h |
| RFI pending | 24h |
| Status sync | 1h |
| Default | 8h |
