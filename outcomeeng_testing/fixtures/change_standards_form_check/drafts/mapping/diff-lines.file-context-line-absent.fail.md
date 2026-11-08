---
title: Item schema types an item as text
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

- Output: The item schema types an item as text.
- Why: A schema that types an item as an object hides the text a reader sees.
- Verification: The audit at close finds the schema typing an item as text.

## Declarations

### spx/21-catalog.enabler/contracts/item.schema.json

```diff
{
  "kind": "item",
-   "type": "object"
+   "type": "string"
}
```
