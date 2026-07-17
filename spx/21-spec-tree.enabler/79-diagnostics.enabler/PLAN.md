# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Declaration applied: `spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`
and `spx/21-spec-tree.enabler/79-diagnostics.enabler/diagnostics.md` declare marketplace-install
diagnosis deriving expected plugin state from the checkout's per-runtime project declarations,
with the manifest-embedded plugin set removed. This declaration carries no unpublished-dependency
gate and is complete.

The node's `[test]` conformance assertion now declares the post-cutover manifest shape (floor,
marketplace identity, and check set; no plugin set), which the shipped manifest and its linked
test do not yet realize. The node is therefore listed in `spx/EXCLUDE`
(`21-spec-tree.enabler/79-diagnostics.enabler`) so the conformance test is not gated against a
declaration it cannot yet satisfy; remove that entry when the cutover below lands.

Pending implementation — BLOCKING dependency: a published `@outcomeeng/spx` release must first
provide the revised diagnose manifest schema and the marketplace-install classification that reads
the checkout's per-runtime project declarations. The currently published `spx diagnose` reads
`expected_plugins` from the manifest, so removing it before the CLI reads the checkout declarations
breaks diagnosis. When the release is published, land these together:

- Advance `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and the CI `SPX_VERSION`
  pin in `.github/workflows/check.yml` to that published version.
- Remove `DiagnoseManifestField.EXPECTED_PLUGINS` and its exact-fields validation from
  `outcomeeng/distribution/diagnose_manifest.py` (`authored_diagnose_manifest_contract`,
  `shipped_diagnose_manifest_contract`), so the contract no longer hard-requires a plugin set.
- Update the `outcomeeng_testing/harnesses/diagnostics.py` harness — `OwnedDiagnoseManifest`,
  `rendered_diagnose_manifests_match_their_owners`, and its per-manifest matcher are built around
  per-plugin ownership and must drop it.
- Remove `expected_plugins` from the shipped diagnose manifest template
  `src/plugins/spec-tree/skills/diagnose/manifest.json`, then regenerate `dist/claude` and
  `dist/codex` via `just build-skills`.
- Update `tests/test_manifest.conformance.l1.py` to assert the manifest carries the spx-version
  floor, the outcomeeng marketplace identity, and the check set only, and embeds no plugin set.
- Remove `21-spec-tree.enabler/79-diagnostics.enabler` from `spx/EXCLUDE`.
