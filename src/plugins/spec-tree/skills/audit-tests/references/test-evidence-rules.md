<objective>

The rule catalog of the test-evidence audit and the contract of the composed language results: the identifier, severity, recording unit, and remediation owner of every rule the audit enforces.

</objective>

<contents>

- `<rule_catalog>` — the identifier, severity, recording unit, and remediation owner of every test-evidence audit rule
- `<remediation_owners>` — the closed set of owners a finding names
- `<language_result_contract>` — the shape of a composed language result and the catalog rule each composed finding takes

</contents>

<rule_catalog>

Every rule the test-evidence audit enforces has one row: one stable identifier, one severity, the unit that records it, and the owner whose change remediates it. A finding names exactly one identifier from this table, carries the severity its row declares, and names no identifier outside it. A defect no row covers is a gap in this standard: the rule enters this table before any finding cites it.

Unit names: the **root** is the run's root unit; an **assertion** unit is one `[test]` assertion; a **file** unit is one linked test file under one concern, `evidence` for this audit's language-neutral properties or `language-<lang>` for a composed language concern.

| Identifier                   | Severity | Rule                                                                                                                                                                                                                | Unit                                              | Remediation owner                                         |
| ---------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------- |
| `context-unavailable`        | blocking | Every decision a loaded record cites by full `spx/` path can be read.                                                                                                                                               | the unit that names it, else the root             | `test-infrastructure`                                     |
| `missing-test-file`          | blocking | Every `[test]` link of an included assertion resolves to a file.                                                                                                                                                    | assertion                                         | `test-file`                                               |
| `untestable-source`          | blocking | The governed production source exposes a seam through which a test observes or drives the assertion-relevant behavior.                                                                                              | assertion                                         | `source-file`                                             |
| `incomplete-evidence-chain`  | blocking | Every artifact the linked test reaches through repository imports or discovery is resolved, read, and classified by role.                                                                                           | file                                              | `test-infrastructure`                                     |
| `assertion-seam`             | blocking | Every behavioral predicate and assertion API call lies in the linked test function or callback, never in a harness, generator, fixture, controlled implementation, or recording collaborator.                       | file                                              | `test-file`                                               |
| `test-owned-configuration`   | blocking | No test binding chooses runner settings, seed policy, retries, setup policy, or lifecycle policy.                                                                                                                   | file                                              | `harness`                                                 |
| `test-owned-data`            | blocking | No test binding chooses case data, boundary bags, expected outputs, fixture contents, or generator domains that the assertion type does not assign to the test.                                                     | file                                              | `generator`, `fixture`, or `eval-case` by the data's role |
| `missing-seed-reporting`     | blocking | A property test runs under a harness-owned seed policy and its failure output carries the seed or replay path.                                                                                                      | file                                              | `harness`                                                 |
| `source-ownership`           | blocking | A source-owned singleton shape, vocabulary, protocol key, command token, or status value comes from its declared owner, never from a copy in a test or its infrastructure.                                          | file                                              | `source-contract`                                         |
| `oracle-independence`        | blocking | An expected result derives from an oracle independent of the production path that produces the actual result.                                                                                                       | file                                              | `independent-oracle`                                      |
| `no-coupling`                | blocking | The test imports codebase behavior, not only its test framework and libraries.                                                                                                                                      | file                                              | `test-file`                                               |
| `laundered-coupling`         | blocking | The test imports no infrastructure module that exists only to expose hardcoded values back to the test.                                                                                                             | file                                              | `source-contract`                                         |
| `false-coupling`             | blocking | A test that imports the module under test calls its assertion-relevant functions.                                                                                                                                   | file                                              | `test-file`                                               |
| `partial-coupling`           | blocking | The test calls the assertion-relevant functions on the inputs and code paths the assertion claims.                                                                                                                  | file                                              | `test-file`                                               |
| `coupling-severed`           | blocking | The test replaces no imported behavior with a mock, fake, stub, or monkeypatch outside the seven legitimate exception cases.                                                                                        | file                                              | `test-file`                                               |
| `prose-coupling`             | blocking | The test asserts executable behavior, never the content of an authored prose or documentation body, directly or through test infrastructure.                                                                        | file                                              | `test-file`                                               |
| `unfalsifiable`              | blocking | A named mutation to each imported module breaks the test.                                                                                                                                                           | file                                              | `test-file`                                               |
| `misaligned`                 | blocking | The test exercises the behavior the assertion describes, and the assertion cannot be unfulfilled while the test passes.                                                                                             | file                                              | `test-file`                                               |
| `strategy-mismatch`          | blocking | The test strategy fits the assertion type: example-based for a scenario, parameterized for a mapping, property-based for a property, tool or schema validation for a conformance, violating cases for a compliance. | file                                              | `test-file`                                               |
| `no-coverage`                | blocking | Reading the test against the governed source shows execution reaching the assertion-relevant path.                                                                                                                  | file                                              | `test-file`                                               |
| `architectural-duplication`  | blocking | Setup and test-infrastructure patterns repeated across assertions have one extraction target.                                                                                                                       | file, else the root for a cross-assertion pattern | `test-infrastructure`                                     |
| `unsupported-language`       | blocking | Every linked test filename ends in a suffix an installed language plugin declares.                                                                                                                                  | assertion                                         | `language-partition`                                      |
| `language-skill-unavailable` | blocking | The `audit-<lang>-tests` skill of every language partition in scope is installed and loads.                                                                                                                         | assertion                                         | `skill-installation`                                      |
| `language-result-invalid`    | blocking | A composed language result carries the shape `<language_result_contract>` states, names the audited target, and agrees with its own overall result.                                                                 | file                                              | `skill-installation`                                      |
| `language-concern`           | blocking | A language-specific finding that no neutral rule above covers is absent from the composed result.                                                                                                                   | file                                              | the owner the composed finding names                      |

</rule_catalog>

<remediation_owners>

A finding names its owner from this closed set: `source-contract`, `harness`, `generator`, `fixture`, `eval-case`, `test-file`, `source-file`, `test-infrastructure`, `independent-oracle`, `skill-installation`, `language-partition`. The owner is the semantic owner of the change, never the location of the defect: copied domain truth found in a harness, generator, fixture, discovery file, or test names `source-contract`.

</remediation_owners>

<language_result_contract>

A composed `audit-<lang>-tests` result is valid when it carries one of two shapes.

A verdict: a JSON object with `skill` naming the language skill, `target`, `overall` of `APPROVED` or `REJECTED`, and `rows`. The row `gate-1-assertion` carries the evidence-property findings. The row `gate-2-architectural` carries `architectural-duplication` findings and is omitted when it is non-applicable or when `gate-1-assertion` rejected the evidence. A row's `status` is `FAIL` exactly when it holds a `REJECT` finding. Each finding carries `id`, `file`, `line`, `assertion`, `property`, `rule`, `severity` of `REJECT`, `FILED`, `WARNING`, or `INFO`, `message`, and `remediation_target`.

A retirement: `{"status": "NOT_APPLICABLE", "subjects": [...], "explanation": "..."}`, carrying no rows and no findings, for subjects that are retired paths with no current `[test]` assertion and no current evidence-chain owner.

Each composed `REJECT` finding takes the catalog rule its `property` and `rule` name; a `FILED`, `WARNING`, or `INFO` finding enters no unit.

| Composed `property`           | Catalog rule                                                                                                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `testability`                 | `untestable-source`                                                                                                                                                  |
| `evidence-chain-completeness` | `incomplete-evidence-chain`                                                                                                                                          |
| `predicate-ownership`         | `assertion-seam`                                                                                                                                                     |
| `declarations`                | `test-owned-configuration` for the label `test-owned configuration`, `missing-seed-reporting` for `missing property seed reporting`, else `test-owned-data`          |
| `source-ownership`            | `source-ownership`                                                                                                                                                   |
| `oracle-independence`         | `oracle-independence`                                                                                                                                                |
| `coupling`                    | the coupling-taxonomy category the finding names: `no-coupling`, `laundered-coupling`, `false-coupling`, `partial-coupling`, `coupling-severed`, or `prose-coupling` |
| `falsifiability`              | `unfalsifiable`, or `coupling-severed` for a mock that severs coupling                                                                                               |
| `alignment`                   | `strategy-mismatch` for an assertion-type strategy failure, else `misaligned`                                                                                        |
| `coverage`                    | `no-coverage`                                                                                                                                                        |
| `architectural-duplication`   | `architectural-duplication`                                                                                                                                          |
| any other value               | `language-concern`                                                                                                                                                   |

</language_result_contract>
