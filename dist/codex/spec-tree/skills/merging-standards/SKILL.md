---
name: merging-standards
user-invocable: false
description: >-
  Shared merge-lifecycle invariants and routing for detailed preflight, branch,
  review, authority-gate, transport, and closeout policy. Loaded by composing
  delivery workflows.
allowed-tools: Read
---

<objective>
A compact shared contract that keeps every merge transport on the same authority, delivered-value, finding-disposition, and closeout semantics.
</objective>

<shared_contract>

- `VERIFICATION_READINESS` governs publication, `MERGE_READINESS` governs merge, and declared `DEPLOYMENT_READINESS` or `RELEASE_READINESS` gates govern their post-merge actions. No earlier success substitutes for a later authority gate.
- Delivered value means the intended change has reached the default branch on origin through the selected transport. A local commit, pushed branch, open pull request, passing check, or approved review is intermediate state.
- Every valid `blocking` finding on text the changeset touches or invalidates is fixed before publication or merge. The repair fixes every instance the cited clause covers, as the cited standard defines it, and changes nothing the clause does not require. A finding on any other text is returned `filed` and recorded in its governing node's `ISSUES.md`, and never blocks the merge. A separate larger concern is recorded in its owning node only when its fix is outside the changeset's bounded concern.
- A review's `debt` finding on text the changeset touches or invalidates waits for a ruling — fix, accept, or drop — from a position at least one rank above the changeset's author and no lower than the Product's Maintainer, and the Author acts on it only as the ruling directs. A `debt` finding counts toward no gate's rejection cap. A finding a ruling accepts is recorded once in the governing node's `ISSUES.md` under a heading that carries its entry key, and every later review reports it `TRACKED`, which blocks nothing.
- Before every local Auditor or Reviewer dispatch, a complete verification-dispatch readiness record binds the exact clean committed head, active objective, changed paths, governing nodes, deterministic results, same-class scans naming for each repair the clause it applies and the check that shows the class closed, assertion-design records when test evidence changed, run ownership, and unresolved-work set. Missing or unresolved fields stop dispatch.
- A second rejection in the same defect class invalidates the prior repair invariant. Analyze the recurrence, widen the repair and same-class scan, and amend the governing workflow or contract before another dispatch. The gate reads the next Verifier's verdict, never the recorded closing check.
- Changes may remain uncommitted until another agent session or human is expected or asked to read them. When repository writes are authorized, commit the exact current version before that reading with verification state `passing`, `failing`, or `not-run`; after any further change, commit the new version before another agent session or human reads it. Without repository-write authorization, defer the reading. Authority gates additionally require their declared verification state on the exact committed subject.
- Detailed lifecycle behavior is transport-neutral and caller-independent. Composing workflows consume the same stable results instead of branching on caller identity.
- Every payload a merge-lifecycle operation sends to `gh` or another tool, such as a pull-request comment body, travels through a file written in the scratch directory the harness names for the session, under a file name unique to the agent, and reaches the tool through its file argument, such as `gh pr comment <pr-number> --body-file <file>`. No heredoc, pipe, or inline form carries a payload, and the agent never removes the file. Where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner. A pull-request number, branch name, or path is a command argument, never a payload.
- Repository-specific transport, merge command, confirmation, preflight, deployment, and release behavior comes only from the optional `spx/local/merging.md` overlay. Its absence selects the defaults.

</shared_contract>

<reference_index>

Load each required bundled reference directly from this index:

- Read `${SKILL_DIR}/references/merge-policy.md` before executing or evaluating any detailed merge-lifecycle operation. It owns the canonical tagged sections for:

  - repository overlay and safety checks;
  - delivered-value and close-phase records;
  - assigned-worktree discipline, branch hygiene, topology, push, and base sync;
  - deterministic scope, local review, authority gates, and auditor verdicts;
  - review inspection, classification, check waits, failure modes, and success criteria.
- Read `${SKILL_DIR}/references/merge-cleanup.md` immediately before a merge mutation. It owns the merge command, overlay checks, worktree transition, and branch cleanup sequence.
- Read `${SKILL_DIR}/references/action-tokens.md` before emitting a merge-lifecycle action token. It owns every token's trigger condition and required follow-up.

The composing skill names the tagged section or operation it needs. Read the matching one-level reference directly from this index and apply it without reimplementing it. A bundled reference never dispatches another bundled reference.

</reference_index>

<success_criteria>

- Every gate decision a transport reports names the `<authority_gates>` predicates in `${SKILL_DIR}/references/merge-policy.md` it read and the observable state each predicate held.
- Repository-specific behavior comes only from the optional local overlay.
- Publication, merge, deployment, and release actions occur only under their matching authority gates.
- Every valid `blocking` finding on touched or invalidated text is fixed, every `debt` finding on that text has a ruling that is acted on, and every `filed` finding, accepted `debt` finding, and separate larger concern has an owning-node record.
- Every Auditor or Reviewer dispatch is backed by one complete head-bound readiness record, one active run writer, and no unresolved work hidden from the Auditor or Reviewer.

</success_criteria>
