---
id: { UUIDv7 }
malleability: { spec | verification | implementation; omit for implementation }
---

# {Node name}

ADAPTS {the provider — the domain or capability this interface makes consumable}
FOR {the consumption context — the medium-agnostic use the contract serves, never a consumer node or a surface by name}
SO THAT {who consumes the contract}
CAN {what they can do through its resources, verbs, selectors, payload shapes, lifecycle, and error semantics}

## Assertions

### Test.Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs, stating every condition the outcomes depend on.}

| Case        | {Output column}   |
| ----------- | ----------------- |
| {case-slug} | {expected result} |

### Test.Scenario: {subject}

- {slug}:
  - Given {context}
  - When {action}
  - Then {result}
  - And {further result}

### Test.Conformance: {subject}

- {slug}: {Output} conforms to {standard or schema}.

### Test.Property: {subject}

- {slug}: {Invariant} holds for all {domain}.

### Test.Compliance: {subject}

- {slug}: ALWAYS {observable behavior that holds} — {why}.
- {slug}: NEVER {prohibited behavior} — {why}.

### Evaluate: {slug}

{One sentence naming the producer, the context it receives, and how the eval compares an output with its expectation.}

| Case        | Input                 | Expected output                  |
| ----------- | --------------------- | -------------------------------- |
| {case-slug} | {the input of a case} | {the verdict the producer emits} |

### Probe: {subject}

- {slug}: {Claim only observing the running node settles.}

### Audit: {subject}

- {slug}: {Semantic constraint requiring judgment} — {why}.
- {slug}: {A constraint stating that the interface owns no rendering.}
