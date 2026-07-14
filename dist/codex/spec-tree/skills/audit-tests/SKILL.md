---
name: audit-tests
description: >-
  Test-evidence audit methodology preloaded by the test-evidence-auditor agent.
  Dispatch test-evidence-auditor to audit test evidence against spec assertions;
  the main conversation reaches this audit only through that agent.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<dispatch_gate>

This audit runs in the test-evidence-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the test-evidence-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on whether a spec node's tests provide behavior-coupled evidence its assertions are fulfilled — APPROVED, or REJECTED with each finding naming the assertion, the failed evidence property or cross-assertion architectural duplication, and the evidentiary gap.

</objective>

<essential_principles>

**OWNERSHIP SCREEN, THEN COUPLING.**

An executed test file that declares variables or constants has already broken the evidence boundary. Screen declarations first, then check imports. A test that imports nothing from the codebase will pass forever regardless of what any file contains. This is not a heuristic — it is a prerequisite.

**COMPLETE THE EVIDENCE CHAIN.**

Start from every linked test and recursively follow repository imports through test infrastructure before judging evidence. Inventory each linked test, harness, generator, fixture reference, and applicable discovery artifact with its path, role, importing artifact, and inspection status. An unresolved import, unread artifact, or unclassified role is `incomplete-evidence-chain` and rejects the audit. Approval requires a complete inventory in verdict metadata.

Four properties must hold, checked in strict order: coupling (the test exercises codebase behavior, not authored prose), falsifiability (a named mutation breaks it), alignment (it exercises the asserted behavior), and coverage (the test drives execution into the assertion-relevant path). A test missing any property has zero evidentiary value regardless of code quality.

**JUDGE COVERAGE BY READING.**

A dispatched agentic audit runs no deterministic verification — the caller brings deterministic verification to passing on the changeset before dispatch, and CI re-runs deterministic verification over the whole repository. Establish coverage by reading whether the test drives execution into the assertion-relevant code path; never run the project's coverage command, test command, or any other deterministic verification inside the audit.

**NO MECHANICAL SUBSTITUTES.**

Mocking patterns, skip patterns, type annotations — these are linting concerns (SemGrep, ESLint). The auditor evaluates evidence quality, not code quality signals. The declaration screen is a read step: identify declarations in the test file, then judge ownership from their evidence role.

The literal rule is applied by reading the test's literals against their sources, never by running a validation tool. No wrapper runs `spx validation literal` or any other deterministic check inside the audit — the caller and the project's configured deterministic workflow own that gate.

**TEST FILES OWN NO DATA OR CONFIGURATION.**

Before coupling, inspect every executed test file for declarations and bindings. Any variable or constant declaration in a test file is an evidence-boundary failure: it owns state in the assertion file, whether that state is test data, expected output, runner settings, property-test configuration, setup policy, reusable cases, fixture path, generator choice, harness handle, diagnostic, or a source-owned singleton shape. Framework-injected fixture parameters and property-generated parameters are test-file bindings too; move them behind harness entrypoints so the assertion file remains a wrapper. Local functions are rejected when they own setup, reusable cases, fixtures, generators, harness behavior, diagnostics, or source-owned vocabulary. Do not classify by naming style or declaration shape: `MAPPING_RUNS`, `mappingRuns`, `runs`, and `function mappingRuns()` are the same ownership problem when the declaration owns runner policy.

The remediation target is part of the finding: source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, or curated eval case data when generation is wasteful and not tractable. Runner settings and property seeds belong in harnesses. Variable input domains belong in generators. Test files keep assertion flow.

**BINARY VERDICT.**

APPROVED or REJECTED. No middle ground. If any property is missing for any assertion, REJECTED.

</essential_principles>

<constraints>

- NEVER modify the tests under audit or any other file — this audit produces a verdict, never a fix or a commit.
- NEVER run the project's coverage command, test command, linter, type-checker, or any other deterministic verification inside the audit — the caller passes deterministic verification on the changeset before dispatch and CI re-runs it over the whole repository; establish coverage by reading whether the test drives execution into the assertion-relevant path.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every REJECT finding.
- ALWAYS reject an incomplete evidence-chain inventory before approval; absence of an artifact is missing evidence, never permission to infer its contents.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the tests for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent, then invoke `/contextualize` on the spec node whose tests are being audited. This loads the spec's assertions, ancestor ADRs/PDRs, and the full hierarchy context.

Do not proceed without live `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers.

</step>

<step name="map_assertions">

**Step 2: Map assertions to test files**

Read the spec's Assertions section. Only assertions carrying `[test]` evidence enter this audit. Skip assertions tagged `[eval]`, `[audit]`, or legacy `[review]`; their evidence belongs to other verification workflows.

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

Read every resolved artifact before continuing. A referenced fixture is inventoried even when consumed only by path. Include every `conftest.py` or equivalent discovery file that applies to the linked test. The final `metadata.evidence_chain` MUST contain exactly one entry for every artifact used to resolve imports, ownership, or discovery, including an inspected discovery artifact that produces no finding.

If an import cannot be resolved from the caller's evidence package or repository, add a `gate-1-assertion` REJECT finding against the unresolved repository-relative path with rule `incomplete-evidence-chain` and `remediation_target: "test-infrastructure"`. Do not attribute the finding to the thin test file. Stop evidence-property judgment for that assertion because the chain is incomplete.

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

| Artifact role | Allowed ownership                                                                      | REJECT with `source-ownership`                                                                              |
| ------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Harness       | Setup, teardown, cleanup, resource policy, access to real behavior, replay diagnostics | Protocol keys, command tokens, status values, expected outputs, arbitrary request payloads, or domain truth |
| Generator     | Variable domains with meaningful variation and shrinking                               | Copied protocol vocabulary, constant-only domains, or hand-picked expected outputs                          |
| Fixture       | Inert whole payload consumed by path or bytes                                          | Isolated tokens, values, expected outputs, or executable exports                                            |
| Discovery     | Test collection and registration policy                                                | Fixture bodies, domain values, generated cases, or hidden setup policy                                      |

For every case input, expected value, protocol key, command token, status value, rule identifier, and payload member, name its source in the inventory. Source-owned values resolve to their production or platform owner. Generated values resolve to a variable generator. Whole-payload samples resolve to an inert fixture. A value with no valid owner produces a finding against the artifact that declares it with `property: "source-ownership"`, rule `source-ownership`, and `remediation_target: "source-contract"`; a harness location never establishes ownership by itself. The finding `file` names the artifact that copied the value, while `remediation_target` names the production contract that must own it — NEVER substitute the artifact role (`harness`, `generator`, or `fixture`) for `source-contract`.

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

Establish coverage by reading, never by running the project's coverage tooling. A dispatched agentic audit runs no deterministic verification — the caller brings deterministic verification to passing on the changeset before dispatch, and CI re-runs deterministic verification over the whole repository. Re-running the coverage command here re-pays a cost already paid.

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

Read the detected language or language partitions from the caller's audit request. When the caller omits them, derive partitions from the mapped linked-test extensions using the explicit supported mapping: `.py` to Python, `.ts` or `.tsx` to TypeScript, and `.rs` to Rust. Reject an unknown extension or an ambiguous partition with property `unsupported-language` and remediation target `language-partition` instead of guessing.

When the caller supplies a completed `language_composition` result, validate its `status` and `findings` fields and consume it without dispatching the same concern again. A `PASS` result with no `REJECT` finding satisfies composition; merge any non-blocking findings into matching rows. A `FAIL` result or malformed composition evidence appends a `gate-1-assertion` `REJECT` finding with property `language-composition` and returns REJECTED.

When completed composition evidence is absent and an `audit-<lang>-tests` skill exists for each language in scope, load and apply each skill through the runtime's supported skill mechanism. It returns a verdict in this same row schema (`gate-1-assertion`, `gate-2-architectural`) carrying language-specific check IDs — it runs no deterministic verification, so it emits no `gate-0-deterministic` row. **Merge its findings into the matching rows by `name`** — append, never replace — and emit one merged verdict. When a required `audit-<lang>-tests` skill is absent or unavailable, append a `FAIL` row with a `REJECT` finding naming the missing skill, property `language-composition`, and remediation target `skill-installation`; never approve incomplete coverage.

</step>

<step name="compose_architectural">

**Step 3g: Roll up composed architectural duplication**

Gate 2 is a composed-language concern. It applies when at least one language-specific verdict returns a `gate-2-architectural` row. Merge every applicable Gate 2 finding by row name, preserving each finding's language-specific rule and extraction target.

- Return Gate 2 `FAIL` when any composed Gate 2 row contains a `REJECT` finding.
- Return Gate 2 `PASS` when every applicable composed Gate 2 row passes.
- Omit Gate 2 only when every composed language verdict omits it as non-applicable.
- Treat a malformed or unevaluated applicable Gate 2 row as failed `language-composition` evidence; never infer architectural approval.

</step>

<step name="verdict">

**Step 4: Issue verdict**

Scan all findings across all assertions, including any folded in from the composed language audit. If any assertion has a property failure: **REJECTED.**

</step>

</audit_workflow>

<verdict_format>

Emit a structured verdict consumed by the composing verification workflow. The skill's entire output is the verdict payload returned to the caller. Skills never hand-format markdown verdicts.

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
          "property": "<testability | evidence-chain-completeness | declarations | source-ownership | coupling | falsifiability | alignment | coverage | language-composition | unsupported-language>",
          "rule": "<assertion-id-or-property-name>",
          "severity": "REJECT",
          "message": "<one-line evidentiary gap>",
          "remediation_target": "<source-contract | harness | generator | fixture | eval-case | test-file | source-file | test-infrastructure | skill-installation | language-partition>"
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
          "remediation_target": "<source-contract | harness | generator | fixture | eval-case | test-file | source-file | test-infrastructure | skill-installation | language-partition>"
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

A non-applicable Gate 2 row is omitted. A required gate that cannot be evaluated uses `status: "FAIL"` with a `REJECT` finding naming the missing evidence. A `source-ownership` finding uses `property: "source-ownership"`, `rule: "source-ownership"`, and `remediation_target: "source-contract"`; other findings select the failed property, rule, and owner that must change from the enumerated values. No skill emits a `gate-0-deterministic` row, because the audit runs no deterministic verification. Language-specific test audit skills inherit this shape — they add language-specific check IDs and extraction targets to the findings but do not change the row names or schema.

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Claude approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. The tests pass if the entire codebase is deleted. Claude was distracted by clean types, good structure, and comprehensive scenarios, and never checked the imports.

How to avoid: Step 3b checks imports before the other evidence properties. Zero codebase imports = instant REJECT.

**Failure 2: Accepted mocking as legitimate coupling**

Claude saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. The real module never ran.

How to avoid: Step 3c checks for mocking after confirming coupling. Import + mock = coupling severed.

**Failure 3: Re-ran the project's coverage command inside the audit**

Claude ran the project's coverage command three times (baseline, with-test, isolated) to measure a delta — re-paying deterministic verification the caller already passed on the changeset before dispatch and CI re-runs over the whole repository. The dispatched audit runs no deterministic verification.

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
