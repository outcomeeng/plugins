# ISSUES — pickup

## The proposal contract has no field for finished, undelivered work

Workflow Step 2b requires eight fields before the operator is asked to continue: expected outcome, classification, changed product surface, planned skill path, evidence infrastructure, verification plan, inspection references, and remaining-work expectation. Every one describes work that would follow approval; none describes work the branch already carries. Steps 6 and 7 display `<persisted>` and `<coordination>`, but as sections to recite rather than inputs to the proposal, so a session whose branch holds a finished, audited, unmerged change can be proposed as new work stacked on top of it. That runs against the delivery boundary the same workflow inherits: completed work that has not reached the default branch is the highest-value action available at pickup.

**Resolution shape**: add a field for finished-and-undelivered work on the branch, derived from `<persisted>`, `<coordination>`, and the branch's commits against its resolved base, and require a proposal that leaves such work undelivered to state why. Consider whether "ship what is already done" belongs among the classifications beside `actionable_here`.

## Claim-time file injection precedes the foundation gate and the base sync

`spx session pickup <id>` resolves the session frontmatter's `specs:` and `files:` and inlines those file bodies into its output; the stored document carries none of them. The claim is workflow Step 1 and `/understand` is Step 2, so the injected bodies enter the conversation before the live `<SPEC_TREE_FOUNDATION>` marker the router requires ahead of reading anything under `spx/` or any source file. The claim also precedes `/sync-base` at Step 4, so on a branch behind its base the bodies come from the un-synced checkout. They arrive in a shape indistinguishable from a completed read, which invites counting them as one.

**Resolution shape**: the injection belongs to the `@outcomeeng/spx` CLI rather than this plugin, so the fix is filed there. Recorded here because the ordering it breaks is this workflow's, and because a resuming agent must not count an injected body as a file it has read.
