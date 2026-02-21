# Out of Stock Runbook

## Overview
This runbook covers resolution steps for orders stuck due to inventory unavailability.

## Common Scenarios
- SKU out of stock at assigned warehouse
- Inventory available at alternate location
- Supplier backorder
- Discontinued item
- Inventory discrepancy (system vs. physical)

## Resolution Steps

### Step 1: Verify Inventory Status
1. Check inventory across ALL warehouses:
   ```sql
   SELECT warehouse_id, quantity_available, quantity_reserved
   FROM inventory.stock_levels
   WHERE sku = '{sku}'
   AND quantity_available > 0;
   ```
2. Check if item is on incoming PO
3. Verify supplier lead time

### Step 2: Determine Resolution Path

#### If Available at Another Warehouse:
1. Calculate shipping cost difference
2. If cost increase < 15%, initiate cross-dock transfer
3. Update order with new fulfillment location
4. Adjust expected delivery date
5. Close ticket

#### If On Incoming PO:
1. Check PO expected arrival date
2. If arrival < 5 days:
   - Hold order
   - Send proactive delay notification to customer
   - Set follow-up for PO arrival date
3. If arrival > 5 days:
   - Proceed to customer contact

#### If Truly Out of Stock:
1. Check for substitute SKUs:
   ```sql
   SELECT * FROM catalog.product_substitutes
   WHERE original_sku = '{sku}'
   AND substitute_available = true;
   ```
2. Contact customer with options

### Step 3: Customer Contact
Send options message:
```
Subject: Update on Your Order {order_id}

Hi {customer_name},

Unfortunately, {product_name} is currently out of stock.

We'd like to offer you the following options:

1. Wait for restock (estimated: {restock_date})
2. Accept a similar item: {substitute_name} (same price)
3. Receive a full refund

Please reply with your preference, or we'll process a 
refund in 48 hours if we don't hear from you.

We apologize for any inconvenience.

Thank you for your patience!
```

### Step 4: Process Customer Response
- **Option 1 (Wait)**: Update order status, set restock follow-up
- **Option 2 (Substitute)**: Swap SKU, update order, release
- **Option 3 (Refund)**: Process refund, cancel order
- **No Response**: Auto-refund after 48 hours

## Inventory Discrepancy
If system shows stock but warehouse reports none:
1. Create inventory adjustment ticket
2. Notify Warehouse Manager
3. Follow "Truly Out of Stock" path for customer

## Escalation
Escalate to Inventory Manager if:
- High-value item (> £300)
- Recurring OOS for same SKU (> 3x in 30 days)
- Bulk order affected
- Customer is repeat offender cancellation

## Related Documentation
- [Inventory Dashboard](/tools/inventory)
- [Cross-Dock Process](/docs/cross-dock)
- [Product Substitution Matrix](/docs/substitutes)
