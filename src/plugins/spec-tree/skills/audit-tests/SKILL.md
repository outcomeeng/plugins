---
name: audit-tests
description: >-
  Test-evidence audit methodology — judges whether a spec node's tests provide
  behavior-coupled evidence its assertions are fulfilled, covering predicate
  ownership, source ownership, coupling, falsifiability, and full-chain
  coverage, and records the judgment as one root unit, one child unit per
  assertion, and one grandchild unit per linked test file and language concern
  in an SPX verification run.
argument-hint: "<JSON object with target and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), {{! tool('use_skill') !}}
---

<objective>

A sealed `spx verification run` judging whether a spec node's tests, or the tests a committed changeset carries, provide behavior-coupled evidence their assertions are fulfilled, with one root unit, one child unit per assertion, and one grandchild unit per linked test file and language concern, every finding on touched text recorded on its unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

- NEVER modify the tests under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `/contextualize` or `/sync-base`: both can move the checkout, and this audit leaves the checkout unmoved. The `load_context` step loads the node spec's context read-only.
- NEVER run the project's coverage command, test command, linter, type-checker, or any other deterministic verification inside the audit — deterministic verification on the changeset is a precondition, and a re-run repeats work already paid for. Establish coverage by reading whether the test drives execution into the assertion-relevant path.
- ALWAYS name the assertion, the failed rule, and the evidentiary gap in every finding — a finding that omits one gives the Fixer no falsifiable gap to repair.
- ALWAYS reject an incomplete evidence-chain inventory before approval; absence of an artifact is missing evidence, never permission to infer its contents.
- ALWAYS draw each finding's `rule` from `<rule_catalog>` in `${CLAUDE_SKILL_DIR}/references/test-evidence-rules.md` and carry the severity its row declares — a rule outside the catalog is a gap in the standard, never a finding.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the tests for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` line.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` in `${CLAUDE_SKILL_DIR}/references/run-recording.md` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`.

</constraints>

<essential_principles>

**PREDICATE AND OWNERSHIP SCREEN, THEN COUPLING.**

The linked test function or callback owns every predicate and assertion API call. Screen the full chain for verdict logic and classify each test-file binding by semantic choice before checking imports. A test that imports nothing from the codebase will pass forever regardless of what any file contains. This is a prerequisite.

**COMPLETE THE EVIDENCE CHAIN.**

Start from every linked test and recursively follow repository imports through test infrastructure before judging evidence. Inventory each linked test, harness, generator, fixture reference, and applicable discovery artifact with its path, role, importing artifact, and inspection status. An unresolved import, unread artifact, or unclassified role is `incomplete-evidence-chain` and rejects the audit. Approval requires every inventoried artifact inspected.

Four properties must hold, checked in strict order: coupling (the test exercises codebase behavior, not authored prose), falsifiability (a named mutation breaks it), alignment (it exercises the asserted behavior), and coverage (the test drives execution into the assertion-relevant path). A test missing any property has zero evidentiary value regardless of code quality.

**NO MECHANICAL SUBSTITUTES.**

Mocking patterns, skip patterns, type annotations — these are linting concerns (SemGrep, ESLint). The auditor evaluates evidence quality, not code quality signals. The declaration screen is a read step: identify declarations in the test file, then judge ownership from their evidence role.

Apply the literal rule by reading the test's literals against their sources.

**TEST FILES OWN PREDICATES AND NO INDEPENDENT DATA OR CONFIGURATION.**

Before coupling, inspect every executed test and imported infrastructure artifact. Every behavioral predicate and assertion API call remains lexically in the linked test function or callback. Reject a harness, generator, fixture, controlled implementation, or recording collaborator that accepts an expected outcome, returns a verdict, calls an assertion API, or exposes matcher-shaped verdict methods.

Classify bindings by what they choose. Observation aliases, actual-result bindings, imported source-contract aliases, generated parameters, callback inputs, and resource handles are valid when they introduce no data or policy. A framework-provided temporary-directory handle, a local binding that receives a harness observation, and an assertion-local projection over observations are therefore valid. NEVER reject a binding merely because it is a parameter, assignment, alias, or local expression; moving those values into a harness would hide assertion flow and can move the predicate across the seam. Reject bindings that choose cases, expectations, runner settings, property configuration, setup policy, reusable data, generator domains, fixture payloads, or verdict rules. The finding names its remediation owner: source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, independent oracle, or curated eval case data when generation is wasteful and not tractable.

</essential_principles>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with the fields `target` and `runDriver`, and an optional `languagePartitions` array of language names. `target` is the product-relative path of the spec node whose tests are audited, spaces preserved, or, for an evidence-scope target, a committed changeset selector: `HEAD`, a branch, or a three-dot range. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` in `${CLAUDE_SKILL_DIR}/references/run-recording.md` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing or empty `target`, a missing, extra, or malformed `runDriver` field, or an unknown field returns `BLOCKED` with run token `not-started` naming the exact field before any command runs. Preserve any supplied `languagePartitions`; never infer a target from adjacent conversation.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that the finding payload of `${CLAUDE_SKILL_DIR}/references/run-recording.md` records in `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<step name="resolve_target">

**Step 1: Resolve the target**

A node target is a path to a spec node file. Read it; an absent or unreadable target returns `BLOCKED` with the exact failure. The run is file-scoped on that path.

An evidence-scope target is a committed changeset. Use skill `spec-tree:scope-changeset`. Invoke it with the selector, and retain the `<COMMITTED_CHANGESET_SCOPE>` marker's `base`, `head`, and `changed_paths`. A stale-base or blocked result returns `BLOCKED` with run token `not-started` and the exact diagnostic; make no replacement scope, synchronization, or retry. The run is changeset-scoped on `<base>..<head>`. Resolve each changed path to the spec node that governs it: a path under `spx/<node>/` belongs to that node, and any other path to the node whose linked test imports it, several nodes resolving to the lowest common ancestor of each pair; audit every resolved node's `[test]` assertions. A deleted test path that no current `[test]` assertion links is a retired path. A path no node reaches is outside the audit.

Resolve the touched text of each inventoried artifact as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, so the later steps can classify each finding.

</step>

<step name="load_context">

**Step 2: Load context read-only**

When the live `<SPEC_TREE_FOUNDATION>` marker is absent: Use skill `spec-tree:understand`.

Use skill `spec-tree:test-evidence-standards`. Apply its complete predicate-seam, semantic-binding, case-provenance, oracle-independence, assertion-type-litmus, mutation litmus, and assertion-design-record rules. A missing standard blocks the audit because `/test` and `/audit-tests` must judge from the same standards.

For each spec node under audit, load its context with `Read`, `Glob`, and `Grep` alone, in this order:

1. The product spec.
2. Each spec and every decision record in each directory on the path from `spx/` to the directory containing the node spec, root first, the node spec excluded.
3. Every decision that a loaded spec or decision cites by full `spx/` path, each read once.

A decision that a loaded record cites and that cannot be read is a `context-unavailable` finding on the unit that names it, else on the root. Do not proceed without the live `<SPEC_TREE_FOUNDATION>` marker.

</step>

<step name="open_run">

**Step 3: Open the run**

Start the run before judging anything. For a node target:

```bash
spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
```

A file-scoped run takes the audited path as its input, passed by path, so the retained input equals the audited file and no start payload is built.

For an evidence-scope target, write the scope as one JSON object with `base`, `head`, and `changed_paths` copied verbatim from the marker, with the file-write tool to a start-input file in the scratch directory, then:

```bash
spx verification run start --verification-type audit --scope-type changeset --scope <base>..<head> --input '<start-input-file>'
```

The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="map_assertions">

**Step 4: Map assertions to test files**

Read each spec's Assertions section. Only assertions carrying `[test]` evidence enter this audit. Skip assertions tagged `[eval]`, `[probe]`, or `[audit]`; their evidence belongs to other verification workflows.

For each included assertion, extract:

| Field          | Extract                                                  |
| -------------- | -------------------------------------------------------- |
| Assertion text | The claim being tested                                   |
| Assertion type | Scenario / Mapping / Conformance / Property / Compliance |
| Test link      | Path from `([test](path))`                               |
| Link status    | File exists or missing                                   |

Number the included assertions by their order in the spec; the ordinal and the spec path identify the assertion's unit. **Missing test file = `missing-test-file` finding on the assertion unit.** Record it and continue to the next assertion.

</step>

<step name="inventory_evidence_chain">

**Step 5: Inventory the complete evidence chain**

Starting from the test links mapped in Step 4, follow each repository import recursively. Record one inventory entry per artifact:

| Field               | Meaning                                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `path`              | Repository-relative artifact path                                                                                            |
| `role`              | `test`, `harness`, `generator`, `fixture`, `discovery`, or `production`                                                      |
| `imported_from`     | Path that introduced the artifact, or null for root artifacts such as the linked test and applicable discovery configuration |
| `inspection_status` | `inspected` or `unresolved`                                                                                                  |

Read every resolved artifact before continuing. A referenced fixture is inventoried even when consumed only by path. Include every applicable discovery or module-resolution artifact the repository supplies: examples include `conftest.py` or pytest configuration, Vitest configuration, `Cargo.toml`, and `go.mod`. A discovery artifact stays in the inventory when it produces no finding. The inventory MUST contain exactly one entry for every artifact used to resolve imports, ownership, collection, or discovery.

If an import cannot be resolved from the repository, record an `incomplete-evidence-chain` finding on the file unit of the linked test whose chain reaches it, naming the unresolved repository-relative path in `location` and attributing nothing to the thin test file. Continue every check the available artifacts support; report a property whose required evidence is unavailable as a failed rule on missing evidence rather than inferring a judgment from unread content.

</step>

<step name="check_testability">

**Step 6: Testability precondition**

For each assertion, read the governed production source and identify the observable boundary, seam, or injection point through which a test can exercise the assertion-relevant behavior. Judge the source shape before judging the linked test.

If the source exposes no way to observe or drive that behavior, record an `untestable-source` finding on the assertion unit, naming the source file in `location`, the missing seam, and its evidentiary consequence. Continue ownership and every other inspectable check; preserve the testability failure regardless of those results.

</step>

<step name="check_ownership">

**Step 7: Ownership across the evidence chain**

Read each linked test file before coupling. Identify every variable, constant, local function, fixture parameter, property-generated parameter, predicate, and assertion API call and classify the proper owner. Use language syntax while reading to enumerate declarations, then classify ownership by reading the declaration and its evidence role. Do not outsource the verdict to a grep pattern or validation command.

Before applying the data rows, resolve anything that looks like case data through the per-assertion-type litmus from `spec-tree:test-evidence-standards`. A case that litmus assigns to the test itself is correctly owned there and is never a finding; demanding it move into a production module is the source laundering the standard forbids.

| Binding or predicate role                                                                                                                       | Verdict                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| Actual result, observation, resource handle, generated parameter, callback input, or imported-contract alias that introduces no choice          | ACCEPT — assertion flow       |
| Behavioral predicate or assertion API call in the linked test function or callback                                                              | ACCEPT — test-owned predicate |
| Predicate, matcher, expected-value parameter, assertion call, or verdict helper in infrastructure                                               | `assertion-seam`              |
| Runner settings, seed policy, retries, setup policy, or lifecycle policy                                                                        | `test-owned-configuration`    |
| Test-invented case data, boundary bags, expected outputs, fixture contents, or generator domains the assertion type does not assign to the test | `test-owned-data`             |
| Source-owned singleton shape or vocabulary copied into the test                                                                                 | `source-ownership`            |
| Expected result derived from the production table, algorithm, parser, or branch logic that produces the actual result                           | `oracle-independence`         |

Do not treat casing or syntax as evidence. Renaming `MAPPING_RUNS` to `mappingRuns`, changing an assignment to destructuring, or receiving a value through a parameter does not change what the binding chooses.

For property-based tests, verify seed and replay behavior by reading the imported harness or property wrapper. A property test with no harness-owned seed policy, or whose failure output omits the seed or replay path, is `test-owned-configuration` or `missing-seed-reporting`.

Apply category-specific ownership checks to every imported test-infrastructure artifact:

| Artifact role | Allowed ownership                                                                      | `source-ownership` finding when it holds                                                                    |
| ------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Harness       | Setup, teardown, cleanup, resource policy, access to real behavior, replay diagnostics | Protocol keys, command tokens, status values, expected outputs, arbitrary request payloads, or domain truth |
| Generator     | Variable domains with meaningful variation and shrinking                               | Copied protocol vocabulary, constant-only domains, or hand-picked expected outputs                          |
| Fixture       | Inert whole payload consumed by path or bytes                                          | Isolated tokens, values, expected outputs, or executable exports                                            |
| Discovery     | Test collection and registration policy                                                | Fixture bodies, domain values, generated cases, or hidden setup policy                                      |

Judge a source symbol the test cites by declared-contract ownership: does production consume it, emit it, publish it as API, register it, or serialize it against a declared schema? An absent in-repository caller opens that question rather than settling it, so inspect the declared surfaces the checkout carries — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting the symbol as laundered. Name the surfaces inspected in the finding. Report the finding when none of them requires the symbol: a consumer outside the checkout is not evidence this audit can gather, so its bare possibility never withholds a finding the declared surfaces support.

For every case input, expected value, protocol key, command token, status value, rule identifier, and payload member, name its source and independent oracle. Apply the per-assertion-type litmus questions from `spec-tree:test-evidence-standards`. A value with no valid owner is a `source-ownership` finding; an expectation derived from the production path under test is an `oracle-independence` finding. The finding's `location` names the artifact that copied or coupled the value, and its remediation owner is the semantic owner the catalog declares, never the artifact holding the defect. The assertion-design record of `spec-tree:test-evidence-standards` is judged as one unit through the steps that own its fields: the assertion through `map_assertions`, the production subject through `check_testability`, case provenance through `source-ownership`, oracle owner through `oracle-independence`, and the rejected mutation with its failure observation through `check_falsifiability`.

</step>

<step name="check_coupling">

**Step 8: Coupling**

Read the test file's import statements. Classify each import:

| Import source                                  | Classification             |
| ---------------------------------------------- | -------------------------- |
| Test framework (vitest, pytest, jest)          | Framework — does not count |
| Node modules / pip packages                    | Library — does not count   |
| Codebase path (relative import, product alias) | Codebase — counts          |

**Zero codebase imports → `no-coupling` (tautology).**

If codebase imports exist, classify using this coupling taxonomy:

| Category           | Definition                                                                                        | Verdict                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Direct             | Test imports the module under test                                                                | Proceed                                                   |
| Indirect           | Test imports a harness wrapping the module                                                        | Proceed — verify harness has real coupling                |
| Transitive         | Test imports a consumer of the module                                                             | Proceed — verify test level matches                       |
| Laundered indirect | Imports a test-infrastructure module that exists only to expose hardcoded values back to the test | `laundered-coupling`                                      |
| False              | Imports module but never calls assertion-relevant functions                                       | `false-coupling`                                          |
| Partial            | Calls functions but on wrong inputs or wrong code paths                                           | `partial-coupling`                                        |
| None               | Test imports only its test framework                                                              | `no-coupling`                                             |
| Severed            | Imports the module under test and replaces its behavior with a mock, fake, stub, or monkeypatch   | `coupling-severed`                                        |
| Prose-coupling     | Reads an authored prose/doc body and asserts its content                                          | `prose-coupling` — couples to authored text, not behavior |

Coupling means exercising executable **behavior**, never reading a document's content. A test whose "subject" is an authored prose or documentation artifact — a skill body, a spec body, a prompt, any text the product authors and maintains — that the test reads and asserts substrings of is NOT behavioral coupling, even when that artifact is the thing the assertion names. The text passes whatever it literally contains; no code runs. This holds full-chain: a harness that exposes the authored path as a constant, or a reader function that performs the read inside test infrastructure, does not convert a prose assertion into behavioral coupling — follow the read to its source and classify by what is ultimately exercised.

A test whose evidence is reading an authored prose or documentation body and asserting on its content is a `prose-coupling` finding. The claim verifies that prose was authored, not that code behaves; its verification type belongs in `[eval]` (a graded judgment over a producer's structured verdict) or `[audit]` (a semantic constraint), and the finding's message names the retag. Reading an authored *source-code* file for a structural lint that exercises a rule is not prose-coupling; the discriminator is whether the subject is authored prose/documentation or executable behavior.

</step>

<step name="check_falsifiability">

**Step 9: Falsifiability**

For each codebase import, name a concrete mutation to the imported module that would cause this test to fail. Write it down:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed result
Impact: "parses nested sections" fails — expect(result.section.key) throws
```

**Cannot name a mutation for any import → `unfalsifiable`.**

Check for mocking. If the test imports a module then replaces it with a mock, the coupling is severed:

```typescript
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn() }));
// Real database.query never runs — coupling severed
```

**Import + mock → `coupling-severed`.**

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

<step name="check_alignment">

**Step 10: Alignment**

Read the spec assertion text. Read the test's expect/assert statements. Answer:

1. Does the test exercise the exact behavior the assertion describes?
2. Could the spec assertion be unfulfilled while the test passes?

If yes to question 2: `misaligned`.

Judge the test against the executable source contract without making the test duplicate or parse the authored spec text. When production exports a value or typed contract, uses it in the behavior under test, and the test imports that same contract while exercising the behavior, a change to the source contract is an intentional behavior change rather than a mutation the test must reject. Name a mutation to the consuming behavior that would break the test. NEVER require a test or test-infrastructure artifact to parse spec or decision Markdown or copy a literal from that prose as an independent oracle; authored prose is verified through spec audit and review, and duplicated literals violate source ownership.

Check assertion-type-to-strategy alignment; a test whose strategy fails its row is a `strategy-mismatch` finding:

| Assertion type | Required test strategy                            | Finding when              |
| -------------- | ------------------------------------------------- | ------------------------- |
| Scenario       | Example-based with Given/When/Then inputs         | Missing concrete scenario |
| Mapping        | Parameterized over input set                      | Only one example tested   |
| Property       | Property-based framework (fast-check, Hypothesis) | Only example-based        |
| Conformance    | Tool or schema validation                         | Manual check              |
| Compliance     | Rule exercised against violating cases            | Only conforming cases     |

</step>

<step name="check_coverage">

**Step 11: Coverage**

Trace, by reading, whether the test drives execution into the assertion-relevant code path:

1. Read the production code the assertion governs and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that production code.
3. Judge whether the test's execution reaches the assertion-relevant path — the lines whose behavior the assertion claims.

**Interpret the trace:**

- **Reaches the assertion-relevant path**: the test exercises the behavior the assertion claims. ✓
- **Imports the module but never drives execution into the assertion-relevant path**: `no-coverage`. Name the specific assertion-relevant path the test fails to reach, traced from the code.
- **The assertion-relevant path is trivially total** (the test obviously exercises every line the assertion claims): record no finding. The test's evidentiary value comes from the other three properties.

Coverage here is execution breadth (does the test reach the assertion-relevant lines), not assertion strength. A property-based test that exercises the same lines over a broader input domain adds behavior-coupled evidence that reading captures and a line count would not.

The judgment is traced from the code and named in the finding — never a measured percentage, and never an unbacked "probably covers."

</step>

<step name="compose_language">

**Step 12: Compose language-specific test-evidence concerns**

The evidence properties above are language-neutral. Language-specific test-evidence concerns are owned by the language test audit skill, not by this one.

Read detected language or language partitions from the request. When absent, derive partitions from the linked-test filenames and the installed language plugins. Take the installed `audit-<lang>-tests` skills from the skill listing already in context; no directory scan is needed. For each, Use skill `{lang}:{lang}-test-standards` and read its filename instantiation of `<subject>.<evidence>.<level>[.<runner>]` — the concrete pattern the standard states, such as `test_<subject>.<evidence>.<level>[.<runner>].py`. The text after the last closing bracket is the declared suffix: a compound suffix such as `.test.ts` as readily as a bare `.py` or `_test.go`. Map every linked test whose filename ends in an installed plugin's declared suffix to that language. A suffix no installed plugin declares, or an ambiguous partition, is an `unsupported-language` finding on the assertion unit instead of a guess; never map an extension from a list this skill carries.

For each language, Use skill `{lang}:audit-{lang}-tests`, passing the audit target and the linked test files of that language. Validate each result against `<language_result_contract>` in `${CLAUDE_SKILL_DIR}/references/test-evidence-rules.md`: its shape, required fields, applicable rows, target, and agreement between findings, row statuses, and overall result. A malformed, mismatched, or inconsistent result is a `language-result-invalid` finding on that language's file unit, and it contributes no partial coverage; continue the remaining languages. When a required `audit-<lang>-tests` skill is absent or unavailable, record `language-skill-unavailable` on the assertion unit naming the missing skill; never approve incomplete coverage.

Take each composed finding's catalog rule from the contract's mapping, keep its message and evidence, and record it on the file unit of the language concern. A composed rejection remains a rejection through `<classification>` of `${CLAUDE_SKILL_DIR}/references/touched-text.md`.

A language audit returns a retirement when every subject it was given is a retired path with no current `[test]` assertion and no current evidence-chain owner. Treat it as neither a pass nor a failure of that language's concerns: record each subject as a `not-applicable` unit, compose the remaining languages normally, and decide the terminal status from the units that carry judgment. When every language in scope returns a retirement and no language-neutral finding was raised, the run still finishes `approved` and the `not-applicable` lines state that no evidence was judged.

</step>

<step name="compose_architectural">

**Step 13: Roll up composed architectural duplication**

Architectural duplication is a composed-language concern. It applies when at least one language-specific result carries a `gate-2-architectural` row. Record every applicable composed finding as `architectural-duplication` on its file unit, or on the root for a pattern that spans assertions, preserving each finding's language-specific detail and extraction target in its evidence.

- Omit the concern only when every composed language result omits the row — as non-applicable, or because that language's Gate 1 rejected the evidence, so its Gate 2 never ran.
- Treat a malformed or unevaluated applicable row as `language-result-invalid`; never infer architectural approval.

</step>

<step name="classify">

**Step 14: Classify and record**

Classify every finding, native or composed, per `${CLAUDE_SKILL_DIR}/references/touched-text.md`: a finding on touched text is recorded on its unit with the severity its catalog row declares; every other finding is standing, returned as a `filed` line, and recorded nowhere in the run.

Once judgment is complete, add the root unit first, because a run admits one root and every child names it, then one child unit per assertion, then each grandchild unit per linked test file and language concern, then each retired path, then each finding on touched text on the unit of the concern it names; a finding that names no child unit sits on the root. A unit holding judgment is `audited`, whether it holds or carries findings. Read `${CLAUDE_SKILL_DIR}/references/run-recording.md` before the first `scope add`; its `<persistence_contract>` gives the unit identities and payloads and its `<payload_files>` gives how each payload reaches a command.

</step>

<step name="finish">

**Step 15: Finish and render**

Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist. Run the finish and render commands with the scope type and scope Step 3 started:

```bash
spx verification run finish --verification-type audit --scope-type <file-or-changeset> --scope <scope> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type <file-or-changeset> --scope <scope> --run <token>
```

</step>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return each standing finding as a `filed` line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`, then each retired path and each concern judged `NOT_APPLICABLE` as a `not-applicable` line:

```text
not-applicable: <unit-key> | subjects: <retired-paths> | explanation: <why no current evidence owns them>
```

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
```

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Claude approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. The tests pass if the entire codebase is deleted. Claude was distracted by clean types, good structure, and comprehensive scenarios, and never checked the imports.

How to avoid: `check_coupling` checks imports before the other evidence properties. Zero codebase imports is `no-coupling`.

**Failure 2: Accepted mocking as legitimate coupling**

Claude saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. The real module never ran.

How to avoid: `check_falsifiability` checks for mocking after confirming coupling. Import + mock is `coupling-severed`.

**Failure 3: Re-ran the project's coverage command inside the audit**

Claude ran the project's coverage command three times (baseline, with-test, isolated) to measure a delta. Those runs added no audit evidence and repeated work excluded by `<constraints>`.

How to avoid: `check_coverage` traces coverage by reading whether the test drives execution into the assertion-relevant path. Name the path from the code; never run the coverage or test command, and never substitute an unbacked "probably covers" for the trace.

**Failure 4: Distracted by code quality signals**

Claude spent the entire audit checking for `as any`, verifying return types, and searching for skip patterns. The test had perfect TypeScript quality and zero evidentiary value. Quality signals are linting concerns, not audit concerns.

How to avoid: Follow the complete ordered audit sequence: inventory the evidence chain, check source testability, screen test-owned declarations, then judge coupling, falsifiability, alignment, and coverage.

**Failure 5: Approved a prose-body substring test as direct coupling**

Claude audited a test that read an authored skill body and asserted that policy substrings were present, and rated coupling PASS — "direct coupling to the artifact; the text is the thing under test" — and falsifiability PASS — "removing the clause from the skill body breaks the test." The test exercises no code; only an edit to the authored prose falsifies it, so it carries no behavioral evidence, yet the four-property model rationalized it as conformance.

How to avoid: `check_coupling` — after identifying what a test reads, classify by whether the subject is executable behavior or authored prose/documentation, not by whether the path resolves to a repository file. A read of an authored prose or documentation body asserted for its content is `prose-coupling`, however the path is resolved and whatever harness mediates the read.

**Failure 6: Accepted renamed test-local configuration**

Claude saw a validation warning for a SCREAMING_CASE test constant used as a property-test run count, renamed it to camelCase, and approved the audit because the validator stopped flagging it. The value was still runner configuration in the executed test file. The rename only evaded a heuristic.

How to avoid: `check_ownership` reads declarations before coupling and classifies ownership. Runner counts, seeds, replay policy, setup choices, boundary bags, expected outputs, fixture paths, and generated domains belong in harnesses, generators, source contracts, inert fixtures, or eval cases — never in the test file under a different name.

**Failure 7: Approved a thin test without auditing its harness**

Claude inspected a linked Python test that imported a harness, then reviewed only three repeated `file.txt` values in the harness and approved them as harness-owned synthetic vocabulary. The harness also declared SPX payload keys, command tokens, producer identities, status values, and expected projection fields. The audit never inventoried the imported artifacts and never classified most values.

How to avoid: `inventory_evidence_chain` inventories and reads the complete evidence chain before judgment. `check_ownership` names the source of every protocol value and records harness-declared domain truth as `source-ownership`. Approval requires every inventoried artifact inspected.

**Failure 8: Rejected observation and resource bindings by syntax**

Claude rejected a temporary-directory fixture parameter and a local `observations` binding even though both only received values selected by their owning infrastructure. The proposed remediation moved those handles into the harness, obscuring assertion flow without changing any semantic owner.

How to avoid: `check_ownership` asks what each binding chooses. Accept parameters and locals that only receive resource handles, observations, source contracts, or generated inputs; reject only bindings that independently choose data, policy, expectations, configuration, or verdict rules.

**Failure 9: Used the defect location as the remediation owner**

Claude correctly found copied protocol fields in a harness and recorded `source-ownership`, then named the harness as the remediation owner because that file contained the defect. Copied domain truth belongs to a source contract regardless of where the copy appears.

How to avoid: Keep location and ownership separate. Put the artifact containing the copy in `location` and name the owner the catalog row declares; every `source-ownership` finding names `source-contract`.

**Failure 10: Omitted a language manifest from the evidence chain**

Claude inspected a Rust test, harness, generator, and production module, then omitted the supplied `Cargo.toml` from the inventory because it carried no finding. The manifest established package and test discovery, so the inventory was incomplete.

How to avoid: Inventory applicable discovery and module-resolution artifacts even when they produce no finding. This includes pytest and Vitest configuration, Cargo manifests, and Go module files when the repository uses them to establish the test boundary.

**Failure 11: Read an absent in-repository caller as proof of laundering**

Claude rejected a package's `__version__` as source-ownership laundering because no module in the checkout consumed it. The packaging manifest declares it as published API, a surface the audit never opened, so a real contract was reported as a test-only address.

How to avoid: Judge ownership by the contract outside the test tree, and read the checkout's declared surfaces — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting a symbol as laundered.

**Failure 12: Loaded context through the synchronizing skills**

Claude invoked `/contextualize` to load the target node's context, and its `/sync-base` step resolved two conflicts and advanced the audited branch to a different head while a concurrent implementation audit ran, so the sealed head of that audit was superseded.

How to avoid: Load context with the read-only steps of `load_context` and never invoke either skill.

</failure_modes>

<success_criteria>

- Every in-scope assertion and every linked test file has an audited unit for each required concern, with no evidence partition left unevaluated.
- Every artifact reached by import from a linked test was inspected before approval.
- Every protocol and domain value resolves to its production or platform owner; generated variable data resolves to a generator, inert whole payloads to fixtures, setup policy to harnesses, and curated examples to eval cases.
- Every recorded finding lies on touched text and sits on an accepted unit, names its assertion, artifact, and falsifiable evidentiary gap, and cites one catalog identifier.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The terminal status is `rejected` exactly when a finding on touched text is recorded, so no standing finding and no unevaluated unit decides it.
- The checkout the audit judged is the checkout it started on and left, so the verdict describes one head.
- Every coverage determination identifies the assertion-relevant source path reached or omitted, and the same evidence package yields the same units, finding keys, and terminal status.

</success_criteria>
