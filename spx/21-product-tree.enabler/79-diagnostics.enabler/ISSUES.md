# Issues: Diagnostics

Known defects, contradictions and gaps in this node.

## The shipped diagnose manifest and its conformance evidence trail the aligned decision

[`spx/21-product-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`](spx/21-product-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md) and the conformance assertion in `diagnostics.md` state that marketplace-install diagnosis derives expected plugin state from Claude Code's project- and local-scope inventory for the invocation checkout and from raw selected-home Codex declarations, disabled and uncached entries included, bounded by committed catalog membership, under [`spx/12-marketplace-state.adr.md`](spx/12-marketplace-state.adr.md). Product activation does not select the Codex home-wide set, native inspection excludes product configuration discovery, and the shipped manifest embeds no plugin set.

The shipped artifact and its evidence still carry the old contract. `outcomeeng/distribution/diagnose_manifest.py` requires `DiagnoseManifestField.EXPECTED_PLUGINS`, `src/plugins/product-tree/skills/diagnose/manifest.json` carries `expected_plugins`, `outcomeeng_testing/harnesses/diagnostics.py` builds `OwnedDiagnoseManifest` and its matcher around per-plugin ownership, and `tests/test_manifest.conformance.l1.py` verifies a manifest that carries the owning plugin's required plugin set.

**Impact.** The node's `[test]` evidence trails the aligned assertion, and the currently published `spx diagnose` reads `expected_plugins` from the manifest, so removing it before the CLI reads each agent's selection authority breaks diagnosis.

**Settlement condition.** A published `@outcomeeng/spx` release provides the revised manifest schema and the marketplace-install classification that reads each agent's selection authority: home-selection parsing, the reading of Claude Code install records for the invocation checkout at project and local scope, and native inspection outside product configuration discovery. The repository's floor and CI pin then sit at that release, the manifest contract, the harness and the shipped template carry no `expected_plugins` or its exact-fields validation, the generated `dist/claude` and `dist/codex` trees agree with their sources, and the conformance test verifies that the manifest carries the spx-version floor, the outcomeeng marketplace identity and the check set only.

**Related.** `outcomeeng/changes#123`, `outcomeeng/changes#122` and `outcomeeng/changes#192` carry the `spx diagnose` side of this move.

## A not-applicable check's remediation item is unstated `src/plugins/product-tree/skills/diagnose/SKILL.md` `workflow step 4` `consistency`

**Evidence.** The diagnostic-remediation Evaluate subsection in `diagnostics.md` and step 4 of the shipped `diagnose` skill add one remediation item per non-healthy check, naming that check, its verdict and its bucket as the item's severity. A check in bucket `not-applicable` is neither healthy nor degraded, so a degraded report that also carries a `not-applicable` check leaves open whether that check gets an item of severity `not-applicable`. No case of the eval mixes a `not-applicable` check with a degraded one. The product-tree-review CI review raised this as a DEBT finding on https://github.com/outcomeeng/plugins/pull/782 at head `1a8d7be6f8c1182a4c386901fbeef4b90d48b51d`, and the Plugins Maintainer ruled it accepted.

**Impact.** Two readings of the skill both pass the eval, so the eval cannot tell whether a consumer sees a remediation item for a check whose surface is absent.

**Settlement condition.** The spec and the skill state whether a `not-applicable` check gets a remediation item in a non-healthy report, and the Evaluate table carries a case that mixes a `not-applicable` check with a degraded one and pins the stated reading.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_manifest.conformance.l1.py`: write a file, start a process, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
