<objective>

The rule catalog of the changeset-coherence audit: every rule identifier a finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `evidence_rules`

</contents>

<key_form>

The unit of a finding is the repository-relative path of the changed artifact that lacks the evidence, or `scope` for a finding that concerns the changeset or a cluster as a whole. The key is `<unit>:<rule-id>`, for example `<changed-path>:missing-generated-source-evidence`. One key covers every location within that unit where the rule is violated, and the finding lists each location.

</key_form>

<evidence_rules>

| Identifier                          | Severity | Rule                                                                                                                                                                          | Stated in               |
| ----------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| `missing-rollback-evidence`         | blocking | Every cluster carries a non-empty rollback story.                                                                                                                             | `verdict_rules`         |
| `missing-verification-evidence`     | blocking | Every cluster carries a non-empty verification story.                                                                                                                         | `verdict_rules`         |
| `missing-behavioral-claim-evidence` | blocking | Every changed authored artifact resolves to an established behavioral claim.                                                                                                  | `verdict_rules`         |
| `missing-dependency-evidence`       | blocking | Two or more clusters carry an explicit dependency array; an absent or `null` set is unresolved.                                                                               | `verdict_rules`         |
| `missing-generated-source-evidence` | blocking | Every generated artifact resolves to its producer through a declared relationship or `generated_from`.                                                                        | `audit_workflow` Step 4 |
| `missing-calibration-evidence`      | debt     | A repository-specific signal that requires calibration to judge the semantic evidence has the calibration it requires; a baseline absent without such a signal is no finding. | `verdict_rules`         |

</evidence_rules>
