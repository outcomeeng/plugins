# {Decision Name}

DEFINES {term} AS {definition — one line for each term the decision owns; omit the paragraph when it owns none}

GOVERNS {the product behavior this decision governs, stated as permanent truth}
SO THAT {who relies on it}
CAN RELY ON {the user-observable behavior, not implementation}

## Verification

- {slug}: {ALWAYS or NEVER, then one sentence stating a rule awaiting verification selection.}

### Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs.}

| Case              | {Output column}   |
| ----------------- | ----------------- |
| {short case name} | {expected result} |

### {Scenario | Conformance | Property | Compliance}: {subject}

- {slug}: {One sentence stating the rule. A group of more than seven rules splits by subject; a group whose rules share no subject takes the heading `### {Scenario | Conformance | Property | Compliance}`.}

### Eval

- {slug}: {One sentence stating behavior of a skill, agent, or classifier whose output has a parseable contract, graded over curated cases.}

### Probe

- {slug}: {One sentence stating a claim about the running node that only an executed observation settles.}

### Audit

- {slug}: {One sentence stating a semantic constraint an audit skill judges, with no deterministic test or graded eval.}
