# Plan: complete instructions follow-ups

This plan preserves two dependency-ordered continuations. Complete the PR 465
track before beginning the create-skill contract track so the open pull request
remains one reviewable unit.

## Complete PR 465

PR 465 remains open from `work/inline-foundation-salvage`, with remote head
`f2a3b97c2abf5d9344ebac9b24cbe55c38a62801`. The repaired, hardened changeset
lives on `work/inline-foundation-salvage-restart`, rebased onto the current
`origin/main`; its commit SHAs are checkout-local and change on every rebase, so
this plan names restart-branch history by branch rather than by SHA. The
pre-rebase preserved head `35001274a20170236016f45aa6403a3fb132f5c4` identifies
the local `work/inline-foundation-salvage` branch content, not the restart
branch. Base synchronization advanced over governance surfaces, so any
verification evidence produced before the rebase is superseded and re-run on the
current base.

Worklist:

1. Start in a runtime where the typed `skill-auditor` and `changes-reviewer`
   roles are available, invoke `/understand`, and contextualize
   `spx/43-instructions.enabler/21-skills.enabler`.
2. Claim the restart session and branch, confirm the complete restart head and
   the live PR 465 remote head, and leave `work/inline-foundation-salvage`
   unpublished until verification readiness holds.
3. Run the focused deterministic lane for the committed restart head:
   `just build-skills`, formatting for changed Markdown, `just check-skills`,
   `just docs-check`, `spx validation markdown`, and
   `spx spec status --format json`.
4. Dispatch a complete-bundle `skill-auditor` over every changed skill file and
   bundled reference in the PR changeset. Resolve every valid bounded finding,
   then repeat the focused lane and audit on a new clean commit.
5. Dispatch `changes-reviewer` against the clean committed head and render its
   sealed review run. Resolve every valid bounded finding and repeat the
   affected deterministic and agentic gates on the new head.
6. After all applicable agentic gates converge on one clean committed head, run
   the terminal full deterministic gate `just check-full` once.
7. Invoke `/sync-base` again. Re-establish any evidence invalidated by base
   movement, then publish the verified history to
   `work/inline-foundation-salvage` through `/manage-pr` with a guarded
   force-with-lease against the observed remote head.
8. Manage PR 465 through current-head integration review and terminal-green
   required checks, merge it, complete the marketplace-source release refresh,
   and close the merge lifecycle.

Do not delete the restart branch until PR 465 is merged and the preserved head
is reachable from the default branch on origin.

## Resolve create-skill authority and final verification

This track incorporates session `2026-07-19_18-19-17`. Begin it as a separate
changeset after PR 465 closes.

Worklist:

1. Reconcile the route-specific permission and auditor Bash contradictions in
   `spx/43-instructions.enabler/21-skills.enabler/ISSUES.md` before changing the
   creator or auditor template. Define one least-privilege contract that the
   standard, template, and auditor can all enforce.
2. Repair the representative-exercise ordering so every exercise-driven edit
   returns through deterministic checks and the complete-bundle skill audit
   before publication.
3. Keep the route-authority change, auditor-capability decision, and final
   verification loop coherent across `/create-skill`, `/skill-standards`,
   `/audit-skills`, and the affected templates and workflows.
4. Regenerate both runtime trees, run the focused skill and documentation
   checks, obtain a complete-bundle `skill-auditor` verdict, run the changeset
   review, and ship the independent changeset through `/merge`.
