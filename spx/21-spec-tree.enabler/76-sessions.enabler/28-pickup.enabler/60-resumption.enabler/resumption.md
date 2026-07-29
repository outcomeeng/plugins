# Resumption

PROVIDES the resumption flow after claim reconciliation — selecting the node to contextualize, reviewing the reconciled evidence, classifying the claimed session, and presenting a no-surprises proposal
SO THAT an agent resuming another context's work
CAN receive an evaluated continuation proposal rather than raw session metadata

## Assertions

### Compliance

- ALWAYS: when a claimed session references multiple nodes, `/pickup` selects the `/contextualize` target by priority — the node named in `next_step` after a `/contextualize` reference, else the first `<nodes>` entry whose coordination notes list a `PLAN.md` or `ISSUES.md` path, else the first node listed in `<nodes>` — trying the rules in order and falling through when a rule matches zero or more than one node; the final rule always resolves, so node multiplicity never triggers a user question and `/pickup` asks which node only when `<nodes>` is empty or unreadable ([audit])
- ALWAYS: after `/contextualize` loads the target node and before asking the operator to choose a continuation path, `/pickup` reviews the session evidence — claim-verification verdicts, persisted artifacts, loaded coordination-note content, overlapping `doing` sessions, branch and worktree ownership, PR ownership, and expected verification — so the operator receives an evaluated proposal rather than raw session metadata ([audit])
- ALWAYS: `/pickup` classifies a claimed session before the operator decision as exactly one of `actionable_here`, `owned_elsewhere`, `stale_or_superseded`, `blocked_on_external_dependency`, or `needs_operator_direction`, using the loaded context and reviewed evidence to select the classification ([audit])
- ALWAYS: when `/pickup` classifies a claimed session as `owned_elsewhere`, it reports the owning session id, branch, worktree, PR, or commit when known and stops without archiving, releasing, handing off, or otherwise mutating the claimed session ([audit])
- ALWAYS: `/pickup` presents a no-surprises proposal before continuation that states the expected outcome, changed product surface, planned skill path, evidence infrastructure, verification plan, inspection references, and remaining-work expectation, and if a later required skill, evidence surface, external dependency, ownership conflict, or verification class was not represented, `/pickup` stops at the next safe checkpoint and presents the delta before continuing ([audit])
