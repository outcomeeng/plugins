---
id: { UUIDv7 }
malleability: { spec | verification | implementation; omit for implementation }
---

# {Variant name}

{The opening of the parent's kind — SUPPLIES, PROVIDES, OWNS, ADAPTS ... FOR, or EXPOSES ... TO — restating the parent's whole contract as this variant implements it}
SO THAT {the parent's consumption context}
CAN {the parent's consumer capability}

## Assertions

### Test.Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs, stating every condition the outcomes depend on.}

| Case        | {Output column}   |
| ----------- | ----------------- |
| {case-slug} | {expected result} |

### Test.Scenario: {subject specific to this implementation}

- {slug}:
  - Given {context specific to this implementation}
  - When {action}
  - Then {result}
  - And {further result}

### Test.Compliance: {subject}

- {slug}: ALWAYS {behavior this implementation guarantees beyond the contract} — {why}.
- {slug}: NEVER {prohibited behavior} — {why}.

### Probe: {subject}

- {slug}: {Claim only observing this variant running settles.}
