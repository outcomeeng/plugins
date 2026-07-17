# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Declaration applied: `spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`
and `spx/21-spec-tree.enabler/79-diagnostics.enabler/diagnostics.md` declare marketplace-install
diagnosis deriving expected plugin state from the checkout's per-runtime project declarations,
with the manifest-embedded plugin set removed. This declaration carries no unpublished-dependency
gate and is complete.

Pending implementation — BLOCKING dependency: a published `@outcomeeng/spx` release must first
provide the revised diagnose manifest schema and the marketplace-install classification that reads
the checkout's per-runtime project declarations. The currently published `spx diagnose` reads
`expected_plugins` from the manifest, so removing it before the CLI reads the checkout declarations
breaks diagnosis. When the release is published:

- Advance `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and the CI `SPX_VERSION`
  pin in `.github/workflows/check.yml` to that published version.
- Remove `expected_plugins` from the shipped diagnose manifest template
  `src/plugins/spec-tree/skills/diagnose/manifest.json`, then regenerate `dist/claude` and
  `dist/codex` via `just build-skills`.
- Update `tests/test_manifest.conformance.l1.py` to assert the manifest carries the spx-version
  floor, the outcomeeng marketplace identity, and the check set only, and embeds no plugin set.
