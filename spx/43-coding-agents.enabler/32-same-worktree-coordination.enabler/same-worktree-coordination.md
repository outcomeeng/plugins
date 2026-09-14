# Same-Worktree Coordination

PROVIDES bounded authority and context exchange for coding agents operating in one worktree
SO THAT advisory collaborators
CAN produce durable results without interfering with tracked files or Git state

## Assertions

- A same-worktree delegation records the sender as the tracked-file and Git owner and assigns the recipient the exact `.spx/delegations/<id>/` read/write scope.
- The sender materializes `request.md` and every required context artifact within the assigned delegation directory before delivery, and the recipient reads those inputs and writes `answer.md` in that directory.
- The recipient never edits tracked files, stages or commits changes, checks out or synchronizes branches, invokes `/sync-base`, or directly traverses product content in the shared worktree.
- Missing, conflicting, or incomplete sender ownership or recipient scope produces a signal gap and no work request.
- Every same-worktree request and terminal handback uses the durable delegation records and pane-pointer delivery supplied by the coding-agent environment and communication contracts.
