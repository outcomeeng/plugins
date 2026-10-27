# Worktree Occupancy Issues

## Fresh occupancy proof before checkout use

An execution session entered a named worktree after inferring availability from its apparent state instead of proving occupancy from the shared worktree registry. A clean tree, detached head, branch name, worktree suffix, or absent visible activity does not establish that a worktree is unoccupied.

The worktree workflow must run `spx worktree status` at session start, after context compaction or runtime restart, and immediately before entering or transitioning a checkout. The selected root is usable only when the output identifies that exact root and the current session's live claim. When the claim is absent or belongs to another session, work stays in the assigned worktree and the occupancy defect is recorded without entering the other checkout.

Revisit when the worktree-occupancy workflow and its consuming lifecycle skills enforce this preflight and deterministic validation covers absent-claim, matching-claim, and foreign-holder states.
