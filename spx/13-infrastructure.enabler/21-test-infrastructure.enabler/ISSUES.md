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

## The spx version-floor compliance test picks its own violating data

`tests/test_spx_version_floor.compliance.l1.py` picks version literals
(`"99.0.0"`, `"1.2.3"`) and builds one-line workflow text in
`_workflow_with_pin` at the test site. It passes no real violating
whole-payload workflow fixture by path, so the compliance evidence exercises a
workflow shape no repository writes.

**Evidence**: filed finding f-002 (rule test-owned data) of the
`spec-tree:test-evidence-auditor` verdict on this node at head
`f445d049316d7ccb1368c53fdad9d26eb1e0deb5`. The diff from merge base
`2cf9cd80eebb49dc8a682f45dd08922551d54d76` changes neither the test file nor
`outcomeeng/validation/spx_version.py`.

**Settlement condition**: the compliance test reads a whole violating workflow
fixture by path and takes its versions from the fixture and the floor's owner.

## The infrastructure-placement predicate lives in a test-file helper

`tests/test_infra_placement.compliance.l1.py` holds the placement predicate
`_misplaced_test_infra` and `_PACKAGE_SEGMENT` in a helper outside the linked
test functions. The three `test_rule_*` cases exercise only that local helper,
with no production enforcement behind them.

**Evidence**: filed finding f-003 (rule assertion-seam) of the same verdict at
head `f445d049316d7ccb1368c53fdad9d26eb1e0deb5`. The diff from merge base
`2cf9cd80eebb49dc8a682f45dd08922551d54d76` changes neither the test file nor
`outcomeeng_testing/harnesses/spec_tree.py`.

**Settlement condition**: the placement rule is source-owned enforcement that
the linked tests drive, and no predicate lives in a test-file helper.
