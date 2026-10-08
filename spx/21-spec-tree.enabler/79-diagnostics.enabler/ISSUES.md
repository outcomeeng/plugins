# Issues: Diagnostics

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The shipped diagnose manifest and its conformance evidence trail the aligned decision

[`spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`](spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md) and the conformance assertion in `diagnostics.md` state that marketplace-install diagnosis derives expected plugin state from Claude Code's project- and local-scope inventory for the invocation checkout and from raw selected-home Codex declarations, disabled and uncached entries included, bounded by committed catalog membership, under [`spx/12-marketplace-state.adr.md`](spx/12-marketplace-state.adr.md). Product activation does not select the Codex home-wide set, native inspection excludes product configuration discovery, and the shipped manifest embeds no plugin set.

The shipped artifact and its evidence still carry the old contract. `outcomeeng/distribution/diagnose_manifest.py` requires `DiagnoseManifestField.EXPECTED_PLUGINS`, `src/plugins/spec-tree/skills/diagnose/manifest.json` carries `expected_plugins`, `outcomeeng_testing/harnesses/diagnostics.py` builds `OwnedDiagnoseManifest` and its matcher around per-plugin ownership, and `tests/test_manifest.conformance.l1.py` verifies a manifest that carries the owning plugin's required plugin set.

**Impact.** The node's `[test]` evidence trails the aligned assertion, and the currently published `spx diagnose` reads `expected_plugins` from the manifest, so removing it before the CLI reads each agent's selection authority breaks diagnosis.

**Settlement condition.** A published `@outcomeeng/spx` release provides the revised manifest schema and the marketplace-install classification that reads each agent's selection authority: home-selection parsing, the reading of Claude Code install records for the invocation checkout at project and local scope, and native inspection outside product configuration discovery. The repository's floor and CI pin then sit at that release, the manifest contract, the harness and the shipped template carry no `expected_plugins` or its exact-fields validation, the generated `dist/claude` and `dist/codex` trees agree with their sources, and the conformance test verifies that the manifest carries the spx-version floor, the outcomeeng marketplace identity and the check set only.

**Related.** `outcomeeng/changes#123`, `outcomeeng/changes#122` and `outcomeeng/changes#192` carry the `spx diagnose` side of this move.
