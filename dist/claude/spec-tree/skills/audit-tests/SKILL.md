---
name: audit-tests
description: >-
  Test-evidence audit methodology — judges whether a spec node's tests provide
  behavior-coupled evidence its assertions are fulfilled, covering predicate
  ownership, source ownership, coupling, falsifiability, and full-chain coverage.
model: sonnet
allowed-tools: Read, Grep, Glob, Skill
---

<objective>

A verdict on whether a spec node's tests provide behavior-coupled evidence its assertions are fulfilled — APPROVED, or REJECTED with each finding naming the assertion, the failed evidence property or cross-assertion architectural duplication, and the evidentiary gap.

</objective>

<constraints>

- NEVER modify the tests under audit or any other file — this audit produces a verdict, never a fix or a commit.
- NEVER run the project's coverage command, test command, linter, type-checker, or any other deterministic verification inside the audit — deterministic verification on the changeset is a precondition, and CI re-runs it over the whole repository; establish coverage by reading whether the test drives execution into the assertion-relevant path.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every REJECT finding.
- ALWAYS construct every finding as one complete record containing `id`, `file`, `line`, `assertion`, `property`, `rule`, `severity`, `message`, and `remediation_target` before adding it to a row — required fields are never deferred to verdict rendering.
- ALWAYS reject an incomplete evidence-chain inventory before approval; absence of an artifact is missing evidence, never permission to infer its contents.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the tests for it.
- This skill grants no `Bash` capability, unlike the language auditors it composes. The omission is deliberate: the no-deterministic-verification constraint above is enforced at the tool-permission layer rather than by prose alone, and this base audit reaches every artifact it judges through `Read`, `Grep`, and `Glob`. Do not add a `Bash` grant for parity.

</constraints>

<essential_principles>

**PREDICATE AND OWNERSHIP SCREEN, THEN COUPLING.**

The linked test function or callback owns every predicate and assertion API call. Screen the full chain for verdict logic and classify each test-file binding by semantic choice before checking imports. A test that imports nothing from the codebase will pass forever regardless of what any file contains. This is a prerequisite.

**COMPLETE THE EVIDENCE CHAIN.**

Start from every linked test and recursively follow repository imports through test infrastructure before judging evidence. Inventory each linked test, harness, generator, fixture reference, and applicable discovery artifact with its path, role, importing artifact, and inspection status. An unresolved import, unread artifact, or unclassified role is `incomplete-evidence-chain` and rejects the audit. Approval requires a complete inventory in verdict metadata.

Four properties must hold, checked in strict order: coupling (the test exercises codebase behavior, not authored prose), falsifiability (a named mutation breaks it), alignment (it exercises the asserted behavior), and coverage (the test drives execution into the assertion-relevant path). A test missing any property has zero evidentiary value regardless of code quality.

**JUDGE COVERAGE BY READING.**

Apply the no-deterministic-verification constraint above by establishing coverage from a source trace into the assertion-relevant code path.

**NO MECHANICAL SUBSTITUTES.**

Mocking patterns, skip patterns, type annotations — these are linting concerns (SemGrep, ESLint). The auditor evaluates evidence quality, not code quality signals. The declaration screen is a read step: identify declarations in the test file, then judge ownership from their evidence role.

Apply the literal rule by reading the test's literals against their sources.

**TEST FILES OWN PREDICATES AND NO INDEPENDENT DATA OR CONFIGURATION.**

Before coupling, inspect every executed test and imported infrastructure artifact. Every behavioral predicate and assertion API call remains lexically in the linked test function or callback. Reject a harness, generator, fixture, controlled implementation, or recording collaborator that accepts an expected outcome, returns a verdict, calls an assertion API, or exposes matcher-shaped verdict methods.

Classify bindings by what they choose. Observation aliases, actual-result bindings, imported source-contract aliases, generated parameters, callback inputs, and resource handles are valid when they introduce no data or policy. A framework-provided temporary-directory handle, a local binding that receives a harness observation, and an assertion-local projection over observations are therefore valid. NEVER reject a binding merely because it is a parameter, assignment, alias, or local expression; moving those values into a harness would hide assertion flow and can move the predicate across the seam. Reject bindings that choose cases, expectations, runner settings, property configuration, setup policy, reusable data, generator domains, fixture payloads, or verdict rules. The remediation target is part of the finding: source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, independent oracle, or curated eval case data when generation is wasteful and not tractable.

**BINARY VERDICT.**

APPROVED or REJECTED. No middle ground. If any property is missing for any assertion, REJECTED.

</essential_principles>

<audit_workflow>

<step name="load_standards">

**Step 0: Load shared test-evidence standards**

Invoke the `spec-tree:test-evidence-standards` skill through the runtime skill-composition surface before proceeding. Apply its complete predicate-seam, semantic-binding, case-provenance, oracle-independence, assertion-type-litmus, and mutation litmus rules. A missing reference blocks the audit because `/test` and `/audit-tests` must judge from the same standards.

</step>

<step name="load_context">

**Step 1: Load context**

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent, then invoke `/contextualize` on the spec node whose tests are being audited. This loads the spec's assertions, ancestor ADRs/PDRs, and the full hierarchy context.

Do not proceed without live `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers.

</step>

<step name="map_assertions">

**Step 2: Map assertions to test files**

Read the spec's Assertions section. Only assertions carrying `[test]` evidence enter this audit. Skip assertions tagged `[eval]` or `[audit]`; their evidence belongs to other verification workflows.

For each included assertion, extract:

| Field          | Extract                                                  |
| -------------- | -------------------------------------------------------- |
| Assertion text | The claim being tested                                   |
| Assertion type | Scenario / Mapping / Conformance / Property / Compliance |
| Test link      | Path from `([test](path))`                               |
| Link status    | File exists or missing                                   |

**Missing test file = finding.** Record it and continue to next assertion.

</step>

<step name="full_chain_ownership">

**Step 2b: Inventory the complete evidence chain**

Starting from the test links mapped in Step 2, follow each repository import recursively. Record one inventory entry per artifact:

| Field               | Meaning                                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `path`              | Repository-relative artifact path                                                                                            |
| `role`              | `test`, `harness`, `generator`, `fixture`, `discovery`, or `production`                                                      |
| `imported_from`     | Path that introduced the artifact, or null for root artifacts such as the linked test and applicable discovery configuration |
| `inspection_status` | `inspected` or `unresolved`                                                                                                  |

Read every resolved artifact before continuing. A referenced fixture is inventoried even when consumed only by path. Include every applicable discovery or module-resolution artifact supplied in the evidence package: examples include `conftest.py` or pytest configuration, Vitest configuration, `Cargo.toml`, and `go.mod`. A discovery artifact remains in `metadata.evidence_chain` when it produces no finding. The final inventory MUST contain exactly one entry for every artifact used to resolve imports, ownership, collection, or discovery.

If an import cannot be resolved from the audit evidence package or repository, add a `gate-1-assertion` REJECT finding against the unresolved repository-relative path with rule `incomplete-evidence-chain` and `remediation_target: "test-infrastructure"`. Do not attribute the finding to the thin test file. Stop evidence-property judgment for that assertion because the chain is incomplete.

**Step 3: Testability precondition**

For each assertion, read the governed production source and identify the observable boundary, seam, or injection point through which a test can exercise the assertion-relevant behavior. Judge the source shape before judging the linked test.

If the source exposes no way to observe or drive that behavior, add a `gate-1-assertion` REJECT finding against the source file with rule `untestable-source` and `remediation_target: "source-file"`. State the missing seam and required production refactor. Skip declarations, coupling, falsifiability, alignment, and coverage for that assertion because test evidence cannot remediate untestable source.

**Step 3a: Ownership across the evidence chain**

Read each linked test file before coupling. Identify every variable, constant, local function, fixture parameter, property-generated parameter, predicate, and assertion API call and classify the proper owner:

Use language syntax while reading to enumerate declarations, then classify ownership by reading the declaration and its evidence role. Do not outsource the verdict to a grep pattern or validation command.

Before applying the data rows, resolve anything that looks like case data through the per-assertion-type litmus from `/test-evidence-standards`, applied below. A case that litmus assigns to the test itself is correctly owned there and is never a REJECT; demanding it move into a production module is the source laundering the standard forbids.

| Binding or predicate role                                                                                                                       | Verdict                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Actual result, observation, resource handle, generated parameter, callback input, or imported-contract alias that introduces no choice          | ACCEPT — assertion flow                  |
| Behavioral predicate or assertion API call in the linked test function or callback                                                              | ACCEPT — test-owned predicate            |
| Predicate, matcher, expected-value parameter, assertion call, or verdict helper in infrastructure                                               | REJECT — assertion seam                  |
| Runner settings, seed policy, retries, setup policy, or lifecycle policy                                                                        | REJECT — test-owned configuration        |
| Test-invented case data, boundary bags, expected outputs, fixture contents, or generator domains the assertion type does not assign to the test | REJECT — test-owned data                 |
| Source-owned singleton shape or vocabulary copied into the test                                                                                 | REJECT — source ownership copied to test |

Do not treat casing or syntax as evidence. Renaming `MAPPING_RUNS` to `mappingRuns`, changing an assignment to destructuring, or receiving a value through a parameter does not change what the binding chooses.

Use `predicate-ownership` with rule `assertion-seam` and remediation target `test-file` when infrastructure owns a predicate, matcher, expected-value parameter, assertion call, or verdict helper. Use `oracle-independence` with remediation target `independent-oracle` when an expected result derives from the production table, algorithm, parser, branch logic, or other implementation path that produces the actual result. Use `source-ownership` when the test copies a source-owned singleton shape or vocabulary. Use `declarations` for the remaining two REJECT rows — test-owned configuration and test-owned data — so a binding that chooses runner settings, seed policy, setup or lifecycle policy, boundary bags, expected outputs, fixture contents, generator domains, or case data the assertion type does not assign to the test always reports one property name rather than an invented one.

For property-based tests, verify seed and replay behavior by reading the imported harness or property wrapper. If a property test has no harness-owned seed policy and no failure output that includes the seed or replay path, REJECT with `test-owned configuration` or `missing property seed reporting`.

Apply category-specific ownership checks to every imported test-infrastructure artifact:

| Artifact role | Allowed ownership                                                                      | REJECT with `source-ownership`                                                                              |
| ------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Harness       | Setup, teardown, cleanup, resource policy, access to real behavior, replay diagnostics | Protocol keys, command tokens, status values, expected outputs, arbitrary request payloads, or domain truth |
| Generator     | Variable domains with meaningful variation and shrinking                               | Copied protocol vocabulary, constant-only domains, or hand-picked expected outputs                          |
| Fixture       | Inert whole payload consumed by path or bytes                                          | Isolated tokens, values, expected outputs, or executable exports                                            |
| Discovery     | Test collection and registration policy                                                | Fixture bodies, domain values, generated cases, or hidden setup policy                                      |

Judge a source symbol the test cites by declared-contract ownership: does production consume it, emit it, publish it as API, register it, or serialize it against a declared schema? An absent in-repository caller opens that question rather than settling it, so inspect the declared surfaces the checkout carries — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting the symbol as laundered. Name the surfaces inspected in the finding. Report the finding when none of them requires the symbol: a consumer outside the checkout is not evidence this audit can gather, so its bare possibility never withholds a finding the declared surfaces support.

For every case input, expected value, protocol key, command token, status value, rule identifier, and payload member, name its source and independent oracle in the inventory. Apply the per-assertion-type litmus questions from `/test-evidence-standards`. A value with no valid owner produces a `source-ownership` finding; an expectation derived from the production path under test produces an `oracle-independence` finding. The finding's `file` names the artifact that copied or coupled the value. Every `source-ownership` finding sets `remediation_target` to `source-contract`, even when the copied value appears in a harness, generator, fixture, discovery file, or test; the defect location never becomes the semantic owner.

</step>

<step name="audit_coupling">

**Step 3b: Coupling**

Read the test file's import statements. Classify each import:

| Import source                                  | Classification             |
| ---------------------------------------------- | -------------------------- |
| Test framework (vitest, pytest, jest)          | Framework — does not count |
| Node modules / pip packages                    | Library — does not count   |
| Codebase path (relative import, product alias) | Codebase — counts          |

**Zero codebase imports → REJECT — "no coupling" (tautology).**

If codebase imports exist, classify using this coupling taxonomy:

| Category           | Definition                                                                                        | Verdict                                         |
| ------------------ | ------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Direct             | Test imports the module under test                                                                | Proceed                                         |
| Indirect           | Test imports a harness wrapping the module                                                        | Proceed — verify harness has real coupling      |
| Transitive         | Test imports a consumer of the module                                                             | Proceed — verify test level matches             |
| Laundered indirect | Imports a test-infrastructure module that exists only to expose hardcoded values back to the test | REJECT — laundering                             |
| False              | Imports module but never calls assertion-relevant functions                                       | REJECT                                          |
| Partial            | Calls functions but on wrong inputs or wrong code paths                                           | REJECT                                          |
| None               | Test imports only its test framework                                                              | REJECT — tautology                              |
| Severed            | Imports the module under test and replaces its behavior with a mock, fake, stub, or monkeypatch   | REJECT — coupling severed                       |
| Prose-coupling     | Reads an authored prose/doc body and asserts its content                                          | REJECT — couples to authored text, not behavior |

Coupling means exercising executable **behavior**, never reading a document's content. A test whose "subject" is an authored prose or documentation artifact — a skill body, a spec body, a prompt, any text the product authors and maintains — that the test reads and asserts substrings of is NOT behavioral coupling, even when that artifact is the thing the assertion names. The text passes whatever it literally contains; no code runs. This holds full-chain: a harness that exposes the authored path as a constant, or a reader function that performs the read inside test infrastructure, does not convert a prose assertion into behavioral coupling — follow the read to its source and classify by what is ultimately exercised.

**A test whose evidence is reading an authored prose or documentation body and asserting on its content → REJECT — "prose-coupling."** The claim verifies that prose was authored, not that code behaves; its verification type belongs in `[eval]` (a graded judgment over a producer's structured verdict) or `[audit]` (a semantic constraint), and the spec assertion is retagged accordingly. Reading an authored *source-code* file for a structural lint that exercises a rule is not prose-coupling; the discriminator is whether the subject is authored prose/documentation or executable behavior.

</step>

<step name="audit_falsifiability">

**Step 3c: Falsifiability**

For each codebase import, name a concrete mutation to the imported module that would cause this test to fail. Write it down:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed result
Impact: "parses nested sections" fails — expect(result.section.key) throws
```

**Cannot name a mutation for any import → REJECT — "unfalsifiable."**

Check for mocking. If the test imports a module then replaces it with a mock, the coupling is severed:

```typescript
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn() }));
// Real database.query never runs — coupling severed
```

**Import + mock = REJECT — "coupling severed."**

**Exception**: Test doubles used under these seven legitimate exception cases from the `/test` methodology are not "coupling severed." Identify the matching exception and verify the double type:

| Exception             | Double type           |
| --------------------- | --------------------- |
| Failure simulation    | Stub returning errors |
| Interaction protocols | Spy recording calls   |
| Time and concurrency  | Fake clock            |
| Safety                | Stub that records     |
| Combinatorial cost    | Configurable fake     |
| Observability         | Spy recording details |
| Contract probes       | Contract stub         |

</step>

<step name="audit_alignment">

**Step 3d: Alignment**

Read the spec assertion text. Read the test's expect/assert statements. Answer:

1. Does the test exercise the exact behavior the assertion describes?
2. Could the spec assertion be unfulfilled while the test passes?

If yes to question 2: **REJECT — "misaligned."**

Judge the test against the executable source contract without making the test
duplicate or parse the authored spec text. When production exports a value or
typed contract, uses it in the behavior under test, and the test imports that
same contract while exercising the behavior, a change to the source contract is
an intentional behavior change rather than a mutation the test must reject.
Name a mutation to the consuming behavior that would break the test. NEVER
require a test or test-infrastructure artifact to parse spec or decision Markdown
or copy a literal from that prose as an independent oracle; authored prose is
verified through spec audit and review, and duplicated literals violate source
ownership.

Check assertion-type-to-strategy alignment:

| Assertion type | Required test strategy                            | REJECT if                 |
| -------------- | ------------------------------------------------- | ------------------------- |
| Scenario       | Example-based with Given/When/Then inputs         | Missing concrete scenario |
| Mapping        | Parameterized over input set                      | Only one example tested   |
| Property       | Property-based framework (fast-check, Hypothesis) | Only example-based        |
| Conformance    | Tool or schema validation                         | Manual check              |
| Compliance     | Rule exercised against violating cases            | Only conforming cases     |

</step>

<step name="audit_coverage">

**Step 3e: Coverage**

Establish coverage by tracing whether the test reaches the assertion-relevant behavior in source.

Trace, by reading, whether the test drives execution into the assertion-relevant code path:

1. Read the production code the assertion governs and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that production code.
3. Judge whether the test's execution reaches the assertion-relevant path — the lines whose behavior the assertion claims.

**Interpret the trace:**

- **Reaches the assertion-relevant path**: the test exercises the behavior the assertion claims. ✓
- **Imports the module but never drives execution into the assertion-relevant path**: REJECT — "no coverage." Name the specific assertion-relevant path the test fails to reach, traced from the code.
- **The assertion-relevant path is trivially total** (the test obviously exercises every line the assertion claims): record `judgment: "saturated"` in `metadata.coverage_traces`. The test's evidentiary value comes from the other three properties.

Coverage here is execution breadth (does the test reach the assertion-relevant lines), not assertion strength. A property-based test that exercises the same lines over a broader input domain adds behavior-coupled evidence that reading captures and a line count would not.

The judgment is traced from the code and named in the finding — never a measured percentage, and never an unbacked "probably covers."

</step>

<step name="compose_language">

**Step 3f: Compose language-specific test-evidence concerns**

The four evidence properties above are language-neutral. Language-specific test-evidence concerns — the per-language check IDs and extraction targets named in `<verdict_format>` — are owned by the language test audit skill, not by this one.

Read detected language or language partitions from the audit inputs. When absent, derive partitions from the linked-test filenames and the installed language plugins. Take the installed `audit-<lang>-tests` skills from the skill listing already in context; no directory scan is needed. For each, load that language's `<lang>-test-standards` skill and read its filename instantiation of `<subject>.<evidence>.<level>[.<runner>]` — the concrete pattern the standard states, such as `test_<subject>.<evidence>.<level>[.<runner>].py`. The text after the last closing bracket is the declared suffix: a compound suffix such as `.test.ts` as readily as a bare `.py` or `_test.go`. Map every linked test whose filename ends in an installed plugin's declared suffix to that language. Reject a suffix no installed plugin declares, or an ambiguous partition, with property `unsupported-language` and remediation target `language-partition` instead of guessing; never map an extension from a list this skill carries.

When the audit inputs include a completed `language_composition` result, validate its `status` and `findings` fields and consume it without dispatching the same concern again. A `PASS` result with no `REJECT` finding satisfies composition; merge any non-blocking findings into matching rows. A `FAIL` result or malformed composition evidence appends a `gate-1-assertion` `REJECT` finding with property `language-composition` and returns REJECTED.

When completed composition evidence is absent and an `audit-<lang>-tests` skill exists for each language in scope, load and apply each skill through the runtime's supported skill mechanism. It returns a verdict in this same row schema (`gate-1-assertion`, `gate-2-architectural`) carrying language-specific check IDs and no `gate-0-deterministic` row. **Merge its findings into the matching rows by `name`** — append, never replace — and emit one merged verdict. When a required `audit-<lang>-tests` skill is absent or unavailable, append a `FAIL` row with a `REJECT` finding naming the missing skill, property `language-composition`, and remediation target `skill-installation`; never approve incomplete coverage.

A language audit returns a third shape when its own scope step finds that every subject it was given is a retired path with no current `[test]` assertion and no current evidence-chain owner: `{"status": "NOT_APPLICABLE", "subjects": [...], "explanation": "..."}`, carrying no rows and no findings. Treat it as neither a pass nor a failure of that language's concerns. Record the reported subjects and explanation in verdict metadata, compose the remaining languages normally, and decide the overall verdict from the rows that do exist. When every language in scope returns `NOT_APPLICABLE` and no language-neutral finding was raised, emit that same shape rather than an approval, because no evidence was judged.

</step>

<step name="compose_architectural">

**Step 3g: Roll up composed architectural duplication**

Gate 2 is a composed-language concern. It applies when at least one language-specific verdict returns a `gate-2-architectural` row. Merge every applicable Gate 2 finding by row name, preserving each finding's language-specific rule and extraction target.

- Return Gate 2 `FAIL` when any composed Gate 2 row contains a `REJECT` finding.
- Return Gate 2 `PASS` when every applicable composed Gate 2 row passes.
- Omit Gate 2 only when every composed language verdict omits it — as non-applicable, or because that language's Gate 1 rejected the evidence, so its Gate 2 never ran.
- Treat a malformed or unevaluated applicable Gate 2 row as failed `language-composition` evidence; never infer architectural approval.

</step>

<step name="verdict">

**Step 4: Issue verdict**

Scan all findings across all assertions, including any folded in from the composed language audit. If any assertion has a property failure: **REJECTED.**

Before row rollup, inspect every finding as a complete record. Require all nine finding fields from `<verdict_format>`, including `remediation_target`, and derive that target from the semantic owner named by the evidence model. Complete a missing field before adding the finding to a row; never emit a partial finding and rely on its message to imply the omitted field.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never emit a prose or markdown verdict.

The skill's `overall` is `APPROVED` iff every applicable gate row is `PASS`; otherwise it is `REJECTED`. A required gate that cannot be evaluated is a `FAIL` row with a `REJECT` finding naming the missing evidence. Findings within each row carry severity `REJECT` for blocking findings (these are what flip a row to `FAIL`), `WARNING` or `INFO` for non-blocking observations. Every finding MUST include every field shown in its row schema: `id`, `file`, `line`, `assertion`, `property`, `rule`, `severity`, `message`, and `remediation_target`; omission of any field is an invalid verdict.

The `metadata.evidence_chain` array MUST project the complete Step 2b inventory. Preserve every applicable discovery artifact in the array even when it carries no finding; omitting an inspected artifact makes the verdict incomplete. The `metadata.coverage_traces` array MUST carry one entry per audited assertion, naming the assertion-relevant source path, the test path followed into it, and the coverage judgment. Use `saturated` only for a trivially total path reached by the test.

```json
{
  "schema_version": 1,
  "skill": "audit-tests",
  "target": "<spec-node-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "gate-1-assertion",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "f-002",
          "file": "<test-file>",
          "line": null,
          "assertion": "<full-assertion-text-or-stable-id>",
          "property": "<testability | evidence-chain-completeness | declarations | predicate-ownership | source-ownership | oracle-independence | coupling | falsifiability | alignment | coverage | language-composition | unsupported-language>",
          "rule": "<assertion-id-or-property-name>",
          "severity": "REJECT",
          "message": "<one-line evidentiary gap>",
          "remediation_target": "<source-contract | harness | generator | fixture | eval-case | test-file | source-file | test-infrastructure | independent-oracle | skill-installation | language-partition>"
        }
      ]
    },
    {
      "name": "gate-2-architectural",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "f-003",
          "file": "<test-file>",
          "line": null,
          "assertion": "<full-assertion-text-or-stable-id | cross-assertion>",
          "property": "architectural-duplication",
          "rule": "<duplication-pattern>",
          "severity": "REJECT",
          "message": "<extraction target>: <nearest common test-infrastructure location>",
          "remediation_target": "<source-contract | harness | generator | fixture | eval-case | test-file | source-file | test-infrastructure | independent-oracle | skill-installation | language-partition>"
        }
      ]
    }
  ],
  "metadata": {
    "branch": "<branch>",
    "evidence_chain": [
      {
        "path": "<repository-relative-path>",
        "role": "test | harness | generator | fixture | discovery | production",
        "imported_from": "<repository-relative-path-or-null>",
        "inspection_status": "inspected | unresolved"
      }
    ],
    "coverage_traces": [
      {
        "assertion": "<full-assertion-text-or-stable-id>",
        "source_path": "<repository-relative-assertion-relevant-path>",
        "test_path": "<repository-relative-test-path-and-call-chain>",
        "judgment": "reaches | saturated | missing"
      }
    ]
  }
}
```

A non-applicable Gate 2 row is omitted. A required gate that cannot be evaluated uses `status: "FAIL"` with a `REJECT` finding naming the missing evidence. A `source-ownership` finding uses `property: "source-ownership"`, `rule: "source-ownership"`, and `remediation_target: "source-contract"`; other findings select the failed property, rule, and owner that must change from the enumerated values. This verdict schema contains no `gate-0-deterministic` row. Language-specific test audit skills inherit this shape — they add language-specific check IDs and extraction targets to the findings but do not change the row names or schema.

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Claude approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. The tests pass if the entire codebase is deleted. Claude was distracted by clean types, good structure, and comprehensive scenarios, and never checked the imports.

How to avoid: Step 3b checks imports before the other evidence properties. Zero codebase imports = instant REJECT.

**Failure 2: Accepted mocking as legitimate coupling**

Claude saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. The real module never ran.

How to avoid: Step 3c checks for mocking after confirming coupling. Import + mock = coupling severed.

**Failure 3: Re-ran the project's coverage command inside the audit**

Claude ran the project's coverage command three times (baseline, with-test, isolated) to measure a delta. Those runs added no audit evidence and repeated work excluded by `<constraints>`.

How to avoid: Step 3e traces coverage by reading whether the test drives execution into the assertion-relevant path. Name the path from the code; never run the coverage or test command, and never substitute an unbacked "probably covers" for the trace.

**Failure 4: Distracted by code quality signals**

Claude spent the entire audit checking for `as any`, verifying return types, and searching for skip patterns. The test had perfect TypeScript quality and zero evidentiary value. Quality signals are linting concerns, not audit concerns.

How to avoid: Follow the complete ordered audit sequence: inventory the evidence chain, check source testability, screen test-owned declarations, then judge coupling, falsifiability, alignment, and coverage.

**Failure 5: Approved a prose-body substring test as direct coupling**

Claude audited a test that read an authored skill body and asserted that policy substrings were present, and rated coupling PASS — "direct coupling to the artifact; the text is the thing under test" — and falsifiability PASS — "removing the clause from the skill body breaks the test." The test exercises no code; only an edit to the authored prose falsifies it, so it carries no behavioral evidence, yet the four-property model rationalized it as conformance.

How to avoid: Step 3b — after identifying what a test reads, classify by whether the subject is executable behavior or authored prose/documentation, not by whether the path resolves to a repository file. A read of an authored prose or documentation body asserted for its content is prose-coupling → REJECT, however the path is resolved and whatever harness mediates the read.

**Failure 6: Accepted renamed test-local configuration**

Claude saw a validation warning for a SCREAMING_CASE test constant used as a property-test run count, renamed it to camelCase, and approved the audit because the validator stopped flagging it. The value was still runner configuration in the executed test file. The rename only evaded a heuristic.

How to avoid: Step 3a reads declarations before coupling and classifies ownership. Runner counts, seeds, replay policy, setup choices, boundary bags, expected outputs, fixture paths, and generated domains belong in harnesses, generators, source contracts, inert fixtures, or eval cases — never in the test file under a different name.

**Failure 7: Approved a thin test without auditing its harness**

Claude inspected a linked Python test that imported a harness, then reviewed only three repeated `file.txt` values in the harness and approved them as harness-owned synthetic vocabulary. The harness also declared SPX payload keys, command tokens, producer identities, status values, and expected projection fields. The verdict omitted the imported-artifact inventory and never classified most values.

How to avoid: Step 2b inventories and reads the complete evidence chain before judgment. Step 3a names the source of every protocol value and rejects harness-declared domain truth with `source-ownership`. Approval requires the inventory in verdict metadata.

**Failure 8: Rejected observation and resource bindings by syntax**

Claude rejected a temporary-directory fixture parameter and a local `observations` binding even though both only received values selected by their owning infrastructure. The proposed remediation moved those handles into the harness, obscuring assertion flow without changing any semantic owner.

How to avoid: Step 3a asks what each binding chooses. Accept parameters and locals that only receive resource handles, observations, source contracts, or generated inputs; reject only bindings that independently choose data, policy, expectations, configuration, or verdict rules.

**Failure 9: Used the defect location as the remediation owner**

Claude correctly found copied protocol fields in a harness and emitted `source-ownership`, then set `remediation_target` to `harness` because that file contained the defect. The verdict failed its structural contract: copied domain truth belongs to a source contract regardless of where the copy appears.

How to avoid: Keep location and ownership separate. Set `file` to the artifact containing the copy and set every `source-ownership` finding's `remediation_target` to `source-contract`.

**Failure 10: Omitted a language manifest from the evidence chain**

Claude inspected a Rust test, harness, generator, and production module, then omitted the supplied `Cargo.toml` from `metadata.evidence_chain` because it carried no finding. The manifest established package and test discovery, so the verdict's inventory was incomplete.

How to avoid: Inventory applicable discovery and module-resolution artifacts even when they produce no finding. This includes pytest and Vitest configuration, Cargo manifests, and Go module files when the evidence package uses them to establish the test boundary.

**Failure 11: Emitted a semantically correct but structurally incomplete finding**

Claude rejected a production-derived oracle with the correct assertion, property, rule, artifact, and evidence chain, then omitted `remediation_target` from the finding. The prose diagnosis named the need for an independent oracle, but prose cannot substitute for a required verdict field and the structured verdict was invalid.

How to avoid: Construct each finding atomically from the canonical nine-field schema before row rollup, derive `remediation_target` from the evidence model, and perform the Step 4 completeness check before emitting the verdict.

**Failure 12: Read an absent in-repository caller as proof of laundering**

Claude rejected a package's `__version__` as source-ownership laundering because no module in the checkout consumed it. The packaging manifest declares it as published API, a surface the audit never opened, so a real contract was reported as a test-only address.

How to avoid: Judge ownership by the contract outside the test tree, and read the checkout's declared surfaces — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting a symbol as laundered.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every in-scope assertion and required language concern has a gate determination, with no evidence partition left unevaluated.
- Every imported evidence artifact appears in verdict metadata with its role, import origin, and inspection status; approval contains only inspected entries.
- Every protocol and domain value resolves to its production or platform owner; generated variable data resolves to a generator, inert whole payloads to fixtures, setup policy to harnesses, and curated examples to eval cases.
- The overall APPROVED/REJECTED value agrees with every applicable gate row.
- Every REJECT finding carries the complete canonical schema and names a falsifiable evidentiary gap against the affected assertion and artifact.
- Every coverage determination identifies the assertion-relevant source path reached or omitted, and the same evidence package yields the same verdict.

</success_criteria>
