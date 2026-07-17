# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Decision and spec aligned: `spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`
re-declares the diagnose contract — marketplace-install diagnosis derives expected plugin state
from the checkout's per-runtime project declarations, and the shipped manifest embeds no plugin
set — and the node's `diagnostics.md` conformance assertion is aligned to that contract in the same
change. Neither carries an unpublished-dependency gate.

The linked test and the shipped artifact are the deferred implementation this slice does not carry:
`tests/test_manifest.conformance.l1.py` (via `outcomeeng_testing/harnesses/diagnostics.py`) still
verifies the current manifest, which still carries the owning plugin's required plugin set, so the
node's `[test]` evidence trails the aligned assertion until the cutover below reconciles them.

Pending implementation — BLOCKING dependency: a published `@outcomeeng/spx` release must first
provide the revised diagnose manifest schema and the marketplace-install classification that reads
the checkout's per-runtime project declarations. The currently published `spx diagnose` reads
`expected_plugins` from the manifest, so removing it before the CLI reads the checkout declarations
breaks diagnosis. When the release is published, land these together so the test and the shipped
artifact rejoin the already-aligned decision and spec:

- Advance `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and the CI `SPX_VERSION`
  pin in `.github/workflows/check.yml` to that published version.
- Remove `DiagnoseManifestField.EXPECTED_PLUGINS` and its exact-fields validation from
  `outcomeeng/distribution/diagnose_manifest.py` (`authored_diagnose_manifest_contract`,
  `shipped_diagnose_manifest_contract`), so the contract no longer requires a plugin set.
- Update the `outcomeeng_testing/harnesses/diagnostics.py` harness — `OwnedDiagnoseManifest`,
  `rendered_diagnose_manifests_match_their_owners`, and its per-manifest matcher are built around
  per-plugin ownership and must drop it.
- Remove `expected_plugins` from the shipped diagnose manifest template
  `src/plugins/spec-tree/skills/diagnose/manifest.json`, then regenerate `dist/claude` and
  `dist/codex` via `just build-skills`.
- Update `tests/test_manifest.conformance.l1.py` to verify the manifest carries the spx-version
  floor, the outcomeeng marketplace identity, and the check set only, and embeds no plugin set.
