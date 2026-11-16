# {Decision Name}

DEFINES {term} AS {definition — one line for each term the decision owns; omit the line when it owns none}

GOVERNS {the product behavior this decision governs, stated as permanent truth}
SO THAT {who relies on it}
CAN RELY ON {the user-observable behavior, not implementation}

## Verification

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

- {slug}: {One sentence stating that an output conforms to a standard or schema. A group of more than ten rules splits by subject; a group whose rules share no subject takes the heading `### Test.Conformance`.}

### Test.Property: {subject}

- {slug}: {One sentence stating an invariant that holds for all code the decision governs.}

### Test.Compliance: {subject}

- {slug}: {ALWAYS or NEVER, then one sentence stating a behavior that holds or is prohibited.}

### Evaluate: {slug}

{One sentence naming the producer, the context it receives, and how the eval compares an output with its expectation.}

| Case        | Input                 | Expected output                  |
| ----------- | --------------------- | -------------------------------- |
| {case-slug} | {the input of a case} | {the verdict the producer emits} |

### Audit: {subject}

- {slug}: {One sentence stating a semantic constraint an audit skill judges, with no deterministic test or graded eval.}
