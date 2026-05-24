# Issues: PR Workflow Enabler

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/standardizing-merging` `<pr_authority_gate>`, `/managing-pr` Step 7, the `MENTION_REVIEW_NEEDED` action token — was added without a `pr-workflow.md` scenario assertion exercising the skip path, and without a corresponding eval.

The node's other gate scenarios (`authority-gate-green`, `authority-gate-production`, `overlay-human-promotion`, `overlay-human-merge`, `authority-gate-hygiene`) each carry an `[eval]` link. A scenario for the skip path would fit that pattern:

> Given `spec-tree-review / spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main" and no current-head three-severity review exists, when the managing flow evaluates the PR authority gate, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `pr-workflow.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

Not a retag of the `spx/15-agent-pr-authority.pdr.md` MUST rules: those rules are "the skill declares X" structural assertions, `[review]` per `spx/15-spec-coverage.adr.md` and consistent with every other MUST rule in that PDR. The follow-up is the enabler-side scenario + eval, not a PDR evidence-tag change.

Deferred from the PR that folded in the reviewer-skipped exception — adding a new eval directory plus a paid eval run is additional scope beyond that PR's realignment-and-integration deliverable.
