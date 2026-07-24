# Plan: complete instructions follow-ups

This plan preserves two dependency-ordered continuations. Ship the
subagent-creator track before beginning the create-skill contract track so the
pull request remains one reviewable unit.

## Ship the subagent-creator rename and hardening

PR 465 is closed, superseded rather than reconciled.
`git cherry work/skill-naming-and-subagent-cluster work/inline-foundation-salvage`
reports twelve of that branch's thirteen commits patch-equivalent. The
thirteenth — the subagent-creator rename — reports non-equivalent because the
this branch reworked the rename further rather than dropping it, so no single
commit retains its patch identity. Its content is carried: on this branch's head
the skill directory is `create-subagent` with all seven references beneath it,
no `create-subagents` reference remains anywhere in the repository, the Claude
marketplace entry reads `/create-subagent`, and the diff against `origin/main`
records those eight paths as renames. Re-run that check and this content
verification after any further rebase, since patch identity does not survive one.
Never publish to `work/inline-foundation-salvage`, force-push over it, or reopen
PR 465.

The changeset lives on `work/skill-naming-and-subagent-cluster`, rebased onto
the current `origin/main`; its commit SHAs are checkout-local and change on every
rebase, so this plan names this branch's history by branch rather than by SHA.
The pre-rebase preserved head `35001274a20170236016f45aa6403a3fb132f5c4`
identifies the local `work/inline-foundation-salvage` branch content, not this branch. Base movement over a governance surface supersedes any
verification evidence produced before it, which is then re-established on the
current base.

Worklist:

1. Run the focused deterministic lane for the committed head: `just
   build-skills`, formatting for changed Markdown, `just check-skills`, `just
   docs-check`, `spx validation markdown`, and `spx spec status --format json`.
2. Dispatch a complete-bundle `skill-auditor` over every changed skill file and
   bundled reference. Resolve every valid bounded finding, then repeat the
   focused lane and audit on a new clean commit.
3. Dispatch `changes-reviewer` against the clean committed head and render its
   sealed review run. Resolve every valid bounded finding and repeat the
   affected deterministic and agentic gates on the new head.
4. After all applicable agentic gates converge on one clean committed head, run
   the terminal full deterministic gate `just check-full` once.
5. Invoke `/sync-base` again. Re-establish any evidence the base movement
   invalidated, then publish `work/skill-naming-and-subagent-cluster` and open
   the fresh pull request through `/merge`.
6. Manage that pull request through current-head integration review and
   terminal-green required checks, merge it, complete the marketplace-source
   release refresh, and close the merge lifecycle.

Do not delete `work/inline-foundation-salvage` until this branch's content
reaches the default branch on origin.

## Resolve create-skill authority and final verification

This track incorporates session `2026-07-19_18-19-17`. Begin it as a separate
changeset after the subagent-creator track merges.

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
   `/audit-skill`, and the affected templates and workflows.
4. Regenerate both runtime trees, run the focused skill and documentation
   checks, obtain a complete-bundle `skill-auditor` verdict, run the changeset
   review, and ship the independent changeset through `/merge`.
