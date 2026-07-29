# Issues: GitHub PR Transport

## 1. Eval implementation absent for PR orchestration scenarios (FOLLOW-UP)

`github-pr.md` defines the eval coverage model for the argument,
existing-changeset, clean-tree interview, and existing open-PR modes. The node
does not carry co-located eval implementations for those cases, so the scenario
assertions rely on `[audit]` evidence.
`[audit]` fits LLM-driven orchestration behavior that no finite automated test
falsifies, but it leaves a structural regression (for example the skill body
losing its `<mode_detection>` block) undetected by the deterministic gate.
Packaging, frontmatter intent, and closeout semantics use `[audit]`; deterministic
tests do not parse skill Markdown as a proxy for LLM-driven orchestration behavior.

The eval lane can add scenarios mirroring the gate evals under
`spx/21-spec-tree.enabler/76-merge.enabler`:

- Add an `evals/<mode-slug>/` directory per mode with `eval.toml`,
  `cases.jsonl`, and `prompt.md` exercising mode detection from arguments
  and git state, the existing-open-PR route, and the interview-first proposal
  boundary. The interview-first boundary is the case where this transport is
  already selected — `/merge` chose GitHub-PR, or `/manage-github-pr` was invoked directly —
  and the working tree is clean; transport selection is complete at that point,
  so the `/manage-github-pr` eval scope never covers transport-selection logic (that is
  `/merge`'s, declared in `merging.md`).
- Run them in the canonical CI execution surface and commit `history.jsonl`.

Surfaced by the local `changes-reviewer` on `feat/pr-skill`.
