---
title: Item schema titles an item
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

- Output: The item schema titles an item.
- Why: A schema with no title hides the name a reader looks for.
- Verification: The audit at close finds the schema titling an item.

## Declarations

### spx/21-catalog.enabler/contracts/item.schema.json

```diff
{
+   "title": "item",
   "type": "object"
}
```
