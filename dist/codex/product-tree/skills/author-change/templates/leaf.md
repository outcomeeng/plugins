---
title: <the intended Output, in at most 15 words>
product: <one Product>
maturity: Proposed
lifecycle: <Submitted for a Change with no Parent, Available for a Child>
parent: <owner/repo#N, or null>
predecessors: []
blockers: []
base: <full head commit of the default branch the Declarations read>
priority: <null, or the Parent's Priority for a Child>
primary_value: null
investment: null
---

## Statement of Intent

- Output: <the Output the Change achieves>
- Why: <the truth the work brings a lower layer up to, what the Operator settled by judgment, the question a prototype answers, or the Output and the condition it moves; with the observed state that gave rise to the Change where one exists>
- Verification: <the verification that shows the Output achieved, by its type, and what it finds>

## Declarations

### <spx/... path of an existing Node or Decision Record at the Base>

```diff
  <a heading the Change keeps>
- <a row as the Base holds it>
+ <the row as the file holds it after the Change>
```

### <spx/.../NN-<slug>.<kind> for a new Node>

Depends on: <`spx/...` sibling paths, or none>

```yaml
malleability: <spec, verification, or implementation>
```

```diff
+ # <Title>
+ <the opening, one line per keyword>
+ ## Assertions
+ ### <assertion type>: <subject>
+ - <slug>: <one sentence>
```

Infrastructure: <slug> <`spx/...` Node paths, or none>
