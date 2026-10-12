# Issues: Runtime parameterization

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The node and its specs use the prohibited agent-concept term

[`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md) maps `runtime`, `per-runtime` and `runtime-specific` to `agent`, `per-agent` and `agent-specific` where the subject is a selectable coding agent. This node's name and its spec use the term in that sense: "runtime-divergent", "per-runtime registry" and "No runtime is the source language", which mean per-agent target rendering. "Runtime" stays valid for execution-time behavior and for an execution environment such as Python.

**Settlement condition.** The node and its spec align to the decision's required wording. The node name encodes the term, so the sweep includes a `/refactor` node rename and is structural, as the entry in `spx/18-plugin-build.enabler/ISSUES.md` records.

## The runtime-parameterization harness raises AssertionError for lifecycle failures

`outcomeeng_testing/harnesses/runtime_parameterization.py` raises `AssertionError` when a resource fails to start or a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the harness owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the harness becomes a lifecycle or dependency error type the harness owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.

## DEBT [evidence]: linked tests delegate every predicate to harness verdict helpers (f-001, f-002, f-003, f-004, f-005)

Five findings (all REJECT) on `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler/tests/test_runtime_parameterization.compliance.l1.py` and its harness `outcomeeng_testing/harnesses/runtime_parameterization.py`:

- f-001 at line 18 of the test file: every linked test body is `assert <harness_fn>()`. The harness renders, compares through `_target_bodies_equal`, and returns a boolean verdict, so inverting an assertion changes only the harness.
- f-002 in `test_runtime_explicit_token_renders_named_runtime_on_every_target` (the audit gave no line): the same defect for the runtime-explicit token.
- f-003 at line 306 of the harness: `_raises_build_error` catches `BuildError` and converts it to a boolean; the linked tests own no `pytest.raises` predicate.
- f-004 at line 279 of the harness: `conditional_renders_absent_capability_only_where_present` renders and returns the equality verdict together with its expected strings.
- f-005 at line 324 of the harness: `registry_is_keyed_by_kind_with_explicit_guard_enforcement`, `registry_guard_contract_rejects_mismatched_enforcement`, and `_registry_contract_holds` return boolean verdicts.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

[`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) governs the opposite arrangement: the linked executed test owns every behavioral predicate and assertion API call, and a harness exposes observations or resource handles, never verdicts.

**Resolution shape**: return observations from the harness, each with its oracle expectation, and move every predicate into the linked tests, including the `pytest.raises` predicates for build failures and the registry-contract predicates.

**Out-of-change evidence**: the text lies outside the Change. `git diff -U0 origin/main...HEAD` reports no hunk in the cited test file or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness drives `render_text` and the runtime-token registry in `outcomeeng/distribution/build.py`, which the changeset does not change.

**Settlement condition**: the harness returns observations only, and each linked test holds its own predicate, so inverting an assertion in a test changes the verdict.

## DEBT [evidence]: harness raises AssertionError for lifecycle and shape failures (f-006)

Finding f-006 (REJECT) in the same audit and head as the entry above: `_require_implemented` and `_rendered_skill_body` raise `AssertionError` for lifecycle and shape failures instead of a harness-owned error type. The entry "The runtime-parameterization harness raises AssertionError for lifecycle failures" above already records this defect, its evidence, and its resolution; this entry adds only the second audit's confirmation, with the same out-of-change and invalidation reasoning as the entry above. The verdict carries no sealed run token.

**Settlement condition**: as recorded in the entry cited above.

## DEBT [evidence]: evidence chain left uninspected (f-008)

Finding f-008 (REJECT) in the same audit and head: the audit left `outcomeeng/distribution/build.py`, `outcomeeng/distribution/contracts.py`, `outcomeeng/validation/runtime_tokens.py`, `outcomeeng_testing/generators/source_and_templating.py`, and `outcomeeng_testing/harnesses/src_tree.py` uninspected, so the full chain from the linked tests to the implementation lacks a judgment.

**Resolution shape**: an audit reads the whole chain; no artifact changes.

**Out-of-change evidence**: the text lies outside the Change. `git diff -U0 origin/main...HEAD` reports no hunk in the cited chain's test file or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The chain neither cites, restates, nor depends on anything this changeset changed; `outcomeeng/distribution/build.py` is unchanged and the changeset's additions sit in `outcomeeng/distribution/profiles.py`, `outcomeeng/validation/profile_configuration.py`, and the model-price and profile-binding generators, harnesses, and tests.

**Settlement condition**: a test-evidence audit reads the listed chain and reaches a verdict on it.

Warning f-007 from the same audit: all twelve tests sit in one `.compliance.l1.py` file though some assertions are mappings, so the assertion-type split of the file awaits the same migration.
