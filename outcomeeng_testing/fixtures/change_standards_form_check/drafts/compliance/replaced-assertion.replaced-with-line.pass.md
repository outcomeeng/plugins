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

### spx/54-billing.enabler/billing.md

```diff
### Test.Compliance: invoicing
- - invoiced: ALWAYS: an invoice is issued
+ - invoiced: ALWAYS: an invoice is issued within a day
```

Infrastructure: invoiced none
