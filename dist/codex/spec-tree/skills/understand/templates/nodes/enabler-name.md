# {Node Name}

PROVIDES {what this enabler offers — the infrastructure, utility, or foundation}
SO THAT {which dependents use it — name the sibling nodes or categories of dependents}
CAN {what those dependents could not do without this enabler}

## Assertions

Choose exactly one verification type for each assertion. Only `[test]` assertions
carry a test assertion type. Include only headings that apply to this node.

### Scenarios

- Given {context}, when {action}, then {result} ([test](tests/{subject}.{evidence}.l1.test.{ext}))

### Mappings

- {input set} maps to {output set} ([test](tests/{subject}.{evidence}.l1.test.{ext}))

### Conformance

- {output} conforms to {standard or schema} ([test](tests/{subject}.{evidence}.l1.test.{ext}))

### Properties

- {invariant} holds for all {domain} ([test](tests/{subject}.{evidence}.l1.test.{ext}))

### Compliance

- ALWAYS: {observable behavior that holds} — {why} ([test](tests/{subject}.{evidence}.l1.test.{ext}))
- NEVER: {prohibited behavior} — {why} ([test](tests/{subject}.{evidence}.l1.test.{ext}))

### Evaluate

- {LLM-driven behavior whose structured output is scored against cases and a threshold} ([eval](evals/{rule-slug}/eval.toml))

### Audit

- ALWAYS: {semantic constraint requiring judgment} — {why} ([audit])
