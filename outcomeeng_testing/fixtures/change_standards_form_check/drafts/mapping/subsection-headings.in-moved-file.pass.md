---
title: Catalog items list in order
product: plugins
maturity: Sliced
lifecycle: Submitted
parent: null
predecessors: []
blockers: []
base: {{BASE}}
priority: null
primary_value: null
investment: null
---

## Statement of Intent

- Output: The catalog lists its items in order.
- Why: A listing in no order hides the item a reader looks for.
- Verification: The audit at close finds the catalog spec stating the order.

## Declarations

### spx/54-billing.enabler/54-invoices.enabler

```diff
rename from spx/54-billing.enabler/54-invoices.enabler
rename to spx/54-billing.enabler/55-invoices.enabler
```

### spx/54-billing.enabler/55-invoices.enabler/contracts/invoice.schema.json

```diff
{
-   "type": "object"
+   "type": "object",
+   "required": []
}
```
