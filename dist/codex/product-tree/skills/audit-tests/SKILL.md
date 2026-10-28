---
name: audit-tests
description: >-
  Test-evidence audit methodology — judges whether a spec node's tests provide
  behavior-coupled evidence its assertions are fulfilled, covering predicate
  ownership, source ownership, coupling, falsifiability, and full-chain
  coverage, and records the judgment as a root unit with one child per
  assertion and one grandchild per linked test file and language concern in an
  SPX file-scoped verification run, or for a committed changeset in an SPX
  changeset-scoped run.
argument-hint: "<JSON object with path or changeset, and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(python3 "${SKILL_DIR}/scripts/resolve_scope.py":*), Bash(git rev-parse:*), Bash(git merge-base:*), Bash(git diff:*)
---

<objective>

A sealed `spx verification run` on one spec node's file, or on a committed changeset's governing spec nodes, against the test-evidence model, whose `terminalStatus` is `approved` or `rejected`, with each finding on touched text recorded on the unit of the assertion and test file it concerns and each inspection that cannot run recorded `incomplete` with its cause, returned as the run token, the run file, and the rendered projection followed by each standing finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

- NEVER modify the tests under audit or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `product-tree:contextualize` or `product-tree:sync-base`, and never fetch, rebase, or otherwise move the checkout — the audit reads the head as it stands, so it changes no checkout state.
- NEVER run the project's coverage command, test command, linter, type-checker, or any other deterministic verification inside the audit — deterministic verification on the changeset is a precondition, and the audit establishes coverage by reading whether the test drives execution into the assertion-relevant path.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every finding — the author repairs from the finding alone, and a finding missing any of the three leaves the repair unbounded.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the tests for it.
- NEVER name a finding rule identifier outside `${SKILL_DIR}/references/rule-catalog.md` and the catalogs of the composed language skills.
- NEVER reject, or record on a unit, a finding that lies outside touched text; classify every finding as `${SKILL_DIR}/references/touched-text.md` states, return each standing finding as `filed`, and never raise its severity or let it reject unless the run names a changed basis.
- ALWAYS reject an incomplete evidence-chain inventory before approval — an absent artifact is missing evidence, and inferring its contents would approve tests the audit never read.
- NEVER substitute a code-quality signal for an evidence judgment — mocking patterns, skip patterns, and type annotations are linting concerns for other tools; identify declarations by reading the test file and judge ownership from the evidence role of each declaration.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` of `${SKILL_DIR}/references/run-recording.md` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER delegate the audit to another session, or finish a run whose inspection is incomplete because of elapsed time, context pressure, or unfinished reading; an unavailable required inspection leaves its unit `incomplete` with the cause recorded, never an unevaluated unit.
- NEVER write the run journal or its context anywhere but the locations `spx verification run` resolves. When the native permission policy refuses a run-recording write — a payload file, a run-recording command, or the journal — stop at that write, retry it no more, write to no other location, and return `BLOCKED` with `diagnostic: configuration error` naming the refused path; the host grants the paths, and this skill never widens its own access.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`, except the one rerun `<payload_files>` of `${SKILL_DIR}/references/run-recording.md` allows for a payload file named absent.

</constraints>

<audit_workflow>

Judge in strict order: the complete evidence-chain inventory, source testability, ownership of every declaration, then the four properties coupling, falsifiability, alignment, and coverage. A test missing any of those four properties has zero evidentiary value regardless of code quality.

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields: `runDriver` and exactly one target field. The target field `path` is the product-relative path of the spec file of the node whose tests are audited, and the run is file-scoped on that path. The target field `changeset` is a selector, `HEAD`, a branch, or an explicit three-dot range, for the committed changeset whose test evidence is audited, and the run is changeset-scoped. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, both target fields, or a `path` that names no spec file returns `BLOCKED` naming the exact field or path before any command runs. Never infer a target from adjacent conversation.

Use skill `product-tree:product-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

<changeset_target>

For a `changeset` target, resolve the selector through this skill's entrypoint over the `scope-changeset` provider, passed as one literal argument:

```bash
python3 "${SKILL_DIR}/scripts/resolve_scope.py" '<selector>'
```

Take `base`, `head`, and `changed_paths` verbatim from the JSON it emits. A nonzero exit, including the `stale-base` refusal, or a malformed result returns `BLOCKED` with that diagnostic before any run starts; never fabricate or substitute a base, endpoint identity, or path. Run `git rev-parse HEAD` and return `BLOCKED` when the resolved `head` differs from its output, because the audit reads the checkout as it stands and a different head would be judged from the wrong tree.

The run identity is `<base>..<head>` from the two full endpoint identities. The audited specs are the spec files of the nodes governing the changed paths: a path under a node's directory belongs to that node, and any other path belongs to the node whose linked test, or whose linked test's evidence chain, reaches it. A node whose spec carries no `[test]` assertion contributes its `not-applicable` child; a changed path that no node governs is outside this audit and recorded nowhere. A changeset that resolves to no governing spec returns `BLOCKED` naming the selector and the empty result.

</changeset_target>

Throughout this skill, `<scope-type>` and `<scope>` stand for the run selectors: `file` and `<path>` for a `path` target, `changeset` and `<base>..<head>` for a `changeset` target. `<spec>` stands for the spec file under audit: `<path>` for a `path` target, and each audited spec in turn for a `changeset` target.

</request_contract>

<execution_sequence>

<step name="load_standards">

**Step 1: Load shared test-evidence standards**

Use skill `product-tree:test-evidence-standards`. Apply its complete predicate-seam, semantic-binding, case-provenance, oracle-independence, assertion-type-litmus, mutation litmus, and assertion-design-record rules. A missing reference blocks the audit because `/test` and this audit must judge from the same standards.

</step>

<step name="load_context">

**Step 2: Load context read-only**

When the live `<PRODUCT_TREE_FOUNDATION>` marker is absent: Use skill `product-tree:understand`.

Load the context of each audited spec node by reading, in this order, and starting no audit phase before every read completes; a changeset target loads each shared directory's spec and decisions once:

1. the product document at `spx/`;
2. at each directory from `spx/` down to the directory containing the node spec, that directory's spec, then every decision record (`*.adr.md`, `*.pdr.md`) in it; in the node's own directory, read its decision records and leave its spec to Step 4;
3. every decision a loaded spec or decision cites by full `spx/` path, repeating for each newly read decision until none is unread; a citation to a missing decision file is a `BLOCKED` result naming the citation and the citing file.

The base for touched text is resolved in Step 14.

</step>

<step name="open_run">

**Step 3: Open the run**

Start the run before judging anything:

```bash
spx verification run start --verification-type audit --scope-type <scope-type> --scope <scope> --input <input-file>
```

A file-scoped run takes the audited path as its `<input-file>`, so the retained input equals the audited file and no start payload is built. A changeset-scoped run takes a start input file written per `<payload_files>` of `${SKILL_DIR}/references/run-recording.md` as one JSON object carrying the selector as `selector` and `base`, `head`, and `changed_paths` copied verbatim from the resolved scope. The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="map_assertions">

**Step 4: Map assertions to test files**

For each audited spec, read its Assertions section. Only assertions carrying `[test]` evidence enter this audit. Skip assertions tagged `[eval]`, `[audit:{rule-slug}]`, or the pathless `[audit]` that the foundation admits for a toolchain without slug support; their evidence belongs to other verification workflows. Number each included assertion by its ordinal among all the spec's assertions, counted from 1 in document order, for the unit identifiers of `<persistence_contract>`.

For each included assertion, extract:

| Field          | Extract                                                  |
| -------------- | -------------------------------------------------------- |
| Assertion text | The claim being tested                                   |
| Assertion type | Scenario / Mapping / Conformance / Property / Compliance |
| Test link      | Path from `([test](path))`                               |
| Link status    | File exists or missing                                   |

**Missing test file = finding** with rule `missing-test-file` against the missing path. Record it and continue to the next assertion.

When a spec carries no `[test]` assertion, no evidence is applicable: record one `not-applicable` child per `<persistence_contract>` and judge nothing further.

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

Read every resolved artifact before continuing. A referenced fixture is inventoried even when consumed only by path. Include every applicable discovery or module-resolution artifact the repository carries for the linked tests: examples include `conftest.py` or pytest configuration, Vitest configuration, `Cargo.toml`, and `go.mod`. The inventory contains exactly one entry for every artifact used to resolve imports, ownership, collection, or discovery, whether or not it produces a finding.

If an import cannot be resolved from the repository, record an `incomplete-evidence-chain` finding against the unresolved repository-relative path, with remediation target `test-infrastructure`, and leave the unit it concerns `incomplete`. Do not attribute the finding to the thin test file. Continue every check supported by the available artifacts; report a property whose required evidence is unavailable as failed missing evidence rather than inferring a judgment from unread content.

</step>

<step name="check_testability">

**Step 6: Testability precondition**

For each assertion, read the governed production source and identify the observable boundary, seam, or injection point through which a test can exercise the assertion-relevant behavior. Judge the source shape before judging the linked test.

If the source exposes no way to observe or drive that behavior, record an `untestable-source` finding against the source file with remediation target `source-file`. State the missing seam and its evidentiary consequence. Continue ownership and every other inspectable property check; preserve the testability failure regardless of those results.

A value the assertion needs that production owns and exposes through no import path is also a missing seam: apply the literal rule of Step 7 and name it.

</step>

<step name="check_ownership">

**Step 7: Ownership across the evidence chain**

Read each linked test file before coupling. Identify every variable, constant, local function, fixture parameter, property-generated parameter, predicate, and assertion API call and classify the proper owner:

Use language syntax while reading to enumerate declarations, then classify ownership by reading the declaration and its evidence role. Do not outsource the verdict to a grep pattern or validation command.

Before classifying data bindings, resolve anything that looks like case data through the per-assertion-type litmus from `/test-evidence-standards`, applied below. A case that litmus assigns to the test itself is correctly owned there and is never a rejection; demanding it move into a production module is the source laundering the standard forbids.

Classify each binding and predicate under `<semantic_binding_ownership>` of `/test-evidence-standards`: assertion flow and linked-test predicates are accepted; an infrastructure predicate, test-owned configuration, test-owned data, and source-owned vocabulary copied into the test are rejected.

Do not treat casing or syntax as evidence. Renaming `MAPPING_RUNS` to `mappingRuns`, changing an assignment to destructuring, or receiving a value through a parameter does not change what the binding chooses.

Use property `predicate-ownership` with rule `assertion-seam` and remediation target `test-file` when infrastructure owns a predicate, matcher, expected-value parameter, assertion call, or verdict helper. Use property `oracle-independence` with rule `oracle-independence` and remediation target `independent-oracle` when an expected result derives from the production table, algorithm, parser, branch logic, or other implementation path that produces the actual result. Use property `source-ownership` with rule `source-ownership` when the test copies a source-owned singleton shape or vocabulary. Use property `declarations` for the remaining two rejections, with rule `test-owned-configuration` for a binding that chooses runner settings, seed policy, or setup or lifecycle policy, and rule `test-owned-data` for a binding that chooses boundary bags, expected outputs, fixture contents, generator domains, or case data the assertion type does not assign to the test.

Apply the literal rule at testability, coupling, falsifiability, and rejection: a literal standing in for a value production owns severs evidence quality regardless of test structure, and a literal outside `{-1, 0, 1, 2}` for numbers or `{""}` plus descriptive callsites for strings is such a literal unless the assertion-type litmus assigns it to the test. Record it as `source-ownership`. A static-literal fixture file is no valid origin: a fixture that exports hardcoded literals recreates laundered indirect coupling under a fixture name. When a bare literal is rejected, the finding's message reports the positive pattern as the remediation, naming the library origin, the production-owned constant, or the generator the test imports from; a value that originates outside the codebase, such as an HTTP status, a POSIX errno, or a protocol opcode, is imported from the platform or library origin production imports from.

For property-based tests, verify seed and replay behavior by reading the imported harness or property wrapper. If a property test has no harness-owned seed policy and no failure output that includes the seed or replay path, record rule `test-owned-configuration` or `missing-property-seed-reporting`.

Apply `<artifact_ownership>` of `/test-evidence-standards` to every imported harness, generator, fixture, and discovery artifact; an artifact that owns anything those rules assign elsewhere is a `source-ownership` finding.

Judge a source symbol the test cites by declared-contract ownership: does production consume it, emit it, publish it as API, register it, or serialize it against a declared schema? An absent in-repository caller opens that question rather than settling it, so inspect the declared surfaces the checkout carries — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting the symbol as laundered. Name the surfaces inspected in the finding. Report the finding when none of them requires the symbol: a consumer outside the checkout is not evidence this audit can gather, so its bare possibility never withholds a finding the declared surfaces support.

For every case input, expected value, protocol key, command token, status value, rule identifier, and payload member, name its source and independent oracle in the inventory. Apply the per-assertion-type litmus questions from `/test-evidence-standards`. A value with no valid owner produces a `source-ownership` finding; an expectation derived from the production path under test produces an `oracle-independence` finding. The finding's `location` names the artifact that copied or coupled the value. Every `source-ownership` finding sets its remediation target to `source-contract`, even when the copied value appears in a harness, generator, fixture, discovery file, or test; the defect location never becomes the semantic owner. The `<assertion_design_record>` of `/test-evidence-standards` is judged as one unit through the steps and properties that already own its fields: the assertion through Step 4's assertion mapping, the production subject through Step 6's testability precondition, case provenance through `source-ownership`, oracle owner through `oracle-independence`, and the rejected mutation with its failure observation through `falsifiability` in Step 9.

</step>

<step name="audit_coupling">

**Step 8: Coupling**

Read the test file's import statements. Classify each import:

| Import source                                  | Classification             |
| ---------------------------------------------- | -------------------------- |
| Test framework (vitest, pytest, jest)          | Framework — does not count |
| Node modules / pip packages                    | Library — does not count   |
| Codebase path (relative import, product alias) | Codebase — counts          |

**Zero codebase imports → `no-coupling` (tautology).**

When codebase imports exist, classify each by the coupling taxonomy in `${SKILL_DIR}/references/coupling-taxonomy.md`, which assigns the rule `laundered-coupling`, `false-coupling`, `partial-coupling`, `severed-coupling`, or `prose-coupling` to each category. Coupling means exercising executable **behavior**: a test that reads an authored prose or documentation body and asserts on its content is a `prose-coupling` finding, however a harness mediates the read.

</step>

<step name="audit_falsifiability">

**Step 9: Falsifiability**

For each codebase import, name a concrete mutation to the imported module that would cause this test to fail. Write it down:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed result
Impact: "parses nested sections" fails — expect(result.section.key) throws
```

**Cannot name a mutation for any import → `unfalsifiable`.** A mutation to a production-owned constant that leaves the test passing, because the test holds a literal copy, is such a case.

Check for mocking. If the test imports a module then replaces it with a mock, the coupling is severed:

```typescript
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn() }));
// Real database.query never runs — coupling severed
```

**Import + mock = `severed-coupling`.**

**Exception**: a test double used under the controlled-implementation relief of `/test-evidence-standards`, one of the seven named exception cases of the `/test` methodology, is not `severed-coupling`. Identify the matching exception and verify the double is the type that case names.

</step>

<step name="audit_alignment">

**Step 10: Alignment**

Read the spec assertion text. Read the test's expect/assert statements. Answer:

1. Does the test exercise the exact behavior the assertion describes?
2. Could the spec assertion be unfulfilled while the test passes?

If yes to question 2: **`misaligned`.**

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

Judge the test strategy against `<type_level_permissions>` and `<assertion_type_litmus>` of `/test-evidence-standards` for the assertion type; a strategy those rules do not permit for that type is `misaligned`.

</step>

<step name="audit_coverage">

**Step 11: Coverage**

Trace, by reading, whether the test drives execution into the assertion-relevant code path:

1. Read the production code the assertion governs and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that production code.
3. Judge whether the test's execution reaches the assertion-relevant path — the lines whose behavior the assertion claims.

**Interpret the trace:**

- **Reaches the assertion-relevant path**: the test exercises the behavior the assertion claims. ✓
- **Imports the module but never drives execution into the assertion-relevant path**: `no-coverage`. Name the specific assertion-relevant path the test fails to reach, traced from the code.
- **The assertion-relevant path is trivially total** (the test obviously exercises every line the assertion claims): the test's evidentiary value comes from the other three properties.

Coverage here is execution breadth (does the test reach the assertion-relevant lines), not assertion strength. A property-based test that exercises the same lines over a broader input domain adds behavior-coupled evidence that reading captures and a line count would not.

The judgment is traced from the code and named in the finding — never a measured percentage, and never an unbacked "probably covers."

</step>

<step name="compose_language">

**Step 12: Compose language-specific test-evidence concerns**

The four evidence properties above are language-neutral. Language-specific test-evidence concerns are owned by the language test audit skill, not by this one. `${SKILL_DIR}/references/language-composition.md` states the language skills the composition reaches, how linked-test filenames map to partitions, and how each language result is validated and merged.

For each language whose audit skill appears in the skill listing, load only that language's standards skill:

- Python: Use skill `python:python-test-standards`.
- TypeScript: Use skill `typescript:typescript-test-standards`.
- Go: Use skill `go:go-test-standards`.
- Rust: Use skill `rust:rust-test-standards`.

Map the linked tests to language partitions as that reference states, then, for each language partition, invoke only that language's audit skill:

- Python: Use skill `python:audit-python-test`.
- TypeScript: Use skill `typescript:audit-typescript-test`.
- Go: Use skill `go:audit-go-test`.
- Rust: Use skill `rust:audit-rust-test`.

Validate and merge each result as that reference states, including the `NOT_APPLICABLE` shape.

</step>

<step name="compose_architectural">

**Step 13: Roll up composed architectural duplication**

Roll up the `gate-2-architectural` findings of the language verdicts as `${SKILL_DIR}/references/language-composition.md` states.

</step>

<step name="classify">

**Step 14: Classify**

Resolve the base and run the diff commands as `${SKILL_DIR}/references/touched-text.md` states, and sort every finding into touched text or standing text.

Before recording, inspect every finding as a complete record: its unit, rule, `location`, observed and expected evidence, and the remediation target derived from the semantic owner the evidence model names. Complete a missing element before recording the finding; never rely on the message to imply an omitted one.

</step>

<step name="record">

**Step 15: Record**

Add the root scope unit first, because a run admits one root and every child names it, then, for a `changeset` target, each node child, then each assertion child, then each grandchild under its assertion in the order of Step 4, then each `not-applicable` child, then each finding on touched text on its unit, per `<persistence_contract>`. A unit whose inspection ran is `audited` whether its properties hold or carry findings; a unit whose required inspection was unavailable is `incomplete` and carries a finding that records its cause. A standing finding is recorded nowhere in the run.

</step>

<step name="finish">

**Step 16: Finish**

Derive `rejected` when a finding on touched text exists or any unit is `incomplete`, and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type <scope-type> --scope <scope> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type <scope-type> --scope <scope> --run <token>
```

</step>

</execution_sequence>

<persistence_contract>

`${SKILL_DIR}/references/run-recording.md` states the units and payload objects that `spx verification run scope add` and `finding add` accept, in its `<persistence_contract>`, and the payload-file procedure for every recording command, in its `<payload_files>`. Read it before Step 3; the recorded run accepts no other payload shape.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED`, `REJECTED`, or `NOT_APPLICABLE` envelope and no restated findings. After the projection, return each standing finding on its own line in the form `${SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
diagnostic: <configuration error naming the refused path, or none>
```

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Claude approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. The tests pass if the entire codebase is deleted. Claude was distracted by clean types, good structure, and comprehensive scenarios, and never checked the imports.

How to avoid: Step 8 checks imports before the other evidence properties. Zero codebase imports is `no-coupling`.

**Failure 2: Accepted mocking as legitimate coupling**

Claude saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. Claude judged the import line alone and never read how the test used the module, so it missed that the real module never ran.

How to avoid: Step 9 checks for mocking after confirming coupling. Import + mock = coupling severed.

**Failure 3: Re-ran the project's coverage command inside the audit**

Claude ran the project's coverage command three times (baseline, with-test, isolated) to measure a delta. Claude took a measured number for evidence, though the audit judges by reading whether execution reaches the assertion-relevant path; the runs added no audit evidence and repeated work excluded by `<constraints>`.

How to avoid: Step 11 traces coverage by reading whether the test drives execution into the assertion-relevant path. Name the path from the code; never run the coverage or test command, and never substitute an unbacked "probably covers" for the trace.

**Failure 4: Distracted by code quality signals**

Claude spent the entire audit checking for `as any`, verifying return types, and searching for skip patterns. The test had perfect TypeScript quality and zero evidentiary value. Claude mistook visible quality signals for evidence quality; they are linting concerns, not audit concerns.

How to avoid: Follow the complete ordered audit sequence: inventory the evidence chain, check source testability, screen test-owned declarations, then judge coupling, falsifiability, alignment, and coverage.

**Failure 5: Approved a prose-body substring test as direct coupling**

Claude audited a test that read an authored skill body and asserted that policy substrings were present, and rated coupling PASS — "direct coupling to the artifact; the text is the thing under test" — and falsifiability PASS — "removing the clause from the skill body breaks the test." The test exercises no code; only an edit to the authored prose falsifies it, so it carries no behavioral evidence, yet the four-property model rationalized it as conformance.

How to avoid: Step 8 — after identifying what a test reads, classify by whether the subject is executable behavior or authored prose/documentation, not by whether the path resolves to a repository file. A read of an authored prose or documentation body asserted for its content is prose-coupling, however the path is resolved and whatever harness mediates the read.

**Failure 6: Accepted renamed test-local configuration**

Claude saw a validation warning for a SCREAMING_CASE test constant used as a property-test run count, renamed it to camelCase, and approved the audit because the validator stopped flagging it. The value was still runner configuration in the executed test file. Claude took the validator's silence for the verdict instead of reading what the value chooses, and the rename only evaded a heuristic.

How to avoid: Step 7 reads declarations before coupling and classifies ownership. Runner counts, seeds, replay policy, setup choices, boundary bags, expected outputs, fixture paths, and generated domains belong in harnesses, generators, source contracts, inert fixtures, or eval cases — never in the test file under a different name.

**Failure 7: Approved a thin test without auditing its harness**

Claude inspected a linked Python test that imported a harness, then reviewed only three repeated `file.txt` values in the harness and approved them as harness-owned synthetic vocabulary. The harness also declared SPX payload keys, command tokens, producer identities, status values, and expected projection fields. The run recorded no inventory and never classified most values.

How to avoid: Step 5 inventories and reads the complete evidence chain before judgment. Step 7 names the source of every protocol value and rejects harness-declared domain truth with `source-ownership`.

**Failure 8: Rejected observation and resource bindings by syntax**

Claude rejected a temporary-directory fixture parameter and a local `observations` binding even though both only received values selected by their owning infrastructure. The proposed remediation moved those handles into the harness, obscuring assertion flow without changing any semantic owner. Claude judged each binding by its syntactic shape rather than by who selects its value.

How to avoid: Step 7 classifies each binding by the semantic-binding rule of `/test-evidence-standards`, never by its syntax.

**Failure 9: Used the defect location as the remediation owner**

Claude correctly found copied protocol fields in a harness and emitted `source-ownership`, then set the remediation target to `harness` because that file contained the defect. Claude conflated where the defect sits with who owns the value. Copied domain truth belongs to a source contract regardless of where the copy appears.

How to avoid: Keep location and ownership separate. Name the artifact containing the copy in `location` and set every `source-ownership` finding's remediation target to `source-contract`.

**Failure 10: Omitted a language manifest from the evidence chain**

Claude inspected a Rust test, harness, generator, and production module, then omitted the package's `Cargo.toml` from the inventory because it carried no finding. The manifest established package and test discovery, so the inventory was incomplete.

How to avoid: Inventory applicable discovery and module-resolution artifacts even when they produce no finding. This includes pytest and Vitest configuration, Cargo manifests, and Go module files when they establish the test boundary.

**Failure 11: Recorded a semantically correct but structurally incomplete finding**

Claude rejected a production-derived oracle with the correct assertion, property, rule, artifact, and evidence chain, then omitted the remediation target from the finding. The prose diagnosis named the need for an independent oracle, but the author repairs from the finding alone and the owner who must change was not stated. Claude treated the prose diagnosis as a complete finding.

How to avoid: Complete each finding in Step 14 before recording it, and derive the remediation target from the evidence model.

**Failure 12: Read an absent in-repository caller as proof of laundering**

Claude rejected a package's `__version__` as source-ownership laundering because no module in the checkout consumed it. The packaging manifest declares it as published API, a surface the audit never opened, so a real contract was reported as a test-only address.

How to avoid: Judge ownership by the contract outside the test tree, and read the checkout's declared surfaces — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting a symbol as laundered.

**Failure 13: Moved the checkout while loading context**

Claude ran the context loader that rebases the audited branch, so the head under audit was replaced by another commit. Claude invoked the loader because the router requires contextualization before node work, and never checked that the loader moves the checkout.

How to avoid: Load the context by reading files at the head as it stands.

**Failure 14: Rejected the run on a defect in text the changeset left alone**

Claude found a real violation in an unchanged test or harness and recorded it on the unit, so the run rejected a changeset that did not cause the defect. Claude treated every real defect it found as grounds for rejection and never sorted findings by whether the diff touched them.

How to avoid: Classify each finding by its location, record only findings on touched text, and return every other finding as `filed`.

</failure_modes>

<success_criteria>

- A `changeset` target resolves through `product-tree:scope-changeset` at a head equal to the checkout's `HEAD`, runs on the changeset scope `<base>..<head>`, and records each audited spec under its own node child.
- Every in-scope assertion has a child unit, every linked test file has an `evidence` grandchild, and every required language concern has a language grandchild, with no evidence partition left unevaluated.
- Every imported evidence artifact was inspected before approval; an artifact that could not be resolved left its unit `incomplete` with the cause recorded, and the run sealed `rejected`.
- Every protocol and domain value resolves to its production or platform owner; generated variable data resolves to a generator, inert whole payloads to fixtures, setup policy to harnesses, and curated examples to eval cases.
- Every recorded finding lies on touched text or records the cause of an `incomplete` unit, sits on an accepted grandchild unit, is keyed by a catalogued identifier, and names the assertion, the failed property, the evidentiary gap, and the remediation target.
- Every coverage determination identifies the assertion-relevant source path reached or omitted.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The `terminalStatus` is `rejected` exactly when a finding on touched text is recorded or a unit is `incomplete`, and `approved` otherwise, whatever standing findings exist.
- The checkout's head is the same before and after the audit.
- The same target, context, evidence chain, and base yield the same units, finding keys, and terminal status.

</success_criteria>
