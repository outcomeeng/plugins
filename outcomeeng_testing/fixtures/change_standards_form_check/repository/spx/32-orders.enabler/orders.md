---
id: 01a1b95b-0000-7000-8000-000000000003
malleability: verification
---

# Orders

PROVIDES orders
SO THAT buyers
CAN buy an item

## Assertions

### Test.Compliance: shipping

- shipped: ALWAYS: an order ships once paid ([test](tests/test_orders.compliance.l1.py))
- refunded: NEVER: an order refunds twice ([test](tests/test_orders.compliance.l1.py))
