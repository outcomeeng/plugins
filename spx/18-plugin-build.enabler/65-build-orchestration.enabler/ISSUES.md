# Issues

## Scenario predicates are hidden in boolean-returning harnesses

Implementation audit `2026-09-14_11-26-09-644-eb39d2a3b433` rejected
`tests/test_build_orchestration.scenario.l1.py:36`: the formatter-version-probe
test asserts a boolean returned by `failing_formatter_version_probe_matches_contract`.
The other scenario tests in that file use the same assertion-delegation pattern.
The test-infrastructure PDR requires predicates in linked tests and observations
from harnesses. Hidden predicates prevent the test file from exposing its oracle.

The audited test file is unchanged by the formatter-version update at
`349e3c3be3f88f496f228666036d6790b5be2a3c`. This records the rejected subject
under the merge policy for audit findings outside the changed files; it supplies
no evidence-audit approval. Settlement requires observation-returning harnesses
and test-owned predicates across this file, followed by a passing evidence audit.
Revisit before relying on this node's evidence-audit approval or changing these tests.

## The build-orchestration harness raises AssertionError for lifecycle failures

`outcomeeng_testing/harnesses/build_orchestration.py` raises `AssertionError` when a resource fails to start, a process fails to announce itself or a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the harness owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the harness becomes a lifecycle or dependency error type the harness owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.

## DEBT [evidence]: build-orchestration verdicts, violating cases, and case literals live in the harness (f-001, f-002, f-003, f-005, f-007)

Findings (REJECT unless noted) of a `spec-tree:test-evidence-auditor` verdict on
this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict
carries no sealed run token. Tests are under
`spx/18-plugin-build.enabler/65-build-orchestration.enabler/tests`; the harness is
`outcomeeng_testing/harnesses/build_orchestration.py`.

- f-001 `test_build_orchestration.scenario.l1.py`: every test body is a bare
  `assert <harness>_matches_contract()`; the harness owns the verdict. This repeats
  the first entry of this file, which records the same defect; its resolution is not
  restated here.
- f-002 `test_build_orchestration.compliance.l1.py`: all eleven tests assert a
  boolean from a harness function; verdict logic, violating-case construction, and
  rejection checks live in infrastructure.
- f-003 harness line 75: verdict-shaped `*_matches_contract` and `*_is_rejected`
  functions return booleans and catch product exceptions (`BuildError`,
  `ConfigPathError`) to produce them.
- f-004 harness lines 115, 140, 181: collaborator stubs raise `AssertionError`
  where a harness-owned error type belongs. This matches the second entry of this
  file, which carries its resolution.
- f-005 harness line 66: case data and policy (`FORMATTER_FAILURE_DIAGNOSTIC`,
  `FORMATTER_VERSION_FAILURE_DIAGNOSTIC`, `FORMATTER_TEST_PATH`, exit codes,
  `INVALID_PATH_SEGMENT`/`INVALID_PATH_SUFFIX`, stub runner behavior) are chosen
  inside the harness; the literals belong at the linked test site.
- f-007 (WARNING) harness line 111: the recording spy lives in the harness with
  its verdict.

**Resolution shape**: the harness returns observations and handles, and the linked
tests own every predicate, violating case, and case literal.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD`
reports no hunk in the cited tests or harness, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py`, narrows the guard in
`outcomeeng/validation/profile_configuration.py`, and adds model-price and
profile-binding generators, harnesses, and tests. The cited harness drives the
build orchestration contracts in `outcomeeng/distribution/orchestration.py`,
`build.py`, and `dist_diff.py`, which the changeset does not change.

**Settlement condition**: the harness holds no verdict-shaped function, no caught
product exception that yields a boolean, and no case literal; each linked test
asserts its own predicate over a harness observation, and the node passes its
test-evidence audit.

## DEBT [evidence]: compliance verdicts share the production contracts they judge (f-006)

Finding f-006 (REJECT, oracle independence) at harness line 257 of
`outcomeeng_testing/harnesses/build_orchestration.py`: compliance verdicts come
from production predicates and the same production contracts module, so the
checker validates itself and the repository-wide self-check tests cannot fail
independently. The audit is the verdict named in the entry above, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`; it carries no sealed run token.

**Resolution shape**: each compliance expectation comes from an oracle that does
not import the production predicate it judges, held by the linked test.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD`
reports no hunk in the cited harness, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed; the same additions and unchanged build
orchestration contracts named in the entry above apply.

**Settlement condition**: a fault in the production contracts module fails a
compliance test that does not consume that module for its expectation.

## DEBT [evidence]: evidence chain uninspected and Python concern not composed (f-008, f-009)

Findings of the verdict named above, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`:

- f-008: the evidence chain left the harnesses `dist_drift`, `dist_tree`,
  `src_tree`, the `source_and_templating` generator, and the production modules
  `build`, `contracts`, `dist_diff`, `orchestration`, `validation/_steps`, and
  `validation/build_orchestration` uninspected.
- f-009: the Python audit concern was not composed into the verdict, so
  Python-specific checks and Gate 2 were unevaluated.

**Resolution shape**: a re-audit that composes the Python concern and inspects
the listed chain settles both; no repair of text is implied.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD`
reports no hunk in the cited chain, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited chain neither cites, restates, nor depends on
anything this changeset changed; the same additions and unchanged build
orchestration contracts named above apply.

**Settlement condition**: a test-evidence audit of this node composes the Python
concern, inspects every listed harness, generator, and production module, and
evaluates Gate 2.
