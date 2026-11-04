---
id: { UUIDv7 }
malleability: { spec | verification | implementation; omit for implementation }
---

# {Node name}

EXPOSES {the outside-facing grammar, rendering, invocation, and protocol this surface provides}
TO {the external audience or boundary — the people, systems, or agents outside the product that use it}
SO THAT {that audience}
CAN {what they can do at this boundary}

## Assertions

- {slug}: {One sentence stating an assertion awaiting verification selection. A surface owns no product-domain semantics; a family surface states the shared audience, affordance class, packaging promise, and the contract that selects among its concrete children. Include only the groups below that apply to this node.}

### Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs.}

| Case              | {Output column}   |
| ----------------- | ----------------- |
| {short case name} | {expected result} |

### Scenario: {subject}

- {slug}: Given {context}, when {action}, then {result}.

### Conformance: {subject}

- {slug}: {Output} conforms to {standard or schema}.

### Property: {subject}

- {slug}: {Invariant} holds for all {domain}.

### Compliance: {subject}

- {slug}: ALWAYS: {observable behavior that holds} — {why}.
- {slug}: NEVER: {prohibited behavior} — {why}.

### Eval

- {slug}: ALWAYS: {LLM-driven behavior with a parseable verdict}.

### Probe

- {slug}: ALWAYS: {claim only observing the running node settles}.

### Audit

- {slug}: ALWAYS: {semantic constraint requiring judgment} — {why}.
