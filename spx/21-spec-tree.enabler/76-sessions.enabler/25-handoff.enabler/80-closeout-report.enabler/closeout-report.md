# Closeout Report

PROVIDES the operator-facing report a closure produces — the product value fields, and the session-mechanics rows the operator can act on
SO THAT an operator reading a closure
CAN understand what changed and what to do next without reconstructing it from a diff, a branch, or a receipt

## Assertions

### Compliance

- ALWAYS: `/handoff` final confirmation explains the completed or preserved work in operator-useful terms before mechanics — product outcome, changed product surface, and human-readable change summary answer why the operator should be glad about the work's delivered or parked state, which shipped product behavior is better or being preserved for pickup, why it matters, and what additional benefit continuing would create when follow-up remains; those value fields translate the loaded ancestry from `spx/outcomeeng.product.md` through the target node into plain product language and exclude PR numbers, branch names, commit SHAs, filenames, file paths, generated-output paths, marketplace-source paths, installed-version receipts, CI/check ids, session ids, and archive receipts, routing those mechanics to verification evidence, inspection references, delivered state, remaining work, Remaining Branches, or session mechanics instead; merge lifecycle closeout includes a compact Remaining Branches section with deleted-local, deleted-remote, retained-with-reason, and needs-operator-decision groups, while small bug fixes and technical-debt cleanup remain describable at their natural scale ([audit])
- ALWAYS: the `/handoff` closeout's session-mechanics block carries only rows the operator can act on — the full session ids a resuming agent claims, the queue mutations the closure made, and the work branch it released — while every thread's disposition and every archive candidate stay in the resolved continuation-thread and artifact-partition markers; a thread whose continuation is absent occupies no row, and neither does a precondition `spx session handoff` already enforces nor compliance with a rule the skill never violates ([audit])
