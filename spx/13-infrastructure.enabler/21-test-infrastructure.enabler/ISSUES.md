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

## CI still provisions credentials the on-demand suite alone consumes

[`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md)
keeps every `l3` test out of CI, yet `.github/workflows/check.yml` still grants
`actions: read` for the `l3` workflow-observability tests and passes `GH_TOKEN`,
`SUBAGENT_DISCOVERY_AUTH_MODE`, and `OPENAI_API_KEY` to the gate step for the `l3`
subagent-discovery probe, and the toolchain paragraph of
[`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md)
still names an authenticated `gh` for those tests.

**Evidence**: `.github/workflows/check.yml` lines 17 and 106 to 112; the toolchain
paragraph of `15-ci-gate.adr.md`.

**Impact**: CI hands a model-provider key and a workflow token to a run that
executes no test consuming either, which spends no quota and widens the secret
surface for no verdict.

**Settlement condition**: the workflow grants and passes only what the executed
gate consumes, and the ADR's toolchain paragraph names none of the `l3` tests'
provisioning.

## The verification PDR names the live-discovery exclusion as the CI scope

[`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)
states that deterministic types widen in CI to the whole repository less the
live-discovery exclusion. The exclusion CI applies is the on-demand suite, every
test whose file name carries the execution level `l3`, of which the two
live-discovery tests are members.

**Evidence**: line 23 of `14-verification.pdr.md` against
[`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md).

**Impact**: a reader takes the CI scope to omit two tests, where it omits every
`l3` test.

**Settlement condition**: the sentence names the on-demand suite as the CI scope's
one exclusion.

## DEBT [evidence]: the static-analysis steps are checked in a step list, not in the `check-full` recipe

Defect class: `alignment`.

Finding: the compliance assertion of `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/21-python-code-quality.enabler/python-code-quality.md` that `ruff check`, `mypy --strict`, and `pyright` run as named steps in `just check-full` is evidenced by `tests/test_python_code_quality.compliance.l2.py`, which reads argv membership of `VALIDATION_STEPS`. No test reads that the `check-full` recipe composes `VALIDATION_STEPS` or that the steps carry names, so narrowing the recipe or renaming a step leaves the test passing.

Evidence: filed finding f-001 of the `spec-tree:test-evidence-auditor` verdict on `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/21-python-code-quality.enabler` at head `06654f813bcc281da60595cb201040462389a7fe`. The diff from merge base `708f150169f21a58087e73e0f61382ea0b7e7dba` changes neither the spec, nor either linked test, nor the step declarations.

Settlement condition: a test reads the `check-full` recipe body and the composed step labels, and narrowing the recipe or renaming a step fails it. The entry "The gate recipe body has no evidence" above names the same recipe body.

## DEBT [evidence]: the package-set oracle for type checking is the production tuple

Defect class: `oracle-independence`.

Finding: `test_type_checking_steps_target_product_packages` in `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/21-python-code-quality.enabler/tests/test_python_code_quality.compliance.l2.py` derives its expected package set from `PYTHON_SOURCE_PATHS`, the tuple `outcomeeng/validation/_steps.py` builds `MYPY_ARGV` and `PYRIGHT_ARGV` from. Dropping a package from the tuple changes the expectation and the argv together, and the test passes. No source outside the production path owns the set of importable product packages.

Evidence: filed finding f-002 of the same verdict and head, with the same base evidence.

Settlement condition: the expected package set derives from a source the step tuple does not feed, such as the packaging metadata's declared packages, and removing a package from `PYTHON_SOURCE_PATHS` fails the test.
