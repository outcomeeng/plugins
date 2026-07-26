# Plan: Merging Enabler

## Delivery lifecycle and readiness-gate rewrite

This plan records the coordinated top-down rewrite for the merge lifecycle. It is coordination only; product truth enters through the PDR, then the first affected specs, then tests, evals, shipped skills, and repo-local overlay.

### Concept

The lifecycle becomes an ordered delivery sequence:

```text
VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE
```

The readiness gates become:

- `VERIFICATION_READINESS`: the selected transport's verification predicates hold for the changeset. The predicates are drawn from the verification taxonomy in `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`: `validate`, `test`, `evaluate`, `review`, and `audit`. Generic shipped skills must leave the concrete local command set and verifier set to the consumer project or transport.
- `MERGE_READINESS`: the selected transport's current-head integration predicates hold: required checks are terminal-green, required integration review state is clean, and branch or pull-request state is acceptable.
- `DEPLOYMENT_READINESS`: any environment mutation after merge is authorized by the project or transport predicates that govern that environment. When no deploy phase is declared, the phase is a no-op.
- `RELEASE_READINESS`: any consumer-visible publication or refresh after deployment is authorized by the project or transport predicates that govern release. When no release phase is declared, the phase is a no-op.

`PRODUCTION_READINESS` exits the model because `production` is not a portable project boundary. Deployment and release are different delivery actions: a project can deploy without releasing, release without an environment deployment, or do both under different predicates.

`REVIEW_READINESS` exits the model because review is one verification type, while the verification phase can include deterministic verification (`validate`, `test`, `evaluate`) and agentic verification (`review`, `audit`). Review remains a verification type and a possible predicate inside `VERIFICATION_READINESS`; it no longer names the whole first gate.

`CLOSE` is the lifecycle reporting, handoff, continuation, or archive decision after every declared phase has either completed or stopped at its explicit gate. It does not replace the Spec Tree rule that specs themselves are never closed.

### Invariants to Preserve

- One word, `gate`, names each authorization point; every condition a gate reads is a predicate.
- Transports bind predicates and actions for the ordered phases; they do not reorder the lifecycle.
- Absence of `PREVIEW`, `DEPLOY`, or `RELEASE` declarations means a no-op phase, never a blocker.
- Generic shipped plugin content stays portable: no marketplace commands, Vercel-specific assumptions, repo-local paths, or single-consumer verification policy.
- A consumer's release action is that consumer's own overlay declaration, never shared methodology.
- `spx/21-spec-tree.enabler/76-merging.enabler/15-merging.pdr.md` does not exist; the governing decision is the product-level `spx/15-merging.pdr.md`. Keep it there unless a later decomposition has a concrete reason to split it.

### First Observable Slice

Observable path: a default-branch-bound changeset runs through `/merge` or the selected transport and reaches the ordered lifecycle, with declared phases executed in order and absent phases skipped.

- Invocation: `/merge` on a committed or dirty changeset, or `/manage-github-pr` when the GitHub-PR transport is already selected for an open PR.
- Input shape: changeset, base ref, selected transport, and optional overlay declarations for `PREVIEW`, `DEPLOY`, and `RELEASE`.
- Behavior: establish `VERIFICATION_READINESS`, run any declared `PREVIEW`, merge under `MERGE_READINESS`, run any declared `DEPLOY` under `DEPLOYMENT_READINESS`, run any declared `RELEASE` under `RELEASE_READINESS`, then close or continue.
- State change: the changeset reaches the default branch on origin, and any declared deploy or release action runs after the merge in phase order.
- Inspection surface: skill status prose, action tokens, PR/check state for PR transports, deterministic tests, eval cases, and whatever state a consumer's declared deploy or release action changes.
- Failure behavior: a missing predicate stops at the named readiness gate with an observable action token or report; a declared release cannot be skipped after merge.
- Verification: spec validation, status check, changed-node tests, lifecycle eval cases, and skill audit after `SKILL.md` edits.

### PR Sequence

1. **Decision PR: lifecycle vocabulary and first lower-spec alignment**
   - Edit `spx/15-merging.pdr.md` to declare the phase sequence and four readiness gates.
   - Replace `REVIEW_READINESS` with `VERIFICATION_READINESS`.
   - Replace `PRODUCTION_READINESS` with `DEPLOYMENT_READINESS` and `RELEASE_READINESS`.
   - Preserve `MERGE_READINESS`, the finding-disposition policy, transport neutrality, assigned-worktree discipline, no time-based settle, and pre-mutation confirmation as an overlay touch-point rather than a gate.
   - Align first affected specs in the same changeset:
     - `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`
     - `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/github-pr.md`
     - `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/32-opening-pr.enabler/opening-pr.md`
     - `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/54-managing-pr.enabler/managing-pr.md`
     - `spx/21-spec-tree.enabler/76-merging.enabler/32-direct-push.enabler/direct-push.md`
   - Record any lower-layer implementation left outside the PR in this `PLAN.md`, tied to the exact affected node.
   - Verification: `spx validation markdown`, `spx spec status --format json`, and the focused tests or evals whose assertions change.

2. **Shared methodology PR: shipped lifecycle vocabulary**
   - Update `src/plugins/spec-tree/skills/merging-standards/SKILL.md` with the phase order, four gate names, predicate rules, and no-op defaults for undeclared `PREVIEW`, `DEPLOY`, and `RELEASE`.
   - Keep consumer verification content open: the shipped standard explains where predicates bind, while the consumer project or transport declares concrete commands, reviewers, checks, previews, deployments, and releases.
   - Update any shared references or generated text that still teaches the three-gate model.
   - Regenerate shipped plugin trees through `just build-skills`.
   - Verification: `just check-skills`, `just docs-check`, focused merging tests, and skill audit.

3. **Transport PR: GitHub-PR and direct-push execution**
   - Update `/merge`, `/open-pr`, `/manage-github-pr`, and `/manage-pr` flow prose to drive:
     `VERIFICATION_READINESS -> PREVIEW -> MERGE_READINESS -> MERGE -> DEPLOYMENT_READINESS -> DEPLOY -> RELEASE_READINESS -> RELEASE -> CLOSE`.
   - Replace `POST_MERGE_VERIFY` with phase progression. A merged PR with a declared release continues to `RELEASE`; it does not exit at merge.
   - Keep `/open-pr` focused on publishing once `VERIFICATION_READINESS` holds; keep `/manage-pr` focused on current-head integration plus later declared phases.
   - Update direct-push to use the same phase sequence, with its transport-specific predicates bound locally.
   - Remove the retired production-readiness implementation and tests once the transport flow and shared methodology use `DEPLOYMENT_READINESS` and `RELEASE_READINESS`.
   - Verification: focused tests for gate mapping and transport behavior, lifecycle eval cases, `just check-skills`, `just docs-check`, and skill audit.

4. **Eval and regression PR: lifecycle order evidence**
   - Add or update eval coverage for:
     - declared `PREVIEW` runs before merge-relevant advancement;
     - absent `PREVIEW` is a no-op;
     - declared `DEPLOY` requires `DEPLOYMENT_READINESS`;
     - absent `DEPLOY` is a no-op;
     - declared `RELEASE` runs after `MERGE` and after any declared `DEPLOY`;
     - absent `RELEASE` is a no-op;
     - a flow that stops after `MERGE` fails when `RELEASE` is declared.
   - Add deterministic mapping coverage for the two newly declared target assertions:
     - `test_declared_deploy_without_authorization_awaits_deployment_authorization`;
     - `test_absent_deploy_declaration_skips_deploy`;
     - `test_declared_release_without_authorization_awaits_release_authorization`;
     - `test_absent_release_declaration_skips_release`.
   - Add lifecycle eval cases for the same observable outcomes when the subject is skill orchestration rather than the pure mapping helper:
     - `declared-deploy-awaits-authorization`;
     - `absent-deploy-skips-phase`;
     - `declared-release-awaits-authorization`;
     - `absent-release-skips-phase`.
   - Rename eval prompts and cases from `review-readiness` and production-readiness vocabulary only where their subject changes; keep review-specific evals when the subject is the `review` verification type.
   - Verification: `just eval-case` or `just eval-node` for changed eval suites, plus focused tests that enforce skill/spec coupling.

5. **Cleanup PR: stale vocabulary and docs sweep**
   - Sweep authored and generated surfaces for stale lifecycle terms:
     - `REVIEW_READINESS` where the subject is the first readiness gate;
     - `PRODUCTION_READINESS`;
     - `post-merge verification`;
     - `post-merge steps` where the phase is really deploy or release.
   - Keep occurrences where the old term appears only in historical migration notes or intentionally quoted old behavior; those occurrences need an explicit reason.
   - Verification: targeted grep review, `just check-skills`, `just docs-check`, and spec-only validation.

### Surfaces Known to Change

- `spx/15-merging.pdr.md`
- `spx/21-spec-tree.enabler/76-merging.enabler/merging.md`
- `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/github-pr.md`
- `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/32-opening-pr.enabler/opening-pr.md`
- `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/54-managing-pr.enabler/managing-pr.md`
- `spx/21-spec-tree.enabler/76-merging.enabler/32-direct-push.enabler/direct-push.md`
- `src/plugins/spec-tree/skills/merging-standards/SKILL.md`
- `src/plugins/spec-tree/skills/merge/SKILL.md`
- `src/plugins/spec-tree/skills/open-pr/SKILL.md`
- `src/plugins/spec-tree/skills/manage-github-pr/SKILL.md`
- `src/plugins/spec-tree/skills/manage-pr/SKILL.md`
- lifecycle eval prompts, cases, histories, and tests under `spx/21-spec-tree.enabler/76-merging.enabler/`

### Naming Guardrails

- Use `VERIFICATION_READINESS` for the first gate.
- Use `review` only for the verification type or for reviewer/finding mechanics.
- Use `DEPLOYMENT_READINESS` only for environment mutation authorization.
- Use `RELEASE_READINESS` only for publication or refresh authorization.
- Use `RELEASE` for a consumer-declared publication or refresh action.
- Use full `spx/...` paths for decisions and nodes in PR descriptions and follow-up notes.

## Direct-push transport: remaining work

The `/merge` dispatcher and the direct-push variant-1 execution path (direct to `origin/main`) are built. The remaining direct-push work — variant 2 (direct to a local trunk checkout) and the `[audit]`→`[eval]` upgrade once a consumer needs the execution evidence — is tracked in `32-direct-push.enabler/PLAN.md`.

## Prose-grep-test lint (next session, validation gate)

Prose-grep conformance tests — `assert "<heading>" in skill_body` — verify a string was typed, not that the skill behaves. Add a validation gate (the `reference-portability` gate is the model) that flags a test asserting the presence/absence of a string in a *skill/spec body* (a `.md` read into a `[test]`-lane Python test) as a non-coupling test. Home: the validation enabler (`spx/15-validation.enabler/`). Like the transport-selection eval suite that replaced prose-grep conformance tests, this gate restores real coupling where a prose-grep would otherwise stand in.

## Add an explicit absent-overlay case to the transport-selection eval

The `[eval]`-backed `/merge` transport-selection assertion now states `spx/local/merging.md` is read "only when present — its absence is normal and applies the default lifecycle, never a blocker." The `transport-selection` eval's ten cases model the selector via `input.overlay_transport_selector` (`none` / `direct-push` / `manage-github-pr`); the `none` cases already exercise the default-fallthrough outcome that an absent overlay produces (default transport, `PROCEED_AUTONOMOUSLY` — no blocker), so the behavioral claim is covered by outcome. What is not modeled literally is the present-but-silent vs. file-absent distinction. Adding an explicit absent-overlay case requires a new `cases.jsonl` entry plus a `prompt.md` change so the producing skill is told the file is absent, plus a baseline run in `history.jsonl`. Deferred as incremental evidence-completeness: the eval suite is not part of the `just check` / CI gate, the outcome is already covered by the `none` cases, and literal absent-file modeling is best authored alongside the assigned-CWD `[eval]` work above. Surfaced by the local `changes-reviewer` on PR #333 (DEBT [evidence]).

## Add an `[eval]` case for the assigned-CWD branch-here-and-continue recovery

The assigned-worktree discipline assertion in `merging.md` is `[audit]`-backed (the skills teach it; an audit reads the skill text), and the governing PDR (`spx/15-merging.pdr.md` property 4) anchors it. What no `[eval]` case yet exercises is the behaviorally novel recovery path: assigned worktree on the default branch or a detached HEAD, or a branch owned by another worktree → the lifecycle creates a task branch in the assigned worktree and continues (a `BRANCH_AND_CONTINUE`-style outcome) rather than emitting a `STOP`. Authoring this needs an eval that models worktree-state inputs (current branch, detached HEAD, sibling-worktree branch ownership), which the `transport-selection` / `local-completion-boundary` eval harnesses do not model today, plus a `prompt.md` and a baseline `history.jsonl` run. Deferred as incremental behavioral evidence: the assertion is `[audit]`-backed and PDR-anchored (no unbacked gap), evals are not part of the `just check` / CI gate, and this is best authored alongside the absent-overlay eval case above. Surfaced by the local `changes-reviewer` on PR #333 (DEBT [evidence]).

## Strict-finding-disposition extraction

PR #447 on `work/merge-skill-runtime-contracts` is the merge-owned consumer cycle. Reconcile it only after the node-local changeset-scope, test-verification, review, and audit contracts it consumes have converged on `origin/main`.

Keep one PR when the authored `/merge`, `/open-pr`, `/manage-github-pr`, `/manage-pr`, shared readiness rules, action tokens, and first affected merging specs form one portable lifecycle contract with one rollback boundary. Split any independently mergeable review-result implementation or verifier infrastructure into its owning node.

**Revisit condition:** update this section after PR #447 is rebased onto its merged prerequisites and a current semantic-cohesion review either approves that lifecycle cluster or identifies the exact replacement PR sequence.
