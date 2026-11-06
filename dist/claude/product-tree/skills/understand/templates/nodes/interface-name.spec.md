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

- {slug}: {One sentence stating an assertion awaiting verification selection. An interface owns no rendering. Include only the groups below that apply to this node.}

### Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs.}

| Case              | {Output column}   |
| ----------------- | ----------------- |
| {short case name} | {expected result} |

### Conformance: {subject}

- {slug}: {Output} conforms to {standard or schema}.

### Scenario: {subject}

- {slug}: Given {context}, when {action}, then {result}.

### Property: {subject}

- {slug}: {Invariant} holds for all {domain}.

### Compliance: {subject}

- {slug}: ALWAYS: {observable behavior that holds} — {why}.
- {slug}: NEVER: {prohibited behavior} — {why}.

### Eval: {slug}

{One sentence stating LLM-driven behavior with a parseable verdict, graded over curated cases.}

| Given                 | Then                             |
| --------------------- | -------------------------------- |
| {the input of a case} | {the verdict the producer emits} |

### Probe

- {slug}: ALWAYS: {claim only observing the running node settles}.

### Audit

- {slug}: ALWAYS: {semantic constraint requiring judgment} — {why}.
