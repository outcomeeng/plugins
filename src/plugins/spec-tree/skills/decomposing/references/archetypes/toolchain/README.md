# Toolchain archetype

A developer tool that transforms authored **source** into an **artifact**, optionally round-tripping
hand-edits to the artifact back into source.

**Outcome topology: none.** The transform is determined by its specification and the users are the
author plus Claude — there is no measurable multi-user behavior change to bet on, so every node is
an enabler. A product seeded from this archetype is correctly outcome-free.

## When the router matches a product here

- Users are few and known (an author + Claude), not many anonymous users.
- The output is fully determined by its transform, not a bet on behavior.
- Primary surface is a CLI, a library, or file output.
- The natural decomposition is a transformation pipeline (ingest → emit → verify).

## What it seeds

- **Core spine** (always): `infrastructure`, `transform-pipeline`.
- **Optional concerns** (gated on product signals — see `archetype.toml` `[concerns.gates]`):
  `domain-vocabulary`, `source-format`, `asset-library`, `authoring-loop`, `reconciliation`.

`seed-tree.json` carries the proposed tree (top-level partition + bookend second layers); every node
is `status: proposed` and re-confirmed against the new product's hypothesis. `decisions.md` lists the
decision topics as prompts. `example/` is the vendored worked example.

## Source

Generalized from **xideck** (`xiperinc/xideck`), a TypeScript→PPTX deck toolchain with
PowerPoint→source round-trip. See `example/` for the real authored bookend tree.
