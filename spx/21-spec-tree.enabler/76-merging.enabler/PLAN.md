# Plan: Merging Enabler

## Direct-push transport: remaining work

The `/merge` dispatcher and the direct-push variant-1 execution path (direct to `origin/main`) are built. The remaining direct-push work — variant 2 (direct to a local trunk checkout) and the `[audit]`→`[eval]` upgrade once a consumer needs the execution evidence — is tracked in `32-direct-push.enabler/PLAN.md`.

## Prose-grep-test lint (next session, validation gate)

Several "conformance" tests in this restructure were prose-greps — `assert "<heading>" in skill_body` — that verify a string was typed, not that the skill behaves. They were deleted this PR, but nothing prevents the anti-pattern from returning. Add a validation gate (the `reference-portability` gate is the model) that flags a test asserting the presence/absence of a string in a *skill/spec body* (a `.md` read into a `[test]`-lane Python test) as a non-coupling test. Home: the validation enabler (`spx/15-validation.enabler/`). Like the transport-selection eval suite that replaced the deleted prose-grep conformance tests, this gate restores real coupling where a prose-grep would otherwise stand in.

## Strengthen the assigned-CWD discipline assertion to `[eval]` (deferred evidence)

The assigned-worktree discipline assertion in `merging.md` is `[audit]`-backed today — sufficient to back the behavioral claim, verified at audit time. The behavioral merge rules it sits beside (`transport-selection`, `local-completion-boundary`) are `[eval]`-backed for deterministic, replayable coverage. Authoring a parallel `evals/assigned-worktree-discipline/` suite (eval.toml, cases.jsonl, prompt.md, history.jsonl) exercising worktree-conflict entry conditions — worktree on the default branch → create a task branch and continue; branch checked out in another worktree → create a fresh branch in the assigned worktree rather than stop; dirty tree → commit then re-sync, never stash — would lift it to `[eval]` parity. Deferred because a new eval suite with a baseline run is substantial evidence authoring beyond this change's scope, and the `[audit]` tag already backs the assertion with no coverage gap. Surfaced by the spec-tree-review CI on PR #333 (DEBT [evidence]).
