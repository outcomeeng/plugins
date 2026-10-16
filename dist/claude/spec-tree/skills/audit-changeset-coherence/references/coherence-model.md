<objective>

The coherence model of the changeset-coherence audit: the artifact roles, semantic clusters, review units, and the rule catalog from which every finding draws its rule.

</objective>

<contents>

- `artifact_roles`
- `semantic_clusters`
- `review_units`
- `evidence_classes`
- `rule_catalog`

</contents>

<artifact_roles>

Classify every changed path by exactly one role: decision or specification, test or eval evidence, implementation, generated artifact, workflow or configuration, documentation, migration, deployment, or release. Every role except generated artifact is authored.

A generated artifact resolves to its producing authored artifact through a repository-declared build relationship: a declaration the repository carries that names the generated extent, its authored sources, and the command that regenerates it. A declaration may name a generated region of an authored file instead of a whole file; that region shares its producer's cluster, and the file's other text keeps its authored role. A role label of `generated`, a path that resembles a source, an artifact count, and the presence of a single authored artifact establish no producer. An artifact whose producer the repository's declarations leave unestablished stays unresolved and feeds `missing-generated-source-evidence`.

Collapse each resolved generated artifact onto its producer before path breadth, authored-change size, or review load is assessed. A generated artifact shares the cluster of its producing authored artifact and is carried as that cluster's generated fanout.

</artifact_roles>

<semantic_clusters>

A semantic cluster is the smallest set of authored artifacts that realizes one behavioral claim. Extract claims from the changed declarations and from the observable behavior of the changed implementation and evidence; a commit message supports a claim and never overrides a changed artifact.

Every authored artifact in scope belongs to exactly one cluster. For each cluster, establish from the committed content:

| Fact                 | Meaning                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------- |
| Outcome              | The behavioral outcome the cluster realizes                                                        |
| Authored artifacts   | The authored paths in the cluster                                                                  |
| Generated fanout     | The generated paths that share the cluster                                                         |
| Verification story   | The evidence that proves the outcome, and the artifacts that carry it                              |
| Rollback story       | The artifact or operation that reverses the outcome                                                |
| Dependencies         | The other clusters whose change this cluster requires, or an established absence of any dependency |
| Mergeable on its own | Whether the cluster can be verified and rolled back without any other cluster                      |
| Review-load signals  | The cluster's authored-change size and path breadth after collapse, or none                        |

Fuse into one inseparable cluster every dependency cycle and every set of clusters that cannot be verified or rolled back separately. Name clusters `cluster-1`, `cluster-2`, and so on, in dependency order, breaking ties between independent clusters by the lexicographically first authored path.

Raw line count, file count, path breadth, and review-load measurements never place an artifact in a cluster and never decide the verdict. A review-load signal raises scrutiny only.

</semantic_clusters>

<review_units>

Every cluster that survives fusion forms one review unit. Order the review units topologically over cluster dependencies, in the same order as their clusters, and name them `review-unit-1`, `review-unit-2`, and so on. A review unit lists the clusters it covers, its authored and generated paths, and the earlier review units it depends on; a review unit references only earlier review units.

Surviving clusters are independently mergeable, a cluster that depends on and merges after an earlier cluster included. A changeset with one surviving cluster is one reviewable semantic unit. A changeset with two or more surviving clusters is an accumulated program of work.

</review_units>

<evidence_classes>

A judgment that rests on evidence the committed content does not establish is undecidable, never inferred:

| Class                  | The evidence                                                                                                                                                                       |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Behavioral claim       | The claim an artifact realizes can be read from the artifact                                                                                                                       |
| Dependency             | The dependency between two clusters, or its absence, is established; evidence that is merely unavailable is not an established absence                                             |
| Generated source       | Every generated artifact resolves to a producer through a repository-declared relationship                                                                                         |
| Verification           | Every cluster has a verification story                                                                                                                                             |
| Rollback               | Every cluster has a rollback story; an empty rollback story is missing evidence before any approval is considered                                                                  |
| Repository calibration | A review-load baseline exists where a repository-specific signal requires it to decide whether the available semantic evidence is sufficient; otherwise its absence forces nothing |

</evidence_classes>

<rule_catalog>

Every rule the audit enforces has one row: one stable identifier, one severity, and the unit that records it. A finding names exactly one identifier from this table, carries the severity its row declares, and names no identifier outside it. A defect no row covers is a gap in this standard: the rule enters this table before any finding cites it.

| Identifier                          | Severity | Rule                                                                                                                                                                        | Unit                  |
| ----------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `split-required`                    | blocking | The changeset realizes one behavioral outcome, or inseparable clusters with one verification story and one rollback story, so it holds one independently mergeable cluster. | the root              |
| `missing-behavioral-claim-evidence` | blocking | The behavioral claim of every changed authored artifact can be established from the committed content.                                                                      | the `incomplete` unit |
| `missing-dependency-evidence`       | blocking | The dependency between every pair of clusters, or its absence, is established.                                                                                              | the `incomplete` unit |
| `missing-generated-source-evidence` | blocking | Every generated artifact resolves to its producing authored artifact through a repository-declared relationship.                                                            | the `incomplete` unit |
| `missing-verification-evidence`     | blocking | Every cluster carries a verification story.                                                                                                                                 | the `incomplete` unit |
| `missing-rollback-evidence`         | blocking | Every cluster carries a rollback story.                                                                                                                                     | the `incomplete` unit |
| `missing-calibration-evidence`      | blocking | A repository-specific signal that requires a review-load baseline finds that baseline established.                                                                          | the `incomplete` unit |

</rule_catalog>
