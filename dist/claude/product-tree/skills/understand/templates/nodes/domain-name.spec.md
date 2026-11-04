---
id: { UUIDv7 }
malleability: { spec | verification | implementation; omit for implementation }
---

# {Node name}

OWNS {the bounded semantic context — its vocabulary, rules, and invariants — that other nodes speak}
SO THAT {the consumption context — the kinds of nodes or the audience that speak it, never a consumer node by name}
CAN {what those consumers could not do without one owner of these semantics}

## Assertions

- {slug}: {One sentence stating an assertion awaiting verification selection. A domain states its class contract — the rule its children satisfy and how their contributions combine — and names no child. Include only the groups below that apply to this node.}

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
