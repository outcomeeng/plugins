# Plan: Merging Enabler

## Direct-push transport: remaining work

The `/merge` dispatcher and the direct-push variant-1 execution path (direct to `origin/main`) are built. The remaining direct-push work — variant 2 (direct to a local trunk checkout) and the `[audit]`→`[eval]` upgrade once a consumer needs the execution evidence — is tracked in `32-direct-push.enabler/PLAN.md`.

## Prose-grep-test lint (next session, validation gate)

Several "conformance" tests in this restructure were prose-greps — `assert "<heading>" in skill_body` — that verify a string was typed, not that the skill behaves. They were deleted this PR, but nothing prevents the anti-pattern from returning. Add a validation gate (the `reference-portability` gate is the model) that flags a test asserting the presence/absence of a string in a *skill/spec body* (a `.md` read into a `[test]`-lane Python test) as a non-coupling test. Home: the validation enabler (`spx/15-validation.enabler/`). Like the transport-selection eval suite that replaced the deleted prose-grep conformance tests, this gate restores real coupling where a prose-grep would otherwise stand in.

## Add an explicit absent-overlay case to the transport-selection eval

The `[eval]`-backed `/merge` transport-selection assertion now states `spx/local/merging.md` is read "only when present — its absence is normal and applies the default lifecycle, never a blocker." The `transport-selection` eval's ten cases model the selector via `input.overlay_transport_selector` (`none` / `direct-push` / `manage-github-pr`); the `none` cases already exercise the default-fallthrough outcome that an absent overlay produces (default transport, `PROCEED_AUTONOMOUSLY` — no blocker), so the behavioral claim is covered by outcome. What is not modeled literally is the present-but-silent vs. file-absent distinction. Adding an explicit absent-overlay case requires a new `cases.jsonl` entry plus a `prompt.md` change so the producing skill is told the file is absent, plus a baseline run in `history.jsonl`. Deferred as incremental evidence-completeness: the eval suite is not part of the `just check` / CI gate, the outcome is already covered by the `none` cases, and literal absent-file modeling is best authored alongside the assigned-CWD `[eval]` work above. Surfaced by the local `changes-reviewer` on PR #333 (DEBT [evidence]).
