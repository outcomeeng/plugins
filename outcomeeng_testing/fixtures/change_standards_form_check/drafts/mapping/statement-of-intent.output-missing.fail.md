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

- Why: Order helps readers.
- Verification: The audit finds it.

## Declarations

### spx/21-catalog.enabler

```diff
### Test.Compliance: listing
- - sorted: ALWAYS: the listing is sorted ([test](tests/test_catalog.mapping.l1.py))
+ - sorted: ALWAYS: the listing is sorted by name ([test](tests/test_catalog.mapping.l1.py))
```
