<objective>

The rule catalog of the test-evidence audit: every rule identifier a native finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog or the catalog of a composed language skill.

</objective>

<contents>
- `key_form`
- `evidence_chain_rules`
- `ownership_rules`
- `evidence_property_rules`
- `blocked_inspection_rules`
- `composed_rules`

</contents>

<key_form>

The unit of a finding is the repository-relative path of the artifact that holds the defect: a test, harness, generator, fixture, discovery artifact, or governed production source. For a finding that names no artifact, because the request carries no target, the unit is `input`. The key is `<unit>:<rule-id>`, for example `spx/55-example.enabler/tests/test_x.mapping.l1.py:source-ownership`. One key covers every location in that file where the rule is violated, and the finding lists each location as the assertion joined to the declaration or call that violates the rule, named by its text, never by a line number.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text takes severity `FILED`.

</key_form>

<evidence_chain_rules>

| Identifier                  | Severity | Rule                                                                                                          | Stated in                                                                              |
| --------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `missing-test-file`         | REJECT   | Every `[test]` link of an included assertion resolves to an existing file.                                    | `audit_workflow` Step 2                                                                |
| `incomplete-evidence-chain` | REJECT   | Every import of the evidence chain resolves, and every inventoried artifact is read and classified by role.   | `audit_workflow` Step 2b                                                               |
| `untestable-source`         | REJECT   | The governed production source exposes the boundary, seam, or injection point the assertion's behavior needs. | `product-tree:test-evidence-standards` `<assertion_design_record>`, production subject |

</evidence_chain_rules>

<ownership_rules>

| Identifier                        | Severity | Rule                                                                                                                                                                                     | Stated in                                                                                         |
| --------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `assertion-seam`                  | REJECT   | The linked test owns every predicate and assertion API call; infrastructure owns no predicate, matcher, expected-value parameter, assertion call, or verdict helper.                     | `product-tree:test-evidence-standards` `<predicate_seam>`                                         |
| `test-owned-configuration`        | REJECT   | A test-file binding chooses no runner setting, seed policy, setup policy, or lifecycle policy.                                                                                           | `product-tree:test-evidence-standards` `<semantic_binding_ownership>`, `<artifact_ownership>`     |
| `missing-property-seed-reporting` | REJECT   | A property test's harness owns the seed policy and reports the seed or replay path on failure.                                                                                           | `product-tree:test-evidence-standards` `<type_level_permissions>`, Property                       |
| `test-owned-data`                 | REJECT   | A test-file binding chooses no case data, boundary bag, expected output, fixture content, or generator domain the assertion type does not assign to the test.                            | `product-tree:test-evidence-standards` `<semantic_binding_ownership>`, `<assertion_type_litmus>`  |
| `source-ownership`                | REJECT   | A source-owned shape, vocabulary, protocol key, command token, or status value is imported from its owner, never copied into a test, harness, generator, fixture, or discovery artifact. | `product-tree:test-evidence-standards` `<artifact_ownership>`, `<case_provenance_and_oracles>`    |
| `oracle-independence`             | REJECT   | Every expected result comes from an oracle independent of the production path under test.                                                                                                | `product-tree:test-evidence-standards` `<case_provenance_and_oracles>`, `<assertion_type_litmus>` |

</ownership_rules>

<evidence_property_rules>

| Identifier           | Severity | Rule                                                                                                                                                        | Stated in                                                                                     |
| -------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `no-coupling`        | REJECT   | The test imports codebase behavior, not only its framework.                                                                                                 | `audit_workflow` Step 3b                                                                      |
| `laundered-coupling` | REJECT   | An imported test-infrastructure module gives the test access to real behavior, never only hardcoded values.                                                 | `audit_workflow` Step 3b                                                                      |
| `false-coupling`     | REJECT   | The test calls the assertion-relevant functions of every module it imports.                                                                                 | `audit_workflow` Step 3b                                                                      |
| `partial-coupling`   | REJECT   | The test calls the assertion-relevant functions on the inputs and code paths the assertion governs.                                                         | `audit_workflow` Step 3b                                                                      |
| `severed-coupling`   | REJECT   | The test replaces no module under test with a mock, fake, stub, or monkeypatch, except under a double type matching a legitimate exception case.            | `audit_workflow` Step 3b                                                                      |
| `prose-coupling`     | REJECT   | The test's evidence is executable behavior, never the content of an authored prose or documentation body.                                                   | `audit_workflow` Step 3b                                                                      |
| `unfalsifiable`      | REJECT   | A concrete mutation to every imported module the test depends on makes the test fail.                                                                       | `product-tree:test-evidence-standards` `<mutation_litmus>`, `<common_litmus_questions>`       |
| `misaligned`         | REJECT   | The test exercises the exact behavior the assertion states, with the strategy its assertion type requires, and fails whenever the assertion is unfulfilled. | `product-tree:test-evidence-standards` `<assertion_type_litmus>`, `<common_litmus_questions>` |
| `no-coverage`        | REJECT   | The test drives execution into the assertion-relevant path of the governed source.                                                                          | `product-tree:test-evidence-standards` `<mutation_litmus>`; `audit_workflow` Step 3e          |

</evidence_property_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection.

| Identifier             | Severity | Rule                                                                                                           | Stated in                |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `missing-target`       | REJECT   | The request carries the spec node or evidence scope.                                                           | `audit_workflow` opening |
| `unsupported-language` | REJECT   | Every linked test maps to exactly one installed language plugin's declared filename suffix.                    | `audit_workflow` Step 3f |
| `language-composition` | REJECT   | The `audit-<lang>-test` skill of each partition is installed and returns a result that satisfies its contract. | `audit_workflow` Step 3f |

</blocked_inspection_rules>

<composed_rules>

A validated composed finding, Gate 1 or Gate 2, keeps the rule identifier from the rule catalog of the invoked `audit-<lang>-test` skill, and its key is `<unit>:<that identifier>`. This catalog adds no identifier for it.

</composed_rules>
