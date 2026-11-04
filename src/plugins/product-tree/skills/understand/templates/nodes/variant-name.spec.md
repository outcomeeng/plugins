---
id: { UUIDv7 }
malleability: { spec | verification | implementation; omit for implementation }
---

# {Variant name}

{The opening of the parent's kind — SUPPLIES, PROVIDES, OWNS, ADAPTS ... FOR, or EXPOSES ... TO — restating the parent's whole contract as this variant implements it}
SO THAT {the parent's consumption context}
CAN {the parent's consumer capability}

## Assertions

- {slug}: {One sentence stating only what the parent's contract does not say. The parent's assertions are this variant's evidence too: the toolchain runs them once with the selection source set to this variant and records the results in this variant's status claim. A variant carries no outcome record. Include only the groups below that apply to this node.}

### Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs.}

| Case              | {Output column}   |
| ----------------- | ----------------- |
| {short case name} | {expected result} |

### Scenario: {subject specific to this implementation}

- {slug}: Given {context specific to this implementation}, when {action}, then {result}.

### Compliance: {subject}

- {slug}: ALWAYS: {behavior this implementation guarantees beyond the contract} — {why}.

### Probe

- {slug}: ALWAYS: {claim only observing this variant running settles}.
