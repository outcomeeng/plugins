# Worked example: xideck (toolchain)

A real, authored toolchain spec tree — the pattern-match reference for the `toolchain` archetype, the
concrete shape the generalized seed is derived from. Source: `xiperinc/xideck`. 39 enablers, 0
outcomes — correctly outcome-free (determined transform; author + agent).

## Top-level partition (as authored)

```text
spx/
  11-testing-architecture.adr.md
  13-capture-protocol.adr.md
  15-infrastructure.enabler/          substrate: test/build runners, PPTX I/O, source<->PPTX sync
  21-build-pipeline.enabler/          deterministic flow: capture -> emission -> lint
  27-design-system.enabler/           tokens -> surfaces -> primitives -> components -> compositions
  33-storyline.enabler/               authored source format: Markdown <-> TSX round-trip
  39-slide-library.enabler/           authored asset catalog: slides -> sections -> decks
  45-deck-authoring.enabler/          author loop: iteration surface, screenshot driver, specimen builder
  51-deck-reconciliation.enabler/     PPTX -> source: diff, duplicate, orphan, confirm, golden round-trip
```

## Bookend second layers (as authored)

```text
infrastructure        -> test-infrastructure | pptx-io | sync-mechanism | build-infrastructure
build-pipeline        -> shape-record | capture | emission | lint-and-verification
deck-authoring        -> iteration-surface | screenshot-driver | specimen-builder
deck-reconciliation   -> diff-classifier | duplicate-of-detection | orphan-shape-classifier | interactive-confirmation | golden-round-trip-test
```

## PROVIDES openings (the authored spec voice)

- **infrastructure** — PROVIDES the foundational substrate every other subtree depends on — test
  runner setup, build runner setup, PPTX I/O primitives, and the PPTX-shape-to-TSX-source sync
  mechanism.
- **build-pipeline** — PROVIDES the deterministic data flow that turns slide TSX into a hand-editable
  `.pptx` and `.potx` — capture, emission, and lint as three composable stages.
- **deck-authoring** — PROVIDES the author's loop — the iteration surface, the specimen builder, and
  the screenshot driver — so authors and Claude compose decks visually and verify the design system
  before any PPTX is built.
- **deck-reconciliation** — PROVIDES the workflow that reads a hand-edited `.pptx`, classifies what
  changed against the TSX source, proposes patches, and applies them on user confirmation.

## How the seed generalizes this

- Renames product-specific slugs: `storyline` → `source-format`, `slide-library` → `asset-library`,
  `design-system` → `domain-vocabulary`, `pptx-io` → `artifact-io`, `capture` → `ingest`,
  `emission` → `emit`, `lint-and-verification` → `verify`, `shape-record` → `ir-contract`,
  `deck-reconciliation` → `reconciliation`.
- Conforms `test-infrastructure` to the normative `testing → {generators, fixtures, harnesses}`
  subtree.
- Marks `design-system`/`source-format`/`asset-library`/`authoring-loop`/`reconciliation` as optional
  concerns gated on product signals, so a headless transformer takes only the core spine.

xideck's own tree is preserved here verbatim as the authored reference; the generalized seed lives in
`../seed-tree.json`.
