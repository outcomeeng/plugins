---
id: 01a0ebba-5f67-715d-9403-9f5cbc27a2d2
malleability: spec
---

# Changeset Coherence

PROVIDES an artifact-type audit that determines whether an exact committed changeset is one reviewable semantic unit and recommends dependency-ordered review units when it is not
SO THAT apply, publication, and merge workflows
CAN reject accumulated programs of work before expensive implementation audits and whole-changeset reviews

## Assertions

### Test.Scenario: scope resolution

- [lagging-local-base](tests/test_resolve_scope.scenario.l1.py):
  - Given a feature branch whose local base ref lags `origin/<base>` by an already-merged commit
  - When the audit resolves its own committed scope
  - Then the resolved scope carries the branch's own change and excludes the already-merged file
- [named-branch-scope](tests/test_resolve_scope.scenario.l1.py):
  - Given a named branch
  - When its scope is resolved while another branch is checked out
  - Then the result carries the named branch's full commit identity and changed paths
  - And resolving the same endpoints as an explicit three-dot range produces the same scope
- [unresolvable-scope](tests/test_resolve_scope.scenario.l1.py):
  - Given a repository without a configured remote base or an explicit range missing its head endpoint
  - When the resolver is invoked
  - Then it exits unsuccessfully with a scope-resolution diagnostic
- [nonexistent-repository](tests/test_resolve_scope.scenario.l1.py):
  - Given a nonexistent repository path
  - When the resolver receives it through `--repo`
  - Then it exits unsuccessfully with a scope-resolution diagnostic naming that path and emits no scope JSON or Python traceback

### Test.Compliance: scope resolver

- [stale-base-relay](tests/test_resolve_scope.compliance.l1.py): ALWAYS: the coherence scope resolver relays the shared resolver's stale-base refusal for a head behind the fetched `origin/<base>` tip — the dedicated exit code and the diagnostic, with no scope payload — so the audit returns the `stale-base` block before it reads a subject

### Evaluate: [coherence-verdict](evals/coherence-verdict/eval.toml)

Handed one already-collected evidence packet for an exact committed changeset by the eval, `/audit-changeset-coherence` collapses each generated artifact onto its producing authored artifact before it assesses path breadth, authored-change size, or review load, clusters its authored artifacts with their generated fanout into semantic clusters that each carry a verification story and a rollback story, every authored artifact belonging to exactly one semantic cluster and each generated artifact sharing the cluster of its producing authored artifact, and returns one coherence verdict that no raw line count, file count, path breadth, or review-load measurement determines without semantic evidence; its run seals `approved` only when the authored artifacts realize one behavioral outcome or inseparable semantic clusters with one verification story and one rollback story, seals `rejected` when two or more semantic clusters are independently mergeable, recording one `review-unit` child per cluster and a `split-required` finding whose evidence carries a dependency-ordered review-unit sequence that covers every semantic cluster exactly once, and, when behavioral claims, dependency evidence, generated-source relationships, verification evidence, rollback evidence, or repository calibration cannot be established, records the unit that needs it as `incomplete` with its cause and seals `rejected`, never authorizing publication; the run records behavioral claims, semantic clusters, authored artifacts, generated fanout, verification stories, rollback stories, dependencies, independent-mergeability judgments, review-load signals, findings, publication authorization, and a recommended review-unit sequence in its units and finding evidence; and the eval compares the verdict's `overall`, review units, findings and publication authorization with the row's expectation, together with the changeset's base and head commit identities copied verbatim.

| Case                                          | Evidence packet                                                                                                                                                                     | Overall    | Review units                                          | Findings                                                               | Publication    |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------- | ---------------------------------------------------------------------- | -------------- |
| single-outcome-approved                       | a spec, its implementation and its test realize "parse nested expressions", with verification and rollback evidence and an empty dependency set                                     | `APPROVED` | none; one cluster                                     | none                                                                   | authorized     |
| coherent-generated-fanout-approved            | one authored producer realizes "classify example evidence", and its two generated artifacts name it through `generated_from`; no repository baseline                                | `APPROVED` | none; one cluster carrying both generated artifacts   | none                                                                   | authorized     |
| large-coherent-change-approved                | one authored artifact realizes "replace protocol schema atomically" in 6800 authored lines against a repository p95 of 420                                                          | `APPROVED` | none; one cluster                                     | none, and no `size-threshold-exceeded` finding                         | authorized     |
| independent-clusters-rejected-in-order        | two implementations with their tests realize "persist audit records" and "render audit summaries", and the dependency evidence orders the second after the first                    | `REJECTED` | `review-unit-1` then `review-unit-2`, one per cluster | one `split-required` finding of severity `blocking`                    | not authorized |
| independent-clusters-with-fanout-rejected     | two authored producers realize "classify alpha evidence" and "classify beta evidence", each with one generated artifact, and an empty dependency set                                | `REJECTED` | `review-unit-1` then `review-unit-2`, one per cluster | one `split-required` finding of severity `blocking`                    | not authorized |
| missing-rollback-evidence-unknown             | an implementation and a deployment realize "migrate stored audit records" with verification evidence and an empty rollback story                                                    | `UNKNOWN`  | none                                                  | one `missing-rollback-evidence` finding of severity `blocking`         | not authorized |
| missing-behavioral-claim-evidence-unknown     | one implementation artifact carries no behavioral claim                                                                                                                             | `UNKNOWN`  | none; no cluster                                      | one `missing-behavioral-claim-evidence` finding of severity `blocking` | not authorized |
| missing-dependency-evidence-unknown           | two implementations realize "persist audit records" and "render audit summaries", and the dependency set is `null`                                                                  | `UNKNOWN`  | none                                                  | one `missing-dependency-evidence` finding of severity `blocking`       | not authorized |
| missing-generated-source-evidence-unknown     | one authored producer realizes "classify example evidence" beside one generated artifact that names no producer, and the generated-relationship evidence reads `missing`            | `UNKNOWN`  | none                                                  | one `missing-generated-source-evidence` finding of severity `blocking` | not authorized |
| missing-verification-evidence-unknown         | one implementation realizes "enforce retention policy" with rollback evidence and an empty verification story                                                                       | `UNKNOWN`  | none                                                  | one `missing-verification-evidence` finding of severity `blocking`     | not authorized |
| missing-required-calibration-evidence-unknown | one implementation realizes "partition repository-specific review units", and an `elevated` repository-specific risk band requires calibration that no repository baseline supplies | `UNKNOWN`  | none                                                  | one `missing-calibration-evidence` finding of severity `blocking`      | not authorized |

### Audit: wrapper and policy

- record-as-judged: ALWAYS: `/audit-changeset-coherence` records the root unit as soon as the run starts, each review unit as soon as the review-unit sequence fixes its position and its own judgment completes, and each finding as soon as it is raised and its unit is recorded, so no unit or finding waits for the judgment of a later unit
- thin-wrapper: ALWAYS: the configured Auditor is a thin read-only wrapper whose policy lives in the audit skill and whose result is the run token, the run file, and the rendered projection, or a blocked diagnostic when spx refuses a recorded payload or the finish
- policy-in-skill: NEVER: a plugin-side helper, tracked file, rendered comment, or wrapper prompt becomes the source of coherence-verdict policy — the policy lives in the audit skill
- caller-independent: ALWAYS: `/audit-changeset-coherence` names no caller and stays invocable on its own; the Author's agent session produces a verdict by dispatching the audit to a separate Verifier's agent session rather than grading its own work in place, per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)
