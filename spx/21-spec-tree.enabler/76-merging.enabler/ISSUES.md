# Issues: PR Workflow Enabler

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/standardizing-merging` `<authority_gates>`, `/managing-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has no `merging.md` scenario assertion exercising the skip path and no dedicated eval.

The node's gate scenarios (`review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence`) each carry an `[eval]` link. A scenario for the skip path would fit that pattern:

> Given the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `merging.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

Not a retag of the `spx/15-agent-pr-authority.pdr.md` MUST rules: those are "the skill declares X" structural assertions, `[review]` per `spx/15-spec-coverage.adr.md`. The follow-up is the enabler-side scenario + eval, not a PDR evidence-tag change.

## 2. The five gate evals run in CI; the node is in `passing` state (RESOLVED)

All five eval suites — `review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence` — passed at 100% in CI run `26720175044` on commit `58b097c` (PR #95), every case clearing the `0.85` threshold (5/5, 6/6, 4/4, 5/5, 15/15 = 35/35 cases). The dominant prior failure mode — graded verdicts rejected as `verdict is not a parseable JSON document` because the model wrapped correct JSON in triple-backtick fences — is fixed by the grader change (`parse_verdict` retries after stripping one fence wrapper) and the runner change (a single `_FORMAT_SUFFIX` appended to every rendered prompt instructing raw-JSON output). Per `durable-map.md`'s node-state taxonomy the node is now `passing`: spec, evals, and implementation (the merging-related skills under `dist/claude/spec-tree`) exist and every assertion verifies. The node is removed from `spx/EXCLUDE`.

The `terminal-green` case-space remains complete: status-context `state == EXPECTED`, `PENDING`, `SUCCESS`, `ERROR`, `FAILURE` and every check-run conclusion the `terminal-green` definition in `spx/15-agent-pr-authority.pdr.md` names (15 cases).

The canonical `history.jsonl` baseline commits on the post-merge run on `main` — the workflow's `Commit history.jsonl appends` step is gated to `refs/heads/main` per `.github/workflows/spec-tree-evals.yml`, so PR runs collect run artifacts but do not commit them. The OAuth developer-session contamination caveat — workstation ambient instructions leaking into the verdict — is a developer-machine concern only; CI runs on a clean runner image, so the result above is the faithful validation surface even before `ANTHROPIC_API_KEY` joins the job env (tracked in the eval-harness `ISSUES.md`) and the workflow gains the `--bare` defense.

## 3. The local reviewing-changes no-findings renderer omits the no-DEBT signal (FOLLOW-UP)

The `MERGE_READINESS` clean-review predicate reads a review as clean when it reports no unresolved `BLOCKING` or `DEBT` finding per the reviewer's no-`BLOCKING`-or-`DEBT` convention (`REVIEW.template.md`: "post a one-line comment saying so" when there are no `BLOCKING` or `DEBT` findings). The CI `spec-tree-review` honors that convention — it posts `No BLOCKING or DEBT findings.`. The local `reviewing-changes` renderer's no-findings template (`src/plugins/spec-tree/skills/reviewing-changes/references/render/no-blockers.md`, emitted by `render_review.py` when no finding is present) still reads `No BLOCKING items.`, omitting the explicit no-`DEBT` signal.

This does not affect `MERGE_READINESS` — that predicate reads the CI review, which already carries the no-`DEBT` signal — so it is not a merge blocker for this PR. It is a parity-of-presentation gap that belongs to the reviewing-changes node, not this merge-flow node.

Required handling (owning node `spx/21-spec-tree.enabler/68-reviewing.enabler/`):

- Align `no-blockers.md` to the `REVIEW.template.md` convention (`No BLOCKING or DEBT findings.`).
- Re-check the per-severity finding templates (`finding-blocking.md`, `finding-debt.md`, `finding-followup.md`) and any reviewing-node assertion that pins the no-findings wording.
- Rebuild `dist` and re-run the reviewing node's evidence.
