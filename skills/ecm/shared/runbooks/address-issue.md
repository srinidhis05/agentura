# Address Issue Runbook

## Overview
This runbook covers resolution steps for orders stuck due to address-related issues.

## Common Causes
- Missing apartment/unit number
- Postcode doesn't match city
- Incomplete address (missing street number)
- Invalid characters in address
- Address exceeds carrier character limit
- PO Box not accepted by carrier

## Resolution Steps

### Step 1: Identify the Issue
1. Check the carrier rejection reason in the shipment logs
2. Review the original customer-provided address
3. Compare against address validation service results

### Step 2: Attempt Auto-Correction
1. Run address through validation API
2. If confidence > 90%, apply suggested correction
3. Log the correction in ticket notes

### Step 3: Customer Contact (if needed)
If auto-correction not possible:
1. Send templated message via marketplace:
   ```
   Subject: Address Confirmation Needed for Order {order_id}
   
   Hi {customer_name},
   
   We're preparing your order for shipment but need to verify your 
   delivery address. Could you please confirm:
   
   - Street address (including apartment/unit if applicable)
   - City
   - Postcode
   
   Current address on file:
   {shipping_address}
   
   Please reply within 24 hours to avoid delays.
   
   Thank you!
   ```

2. Set ticket status to "Awaiting Customer"
3. Set follow-up reminder for 24 hours

### Step 4: Update and Release
Once address is verified:
1. Update address in OMS
2. Validate with carrier API
3. Release hold on order
4. Close ticket with resolution notes

## Escalation
Escalate to Shipping Supervisor if:
- Customer unresponsive after 48 hours
- Address validation consistently fails
- High-value order (> £200)

## Related Documentation
- [Address Validation API Docs](/docs/address-validation)
- [Carrier Character Limits](/docs/carrier-limits)
- [Customer Contact Templates](/templates/customer-contact)
