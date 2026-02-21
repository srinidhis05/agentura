# Carrier Exception Runbook

## Overview
This runbook covers resolution steps for orders stuck due to carrier/shipping exceptions.

## Common Exception Types
| Code | Description | Typical Resolution |
|------|-------------|-------------------|
| `ADDR_UNDELIVERABLE` | Address not found | Coordinate re-attempt with correct address |
| `RECIPIENT_UNAVAILABLE` | No one to receive | Schedule re-delivery |
| `DAMAGED_IN_TRANSIT` | Package damaged | Return & replace |
| `CUSTOMS_HOLD` | Held at customs | Provide documentation |
| `WEATHER_DELAY` | Weather-related delay | Wait & notify customer |
| `LOST_IN_TRANSIT` | Package lost | File claim & replace |

## Resolution Steps

### Step 1: Get Exception Details
1. Check carrier tracking portal
2. Note exception code and timestamp
3. Identify current package location
4. Check for delivery attempt history

### Step 2: Exception-Specific Resolution

#### Address Undeliverable
1. Contact carrier to confirm issue
2. Get specific reason (wrong postcode, no such address, etc.)
3. Follow [Address Issue Runbook](./address-issue.md)
4. Request carrier hold at depot if address being corrected

#### Recipient Unavailable
1. Check delivery attempt count
2. If < 3 attempts:
   - Contact customer to arrange re-delivery
   - Provide carrier's re-delivery scheduling link
3. If 3+ attempts:
   - Initiate return to sender
   - Contact customer about re-shipment or refund

#### Damaged in Transit
1. Request photos from carrier if available
2. File damage claim with carrier
3. Initiate replacement shipment immediately
4. DO NOT wait for claim resolution
5. Contact customer proactively:
   ```
   Subject: Replacement on the Way - Order {order_id}
   
   Hi {customer_name},
   
   We've been notified that your package was damaged during 
   shipping. We're so sorry about this!
   
   Good news: We've already shipped a replacement, which 
   should arrive by {new_eta}.
   
   New tracking number: {new_tracking}
   
   No action needed on your part. Thank you for your patience!
   ```

#### Customs Hold
1. Check required documentation
2. Contact customer for any needed info (ID, tax forms)
3. Submit documentation to carrier
4. Update customer on timeline
5. Monitor daily until cleared

#### Lost in Transit
1. Confirm with carrier (no tracking update > 7 days domestic, > 14 days international)
2. File lost package claim
3. Ship replacement immediately
4. Contact customer with new tracking

### Step 3: Update Customer
Always update customer with:
- What happened
- What we're doing about it
- New expected delivery date
- Any action they need to take

### Step 4: Close Ticket
Include in resolution notes:
- Exception type
- Resolution action taken
- Carrier claim reference (if applicable)
- New tracking number (if reshipped)
- Customer communication summary

## Carrier Contact Quick Reference
| Carrier | Support Line | Portal |
|---------|--------------|--------|
| Royal Mail | 0345 774 0740 | royalmail.com/track |
| DPD | 0121 275 0500 | dpd.co.uk |
| Hermes | 0330 808 5456 | myhermes.co.uk |
| UPS | 0345 787 7877 | ups.com |
| FedEx | 0345 600 0068 | fedex.com |

## Escalation
Escalate to Shipping Manager if:
- High-value shipment (> £500)
- Multiple exceptions on same order
- Carrier dispute
- International customs complexity
- Customer threatening chargeback

## Related Documentation
- [Carrier Portal Access](/tools/carrier-portals)
- [Claims Process](/docs/carrier-claims)
- [Reshipping Policy](/docs/reship-policy)
