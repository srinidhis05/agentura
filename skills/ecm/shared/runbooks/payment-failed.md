# Payment Failed Runbook

## Overview
This runbook covers resolution steps for orders stuck due to payment processing failures.

## Common Causes
- Card declined (insufficient funds, expired, blocked)
- Gateway timeout/error
- 3D Secure authentication failed
- Currency conversion issue
- Fraud detection triggered
- Bank authorization hold

## Error Code Reference
| Code | Meaning | Action |
|------|---------|--------|
| `DECLINED_INSUFFICIENT` | Insufficient funds | Request payment update |
| `DECLINED_EXPIRED` | Card expired | Request payment update |
| `DECLINED_BLOCKED` | Card blocked by bank | Request alternative payment |
| `GATEWAY_TIMEOUT` | Processing timeout | Retry payment |
| `3DS_FAILED` | Authentication failed | Request payment update |
| `FRAUD_SUSPECTED` | Fraud flags triggered | Escalate to Finance |

## Resolution Steps

### Step 1: Check Payment Gateway Logs
1. Access payment gateway dashboard
2. Locate transaction by order ID
3. Note the specific error code and timestamp
4. Check if multiple attempts were made

### Step 2: Determine Action Based on Error

#### For Card Declined:
1. Send payment update request to customer:
   ```
   Subject: Payment Update Required - Order {order_id}
   
   Hi {customer_name},
   
   We were unable to process your payment for order {order_id}.
   
   Please update your payment method to complete your order:
   [Update Payment Link]
   
   If you have questions about this charge, please contact 
   your bank.
   
   Your order will be held for 7 days.
   
   Thank you!
   ```
2. Set ticket to "Awaiting Customer"
3. Set 48-hour follow-up

#### For Gateway Timeout:
1. Wait 15 minutes (avoid duplicate charges)
2. Verify no successful transaction exists
3. Retry payment processing
4. If retry fails, contact gateway support

#### For Fraud Suspected:
1. DO NOT retry payment
2. Escalate to Finance team immediately
3. Add "FRAUD_REVIEW" tag to ticket

### Step 3: After Successful Payment
1. Verify funds captured (not just authorized)
2. Release order for fulfillment
3. Update ticket with transaction ID
4. Close ticket

## Refund Scenarios
If customer requests cancellation:
1. Check if payment was captured
2. If authorized only: void authorization
3. If captured: process full refund
4. Update ticket and close

## Escalation
Escalate to Finance if:
- Fraud suspected
- Refund > £500
- Payment disputes/chargebacks
- Gateway errors persisting > 2 hours

## Related Documentation
- [Payment Gateway Dashboard](/tools/payment-gateway)
- [Refund Process](/docs/refunds)
- [Fraud Detection Guidelines](/docs/fraud-detection)
