<objective>

The rule catalog of the changeset-coherence audit: every rule identifier a finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `evidence_rules`

</contents>

<key_form>

The unit of a finding is the `unitId` of the recorded unit the finding concerns: the root unit `<scope>` for a finding about the changeset as a whole, `coherence:cluster-<n>` for a finding about one cluster, and `coherence:unresolved:<path-or-scope>` for a finding about an artifact or a calibration that no cluster holds. The key is `<unit>:<rule-id>`, for example `coherence:unresolved:<changed-path>:missing-generated-source-evidence`. One key covers every location within that unit where the rule is violated, and the finding lists each location.

</key_form>

<evidence_rules>

| Identifier                          | Severity | Rule                                                                                                                                                                          | Recorded on                          | Stated in                   |
| ----------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | --------------------------- |
| `split-required`                    | blocking | The changeset's semantic clusters are not independently mergeable; two or more clusters that are independently mergeable form separate review units.                          | The root unit                        | `verdict_rules`             |
| `missing-rollback-evidence`         | blocking | Every cluster carries a non-empty rollback story.                                                                                                                             | The cluster's unit                   | `verdict_rules`             |
| `missing-verification-evidence`     | blocking | Every cluster carries a non-empty verification story.                                                                                                                         | The cluster's unit                   | `verdict_rules`             |
| `missing-behavioral-claim-evidence` | blocking | Every changed authored artifact resolves to an established behavioral claim.                                                                                                  | The artifact's unresolved unit       | `execution_sequence` Step 5 |
| `missing-dependency-evidence`       | blocking | Two or more clusters carry an explicit dependency array; an absent or `null` set is unresolved.                                                                               | The lowest-numbered affected cluster | `verdict_rules`             |
| `missing-generated-source-evidence` | blocking | Every generated artifact resolves to its producer through a declared relationship or `generated_from`.                                                                        | The artifact's unresolved unit       | `execution_sequence` Step 4 |
| `missing-calibration-evidence`      | blocking | A repository-specific signal that requires calibration to judge the semantic evidence has the calibration it requires; a baseline absent without such a signal is no finding. | `coherence:unresolved:scope`         | `verdict_rules`             |

</evidence_rules>
