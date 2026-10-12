# Issues

## Catalog sentinel matching lacks line-start anchoring

`outcomeeng/catalog/plugin_catalog.py` locates the README catalog sentinels with bare `readme.find(BEGIN_SENTINEL)` / `readme.find(END_SENTINEL)`, so a sentinel quoted mid-line elsewhere in `README.md` could be taken for a real boundary. `spx/local/generated-sources.toml` declares line-start matching for this marker family and notes the deviation; the declared rule governs attribution, per [`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md).

**Resolution shape**: anchor the sentinel search to line starts in `splice_catalog`, cover the anchoring in this node's catalog tests, then drop the deviation note from `spx/local/generated-sources.toml`.

## DEBT [evidence]: harness returns verdicts and derives the oracle from production (f-001 to f-008)

Eight findings (all REJECT) from a `spec-tree:test-evidence-auditor` verdict on
this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict
carries no sealed run token. The findings sit on the harness
`outcomeeng_testing/harnesses/plugin_catalog.py` and the test file
`spx/21-catalog.enabler/tests/test_plugin_catalog.compliance.l1.py`:

- f-001 at harness line 50: `generated_catalog_is_deterministic()` builds
  fixtures, compares renders, checks entry kinds, and returns a boolean; the
  linked test only runs `assert harness()`.
- f-002 at harness line 71: `generated_catalog_uses_declared_sentinels()`
  returns the startswith/endswith verdict. The coverage trace also judges it
  saturated.
- f-003 at harness line 78: `check_mode_fails_when_readme_catalog_drifts()`
  returns `== 1` from `main()`.
- f-004 at harness line 87:
  `runtime_divergent_skill_descriptions_name_each_target()` computes the
  expected value and returns the equality verdict.
- f-005 at harness line 98 (oracle independence, also lines 133-142): the
  expected purpose is built from production `shorten_purpose` and
  `render_target_values`, the same functions that produce the actual value.
- f-006 at harness line 146: `purpose_shortening_preserves_untrimmed_em_dash()`
  returns the verdict; an input the em-dash terminator would trim is not
  exercised.
- f-007 at test file line 15: every linked test body is `assert <harness>()`,
  so a failure reports only `assert False`.
- f-008 on the evidence chain: `outcomeeng/distribution/build.py` and
  `outcomeeng/distribution/contracts.py` were only symbol-grepped, and
  `outcomeeng_testing/generators/source_and_templating.py` was read only up to
  `source_scenarios`.

**Resolution shape**: for f-001 to f-004, f-006, and f-007, the harness returns
observations and the linked tests own every predicate. For f-005, construct the
expected purpose by an independent construction law that does not call
`shorten_purpose` or `render_target_values`. For f-006, add an input the
em-dash terminator would trim. For f-008, an audit reads the full chain.

**Out-of-change evidence**: the text lies outside the Change.
`git diff -U0 origin/main...HEAD` reports no hunk in the cited test file or
harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py`, narrows the guard in
`outcomeeng/validation/profile_configuration.py`, and adds model-price and
profile-binding generators, harnesses, and tests. The cited harness drives
`outcomeeng/catalog/plugin_catalog.py`, which the changeset does not change.

**Settlement condition**: the harness returns observations and each linked test
owns its predicates (f-001 to f-004, f-006, f-007); the expected purpose is
built independently of the production functions that produce the actual value
(f-005); an audit reads the full evidence chain, including
`outcomeeng/distribution/build.py`, `outcomeeng/distribution/contracts.py`, and
`outcomeeng_testing/generators/source_and_templating.py` (f-008).
