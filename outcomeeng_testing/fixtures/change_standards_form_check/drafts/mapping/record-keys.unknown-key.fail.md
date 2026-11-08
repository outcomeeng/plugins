---
title: Catalog items list in order
product: plugins
maturity: Sliced
lifecycle: Submitted
parent: null
severity: high
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

### spx/21-catalog.enabler

```diff
### Test.Compliance: listing
- - sorted: ALWAYS: the listing is sorted ([test](tests/test_catalog.mapping.l1.py))
+ - sorted: ALWAYS: the listing is sorted by name ([test](tests/test_catalog.mapping.l1.py))
```
