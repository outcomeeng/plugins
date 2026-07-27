# Outcome Engineering Methodology Changelog

What changed in the **methodology**, for a consumer repository upgrading to a new release.

This file is not the `spec-tree` plugin's changelog. The plugin delivers the methodology and versions itself independently; `CHANGELOG.md` in this directory records the plugin. A methodology release keeps its identity regardless of which plugin version delivers it.

An entry appears here when a change alters what a consumer can rely on, must do, or must know. A change that leaves the consumer contract untouched is excluded, whatever artifact it lived in.

**Editions.** The major axis is the edition — the grammar an artifact is written against. Only an edition change can invalidate an existing artifact; a minor or patch release never can.

Dates are the commits where this repository adopted each release.

## 3.1.0 — 2026-06-02

Verification became a closed vocabulary, and agentic evidence gained a deterministic sibling.

### Added

- **`[eval]` evidence.** An assertion whose subject is LLM-driven behavior emitting a parseable verdict is now scored deterministically against cases and a threshold, rather than judged. `[eval]` carries no assertion type. Evidence is co-located under `evals/{rule-slug}/` with `eval.toml`, `cases.jsonl`, `prompt.md`, and `history.jsonl`.
- **Five fixed verification types** — audit, validate, review, evaluate, test — over two independent axes: verdict mode (deterministic or agentic) and purpose (conformance or correctness). Every verification activity declares its type and purpose. A type's verdict mode is fixed, so a model never judges a deterministic verdict. Only `test`, `evaluate`, and `audit` back an assertion tag; `validate` and `review` back none.

### Changed

- **`[audit]` is the assertion tag for agentic evidence.** Review itself becomes an open-ended changeset gate that backs no assertion tag.

### Requires

- Edition 3. No artifact valid under 3.0.0 is invalidated by this release.

## 3.0.0 — 2026-03-23

Edition 3. Recursive enabler and outcome nodes with deterministic context loading.

### Breaking

- **The capability, feature, and story hierarchy is replaced by two recursive node types.** An enabler provides infrastructure (`PROVIDES ... SO THAT ... CAN ...`); an outcome states a hypothesis (`WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`). Both nest recursively, with one restriction: an enabler can never contain an outcome. The fixed three-level shape is gone, so every existing node is re-typed and re-nested.
- **Sibling integer prefixes became semantic.** Nodes, ADRs, and PDRs share one numeric namespace per directory, and the prefix drives context loading: lower-index siblings constrain the target and are read; same-index siblings are independent peers; higher-index siblings may depend on the target. Assigning an index now declares a dependency rather than an ordering preference.

### Added

- Derived node states — declared, specified, failing, passing — computed from spec, evidence, and implementation rather than stored.
- Five assertion types for `[test]` evidence, selected from the claim's quantifier: scenario, mapping, conformance, property, compliance. A universal is never a scenario.

## 2.0.0 — 2026-01-28

Edition 2. The durable map moves to `spx/`.

### Breaking

- **`specs/work/` is replaced by a durable `spx/` tree.** Specs stop being work items that complete and start being a standing map of what the product does. Backlog operations — close, archive, mark done, assign status — cease to exist. The capability, feature, and story structure carries over unchanged.

## 1.0.0 — 2026-01-05

Edition 1. The first methodology release: `specs/work/` with capability, feature, and story structure.
