# Issues: PR Orchestration Enabler

## 1. Scenario assertions lack eval-backed coverage (FOLLOW-UP)

The three Scenario assertions in `pr-orchestration.md` — the argument,
existing-changeset, and clean-tree interview modes — carry `[review]`
evidence. `[review]` fits LLM-driven orchestration behavior that no finite
automated test falsifies, but it leaves a structural regression (for
example the skill body losing its `<mode_detection>` block) undetected by
the gate. The Conformance assertion already carries a `[test]`, so the
node's `tests/` directory exists.

A future eval-coverage sweep can add `[eval]` scenarios mirroring the
sibling `spx/21-spec-tree.enabler/76-merging.enabler` gate evals:

- Add an `evals/<mode-slug>/` directory per mode with `eval.toml`,
  `cases.jsonl`, and `prompt.md` exercising mode detection from arguments
  and git state, and the interview-first proposal boundary.
- Run them in the canonical CI execution surface and commit `history.jsonl`.

Surfaced by the local `changes-reviewer` on `feat/pr-skill`.
