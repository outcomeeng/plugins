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
- Every valid in-scope finding and its in-scope same-class instances are fixed before publication or merge. A separate larger concern is recorded in its owning node only when its fix is outside the changeset's bounded concern.
- Detailed lifecycle behavior is transport-neutral and caller-independent. Composing workflows consume the same stable results instead of branching on caller identity.
- Repository-specific transport, merge command, confirmation, preflight, deployment, and release behavior comes only from the optional `spx/local/merging.md` overlay. Its absence selects the defaults.

</shared_contract>

<reference_index>

Load each required bundled reference directly from this index:

- Read `${CLAUDE_SKILL_DIR}/references/merge-policy.md` before executing or evaluating any detailed merge-lifecycle operation. It owns the canonical tagged sections for:

  - repository overlay and safety checks;
  - delivered-value and close-phase records;
  - assigned-worktree discipline, branch hygiene, topology, push, and base sync;
  - deterministic scope, local review, authority gates, and auditor verdicts;
  - review inspection, classification, check waits, failure modes, and success criteria.
- Read `${CLAUDE_SKILL_DIR}/references/merge-cleanup.md` immediately before a merge mutation. It owns the merge command, overlay checks, worktree transition, and branch cleanup sequence.
- Read `${CLAUDE_SKILL_DIR}/references/action-tokens.md` before emitting a merge-lifecycle action token. It owns every token's trigger condition and required follow-up.

The composing skill names the tagged section or operation it needs. Read the matching one-level reference directly from this index and apply it without reimplementing it. A bundled reference never dispatches another bundled reference.

</reference_index>

<success_criteria>

- Every composing workflow applies `<shared_contract>` and reads the detailed policy before using its tagged lifecycle sections.
- Repository-specific behavior comes only from the optional local overlay.
- Publication, merge, deployment, and release actions occur only under their matching authority gates.
- Every valid in-scope finding is fixed, and every separate larger concern has an owning-node record.

</success_criteria>
