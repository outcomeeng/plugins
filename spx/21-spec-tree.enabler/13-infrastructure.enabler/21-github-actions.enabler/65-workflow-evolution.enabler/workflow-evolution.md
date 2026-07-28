# Workflow Evolution

PROVIDES maintenance and rearchitecture decisions for existing automation, grounded in lower-index evidence of drift, fragility, or bad structure
SO THAT narrower descendants performing specific evolution work (dependency maintenance, runner-runtime upgrades, structural rewrites)
CAN scope changes to evidence-backed concerns rather than speculative cleanup

## Assertions

### Compliance

- ALWAYS: an evolution decision cites the lower-index evidence (review verdict, runtime failure, dependency advisory) that justifies the change — speculative rewrites are forbidden ([audit])
- ALWAYS: maintenance covers Dependabot configuration, action commit-SHA revisions, runner image and runtime deprecations, CodeQL setup drift, scheduled-validation drift, cache keys, artifact retention, and cloud authentication mode — partial maintenance leaves drift in unchecked dimensions ([audit])
- ALWAYS: a rearchitecture preserves the workflow's existing assertions about behavior — any intentional behavior change is declared by an aligned assertion under the design model ([audit])
- NEVER: a workflow rearchitecture lacks evidence from `54-workflow-review` or `54-runtime-operations` — evolution without evidence is forbidden ([audit])
- NEVER: hide a failing check by weakening or removing the command that exposes the failure — silenced checks rot until the underlying issue ships to production ([audit])
