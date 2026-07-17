# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Decision applied: `spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`
re-declares the diagnose contract so marketplace-install diagnosis derives expected plugin state
from the checkout's per-runtime project declarations and the shipped manifest embeds no plugin
set. This decision carries no unpublished-dependency gate and leads its implementation: the
node's spec conformance assertion, its linked test, and the shipped manifest still describe the
current contract (the manifest carries the owning plugin's required plugin set) and stay mutually
consistent until the cutover below reconciles them to the decision in one change.

Pending implementation — BLOCKING dependency: a published `@outcomeeng/spx` release must first
provide the revised diagnose manifest schema and the marketplace-install classification that reads
the checkout's per-runtime project declarations. The currently published `spx diagnose` reads
`expected_plugins` from the manifest, so removing it before the CLI reads the checkout declarations
breaks diagnosis. When the release is published, land these together in one change so the spec,
test, and shipped artifact never disagree:

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
- Rewrite the `diagnostics.md` conformance assertion to declare the manifest carries the
  spx-version floor, the outcomeeng marketplace identity, and the check set only, and embeds no
  plugin set.
- Update `tests/test_manifest.conformance.l1.py` to verify that reconciled manifest shape.
