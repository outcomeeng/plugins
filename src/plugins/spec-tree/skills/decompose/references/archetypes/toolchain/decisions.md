# Toolchain archetype — decision topics

Decisions a toolchain product typically needs, expressed as **prompts to confirm or prune** against
the new product's hypothesis. Each is a proposal, never an inherited answer — a product seeded from
this archetype keeps only the decisions its own design requires. Derived from the decision records in
the source product (xideck).

## Root-level

- **Testing architecture** (`15`, ADR) — How are deterministic transforms tested? Fixture corpus,
  golden artifacts, and test levels (l1 transform units / l2 stage integration / l3 full round-trip).
- **Ingest protocol** (`18`, ADR) — The closed contract between authored source and the pipeline's
  first stage: the kinds, tokens, or attributes the ingest step recognizes. (xideck: the
  `data-box-type` capture protocol.)

## Under `transform-pipeline → emit`

- **Emit / output architecture** (`15`, ADR) — How the artifact is generated: native constructs vs
  rasterized/fallback rendering, embedding, templates/masters, content-type rewrites.

## Under `source-format` (if the concern is present)

- **Source format grammar** (`15`, ADR) — The authored representation's grammar and its
  parse/serialize round-trip mapping. (xideck: storyline Markdown ↔ TSX.)

## Under `asset-library` (if the concern is present)

- **Asset routing / index** (`15`/`17`, ADR) — How authored assets are addressed and catalogued: the
  routing scheme and the index-file shape.

## Under `reconciliation → orphan-classifier` (if the concern is present)

- **Reconciliation default** (`15`, PDR) — How ambiguous back-sync cases resolve by default (e.g.
  orphaned artifact elements: attach-to-nearest, author-confirmed).
