# Plan: Merging Enabler

Coordination only; product truth lives in `spx/15-merging.pdr.md` and this node's spec.

## Lifecycle-order eval coverage for declared deploy and release phases

`tests/test_merge_gate_policy.mapping.l1.py` covers the deterministic gate mapping. No eval exercises
the phase ordering a declaring consumer depends on, and the node ships only the `transport-selection`
and `local-completion-boundary` suites. Add cases for:

- a declared `DEPLOY` requiring `DEPLOYMENT_READINESS`, and an absent declaration skipping the phase;
- a declared `RELEASE` running after `MERGE` and after any declared `DEPLOY`, and an absent
  declaration skipping the phase;
- a flow that stops after `MERGE` while a declared `RELEASE` remains.

This repository declares neither action, so the cases model a consumer that does; they verify the
shipped skills' phase ordering, not this repo's overlay.

## Direct-push transport: remaining work

The `/merge` dispatcher and the direct-push variant-1 execution path (direct to `origin/main`) are
built. The remaining direct-push work — variant 2 (direct to a local trunk checkout) and the
`[audit]`→`[eval]` upgrade once a consumer needs the execution evidence — is tracked in
`32-direct-push.enabler/PLAN.md`.

## Prose-grep-test lint (validation gate)

Prose-grep conformance tests — `assert "<heading>" in skill_body` — verify a string was typed, not
that the skill behaves. Add a validation gate (the `reference-portability` gate is the model) that
flags a test asserting the presence or absence of a string in a *skill/spec body* (a `.md` read into
a `[test]`-lane Python test) as a non-coupling test. Home: the validation enabler
(`spx/15-validation.enabler/`). Like the transport-selection eval suite that replaced prose-grep
conformance tests, this gate restores real coupling where a prose-grep would otherwise stand in.

## Add an explicit absent-overlay case to the transport-selection eval

The `[eval]`-backed `/merge` transport-selection assertion states `spx/local/merging.md` is read
"only when present — its absence is normal and applies the default lifecycle, never a blocker." The
`transport-selection` suite models the selector via `input.overlay_transport_selector`
(`none` / `direct-push` / `manage-github-pr`), and the `none` cases already exercise the
default-fallthrough outcome an absent overlay produces, so the behavioral claim is covered by
outcome. What is not modeled literally is present-but-silent versus file-absent. Adding the case
requires a new `cases.jsonl` entry, a `prompt.md` change so the producing skill is told the file is
absent, and a baseline run in `history.jsonl`. Best authored alongside the assigned-CWD eval below.
Surfaced by the local `changes-reviewer` on PR #333 (DEBT [evidence]).

## Add an `[eval]` case for the assigned-CWD branch-here-and-continue recovery

The assigned-worktree discipline assertion in `merging.md` is `[audit]`-backed and anchored by
`spx/15-merging.pdr.md` property 4. No `[eval]` case exercises the behaviorally novel recovery path:
assigned worktree on the default branch or a detached HEAD, or a branch another worktree owns → the
lifecycle creates a task branch in the assigned worktree and continues rather than stopping.
Authoring it needs an eval that models worktree-state inputs (current branch, detached HEAD, sibling
ownership), which the existing harnesses do not model, plus a `prompt.md` and a baseline
`history.jsonl` run. Surfaced by the local `changes-reviewer` on PR #333 (DEBT [evidence]).

## Strict-finding-disposition extraction

PR #447 ("fix(merging): make PR lifecycle portable across runtimes") closed unmerged on
2026-07-23. Its work survives only on `work/merge-skill-runtime-contracts` at
`6046ed5354fc02350cadade7d45f253d854ebfa0` — 82 commits that are neither ancestors of nor
patch-equivalent to the default branch, so nothing of it has shipped.

Decide the disposition before that branch is treated as either live or disposable: re-open the
lifecycle cluster as a new PR rebased onto current `main`, or retire the branch and re-derive
whatever of it still applies. The node-local changeset-scope, test-verification, review, and audit
contracts it consumed have moved since it closed, so the cluster needs re-reading against current
truth rather than a mechanical rebase.

Keep one PR when the authored `/merge`, `/open-pr`, `/manage-github-pr`, `/manage-pr`, shared
readiness rules, action tokens, and first affected merging specs form one portable lifecycle contract
with one rollback boundary. Split any independently mergeable review-result implementation or
verifier infrastructure into its owning node.
