# Verify Skill

PROVIDES verification-type selection and evidence-work orchestration from one assertion or canonical spec-tree scope
SO THAT authoring, applying, architecture, test-auditing, and evidence-maintenance workflows
CAN route every assertion to test, evaluate, probe, or audit before a specialist chooses lower-level evidence details

## Assertions

### Mappings

- Every supported subject capability maps to one verification type and specialist result: deterministic behavior maps to test and `/test`, model-generated behavior with structured output maps to evaluate and `/eval`, a claim only an executed observation of the running node settles maps to probe and its protocol link or missing authoring capability, and a semantic constraint with no deterministic or attested verdict maps to audit and its isolated-verifier requirement ([eval](evals/routing/eval.toml))

### Compliance

- ALWAYS: select from exactly test, evaluate, probe, and audit by the verdict the real assertion subject can produce; deterministic CLI state routes to test when an LLM only reports that state for an independent comparison, while model-generated behavior routes to evaluate even when a CLI exposes it ([eval](evals/routing/eval.toml))
- ALWAYS: test assertion typing occurs only after test is selected ([audit])
- ALWAYS: report a missing selected specialist as an explicit capability gap ([eval](evals/routing/eval.toml))
- NEVER: recognize, name, alias, or translate any tag outside the verification-type set ([eval](evals/routing/eval.toml))
- ALWAYS: emit one structured result per assertion carrying `verification_type`, `specialist`, `status`, `evidence_shape`, and `reason`, with `status` one of `routed`, `capability-required`, or `blocked`; a blocked result carries the reason `unsupported-tag-shape` with `verification_type`, `specialist`, and `evidence_shape` null, and the human report table renders from that same result with an em dash for each null field ([eval](evals/routing/eval.toml))

- ALWAYS: every workflow that delegates verification-type selection invokes `/verify` rather than a type-specific specialist ([audit])
- NEVER: duplicate test assertion typing, language expression, eval producer specialization, or audit judgment inside `/verify` ([audit])
