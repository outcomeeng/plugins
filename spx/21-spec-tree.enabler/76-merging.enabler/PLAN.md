# Plan: Merging Enabler

## Eval recalibration (out-of-band)

The `production-readiness` eval (`ISSUES.md`) and the `merge-readiness` eval data-model change (`32-github-pr.enabler/54-managing-pr.enabler/ISSUES.md` item 5, now also carrying the bounded-vs-deferrable disposition dimension) require live eval re-runs; they ride the next eval-coverage sweep, not a mechanical edit.

## Direct-push transport: remaining work

The `/merge` dispatcher and the direct-push variant-1 execution path (direct to `origin/main`) are built. The remaining direct-push work — variant 2 (direct to a local trunk checkout) and the `[audit]`→`[eval]` upgrade once a consumer needs the execution evidence — is tracked in `32-direct-push.enabler/PLAN.md`.

## `/merge` transport-selection: `[audit]` → `[eval]` (next session)

`merging.md` Compliance declares `/merge`'s transport selection and delegation as `[audit]` (the line-23 transport-dispatch rule and the `/merge` selection + delegation Compliance assertions). Transport selection is LLM-driven orchestration with a determinate expected answer per case — overlay-declared → that transport; coordination-note-only → direct-push; mixed or empty → GitHub-PR; then the right delegation — so it is `[eval]`-shaped, not `[audit]`. Author an `evals/transport-selection/` suite (`eval.toml`, `cases.jsonl`, `prompt.md`) replaying a changeset state + overlay → expected transport across each precedence branch, retag the affected assertions `[audit]`→`[eval]`, and make the suite pass through the eval harness (mirroring the existing gate evals under this node). Until then the behavior is audit-backed only.

## Prose-grep-test lint (next session, validation gate)

Several "conformance" tests in this restructure were prose-greps — `assert "<heading>" in skill_body` — that verify a string was typed, not that the skill behaves. They were deleted this PR, but nothing prevents the anti-pattern from returning. Add a validation gate (the `reference-portability` gate is the model) that flags a test asserting the presence/absence of a string in a *skill/spec body* (a `.md` read into a `[test]`-lane Python test) as a non-coupling test. Home: the validation enabler (`spx/15-validation.enabler/`). Pair it with the transport-selection evals above — both restore real evidence where prose-greps stood in.
