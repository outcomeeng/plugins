# Billing

PROVIDES billing
SO THAT buyers
CAN pay for an order

The orders live in spx/32-orders.enabler and bill through it.

## Assertions

### Test.Compliance: invoicing

- invoiced: ALWAYS: an invoice is issued
- voided: NEVER: an invoice is voided twice
