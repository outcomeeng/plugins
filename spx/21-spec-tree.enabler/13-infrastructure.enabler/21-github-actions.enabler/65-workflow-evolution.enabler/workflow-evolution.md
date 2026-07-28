# Workflow Evolution

PROVIDES maintenance and rearchitecture decisions that change existing automation after lower-index evidence identifies drift, fragility, or bad structure
SO THAT narrower descendants performing specific evolution work (dependency maintenance, runner-runtime upgrades, structural rewrites)
CAN scope changes to evidence-backed concerns rather than speculative cleanup

## Assertions

### Compliance

- ALWAYS: an evolution decision cites the lower-index evidence (review verdict, runtime failure, dependency advisory) that justifies the change — speculative rewrites are forbidden ([audit])
- ALWAYS: maintenance covers Dependabot configuration, action commit-SHA revisions, runner image and runtime deprecations, CodeQL setup drift, scheduled-validation drift, cache keys, artifact retention, and cloud authentication mode — partial maintenance leaves drift in unchecked dimensions ([audit])
- ALWAYS: a rearchitecture preserves the workflow's existing assertions about behavior — if the new shape breaks an assertion, the assertion is updated first under the design model ([audit])
- NEVER: rearchitect a workflow without first auditing it via `54-workflow-review` or diagnosing it via `54-runtime-operations` — evolution without evidence is forbidden ([audit])
- NEVER: hide a failing check by weakening or removing the command that exposes the failure — silenced checks rot until the underlying issue ships to production ([audit])
