---
id: { UUIDv7 }
malleability: { spec | verification | implementation; omit for implementation }
---

# {Node name}

OWNS {the bounded semantic context — its vocabulary, rules, and invariants — that other nodes speak}
SO THAT {the consumption context — the kinds of nodes or the audience that speak it, never a consumer node by name}
CAN {what those consumers could not do without one owner of these semantics}

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
- {slug}: {The class contract: the rule this domain's children satisfy and how their contributions combine, naming no child.}
