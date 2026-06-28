# PLAN: downstream-alignment conformance in `/align`

## Deferred from the future-product-truth concept change

`durable-map.md` `<decision_to_spec_alignment>` and the new `ALWAYS` assertion in
`spx/21-spec-tree.enabler/spec-tree.md` (the `/understand` references declare the
downstream-alignment contract) declare that a change to a higher-level declaration
aligns the first affected lower specs in the same change. The `/align` enforcement
of that contract is concrete downstream implementation this slice does not carry.

## Next implementation step

Add a downstream-alignment conformance check to `/align`: over a changeset's
changed-file set, report a changed higher-level declaration (product spec, PDR, ADR, or
ancestor spec) that has no aligned lower spec under its constraining scope and no
node-local `PLAN.md` grounding. Derive the changed-file set from the `scope-changeset`
skill's `branch_scope(base, repo)` — never hand-roll git base-ref or diff derivation
inside `/align`, per `spx/21-spec-tree.enabler/17-audit.adr.md`.

## Governing higher-level artifacts

- `src/plugins/spec-tree/skills/understand/references/durable-map.md` — `<decision_to_spec_alignment>`
- `spx/21-spec-tree.enabler/spec-tree.md` — the `/understand`-references downstream-alignment `ALWAYS` assertion
