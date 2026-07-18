# Plan: semantic test seams and evidence rerouting

This change makes `/test` the only route from an assertion to `[test]`, `[eval]`, or `[audit]`, keeps every assertion predicate in its linked test, and removes the false `[review]`-as-`[audit]` compatibility model.

This file is a coordination note. The governing product truth remains [the evidence enabler](evidence.md), [the verification decision](../../31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), and [the test-infrastructure decision](../../31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md).

## Historical cause

`[review]` entered the tree when review was the only alternative to deterministic tests. Evaluate and audit did not exist. The current model has five verification types and three assertion tags:

| Verification type | Verdict mode  | Assertion tag |
| ----------------- | ------------- | ------------- |
| validate          | deterministic | none          |
| test              | deterministic | `[test]`      |
| evaluate          | deterministic | `[eval]`      |
| review            | agentic       | none          |
| audit             | agentic       | `[audit]`     |

Review remains an open-ended correctness gate over a changeset. It backs no assertion tag. A legacy `[review]` assertion is therefore **unrouted**: its author chose the old non-test alternative before the current distinction between evaluate and audit existed. Treating it as an alias for `[audit]` guesses the answer and erases the possibility that the claim belongs in `[test]` or `[eval]`.

## Decisions

1. **No compatibility alias.** Authored skills, templates, examples, specs, eval prompts, and generated output never describe `[review]` as a spelling or alias of `[audit]`.
2. **Route every occurrence afresh.** `/test` selects `[test]`, `[eval]`, or `[audit]` from the current assertion and real producer. A mechanical `[review]` -> `[audit]` replacement is invalid.
3. **Use a touched-file migration boundary.** When a changeset edits a spec file, it reroutes every `[review]` assertion in that file. Untouched spec files remain visible migration debt.
4. **Keep review as a changeset gate.** Review continues to judge a changeset through the review workflow and journal. It never becomes an assertion evidence tag.
5. **Keep predicates in linked tests.** Test infrastructure supplies context, resources, generated inputs, inert payloads, and observations. The linked test file owns the truth predicate that proves its spec assertion.
6. **Keep oracles independent.** The actual producer and expected producer cannot select their results through the same implementation table, algorithm, parser, branch logic, or collaborator verdict method.
7. **Keep durable edits in authored source.** Plugin changes are made under `src/plugins/`; `dist/claude/` and `dist/codex/` are regenerated.

## Current baseline

Inventory was re-run on full base SHA `d48a9fa122c927ae1cf160182b08b97b2275873f`.

- 282 `([review])` assertions remain across 52 node spec files.
- 299 `([review])` tokens remain across 60 Markdown files when coordination notes and eval material are included.
- Authored plugin source contains 14 `[review]` tokens across 10 Markdown files.
- Generated Claude and Codex trees contain 28 `[review]` tokens across 20 Markdown files. This count includes legitimate invalid-input examples and must be classified by meaning.
- The audit-tests full-chain eval corpus contains five cases: `rejects-harness-owned-protocol`, `approves-source-owned-protocol`, `rejects-unread-import`, `rejects-transitive-generator-owned-protocol`, and `rejects-rust-generator-owned-protocol`.
- The corpus contains no case that distinguishes an implementation-derived oracle from an independent oracle.

Residual spec assertions by top-level subtree:

| Subtree                         | Files | Assertions |
| ------------------------------- | ----: | ---------: |
| `spx/13-infrastructure.enabler` |     2 |          9 |
| `spx/15-validation.enabler`     |     1 |          2 |
| `spx/18-plugin-build.enabler`   |     1 |          2 |
| `spx/21-hygiene.enabler`        |     2 |          3 |
| `spx/21-spec-tree.enabler`      |    19 |         83 |
| `spx/32-distribution.enabler`   |     1 |          1 |
| `spx/43-frontend.enabler`       |     1 |          2 |
| `spx/43-hdl.enabler`            |     1 |          2 |
| `spx/43-instructions.enabler`   |     2 |         12 |
| `spx/43-prose.enabler`          |     1 |          2 |
| `spx/43-python.enabler`         |     9 |         75 |
| `spx/43-rust.enabler`           |     1 |          9 |
| `spx/43-typescript.enabler`     |    10 |         76 |
| `spx/43-work.enabler`           |     1 |          4 |

Re-run this inventory before implementation because the base may advance. Preserve both counts: node-spec assertions and all Markdown occurrences answer different questions.

## Defect chain

The authored sources below currently create, accept, skip, or semantically reinterpret the invalid marker.

| Authored source                                                                                             | Current defect                                         | Required result                                                                                                                        |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `src/plugins/spec-tree/skills/understand/SKILL.md:248`                                                      | Declares `[review]` the legacy spelling of `[audit]`   | Declares `[review]` an unrouted legacy marker; review backs no tag                                                                     |
| `src/plugins/spec-tree/skills/author/SKILL.md:166`                                                          | Teaches the alias while authoring assertions           | Refuses to author `[review]`; routes through `/test`                                                                                   |
| `src/plugins/spec-tree/skills/test/SKILL.md:136`                                                            | Teaches the alias in the evidence-link step            | Selects only `[test]`, `[eval]`, or `[audit]`; reports `[review]` as unresolved                                                        |
| `src/plugins/spec-tree/skills/audit-specs/SKILL.md:21,109`                                                  | Accepts bare `[review]` as valid audit evidence        | Rejects it as `unrouted-legacy-evidence` without guessing a replacement                                                                |
| `src/plugins/spec-tree/skills/audit-tests/SKILL.md:77`                                                      | Silently skips legacy `[review]`                       | Reports the routing defect or requires a completed spec-audit prerequisite; never silently treats it as another workflow's valid input |
| `src/plugins/spec-tree/skills/align/SKILL.md:165`                                                           | Calls ancestor `[review]` audit-like semantic evidence | Treats `[review]` as unknown evidence and requires rerouting before evidence-specialization comparison                                 |
| `src/plugins/instructions/skills/audit-skills/references/operational-effectiveness-examples.md`             | Gives `[review]` as a resolving evidence link          | Uses only the three current tags and current verdict shapes                                                                            |
| `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler/audit-specs.md:15`                        | Product truth repeats the alias                        | Declares rejection of an unrouted marker                                                                                               |
| `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler/evals/structure/prompt.md:25,113`         | Generated producer prompt accepts the alias            | Regenerates from corrected producer and rejects it                                                                                     |
| `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership*/prompt.md:81` | Generated producer prompts inherit silent skipping     | Regenerate after correcting `audit-tests`                                                                                              |

The decision-audit sources currently cite bare `[review]` only as invalid input. Preserve that rejection behavior in `audit-adr`, `audit-pdr`, and `pdr-evidence-model.md`. Wording may change from "bare mechanism" to "unsupported legacy marker," while acceptance remains forbidden.

Coordination notes also carry the obsolete migration model:

- `spx/ISSUES.md:21-25` prescribes a tree-wide mechanical `[review]` -> `[audit]` batch.
- `spx/13-infrastructure.enabler/25-eval-harness.enabler/ISSUES.md:75-77` offers audit or no assertion lane and omits fresh routing to test or eval.
- `spx/21-spec-tree.enabler/54-aligning.enabler/ISSUES.md` repeatedly treats `[review]` as a known semantic-evidence class.
- `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md:9-16` records a superseded evidence model.
- `spx/21-spec-tree.enabler/35-evidence.enabler/ISSUES.md:15` groups `[audit]` and `[review]` together under semantic judgment.

Replace those recommendations with the touched-file policy and remove statements whose only purpose was the invalid compatibility period.

## Semantic assertion seam

The linked test file is the only layer that owns the assertion predicate. A test such as `assert handoff_creates_session_file()` is invalid when `handoff_creates_session_file()` decides whether the spec assertion passed. The function name and Boolean return hide the predicate in a harness file that the spec does not link.

Valid responsibilities:

| Layer       | Owns                                                                                   | Must avoid                                                                             |
| ----------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Source      | Product behavior and source-owned contracts                                            | Test-only truth APIs                                                                   |
| Harness     | Resource lifecycle, setup, cleanup, dependency checks, execution, and raw observations | Expected outputs, verdict booleans, assertion helpers, or collaborator verdict methods |
| Generator   | Variable input domains with variation, composition, shrinking, and replay              | Constant wrappers, expected outputs, and implementation-derived case selection         |
| Fixture     | Inert whole-payload input consumed by path, bytes, or copy                             | Isolated expected values or executable exports                                         |
| Linked test | Arrangement through imported owners, behavior execution, and the final predicate       | Reusable case data, runner policy, or copied source vocabulary                         |

Add these questions to the shared `/test` methodology, language test standards, and test-evidence audits:

1. **Predicate inversion.** If the assertion predicate were changed to its logical opposite while setup and behavior boundary stayed the same, would any harness, generator, fixture, or controlled collaborator need to change? A "yes" means that layer encodes assertion logic.
2. **Raw observation.** Does the harness return observations or domain results that the linked test can inspect, or does it collapse them into `True`, `False`, `approved`, `matches`, `was_called_with`, or another verdict?
3. **Mutation visibility.** Name a source mutation that violates the assertion. Does the linked test predicate fail while the test infrastructure remains unchanged?
4. **Boundary preservation.** Does a controlled implementation preserve the production protocol and behavior boundary, including meaningful state transitions, or does it replace the asserted behavior with a canned answer?
5. **Spec linkage.** Can a reader understand the complete predicate by reading the linked test file and its source contracts without discovering a hidden assertion in imported test infrastructure?

Recording collaborators and spies expose recorded calls or events as data. The linked test asserts on that record. Methods such as `was_called_with(...)` are forbidden because they evaluate the predicate inside the collaborator.

## Oracle and test-data independence

Actor separation does not create oracle independence. One person or agent may write source and tests only when case and expected-result provenance come from independent product truth.

Apply these general questions before accepting any case:

1. Who selected the input, and where is that selection declared?
2. Who selected the expected result, and through which source or derivation?
3. Would changing the implementation automatically change the expected result? Automatic co-change exposes a shared producer and invalidates the oracle.
4. Does the expected path call the same parser, table, branch logic, normalization routine, or collaborator verdict method as the actual path?
5. Could an independently introduced defect affect actual and expected in the same direction?
6. Does the case come from the assertion, a complete source-owned domain, a variable generator, an external standard, a real payload, or a decision-derived violation?
7. Is a hand-picked "reasonable" example standing in for an open domain or a complete finite set?

Per-assertion litmus tests:

| Assertion type | Valid case source and oracle                                                                                              | Questions that must pass                                                                                                    | Reject                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Scenario       | The specific interaction declared by the spec, with expected behavior derived independently from the implementation       | Does the spec identify this case? Does the expected outcome come from the declaration, protocol, or real boundary response? | An invented representative example or a harness-owned success Boolean                                      |
| Mapping        | Every member of a finite source-owned domain, with expectations derived from a separate contract or mathematical relation | Is the domain complete? Would an implementation-table defect escape the expected path?                                      | A copied expected-output table or a subset selected by the implementation author                           |
| Conformance    | An external standard, schema validator, reference implementation, or independent parser                                   | Is the oracle owned outside the module under test? Does an intentionally malformed output fail it?                          | A validator copied from the same interpretation or built from the implementation parser                    |
| Property       | A meaningful generated domain plus an invariant or metamorphic relation independent of the implementation algorithm       | Does the generator explore and shrink? Can the invariant detect a plausible wrong algorithm?                                | Constant-only generation, "does not throw," or expected output computed by the algorithm under test        |
| Compliance     | Decision-derived violating cases and a rule oracle that exercises enforcement                                             | Is at least one real violation rejected? Does the rule oracle remain independent of the enforcement branch?                 | Passing-only examples, prose inspection, or a decision rule used as a case without a violating realization |

Strengthen `src/plugins/python/skills/python-test-standards/SKILL.md` and `src/plugins/python/skills/test-python/SKILL.md` with this seam. Preserve their current source-first, no-mocking, provenance, generator, fixture, and oracle-independence rules. Correct any table row that suggests a decision sentence alone is sufficient compliance case data; compliance needs a violating realization derived from the decision.

## Python architecture alignment

Correct the authored Python architecture references without weakening dependency injection or the no-mocking standards:

| File                                                                                    | Defect                                                                                                            | Replacement direction                                                                                                                               |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/plugins/python/skills/architect-python/references/type-system-patterns.md:125`     | "Enables easy mocking in tests"                                                                                   | Protocols permit dependency-injected controlled implementations and recording collaborators                                                         |
| `src/plugins/python/skills/architect-python/references/testability-patterns.md:273-299` | "Dependency Injection Enables Mocking," `MockUserRepository`, `MockNotifier`, `was_called_with`, and "Can't mock" | Use a controlled repository and recording notifier that implement the real protocols; expose records as data; keep the predicate in the linked test |
| `src/plugins/python/skills/architect-python/references/architecture-patterns.md:207`    | "Inject mocks for testing"                                                                                        | Inject controlled implementations, real local adapters, or recording collaborators according to the `/test` router                                  |

Sweep every file under `src/plugins/python/skills/architect-python/references/` for the same defect class. Current search also finds "No mocking needed," which can remain when it describes a pure function and does not teach replacement mocks. Preserve and strengthen the no-mocking rules in `python-test-standards/SKILL.md` and `python-architecture-standards/SKILL.md`.

## Runtime-derived eval producer corpus

The full-chain audit-tests evals must exercise the generated producer for each runtime surface:

- The Claude suite derives its prompt from `dist/claude/spec-tree/skills/audit-tests/SKILL.md`.
- The Codex suite derives its prompt from `dist/codex/spec-tree/skills/audit-tests/SKILL.md`.
- Authored `src/plugins/spec-tree/skills/audit-tests/SKILL.md` remains an owned path so a source edit selects both generated runtime suites after `just build-skills`.
- `prompt.md` stays generated through `just eval-materialize-prompts`; no prompt body is edited by hand.
- The shared case corpus supplies only scenario inputs and withheld grader expectations. It never carries a copied producer policy as a substitute for the generated runtime producer.

Add at least two oracle-independence cases:

1. A rejecting case in which actual and expected outputs come from the same implementation table, parser, branch logic, or harness verdict method. The required finding property is `oracle-independence`.
2. A control case with the same behavior boundary and an independently derived oracle. It must avoid an `oracle-independence` finding.

Include the rejecting case in the smoke set after it proves stable. Re-materialize both prompts after the producer changes. Do not run a paid eval in the fresh session unless the operator explicitly reauthorizes it; deterministic prompt materialization, case loading, schema checks, and eval-evidence audit remain required.

## Execution sequence for the fresh session

### 1. Establish the branch and context

1. Invoke `/understand` after any compaction.
2. Invoke `/contextualize spx/21-spec-tree.enabler/35-evidence.enabler`.
3. Invoke `/slice` to select the executable slice. Do not use a plan-slice workflow.
4. Invoke `/apply` before implementation, `/test` before test work, and `instructions:create-skills` before editing any skill content.
5. Contextualize every additional governing node before touching its spec, source, tests, or eval artifacts. At minimum this includes the audit-specs, audit-tests, align, Python tests, Python architecture, and eval-harness nodes reached by the slices below.

### 2. Correct the declaration and migration policy

1. Amend `evidence.md` so the three assertion tags are exclusive and legacy `[review]` is an unrouted error.
2. Replace the root bulk-migration issue with the touched-file policy.
3. Correct the stale evidence, align, eval-harness, and template coordination notes listed in the defect chain.
4. Route every `[review]` in each spec file edited by this slice through `/test`. Record the chosen producer and reason for `[test]`, `[eval]`, or `[audit]` in the implementation journal or commit notes.

### 3. Correct core methodology producers and consumers

1. Add the semantic assertion seam, provenance questions, and per-assertion litmus table to the shared `/test` methodology.
2. Make `understand`, `author`, and `test` refuse the alias.
3. Make `audit-specs` reject the marker with a dedicated finding.
4. Make `audit-tests` surface the routing gap instead of silently skipping it.
5. Make `align` stop evidence-specialization comparison until an old marker is rerouted.
6. Correct the instructions audit example.
7. Sweep all authored plugin references to `[review]`; classify each occurrence as legitimate review verification, invalid-input rejection, or defective assertion-tag guidance. Remove only the defective guidance.

### 4. Correct test seams and Python architecture guidance

1. Strengthen the shared test standards and Python test standards with predicate inversion, raw-observation, mutation-visibility, and oracle-independence checks.
2. Update test-evidence auditor guidance so `assert harness_verdict()` and collaborator-owned verdict methods are explicit rejection shapes.
3. Correct the three named architect-python references.
4. Sweep all architect-python references for mocking-positive language and assertion predicates hidden in controlled collaborators.
5. Route every `[review]` in each Python spec file edited by this slice through `/test`; do not migrate neighboring untouched specs.

### 5. Correct and extend eval evidence

1. Point each full-chain suite at its generated runtime producer.
2. Add the rejecting and control oracle-independence cases.
3. Update `owned_paths` and `smoke_cases` from product truth.
4. Run `just build-skills` before prompt materialization.
5. Run `just eval-materialize-prompts spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals`.
6. Run `just eval-materialize-prompts-check spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals`.
7. Run deterministic case loading and schema checks through the repository's selected test targets.
8. Treat paid eval freshness as a named remaining gate until the operator authorizes a paid run.

### 6. Regenerate and verify

Run the narrow checks after each slice, then the full sequence on the clean committed head:

1. `just fmt <every changed Markdown file>`
2. `just build-skills`
3. Focused `just test <spec test paths>` for changed Python or eval-harness behavior
4. `spx validation markdown`
5. `spx spec status --format json`
6. `just check-skills`
7. `just docs-check`
8. `just eval-materialize-prompts-check spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals`
9. `just check`
10. Commit through `/commit-changes`
11. Dispatch `spec-auditor` for every touched spec node
12. Dispatch `skill-auditor` for every changed skill and reference
13. Dispatch `eval-evidence-auditor` for the changed audit-tests eval suites
14. Dispatch `implementation-auditor` when implementation code or Python test infrastructure changes
15. Dispatch `changes-reviewer` over the exact clean committed head
16. Run `just check-full` only after every applicable agentic gate converges on that same head
17. Route publication and merge through `/merge`

Any edit after an agentic verdict invalidates that verdict for the prior head. Close every verifier handle after collecting its result.

## Scope controls

- Keep the implementation confined to `/Users/shz/Code/outcomeeng/plugins/plugins-c`.
- Preserve legitimate uses of review as a changeset verification type.
- Preserve invalid-input guards in decision auditors.
- Avoid a repository-wide rewrite of the 282 remaining node assertions.
- Avoid hand-editing generated `dist/` trees or generated eval prompts.
- Avoid replacing framework mocks with fakes that return the expected answer. Controlled implementations must preserve the real protocol and expose observations.
- Avoid moving expected values from a test into a harness, generator, fixture, or collaborator. Relocation does not create independence.
- Keep one semantic rollback story. If implementation reveals a separate product behavior with independent ownership and rollback, record it in the owning node and split it through the repository workflow.

## Acceptance criteria

- Authored source contains no statement that `[review]` aliases, resolves to, or is accepted as `[audit]`.
- Authoring and routing skills never create `[review]` assertions.
- Spec audit rejects `[review]` as unrouted legacy evidence.
- Test audit never silently skips `[review]` as valid evidence owned elsewhere.
- Align never compares `[review]` as a known evidence class.
- Every touched spec file contains zero `[review]` assertions, with each former assertion routed independently through `/test`.
- Untouched legacy assertions remain visible and tracked under the touched-file migration policy.
- Linked tests own their assertion predicates; harnesses, generators, fixtures, and controlled collaborators expose observations without verdict helpers.
- Per-assertion standards state valid case provenance, valid oracle provenance, rejection shapes, and litmus questions.
- A defect shared by actual and expected production logic fails the new oracle-independence eval case.
- The control eval case passes with an independently derived oracle.
- Python architecture references teach dependency-injected controlled implementations, real boundaries, recording collaborators, or spies while keeping the predicate in the linked test.
- `python-test-standards` and `python-architecture-standards` retain and strengthen their no-mocking rules.
- Claude and Codex eval prompts derive from their generated runtime producers and pass prompt-drift checks.
- Generated Claude and Codex plugin trees match authored source.
- Deterministic checks and all applicable isolated auditor and reviewer gates pass on one clean committed head.
- Any unavailable paid eval is reported as the exact remaining freshness blocker rather than represented as passing.
