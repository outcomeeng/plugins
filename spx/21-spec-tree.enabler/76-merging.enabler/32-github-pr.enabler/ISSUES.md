# Issues: GitHub PR Transport

## 1. Eval implementation absent for PR orchestration scenarios (FOLLOW-UP)

`github-pr.md` defines the eval coverage model for the argument,
existing-changeset, clean-tree interview, local lifecycle overlay, and existing
open-PR modes. The node does not carry co-located eval implementations for
those cases, so the scenario assertions still rely on `[review]` evidence.
`[review]` fits LLM-driven orchestration behavior that no finite automated test
falsifies, but it leaves a structural regression (for example the skill body
losing its `<mode_detection>` block) undetected by the deterministic gate. The
Conformance assertions carry `[test]`, so the node's `tests/` directory covers
packaging and static routing properties only.

The eval lane can add scenarios mirroring the gate evals under
`spx/21-spec-tree.enabler/76-merging.enabler`:

- Add an `evals/<mode-slug>/` directory per mode with `eval.toml`,
  `cases.jsonl`, and `prompt.md` exercising mode detection from arguments
  and git state, the local overlay route, the existing-open-PR route, and the
  interview-first proposal boundary.
- Run them in the canonical CI execution surface and commit `history.jsonl`.

Surfaced by the local `changes-reviewer` on `feat/pr-skill`.

## 2. `/pr` cedes transport selection to `/merge` (FOLLOW-UP)

This node became the GitHub-PR transport under `spx/21-spec-tree.enabler/76-merging.enabler`, whose `merging.md` now declares `/merge` as the transport dispatcher: `/merge` reads `spx/local/merging.md`, selects the transport (GitHub-PR or direct-push), and delegates to it. The refocus of `/pr` from generic lifecycle router to GitHub-PR-transport orchestration is coupled to building the `/merge` skill, so it is deferred to the skill-materialization step.

When `/merge` is authored:

- Refocus `github-pr.md` `PROVIDES` to name `/pr` as the GitHub-PR transport's lifecycle orchestration invoked by `/merge`, not a generic router.
- Remove the transport-selection scenarios from `github-pr.md` (the "no local lifecycle overlay changes the route" and "declares a no-PR route ... overlay governs the lifecycle route instead of the default PR route" cases) and the "Local lifecycle overlay mode" bullet from the Eval Coverage Model — transport selection is `/merge`'s, declared in `merging.md`.
- Update the conformance test `tests/test_pr_orchestration.conformance.l1.py` accordingly (the `test_understanding_reads_local_merging_overlay` and `test_spec_describes_eval_model_without_eval_links` cases), and the `/understanding` overlay-routing prose it asserts, so the foundation routes through `/merge`.

Until then, `merging.md` (`/merge` selects the transport) and `github-pr.md` (`/pr` follows the overlay route) overlap on overlay handling — a known transient pending the `/merge` build, not a standing contradiction.
