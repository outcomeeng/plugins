# Issues

## The verify-result cases have no eval

**Evidence:** The `Evaluate: verify-result` subsection of `verify-skill.md` declares six cases: `unsupported-tag`, `probe-decision-rule`, `cli-state-input`, `cli-model-input`, `failed-route` and `failed-validation`. Its slug links no eval. The Node's one eval, `evals/routing/`, holds the eight cases of `Evaluate: routing` and none of the six.

**Impact:** No run checks the result records, the decision-rule placement, the rollback after a failed route or a failed `spx validation markdown`, or the CLI-backed selections these cases state. The Node is Spec-Malleable, and an Assertion that links no artifact needs no result for Passing, so the Node can stand Passing while the six cases are unproven.

**Settlement condition:** An eval under `evals/` holds the six cases with their inputs and expected results, the `verify-result` slug links its `eval.toml`, and a recorded run passes every case.
