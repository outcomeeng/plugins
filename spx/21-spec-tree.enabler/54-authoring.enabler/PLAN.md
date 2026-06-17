# PLAN: same-PR alignment step in `/author`

## Deferred from the future-product-truth concept change

`durable-map.md` `<decision_to_spec_alignment>` and the new `ALWAYS` assertion in
`spx/21-spec-tree.enabler/spec-tree.md` declare that authoring a higher-level
declaration carries it down to the first affected lower specs in the same change. The
`/author` enforcement of that contract is concrete downstream implementation this
slice does not carry.

## Next implementation step

Add an align step to `/author`: after any product spec, ADR, PDR, or ancestor spec
change, invoke `/align`, update the first affected lower specs in the same change,
and record any remaining downstream implementation in the first affected node's
`PLAN.md`. Pair this with the `/align` conformance check tracked in
`spx/21-spec-tree.enabler/54-aligning.enabler/PLAN.md`.

## Governing higher-level artifacts

- `src/plugins/spec-tree/skills/understand/references/durable-map.md` — `<decision_to_spec_alignment>`
- `spx/21-spec-tree.enabler/spec-tree.md` — the `/understand`-references downstream-alignment `ALWAYS` assertion
