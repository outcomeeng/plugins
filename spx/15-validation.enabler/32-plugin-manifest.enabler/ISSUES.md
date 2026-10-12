# ISSUES — plugin manifest validation

Known defects and contradictions in the plugin manifest surface. Each entry names the artifact, the rule it violates, and the smallest unit of work that resolves it.

## No manifest expresses that the spec-tree plugin is mandatory

Every plugin operationalizes a methodology the spec-tree plugin carries, and a consumer is expected to have that plugin installed. No manifest says so. `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` carry name, version, description, author, repository, license, and keywords; neither declares a dependency, and neither marketplace catalog records one. The two catalogs list ten independently installable entries, and `README.md` presents each standalone repository as separately installable.

The mandate therefore lives only in operator knowledge. Anything reasoning from the artifacts alone — a reviewer, a validator, `spx`, or the next author — reads ten independent plugins and concludes a consumer may install any one of them alone. That conclusion is wrong, and nothing in the repository corrects it.

The gap has a concrete cost: content that only the spec-tree plugin ships is unreachable for a consumer the artifacts say may exist, so any review of such a change raises a blocking finding that only operator knowledge can refute.

**Resolution shape**: express the relationship where a reader already looks. A `methodology` block in each manifest declaring the methodology releases that plugin supports — with the providing plugin declaring what it provides — makes the dependency legible and checkable, and is the same declaration a consumer's own methodology version is validated against. Whether the relationship additionally warrants a hard dependency field in both catalogs is a separate question this entry does not settle.

**Evidence**: raised as a blocking `consistency` finding by the changeset reviewer against the marketplace-changelog relocation, on the grounds that no `plugin.json` declares a dependency on the spec-tree plugin and nothing in that changeset added one. The finding's premise was refuted by the operator, who confirmed the plugin is mandatory; the absence of any artifact expressing it is what the finding actually exposed.

## DEBT [evidence]: harness entry points own the pass/fail predicates (f-001)

Finding f-001 (REJECT) at `outcomeeng_testing/harnesses/plugin_manifest.py:91`, covering every entry point from `marketplace_is_validated` through `invocation_exit_is_not_blocked_by_descendant` (lines 91-330): each evaluates the full pass/fail predicate (exit codes, stderr substrings, command equality, elapsed time) and returns a boolean, and the linked scenario tests contain only `assert helper()`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness entry points return observations, and every predicate moves into the linked tests.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited file, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness drives `outcomeeng/validation/plugins.py`, which the changeset does not change.

**Settlement condition**: every linked test asserts the predicate over observations the harness returns, and no harness entry point returns a verdict.

## DEBT [evidence]: symmetric-parity invariant asserted inside the harness (f-002)

Finding f-002 (REJECT) at `spx/15-validation.enabler/32-plugin-manifest.enabler/tests/test_plugin_manifest.property.l1.py:11`: the symmetric-parity invariant (`len(errors) == 1` for both orders) is asserted inside the harness function `_generated_manifest_version_parity_is_symmetric`, and the test runs `assert manifest_version_parity_is_symmetric()`.

The audit is the verdict named in the entry above, at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`; the verdict carries no sealed run token.

**Resolution shape**: the invariant moves into the linked property test, which asserts it over the observations the harness returns.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited file, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness drives `outcomeeng/validation/plugins.py`, which the changeset does not change.

**Settlement condition**: the property test itself asserts that both orders yield exactly one error.

## DEBT [evidence]: universal no-drift assertion linked to scenario evidence (f-003)

Finding f-003 (REJECT) at `spx/15-validation.enabler/32-plugin-manifest.enabler/tests/test_plugin_manifest.scenario.l1.py:1`: a universal NEVER assertion (no manifest version drift) is linked to a scenario-typed file. Universal assertions take compliance evidence in a `.compliance.l1.py` file that asserts the violating drift case itself.

The audit is the verdict named in the entries above, at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`; the verdict carries no sealed run token.

**Resolution shape**: add compliance evidence in a `.compliance.l1.py` file that exercises the violating drift case and is rejected, and relink the assertion to it.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited files, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness drives `outcomeeng/validation/plugins.py`, which the changeset does not change.

**Settlement condition**: the no-drift assertion links compliance evidence that rejects a generated drifted manifest.
