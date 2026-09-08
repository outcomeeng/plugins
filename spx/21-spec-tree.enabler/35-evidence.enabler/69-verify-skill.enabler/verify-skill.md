# Verify Skill

PROVIDES verification-type selection and evidence-work orchestration from one assertion or canonical spec-tree scope
SO THAT authoring, applying, architecture, test-auditing, and evidence-maintenance workflows
CAN route every assertion to test, evaluate, probe, or audit before a specialist chooses lower-level evidence details

## Assertions

### Scenarios

- Given an assertion whose real subject produces deterministic behavior, structured producer output, a claim only an executed observation of the running node settles, or no deterministic verdict, when `/verify` classifies it, then the assertion routes respectively to `/test`, `/eval`, a probe protocol link, or an audit requirement ([eval](evals/routing/eval.toml))

### Mappings

- The verification types map to one specialist result: test maps to `/test`, evaluate maps to `/eval`, probe maps to the protocol link or the missing probe-authoring capability, and audit maps to the applicable isolated-verifier requirement ([eval](evals/routing/eval.toml))

### Compliance

- ALWAYS: select from exactly test, evaluate, probe, and audit by the verdict the real assertion subject can produce ([eval](evals/routing/eval.toml))
- ALWAYS: test assertion typing occurs only after test is selected ([audit])
- ALWAYS: report a missing selected specialist as an explicit capability gap ([eval](evals/routing/eval.toml))
- NEVER: recognize, name, alias, or translate any tag outside the verification-type set ([eval](evals/routing/eval.toml))

- ALWAYS: every workflow that delegates verification-type selection invokes `/verify` rather than a type-specific specialist ([audit])
- NEVER: duplicate test assertion typing, language expression, eval producer specialization, or audit judgment inside `/verify` ([audit])
