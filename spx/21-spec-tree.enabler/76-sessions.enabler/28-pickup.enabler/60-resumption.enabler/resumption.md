# Resumption

PROVIDES the resumption flow after claim reconciliation — selecting the node to contextualize, reviewing the reconciled evidence, classifying the claimed session, and presenting a no-surprises proposal
SO THAT an agent resuming another context's work
CAN receive an evaluated continuation proposal rather than raw session metadata

## Assertions

### Compliance

- ALWAYS: `/pickup` selects the `/contextualize` target without making the operator search the tree — for multiple recorded nodes it uses the node named in `next_step` after a `/contextualize` reference, else the first `<nodes>` entry whose coordination notes list a `PLAN.md` or `ISSUES.md` path, else the first listed node; when `<nodes>` is empty or unreadable it runs `spx spec status --format json`, traverses the projected tree from the root downward in emitted order, and contextualizes session-relevant nodes as encountered until authoritative context identifies the next workflow with no relevant branch unresolved; the traversal never asks the operator to select a node, an unavailable projection stops with its exact diagnostic, and exhausting the projection without reaching that resume-ready state classifies the handoff as `stale_or_superseded` ([audit])
- ALWAYS: after `/contextualize` loads the target node and before asking the operator to choose a continuation path, `/pickup` reviews the session evidence — claim-verification verdicts, persisted artifacts, loaded coordination-note content, overlapping `doing` sessions, branch and worktree ownership, PR ownership, and expected verification — so the operator receives an evaluated proposal rather than raw session metadata ([audit])
- ALWAYS: `/pickup` classifies a claimed session before the operator decision as exactly one of `actionable_here`, `owned_elsewhere`, `stale_or_superseded`, `blocked_on_external_dependency`, or `needs_operator_direction`, using the loaded context and reviewed evidence to select the classification ([audit])
- ALWAYS: when `/pickup` classifies a claimed session as `owned_elsewhere`, it reports the owning session id, branch, worktree, PR, or commit when known and stops without archiving, releasing, handing off, or otherwise mutating the claimed session ([audit])
- ALWAYS: `/pickup` presents a no-surprises proposal before continuation that states the expected outcome, changed product surface, planned skill path, evidence infrastructure, verification plan, inspection references, and remaining-work expectation, and if a later required skill, evidence surface, external dependency, ownership conflict, or verification class was not represented, `/pickup` stops at the next safe checkpoint and presents the delta before continuing ([audit])
