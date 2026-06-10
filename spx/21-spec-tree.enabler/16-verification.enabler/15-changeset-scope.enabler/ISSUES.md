# Issues: Changeset Scope Enabler

## 1. No base-advance overlap primitive — PR-flow conflict prediction gets hand-rolled (FOLLOW-UP)

This node provides `branch_scope` / `expand_diff_range` / `remote_tracking_ref` for deriving a changeset's **own** diff against `origin/<base>` (three-dot, merge-base). It has no primitive for the inverse PR-flow question: **"the base advanced — what did the advancing commits change, and does that overlap my branch's changed-file set?"** That is the question `/pr` and `/managing-pr` `<base_sync>` must answer to predict a rebase conflict before rebasing.

**Observed failure (2026-06-10, branch `feat/two-severity-review-taxonomy`).** Lacking a primitive, the PR flow hand-rolled `git diff HEAD..origin/main` — a **two-dot** diff, which is the total tree difference and therefore lists every file the branch itself changed. The advancing commit had only appended 7 lines across `evals/*/history.jsonl`, but the two-dot output made it look like upstream had rewritten all ~50 of the branch's changed files, producing a false "near-100% overlap, expect heavy conflicts" read. The correct derivation is the advancing commits' **own** change set — `git diff-tree --no-commit-id --name-only -r` over the `HEAD..origin/<base>` commits — intersected with the branch's changed-file set from `branch_scope`.

**My stance / required handling.**

- Add a primitive here — e.g. `base_advance_paths(base)` returning the changed-file set of the `HEAD..origin/<base>` commits (the commits the branch is behind), and an `overlap(base)` helper intersecting it with the branch's own `branch_scope` set. That intersection is the conflict-prediction surface; empty intersection ⇒ a clean rebase.
- Add a Compliance/Audit NEVER here and propagate it into `standardizing-merging` `<base_sync>` / `<branch_topology>`: base-advance / overlap / conflict prediction routes through changeset-scope, **NEVER** an ad-hoc `git diff A..B`. Two-dot `A..B` is banned for any "what changed" question — it conflates the branch's own edits with the base's. Three-dot (`A...B`) or per-commit `diff-tree` is the only correct form.
- This is the same class of rule the node already enforces for diff **widening** (the `origin/<base>` three-dot scoping in `13-changeset-derivation.adr.md`); extend it to the base-advance / overlap direction so the two halves of "scope a changeset against a moving base" both have one owner.

Surfaced during the `feat/two-severity-review-taxonomy` PR flow (2026-06-10): the two-dot overlap blunder produced a wrong conflict-risk assessment and an avoidable reconciliation detour.

## 2. No proactive stale-base pre-check at work-start in a multi-worktree pool (FOLLOW-UP)

This node fixes stale-local-ref diff **widening** at scope-derivation time — reviews and audits scope against the fetched `origin/<base>`, so a lagging local `main` cannot widen them (`13-changeset-derivation.adr.md`). It does **not** warn, **before** substantial work begins, that the working tree itself is N commits behind `origin/<base>` — the precondition that makes a large reconciliation necessary in the first place.

**Observed failure (2026-06-10).** A bare-repo pool worktree (per `spx/21-spec-tree.enabler/11-repository-layout.pdr.md`) was parked ~4 merged PRs behind `origin/main`. An entire multi-node change — a decision record plus a cross-skill cascade plus audits — was authored on that stale base, and the staleness only surfaced at PR-open time, forcing a full rebase + re-verify + re-audit and a manifest-version reconciliation. The `reviewing-changes` `ISSUES.md` items #2 and #7 already document multi-worktree staleness as a recurring hazard; nothing pre-checks it.

**My stance / required handling.**

- Add a work-start staleness pre-check: `git fetch origin <base>` then surface when `HEAD` is behind (`git rev-list --count HEAD..origin/<base>`), and — higher signal — when the base-advance overlaps files the session is about to edit (reuse the `overlap` primitive from item 1).
- Placement is debatable: the primitive belongs **here** (changeset-scope owns base-ref derivation), but the **invocation** belongs where work starts — a `/pr` pre-flight, a `/contextualizing` step, or a session-start check keyed off the `11-repository-layout` pool topology. Decide placement when authoring; do not bury a heavy check in a hot path.
- Goal: surface "you are on a stale base — rebase first" **before** the work, so the fix is a one-line rebase rather than a post-hoc merge of a change that diverged from main while it was being written.

Surfaced during the `feat/two-severity-review-taxonomy` session (2026-06-10).
