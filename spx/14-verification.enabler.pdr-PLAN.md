# PLAN — verification taxonomy as foundational PDR

Deferred capture. Not yet authored. This node directory stakes the placement; the spec, the grounding PDR, and the understanding reference are authored in a later, separate change (distinct concern from the validity+phase review-gate change).

## Goal

Declare the four-kind **verification** taxonomy as spec-tree foundation, loaded by `/understanding`, grounded in a higher-level PDR.

## The taxonomy

Verification is the top-level category over the validation and test runners. Four kinds:

1. **Validation** — static analysis (linting, structural checks). Fully deterministic.
2. **Testing** — tests conforming to spec-tree methodology. Fully deterministic.
3. **Auditing** — auditing skills for spec-tree and per language. LLM-driven; the skills are themselves validated by evals in this repo.
4. **Review** — the `reviewing-changes` skill. LLM-driven; validated by evals in this repo.

Two deterministic kinds (validation, testing) and two LLM kinds (auditing, review); the LLM kinds are themselves eval-validated.

## Proposed artifacts and placement

1. **Higher-level PDR** grounding the taxonomy. Proposed: top-level `spx/14-verification.pdr.md` (peer to the other foundational methodology decisions — `spx/15-test-language.adr.md`, `spx/16-evidence-execution-lanes.adr.md`, `spx/15-spec-coverage.adr.md`). A low top-level index constrains the evidence-lanes ADR, the kind-specific decisions at index 15, and the whole `spx/21-spec-tree.enabler/` verification subtree as descendants. The PDR carries the repo-specific detail (LLM kinds validated by evals in this repo / `outcomeeng_evals`).

2. **Understanding foundation reference** — new `src/plugins/spec-tree/skills/understanding/references/verification-kinds.md`, wired into `/understanding`: the core-references read list, a new numbered principle, the `<SPEC_TREE_FOUNDATION>` marker line, and the success criteria. Shipped and language-neutral: it states the four kinds and that the LLM kinds are eval-validated, without naming this repo. Two audiences — the reference is the consumer-facing authority; the PDR grounds it for this product.

3. **Reconcile the existing contract node** — `spx/21-spec-tree.enabler/16-verification.enabler/verification.md` currently carries a partial, informal `## Verification` section (three kinds: validation, auditing, reviewing — no "Testing", no determinism/eval framing). Trim that section; the node stays the verification *contract* (persistence model, verification discipline, wrapper-agent shape) and aligns under the new PDR.

## Distinct from related artifacts

- `spx/16-evidence-execution-lanes.adr.md` governs a different axis — assertion *evidence tags* (`[test]` / `[eval]` / `[review]`), not the runner taxonomy. The kinds map onto lanes (testing → `[test]`; auditing/review skills eval-validated via `[eval]`; validation is code-quality checking, not assertion evidence) but the two stay separate decisions.
- `spx/21-spec-tree.enabler/17-auditing.adr.md` and the `68-auditing.enabler` / `68-reviewing.enabler` nodes detail individual kinds; they derive from the umbrella PDR.

## Open questions for the authoring pass

- **PDR vs node shape.** This directory is staked as `14-verification.enabler`, but the proposal grounds the taxonomy in a top-level PDR (`spx/14-verification.pdr.md`). Decide whether the taxonomy lives in a top-level PDR alone, in this enabler node's spec governed by a lower-index PDR, or both. A PDR and this node both at index 14 are same-index peers and do not constrain each other — if the PDR must constrain this node, give the PDR a lower index.
- **Relationship to `spx/21-spec-tree.enabler/16-verification.enabler`.** Is the top-level node the umbrella (foundation/taxonomy) distinct from the deeper contract node, or should the contract move up under this node? Resolve before authoring to avoid two competing "verification" nodes.
- **Index confirmation.** Confirm index 14 against the top-level sibling set at authoring time.

## Authoring entry point

Invoke `/authoring` for the PDR and the understanding reference; `/contextualizing` on this node's parent first. Run the full audit + `just check` gate after authoring.
