# Python Workflow

PROVIDES operational Python workflows for implementation, remediation, code review, test review, and architecture review
SO THAT Python products using spec-tree
CAN turn specs, decisions, and test standards into source changes that survive adversarial audit

## Assertions

### Compliance

- ALWAYS: Python implementation work starts from complete spec-tree context, governing ADRs/PDRs, and lower-index Python standards — code follows declared product truth rather than local precedent ([audit])
- ALWAYS: Python coding workflows distinguish discovery from authority — code search locates artifacts to reuse, while specs, decisions, local instructions, and skills decide how the work is done ([audit])
- ALWAYS: implementation and remediation workflows keep source changes aligned with Python architecture standards, product validation commands, and Python test standards — lower-index enablers provide the rules this workflow consumes ([audit])
- ALWAYS: Python code uses strict type annotations, typed boundaries for unknown input, source-owned vocabulary, and injected side-effect dependencies — source modules expose contracts that callers and tests can observe without replacement mocks ([audit])
- ALWAYS: a rendered artifact (YAML, HCL, JSON, IaC template, shell) is downstream of the Python module that renders or consumes it — that module owns the artifact's labels, keys, paths, and tokens, and every production consumer imports them rather than hand-writing them; container keys and set or tuple members are vocabulary that follows source ownership, while only values may be synthetic at the call site ([audit])
- ALWAYS: Python test changes load the Python testing standard and route evidence through the selected assertion type and execution level — implementation workflows do not redeclare testing policy locally ([audit])
- ALWAYS: Python audit and remediation workflows run repository-canonical validation, inspect behavior through source comprehension and evidence quality, update every affected artifact in the same concern, and rerun verification before reporting readiness ([audit])
- NEVER: preserve legacy aliases, compatibility shims, parallel APIs, or style-only approvals — Python artifacts satisfy the governing spec, use the active source contract, and meet the evidence model that applies to them ([audit])
