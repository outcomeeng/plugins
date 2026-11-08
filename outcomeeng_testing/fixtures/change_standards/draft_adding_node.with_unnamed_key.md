---
title: Add the third example Node
product: example
maturity: Framed
lifecycle: Submitted
parent: null
predecessors: []
blockers: []
base: ccebeceeefd036736dbded2c2072a6a2d5aed977
priority: null
primary_value: null
investment: null
reviewer: null
---

## Statement of Intent

- Output: A third example Node between the first and the second.
- Why: The example tree needs one more Node so that a Draft can add it.
- Verification: A reachability test judges this Draft and finds it passing.

## Declarations

### new enabler `third`, between `21-first.enabler` and `55-second.enabler`

```yaml
malleability: spec
```

```diff
+ PROVIDES the third example behavior
+ SO THAT the example tree holds one more Node
+ CAN judge a Draft that adds a Node
+ ### Compliance: third
+ - third-rule: ALWAYS: the third holds.
```
