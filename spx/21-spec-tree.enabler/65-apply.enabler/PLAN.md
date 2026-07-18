# Plan: partition `work/strict-finding-disposition`

The preserved `origin/work/strict-finding-disposition` aggregate is partitioned into dependency-ordered pull requests that each carry one behavioral claim, one verification story, and one rollback story.

## Source and boundary

The recovery source is `origin/work/strict-finding-disposition` at `5f26a67a9aef9327e57fd5e02d130c8363578a07`. Against `origin/main` at `681e59bda5fd0481b079804732a19eafc0d30d2b`, it contains 103 branch commits and changes 189 paths. The aggregate remains recovery material. It never enters whole-changeset verification or publication as one pull request.

This plan governs the existing nodes that own the observable path:

- `spx/13-infrastructure.enabler/25-eval-harness.enabler`
- `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler`
- `spx/21-spec-tree.enabler/65-apply.enabler`
- `spx/21-spec-tree.enabler/68-audit.enabler`
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`
- `spx/21-spec-tree.enabler/76-merging.enabler`
- `spx/43-typescript.enabler/25-typescript-standards.enabler/29-typescript-code.enabler`

The changeset-coherence auditor on `origin/work/changeset-coherence-auditor` is excluded from this partitioning pass by operator direction. Its branch remains available for a separate specification and implementation review after the preserved aggregate has been drained.

## Observable slice

**Demonstrable value:** a Spec Tree workflow can derive one exact committed changeset, verify its evidence and implementation contracts, review findings with source-backed resolution, and advance one reviewable unit through the merge lifecycle.

| Element              | Slice contract                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Actor                | A maintainer or coding-agent workflow running review, audit, or merge over a committed branch                                        |
| Invocation           | Changeset scoping followed by the applicable evidence audits, implementation audit, changeset review, and merge transport            |
| Inputs               | Repository path, resolved base ref, committed head, governing node context, and source-owned evidence inputs                         |
| Behavior             | Derive the exact changed set, run producer-coupled verification, preserve source ownership, and require explicit finding disposition |
| External result      | One independently mergeable pull request reaches `origin/main` with its generated output and verification evidence                   |
| Inspection           | Focused tests, evidence-auditor projections, implementation-audit projection, sealed review run, CI checks, and pull-request diff    |
| First useful failure | Reject a scope whose changed-set identity, evidence ownership, finding resolution, or semantic cohesion cannot be established        |

The observable slice spans several merge cycles. Each cycle below must be independently mergeable and inspectable; completion of one cycle never authorizes publishing the remaining aggregate.

## Current extraction ledger

This table is a navigation snapshot. Recompute every branch against current `origin/main` before verification or merge because merged prerequisites and repair commits change path counts and patch identity.

| Order | Branch or PR                                      | Current scope                                                                | Disposition                                                                                                                                                                                                              |
| ----- | ------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1     | PR #451, `work/changeset-scope-fixture-manifest`  | 24 paths on the published branch; local repaired head is ahead               | Finish the exact current-head gates and merge first. It establishes the real-Git fixture manifest and canonical changeset-scope evidence consumed by later verifier work.                                                |
| 2     | PR #448, `work/assertion-flow-governance`         | 17 paths                                                                     | Reconcile with current test-ownership decisions, then merge before test-methodology implementation that consumes those decisions.                                                                                        |
| 3     | PR #454, `work/python-test-seam-standards`        | 95 paths                                                                     | Re-run semantic-cohesion analysis. Keep one PR only when the authored source is one cross-language ownership rule with deterministic generated fan-out; otherwise split by independently mergeable methodology contract. |
| 4     | `work/eval-evidence-hygiene`                      | 19 paths, no pull request identified in the current snapshot                 | Establish whether it belongs to the preserved aggregate. Extract only the producer-coupled eval-runner behavior required by later audit and review evidence.                                                             |
| 5     | Review journal and result contracts               | Present in the preserved aggregate; no dedicated extracted branch identified | Reconstruct from current `main` as the smallest cluster that emits one raw run token, records grounded findings, and proves the result through source-owned test infrastructure.                                         |
| 6     | `work/audit-runtime-evidence`                     | 59 paths, no pull request identified in the current snapshot                 | Partition before publication. Separate implementation-audit run contracts from Python authoring or distribution changes whenever either can merge and verify independently.                                              |
| 7     | TypeScript implementation and remediation routing | Present in the preserved aggregate; no dedicated extracted branch identified | Reconstruct after shared review and audit contracts so TypeScript consumes established verification behavior instead of carrying a parallel policy.                                                                      |
| 8     | PR #447, `work/merge-skill-runtime-contracts`     | 34 paths                                                                     | Reconcile after review and audit contracts converge. Merge only the portable PR lifecycle cluster whose checks, finding disposition, and action tokens share one rollback boundary.                                      |

Branches outside this ledger are evidence to inspect, never proof that an aggregate commit has been extracted. Path overlap, commit ancestry, and generated fan-out are signals. The current `git cherry` result reports every preserved aggregate commit as patch-distinct from current `main`, so no original commit may be marked consumed solely because a related PR merged.

## Extraction procedure

For each merge cycle:

1. Fetch and synchronize current `origin/main` through `/sync-base`.
2. Recompute the preserved aggregate diff and subtract behavior already present on `main` by source contract and tests, rather than by commit subject or path name alone.
3. Select one behavioral claim and trace its complete decision-to-spec-to-evidence-to-source chain.
4. Collapse generated `dist/claude/` and `dist/codex/` fan-out onto the authored `src/plugins/` producer when evaluating cohesion and review load.
5. Create the extraction branch from current `origin/main`. Reconstruct the minimal coherent patch from the preserved branch and any repaired extracted branch; avoid replaying tangled commits wholesale.
6. Keep governing decisions, first affected specs, tests or evals, authored implementation, and generated output in the same PR when they form one atomic contract.
7. Run focused deterministic verification, every applicable evidence auditor, the implementation auditor, and the changeset reviewer on one clean committed head. Run the full deterministic gate last when the repository overlay requires it.
8. Merge and complete branch cleanup before starting a dependent extraction.
9. Recompute the residual aggregate against the new `origin/main` and update this ledger in place.

## Split rules

Split a candidate when any of these conditions holds:

- It contains independently mergeable behavioral claims.
- Its verification story can pass for one cluster while another remains absent.
- Its rollback would require retaining only part of the PR.
- It mixes a shared verification contract with a language-specific consumer that can adopt the contract later.
- It mixes an eval-harness capability with audit or review policy that merely consumes the capability.
- It combines authored behavior with unrelated generated output.

Keep a candidate together when its apparent breadth is deterministic fan-out from one authored producer, or when separating the files would leave a governing decision, spec, evidence file, consumer, or generated tree inconsistent.

Raw lines and path counts trigger inspection. They never decide cohesion.

## Completion criteria

The partitioning work is complete when:

- Every behavioral claim from `origin/work/strict-finding-disposition` is present on `origin/main`, explicitly superseded by current product truth, or recorded in the owning node's `PLAN.md` or `ISSUES.md` with a concrete revisit condition.
- Every extracted PR has an independent verification and rollback story.
- No remaining aggregate diff is treated as one publication subject.
- `origin/work/strict-finding-disposition` can be deleted after a final source-contract comparison against `origin/main` finds no unclassified value.
- The separate changeset-coherence auditor remains outside this plan until the operator starts that work explicitly.
