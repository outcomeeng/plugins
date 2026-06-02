# Issues: PR Workflow Enabler

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/standardizing-merging` `<authority_gates>`, `/managing-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has no `merging.md` scenario assertion exercising the skip path and no dedicated eval.

The node's gate scenarios (`review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence`) each carry an `[eval]` link. A scenario for the skip path would fit that pattern:

> Given the CI `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main" and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `merging.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

Not a retag of the `spx/15-agent-pr-authority.pdr.md` MUST rules: those are "the skill declares X" structural assertions, `[review]` per `spx/15-spec-coverage.adr.md`. The follow-up is the enabler-side scenario + eval, not a PDR evidence-tag change.

## 2. The five gate evals run in CI; the node is in `passing` state (RESOLVED)

All five eval suites — `review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence` — passed at 100% in CI run `26720175044` on commit `58b097c` (PR #95), every case clearing the `0.85` threshold (5/5, 6/6, 4/4, 5/5, 15/15 = 35/35 cases). The dominant prior failure mode — graded verdicts rejected as `verdict is not a parseable JSON document` because the model wrapped correct JSON in triple-backtick fences — is fixed by the grader change (`parse_verdict` retries after stripping one fence wrapper) and the runner change (a single `_FORMAT_SUFFIX` appended to every rendered prompt instructing raw-JSON output). Per `durable-map.md`'s node-state taxonomy the node is now `passing`: spec, evals, and implementation (the merging-related skills under `dist/claude/spec-tree`) exist and every assertion verifies. The node is removed from `spx/EXCLUDE`.

The `terminal-green` case-space remains complete: status-context `state == EXPECTED`, `PENDING`, `SUCCESS`, `ERROR`, `FAILURE` and every check-run conclusion the `terminal-green` definition in `spx/15-agent-pr-authority.pdr.md` names (15 cases).

The canonical `history.jsonl` baseline commits on the post-merge run on `main` — the workflow's `Commit history.jsonl appends` step is gated to `refs/heads/main` per `.github/workflows/spec-tree-evals.yml`, so PR runs collect run artifacts but do not commit them. The OAuth developer-session contamination caveat — workstation ambient instructions leaking into the verdict — is a developer-machine concern only; CI runs on a clean runner image, so the result above is the faithful validation surface even before `ANTHROPIC_API_KEY` joins the job env (tracked in the eval-harness `ISSUES.md`) and the workflow gains the `--bare` defense.

## 3. `opening-pr` Step 3 iteration omits the joint-fixpoint loop (FOLLOW-UP)

`/opening-pr` Step 3b's iteration instruction says "after every iteration that commits, re-run `<branch_hygiene>` and re-run deterministic verification so both predicates stay current" — it does not state that a verification-driven fix must also re-run the local review (and that a review-driven fix must re-run verification). `/managing-pr` Step 6 spells out this joint-fixpoint loop explicitly: "Any fix in either sub-step mutates the tree, so loop … re-run both predicates after every commit until a single tree passes deterministic verification and carries no unaddressed valid finding." An agent following `/opening-pr` alone could push a tree whose local-review predicate was established before the last verification-driven fix. The `<failure_modes>` section added to `opening-pr` in `fix/merging-review-by-shape` mirrors the same omission.

Required handling:

- Extend `/opening-pr` Step 3's iteration instruction to match the joint-fixpoint loop principle from `/managing-pr` Step 6 — re-run BOTH `REVIEW_READINESS` predicates after every commit until one tree passes both, and push only that tree.
- Update the `opening-pr` `<failure_modes>` entry to name both predicates explicitly.
- Rebuild `dist/` after editing `src/`.

Surfaced by the local `changes-reviewer` on `fix/merging-review-by-shape`. Out of scope for that PR (the merge-review-predicate reframe); this is a pre-existing completeness gap in `opening-pr`'s iteration semantics.
