# Issues

## The verify-result cases have no eval

**Evidence:** The `Evaluate: verify-result` subsection of `verify-skill.md` declares six cases: `unsupported-tag`, `probe-decision-rule`, `cli-state-input`, `cli-model-input`, `failed-route` and `failed-validation`. Its slug links no eval. The Node's one eval, `evals/routing/`, holds the eight cases of `Evaluate: routing` and none of the six.

**Impact:** No run checks the result records, the decision-rule placement, the rollback after a failed route or a failed `spx validation markdown`, or the CLI-backed selections these cases state. The Node is Spec-Malleable, and an Assertion that links no artifact needs no result for Passing, so the Node can stand Passing while the six cases are unproven.

**Settlement condition:** An eval under `evals/` holds the six cases with their inputs and expected results, the `verify-result` slug links its `eval.toml`, and a recorded run passes every case.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_render_report.scenario.l1.py`: write a file, start a process, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
