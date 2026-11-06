# {Decision Name}

DEFINES {term} AS {definition — one line for each term the decision owns; omit the paragraph when it owns none}

CONSTRAINS {the part of the build this decision governs}
TO {the chosen mechanism, stated as permanent truth}
SO THAT {the property the build gains, never an audience and never a restatement of the mechanism}

## Verification

- {slug}: {ALWAYS or NEVER, then one sentence stating a rule awaiting verification selection.}

### Mapping: {slug}

{One sentence mapping a finite set of inputs to their outputs.}

| Case              | {Output column}   |
| ----------------- | ----------------- |
| {short case name} | {expected result} |

### {Scenario | Conformance | Compliance}: {subject}

- {slug}: {One sentence stating the rule. A group of more than ten rules splits by subject; a group whose rules share no subject takes the heading `### {Scenario | Conformance | Compliance}`.}

### Property: {subject}

- {slug}: {One sentence stating an invariant that holds for all code the decision governs.}

### Eval: {slug}

{One sentence stating behavior of a skill, agent, or classifier whose output has a parseable contract, graded over curated cases.}

| Given                 | Then                             |
| --------------------- | -------------------------------- |
| {the input of a case} | {the verdict the producer emits} |

### Probe

- {slug}: {One sentence stating a claim about the running node that only an executed observation settles.}

### Audit

- {slug}: {One sentence stating a semantic constraint an audit skill judges, with no deterministic test or graded eval.}
