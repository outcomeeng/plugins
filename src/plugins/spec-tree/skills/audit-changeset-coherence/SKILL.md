---
name: audit-changeset-coherence
description: >-
  Changeset-coherence audit methodology — judges whether an exact committed
  changeset forms one coherent review unit, covering semantic clustering,
  generated-source attribution, evidence completeness, and dependency-ordered
  review-unit sequencing.
model: sonnet
argument-hint: "<branch-or-base...head>"
allowed-tools: Read, Grep, Glob, Bash(python3:*resolve_scope.py*), Bash(git diff:*), Bash(git show:*)
---

<objective>

A verdict on whether one exact committed changeset forms one coherent review unit — `APPROVED`, `REJECTED`, or `UNKNOWN`, with each finding naming the violated rule, its location, and the evidence.

</objective>

<constraints>

- Read-only — produce one verdict and NEVER edit files, commits, branches, reviews, or pull requests.
- MUST preserve full base and head commit identities exactly as resolved from the supplied scope in every coherence verdict.
- MUST inspect every changed authored artifact; collapse deterministic generated artifacts onto their producers before judging breadth.
- NEVER use line count, file count, path breadth, or an uncalibrated review-load score as a verdict rule.
- NEVER infer missing behavioral, dependency, generated-source, verification, rollback, or calibration evidence; return `UNKNOWN` when the missing evidence can change the classification.
- NEVER return prose outside the JSON object in `<verdict_format>`.

</constraints>

<audit_workflow>

1. Require `$ARGUMENTS` to identify a branch, `HEAD`, or a committed `<base>...<head>` scope. When no exact committed scope can be resolved, return the `BLOCKED` JSON object in `<verdict_format>`; scope failure occurs before a coherence verdict and never fabricates commit identities.
2. Resolve the exact committed scope by running `python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_scope.py" "<scope>"`, which routes base-ref resolution, remote-tracking-ref composition, commit identity, and three-dot diff scope through the canonical changeset-scope primitives. Preserve its `base`, `head`, and `changed_paths` verbatim. NEVER derive base-ref, commit identity, or diff scope from raw git; a bare local branch ref lags `origin/<base>` in a multi-worktree checkout and re-admits already-merged commits. A nonzero exit returns the `BLOCKED` JSON object. Read changed content only within the resolved scope.
3. Enumerate every changed path and classify its role: decision/specification, test/eval evidence, implementation, generated artifact, workflow/configuration, documentation, migration, deployment, or release.
4. Resolve every generated artifact to its producing authored artifact from repository-declared build relationships. In an already-collected evidence packet, `role: generated` classifies the artifact kind only; it never establishes provenance. Require `generated_from`, a declared relationship record, or equivalent explicit evidence. When `generated_relationship_evidence.status` is `missing`, return `UNKNOWN` with `missing-generated-source-evidence` before clustering the unresolved artifact. Exclude resolved generated fanout from authored breadth while retaining it in each producer cluster's `generated_fanout`.
5. Extract behavioral claims from the changed declarations and observable implementation/evidence. Use commit messages only as supporting evidence; they never override changed artifacts.
6. Build the smallest semantic clusters whose artifacts realize one claim. Record each cluster's authored artifacts, generated fanout, verification story, rollback story, dependencies, and independent-mergeability judgment.
7. Collapse dependency cycles and clusters that cannot be verified or rolled back separately into one inseparable cluster. Order remaining clusters topologically, breaking independent ties by the lexicographically first authored path. Every cluster that survives this collapse forms its own review unit, so its `independently_mergeable` is `true` — a lone cluster and a cluster that depends on and merges after an earlier cluster are both `true`. A `false` judgment applies only to a cluster still fused with another before collapse, and such a cluster never survives into the projection.
8. Record review-load signals and whether a repository baseline exists. Use those signals to increase scrutiny only.
9. Apply `<verdict_rules>`, create findings, and return the exact schema in `<verdict_format>`.

</audit_workflow>

<verdict_rules>

- `APPROVED`: the authored change realizes one behavioral outcome, or several inseparable clusters sharing one verification and rollback story. `publication_authorized` is `true`; `recommended_pr_sequence` is empty.
- `REJECTED`: two or more semantic clusters are independently mergeable. `publication_authorized` is `false`; `recommended_pr_sequence` covers every cluster exactly once in dependency order.
- `UNKNOWN`: missing evidence can change cluster membership, dependency order, generated-source attribution, verification unity, rollback unity, or independent mergeability. `publication_authorized` is `false`.

In the final schema every cluster carries `independently_mergeable: true`; the verdict is distinguished by cluster count — one cluster approves, two or more independently mergeable clusters reject — never by a per-cluster `false`.

An empty rollback story for any cluster ALWAYS yields `UNKNOWN`, `publication_authorized: false`, and a blocking finding whose rule is `missing-rollback-evidence`. Missing verification evidence follows the same boundary with rule `missing-verification-evidence`. Use `missing-behavioral-claim-evidence`, `missing-dependency-evidence`, `missing-generated-source-evidence`, and `missing-calibration-evidence` for the other evidence classes. A review-load baseline may be absent without forcing `UNKNOWN` when the semantic evidence is otherwise complete; missing calibration yields `UNKNOWN` only when a repository-specific signal explicitly requires that calibration to determine whether the available semantic evidence is sufficient.

For two or more semantic clusters, an absent or `null` dependency set ALWAYS yields `UNKNOWN` with `missing-dependency-evidence`; an explicit empty dependency array establishes that no dependency exists. In every projected cluster the `dependencies` field is an array — `[]` when no dependency on another cluster is established — NEVER a `null` copied from the packet; unresolved packet dependency evidence is recorded only in the `missing-dependency-evidence` finding, NEVER echoed into a cluster. Every artifact classified as generated MUST resolve through an explicit repository-declared relationship or a `generated_from` field in an already-collected evidence packet. NEVER infer a generated artifact's producer from path similarity, artifact count, or the presence of only one authored artifact; unresolved attribution yields `UNKNOWN` with `missing-generated-source-evidence`.

When an evidence packet supplies already-collected claims, artifact paths, evidence paths, dependencies, or review-load signals, preserve those values verbatim in the projection. Sort claim and path arrays lexicographically. Copy `review_load` without reinterpretation. Every normal verdict carries every field in the schema, using empty arrays or objects when a field has no entries.

Use deterministic identities: `cluster-1`, `cluster-2`, and so on in dependency order; rejected review units are `review-unit-1`, `review-unit-2`, and so on in the same order.

</verdict_rules>

<verdict_format>

When scope resolution fails before an exact changeset exists, return only this JSON object:

```json
{
  "schema_version": 1,
  "status": "BLOCKED",
  "reason": "scope-unresolved",
  "scope_input": "<caller-supplied scope or empty string>"
}
```

For an exact committed changeset, return one coherence-verdict JSON object:

```json
{
  "schema_version": 1,
  "overall": "APPROVED | REJECTED | UNKNOWN",
  "scope": { "base": "<full-commit-id>", "head": "<full-commit-id>" },
  "behavioral_claims": ["<claim>"],
  "clusters": [
    {
      "id": "cluster-1",
      "outcome": "<behavioral outcome>",
      "authored_artifacts": ["<path>"],
      "generated_fanout": ["<path>"],
      "verification_story": ["<evidence>"],
      "rollback_story": ["<artifact or operation>"],
      "dependencies": ["<cluster-id>"],
      "independently_mergeable": true
    }
  ],
  "review_load": {
    "repository_baseline_available": true,
    "signals": {}
  },
  "findings": [
    {
      "rule": "<rule-id>",
      "severity": "blocking | debt",
      "location": "<path-or-scope>",
      "message": "<finding>",
      "evidence": { "observed": "<fact>", "expected": "<required evidence>" }
    }
  ],
  "publication_authorized": false,
  "recommended_pr_sequence": [
    {
      "id": "review-unit-1",
      "cluster_ids": ["cluster-1"],
      "outcome": "<review-unit outcome>",
      "artifacts": ["<authored and generated paths>"],
      "depends_on": []
    }
  ]
}
```

Every changed authored artifact whose behavioral claim is established appears in exactly one cluster. Every generated artifact whose producer relationship is established appears under exactly one producer cluster. An `UNKNOWN` verdict names every unresolved artifact in its findings without inventing cluster membership. A rejected sequence covers every cluster exactly once and references only earlier review units in `depends_on`.

</verdict_format>

<failure_modes>

**Failure 1: Missing rollback evidence received approval.**

What happened: Claude classified a migration packet as coherent even though the packet contained no rollback evidence.

Why it failed: The general missing-evidence rule did not make an empty rollback story an explicit terminal boundary, so semantic cohesion overshadowed reversibility.

How to avoid: Treat every empty cluster rollback story as `UNKNOWN`, prohibit publication, and emit `missing-rollback-evidence` before considering approval.

**Failure 2: Unresolved scope was forced into the verdict schema.**

What happened: Claude was instructed to return `UNKNOWN` for an unresolved scope while the same schema required full base and head commit identities.

Why it failed: Scope resolution failure occurs before an exact changeset exists, so a normal verdict would require fabricated identities or an internally invalid object.

How to avoid: Return the separate `BLOCKED` JSON object for scope resolution failure and emit a coherence verdict only after both full commit identities resolve.

**Failure 3: A null dependency set was treated as an empty set.**

What happened: Claude rejected two independently understandable clusters and ordered them as unrelated review units even though the evidence packet supplied `dependencies: null`.

Why it failed: Claude collapsed “dependency evidence unavailable” into “dependency evidence establishes no relationships,” producing a split without a defensible order.

How to avoid: Distinguish absent or `null` dependency evidence from an explicit empty array and return `UNKNOWN` whenever the unavailable evidence can change a multi-cluster classification or order.

**Failure 4: A generated artifact was attached by proximity.**

What happened: Claude attached one generated artifact to the only authored artifact and approved the changeset even though no repository relationship or `generated_from` field established that producer.

Why it failed: Artifact count and nearby paths were treated as provenance, inventing the relationship the audit was required to verify.

How to avoid: Require an explicit repository-declared generated-source relationship and return `UNKNOWN` with `missing-generated-source-evidence` when attribution cannot be established.

</failure_modes>

<success_criteria>

- Every changed authored artifact and generated artifact is accounted for exactly once.
- The overall result follows semantic cohesion, verification unity, rollback unity, and independent mergeability with no size threshold acting as a verdict rule.
- Every `REJECTED` result carries a complete dependency-ordered sequence; every `UNKNOWN` result names the evidence gap that prevents classification.
- The same committed scope and repository evidence produce the same cluster identities, ordering, and result.

</success_criteria>
