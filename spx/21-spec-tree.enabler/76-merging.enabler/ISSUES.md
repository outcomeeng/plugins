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

## 3. The local reviewing-changes no-findings render (RESOLVED)

**Resolved** in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`. The local `reviewing-changes` renderer now reports a uniform per-severity census: each empty severity bucket renders its `none-<severity>.md` marker (`BLOCKING: none` / `DEBT: none` / `FOLLOW-UP: none`), and the single blocking-only `no-blockers.md` was replaced by `none-blocking.md` / `none-debt.md` / `none-followup.md`. This separates the reviewer's mechanical census from the consumer's merge judgment, superseding the originally-prescribed single-line alignment of `no-blockers.md` to `"No BLOCKING or DEBT findings."` (the earlier framing of `no-blockers.md` as a "no findings" message was imprecise — it was the BLOCKING-section empty-state; the census model reports every severity uniformly). Format parity between the local render and the GH CI `spec-tree-review` workflow's clean-review message lives in `outcomeeng/gh-actions` and is a separate concern if pursued.

## 4. Heartbeat continuation-prompt payload shape is skill prose, not a spec assertion (FOLLOW-UP)

`/tracking-tasks` `<heartbeat_payload>` and `/standardizing-merging` `<heartbeat>` define the continuation prompt as exactly the skills to reload plus the pointers each skill handles, with the directive, finding assessments, and rationale reconstructed on wake-up from the durable artifacts. The constraint lives only as skill prose and a `/tracking-tasks` success-criterion; no `merging.md` assertion declares it and no eval verifies that a `/managing-pr` heartbeat prompt conforms to the two-item structure.

This is the deferred "declare in the spec" path: the change shipped as skill prose only by operator decision. To govern and verify the behavior when an eval-coverage sweep happens:

- Add a compliance assertion to `merging.md` declaring the heartbeat re-entry payload (skills + pointers, no reconstructable state), as the PR-flow instance of the `/tracking-tasks` rule.
- Create `evals/heartbeat-payload/` (`eval.toml`, `cases.jsonl`, `prompt.md`) exercising whether a `/managing-pr` heartbeat prompt carries only the skill re-entry and the PR-number pointer, with the directive, finding assessments, and rationale reconstructed rather than restated.
- Run the eval to populate `history.jsonl`.

Same shape as item 1: an enabler-side assertion + eval, not a `spx/15-agent-pr-authority.pdr.md` evidence-tag change.
