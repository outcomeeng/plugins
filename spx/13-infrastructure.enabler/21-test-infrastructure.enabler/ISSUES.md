# Issues

## The gate recipe body has no evidence

The compliance assertion that CI runs the full gate "never an inlined or
filtered subset" is verified from two ends that do not meet. One end reads
`.github/workflows/check.yml` and confirms a step runs `just check-full`. The
other reads `VALIDATION_STEPS` and confirms each declared step, including the
workflow and shell linters, belongs to the composed gate.

Between them sits the `check-full` recipe in the repository `Justfile`, which
dispatches to `python3 -m outcomeeng.validation check-full`. No evidence reads
that recipe body. Narrowing it — to `check`, which composes only the validation
recipe and drops the test recipe, or to any filtered invocation — leaves every
test in this node green while CI runs a subset.

Closing this needs an assertion naming the recipe-to-module dispatch and a
harness that reads the recipe body, so it reaches beyond the evidence surfaces
the current changeset touches.
