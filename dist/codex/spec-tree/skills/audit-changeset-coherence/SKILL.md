---
name: audit-changeset-coherence
user-invocable: false
description: >-
  Changeset-coherence audit methodology invoked by its dedicated auditor for an
  exact committed scope.
argument-hint: "<branch-or-base...head>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git diff:*), Bash(git rev-parse:*), Bash(git show:*)
---

<objective>

A structured verdict on one exact committed changeset — `APPROVED`, `REJECTED`, or `UNKNOWN` — carrying complete semantic clusters, evidence stories, publication authorization, findings, and a dependency-ordered review-unit sequence.

</objective>

<constraints>

- Read-only — produce one verdict and NEVER edit files, commits, branches, reviews, or pull requests.
- MUST preserve full base and head commit identities exactly as resolved from the supplied scope.
- MUST inspect every changed authored artifact; collapse deterministic generated artifacts onto their producers before judging breadth.
- NEVER use line count, file count, path breadth, or an uncalibrated review-load score as a verdict rule.
- NEVER infer missing behavioral, dependency, generated-source, verification, rollback, or calibration evidence; return `UNKNOWN` when the missing evidence can change the classification.
- NEVER return prose outside the JSON object in `<verdict_format>`.

</constraints>

<audit_workflow>

1. Require `$ARGUMENTS` to identify a branch, `HEAD`, or a committed `<base>...<head>` scope. Return `UNKNOWN` with a `scope-unresolved` finding when no exact committed scope can be resolved.
2. Invoke `spec-tree:scope-changeset` and apply its canonical remote-base, commit-identity, and three-dot diff semantics. Resolve the full base and head commit IDs and preserve them verbatim.
3. Enumerate every changed path and classify its role: decision/specification, test/eval evidence, implementation, generated artifact, workflow/configuration, documentation, migration, deployment, or release.
4. Resolve every generated artifact to its producing authored artifact from repository-declared build relationships. Exclude generated fanout from authored breadth while retaining it in each cluster's `generated_fanout`.
5. Extract behavioral claims from the changed declarations and observable implementation/evidence. Use commit messages only as supporting evidence; they never override changed artifacts.
6. Build the smallest semantic clusters whose artifacts realize one claim. Record each cluster's authored artifacts, generated fanout, verification story, rollback story, dependencies, and independent-mergeability judgment.
7. Collapse dependency cycles and clusters that cannot be verified or rolled back separately into one inseparable cluster. Order remaining clusters topologically, breaking independent ties by the lexicographically first authored path.
8. Record review-load signals and whether a repository baseline exists. Use those signals to increase scrutiny only.
9. Apply `<verdict_rules>`, create findings, and return the exact schema in `<verdict_format>`.

</audit_workflow>

<verdict_rules>

- `APPROVED`: the authored change realizes one behavioral outcome, or several inseparable clusters sharing one verification and rollback story. `publication_authorized` is `true`; `recommended_pr_sequence` is empty.
- `REJECTED`: two or more semantic clusters are independently mergeable. `publication_authorized` is `false`; `recommended_pr_sequence` covers every cluster exactly once in dependency order.
- `UNKNOWN`: missing evidence can change cluster membership, dependency order, generated-source attribution, verification unity, rollback unity, or independent mergeability. `publication_authorized` is `false`.

An empty rollback story for any cluster ALWAYS yields `UNKNOWN`, `publication_authorized: false`, and a blocking finding whose rule is `missing-rollback-evidence`. Missing verification evidence follows the same boundary with rule `missing-verification-evidence`. A review-load baseline may be absent without forcing `UNKNOWN` when the semantic evidence is otherwise complete.

Use deterministic identities: `cluster-1`, `cluster-2`, and so on in dependency order; rejected review units are `review-unit-1`, `review-unit-2`, and so on in the same order.

</verdict_rules>

<verdict_format>

Return one JSON object:

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

Every changed authored artifact appears in exactly one cluster. Every generated artifact appears under exactly one producer cluster. A rejected sequence covers every cluster exactly once and references only earlier review units in `depends_on`.

</verdict_format>

<success_criteria>

- Every changed authored artifact and generated artifact is accounted for exactly once.
- The overall result follows semantic cohesion, verification unity, rollback unity, and independent mergeability with no size threshold acting as a verdict rule.
- Every `REJECTED` result carries a complete dependency-ordered sequence; every `UNKNOWN` result names the evidence gap that prevents classification.
- The same committed scope and repository evidence produce the same cluster identities, ordering, and result.

</success_criteria>
