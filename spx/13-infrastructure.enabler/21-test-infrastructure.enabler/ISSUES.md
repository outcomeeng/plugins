# Issues: Test Infrastructure Enabler

## 1. Canonical test-infrastructure category subtree is absent

`spx/15-test-infrastructure.pdr.md` mandates the canonical subtree
`infrastructure → testing → {generators, fixtures, harnesses}` with those exact
slugs, and requires every test-infrastructure artifact to be traceable to a
category node (covered by the node's assertions, or by a child spec).

This product's `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/`
has only a `21-python-code-quality.enabler` child — no `harnesses`,
`generators`, or `fixtures` category nodes. Meanwhile `outcomeeng_testing/`
already ships `harnesses/` (15 harness modules, including `git_context.py`),
`generators/`, and `fixtures/` with no governing category node.

The gap is pre-existing and product-wide: it predates and is unrelated to any
single harness. `git_context.py` (added for the sessions scenario-test
hermeticity fix) only surfaced it.

**Required handling** (out of scope for a single harness change):

- Author the `generators`, `fixtures`, and `harnesses` category nodes under
  `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/` via
  `/authoring`, declaring the category-wide contract each enforces per
  `spx/15-test-infrastructure.pdr.md`.
- Establish traceability from each `outcomeeng_testing/{harnesses,generators,fixtures}/`
  artifact to the matching category node.

Surfaced during the `fix/sessions-test-hermeticity` change review.
