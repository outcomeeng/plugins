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

### new enabler `60-shipping`, between `21-catalog.enabler` and `32-orders.enabler`

```yaml
malleability: spec
```

```diff
+ PROVIDES shipping
+ SO THAT buyers
+ CAN ship
```
