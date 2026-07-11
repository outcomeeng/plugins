<!-- Generated from the full_chain_ownership concern at src/plugins/spec-tree/skills/audit-tests/SKILL.md. -->

This eval runs in the isolated verifier context required by the producer concern below. The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Required language-concern composition has already succeeded, as recorded in `input.language_composition`. Apply the selected language-neutral concern to the supplied test-evidence package. Return only the structured JSON verdict defined by that concern.

<step name="full_chain_ownership">

**Step 2b: Inventory the complete evidence chain**

Starting from the test links mapped in Step 2, follow each repository import recursively. Record one inventory entry per artifact:

| Field | Meaning |
| --- | --- |
| `path` | Repository-relative artifact path |
| `role` | `test`, `harness`, `generator`, `fixture`, `discovery`, or `production` |
| `imported_from` | Path that introduced the artifact, or null for root artifacts such as the linked test and applicable discovery configuration |
| `inspection_status` | `inspected` or `unresolved` |

Read every resolved artifact before continuing. A referenced fixture is inventoried even when consumed only by path. Include every `conftest.py` or equivalent discovery file that applies to the linked test.

If an import cannot be resolved from the caller's evidence package or repository, add a `gate-1-assertion` REJECT finding against the unresolved repository-relative path with rule `incomplete-evidence-chain`. Do not attribute the finding to the thin test file. Stop evidence-property judgment for that assertion because the chain is incomplete.

**Step 3: Testability precondition**

For each assertion, read the governed production source and identify the observable boundary, seam, or injection point through which a test can exercise the assertion-relevant behavior. Judge the source shape before judging the linked test.

If the source exposes no way to observe or drive that behavior, add a `gate-1-assertion` REJECT finding against the source file with rule `untestable-source` and `remediation_target: "source-file"`. State the missing seam and required production refactor. Skip declarations, coupling, falsifiability, alignment, and coverage for that assertion because test evidence cannot remediate untestable source.

**Step 3a: Ownership across the evidence chain**

Read each linked test file before coupling. Identify every variable, constant, local function, fixture parameter, or property-generated parameter and classify the proper owner:

Use language syntax while reading to enumerate declarations, then classify ownership by reading the declaration and its evidence role. Do not outsource the verdict to a grep pattern or validation command.

| Declaration                                | Verdict                                   |
| ------------------------------------------ | ----------------------------------------- |
| Any variable or constant                   | REJECT — test-file state                  |
| Framework fixture or property parameter    | REJECT — test-file binding                |
| Runner settings, seed policy, retries      | REJECT — test-owned configuration         |
| Test data, boundary bags, expected outputs | REJECT — test-owned data                  |
| Fixture paths, fixture contents            | REJECT — fixture ownership in test file   |
| Generator choices, arbitrary domains       | REJECT — generator ownership in test file |
| Harness setup policy or reusable resources | REJECT — harness ownership in test file   |
| Source-owned singleton shape or vocabulary | REJECT — source ownership copied to test  |

Do not treat casing as evidence. Renaming `MAPPING_RUNS` to `mappingRuns` only hides a heuristic trigger; it does not change ownership.

For property-based tests, verify seed and replay behavior by reading the imported harness or property wrapper. If a property test has no harness-owned seed policy and no failure output that includes the seed or replay path, REJECT with `test-owned configuration` or `missing property seed reporting`.

Apply category-specific ownership checks to every imported test-infrastructure artifact:

| Artifact role | Allowed ownership | REJECT with `source-ownership` |
| --- | --- | --- |
| Harness | Setup, teardown, cleanup, resource policy, access to real behavior, replay diagnostics | Protocol keys, command tokens, status values, expected outputs, arbitrary request payloads, or domain truth |
| Generator | Variable domains with meaningful variation and shrinking | Copied protocol vocabulary, constant-only domains, or hand-picked expected outputs |
| Fixture | Inert whole payload consumed by path or bytes | Isolated tokens, values, expected outputs, or executable exports |
| Discovery | Test collection and registration policy | Fixture bodies, domain values, generated cases, or hidden setup policy |

For every case input, expected value, protocol key, command token, status value, rule identifier, and payload member, name its source in the inventory. Source-owned values resolve to their production or platform owner. Generated values resolve to a variable generator. Whole-payload samples resolve to an inert fixture. A value with no valid owner produces a finding against the artifact that declares it with `property: "source-ownership"`, rule `source-ownership`, and `remediation_target: "source-contract"`; a harness location never establishes ownership by itself. The finding `file` names the artifact that copied the value, while `remediation_target` names the production contract that must own it — NEVER substitute the artifact role (`harness`, `generator`, or `fixture`) for `source-contract`.

For an isolated ownership-concern verdict, return only this JSON shape. Set `overall` to `APPROVED` only when the gate row passes with no `REJECT` finding. Include every inventoried artifact in `metadata.evidence_chain`; an approval with an unresolved or omitted artifact is invalid.

```json
{
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "gate-1-assertion",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "stable-finding-id",
          "file": "repository-relative-path",
          "line": "line-number-or-location",
          "assertion": "full assertion text",
          "property": "failed evidence property",
          "rule": "failed rule",
          "severity": "REJECT | WARNING | INFO",
          "message": "evidentiary gap",
          "remediation_target": "source-contract | source-file | test | harness | generator | fixture | spec"
        }
      ]
    }
  ],
  "metadata": {
    "evidence_chain": [
      {
        "path": "repository-relative-path",
        "role": "test | harness | generator | fixture | discovery | production",
        "imported_from": "repository-relative-path | null",
        "inspection_status": "inspected | unresolved"
      }
    ]
  }
}
```

</step>
The test-evidence package (JSON-encoded):

```json
{input_json}
```
