# Issues: PR Orchestration Enabler

## 1. Eval implementation absent for PR orchestration scenarios (FOLLOW-UP)

`pr-orchestration.md` defines the eval coverage model for the argument,
existing-changeset, clean-tree interview, local lifecycle overlay, and existing
open-PR modes. The node does not carry co-located eval implementations for
those cases, so the scenario assertions still rely on `[review]` evidence.
`[review]` fits LLM-driven orchestration behavior that no finite automated test
falsifies, but it leaves a structural regression (for example the skill body
losing its `<mode_detection>` block) undetected by the deterministic gate. The
Conformance assertions carry `[test]`, so the node's `tests/` directory covers
packaging and static routing properties only.

The eval lane can add scenarios mirroring the sibling
`spx/21-spec-tree.enabler/76-merging.enabler` gate evals:

- Add an `evals/<mode-slug>/` directory per mode with `eval.toml`,
  `cases.jsonl`, and `prompt.md` exercising mode detection from arguments
  and git state, the local overlay route, the existing-open-PR route, and the
  interview-first proposal boundary.
- Run them in the canonical CI execution surface and commit `history.jsonl`.

Surfaced by the local `changes-reviewer` on `feat/pr-skill`.
