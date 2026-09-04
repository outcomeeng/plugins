---
name: test
description: >-
  ALWAYS invoke this skill before writing or repairing deterministic tests for
  a spec assertion, selecting a decision Testing rule's assertion type, or when
  learning the testing approach.
argument-hint: <full-spx-node-or-decision-path> [selected-assertions-json-array]
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, AskUserQuestion
---

<objective>
Spec-tree assertion tests and decision Testing rules that are canonically assertion-typed, source-contract-coupled, language-routed, and reproducible where executable evidence exists.
</objective>

<prerequisites>

Invoke the `spec-tree:test-evidence-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop before writing test evidence.

</prerequisites>

<shared_standards>

`/test-evidence-standards` authoritatively owns the predicate-seam, semantic-binding, case-provenance, oracle-independence, assertion-type-litmus, and mutation litmus rules that test authoring and test auditing both apply. It owns the assertion-type litmus (the reject-condition checks), not assertion-type selection — this skill's routing retains that. Where the inlined methodology below and that shared standard both speak to binding ownership or oracle independence, the shared standard governs.

</shared_standards>

<testing_methodology>

<non_negotiable_rules>

- No mocking. Ever.
- Reality is the oracle. Prefer real systems whenever they are cheap, deterministic, safe, and observable enough to prove the behavior.
- Test doubles are exceptions, not defaults. The seven exception cases in Stage 5 are the only legitimate reasons to avoid the real dependency.
- Route every assertion through all five stages. Do not skip ahead.
- Name tests by subject, assertion type, execution level, and optional runner.
- Derive the assertion type from the assertion's quantifier and evidence shape, never from the section containing the rule.
- Verification routing selects the verification type. This test specialist owns assertion-type selection, execution-level selection, and controlled-implementation exceptions after test evidence is selected.

</non_negotiable_rules>

<purpose>

Every test serves at least one purpose:

1. **Prove behavior**: confirm that a requirement, scenario, or invariant holds in production-relevant execution.
2. **Catch failures early**: detect concrete breakages before users, operators, or downstream systems see them.
3. **Improve debugging economics**: place evidence at the lowest level that can prove the claim so diagnosis is fast when something breaks.

Delete a test that serves none of these purposes.

</purpose>

<pre_test_questions>

Every test answers:

1. What production behavior could be wrong?
2. If this test passes, what does it prove about the real system?
3. What failure would this catch before users see it?

Stop when all three cannot be answered.

</pre_test_questions>

<source_contract_first_gate>

Before writing or repairing evidence, read the spec assertion, the existing or planned test, and the code under test. State the production contract the test exercises:

- source-owned values: protocol tokens, status values, command names, route names, schema fields, rule identifiers, message identifiers, registries, constructors, typed factories, or public vocabulary
- observable behavior: pure functions, constructors, dataclasses, enums, schemas, protocols, typed collaborators, emitted artifacts, or side-effect boundaries
- oracle: expected output derived from the input through an independently owned computation, an independent reference, a source-owned contract, or a real system response — never recomputed by the production path under test

If the source does not expose the contract the assertion needs, fix the source contract first. Do not patch test predicates around a reviewer example, copy literals into tests, hide domain values in fixtures or generators, or replace behavior the assertion claims to verify.

</source_contract_first_gate>

<assertion_file_ownership>

An executed test file is a typed assertion file. It owns the assertion flow: arrange behavior through imported source contracts or infrastructure, execute the behavior, and assert the outcome. It owns no reusable values or execution policy.

| Concern                          | Owner                                                                                                                      |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Test configuration               | A spec-governed harness: run counts, property seeds, retry policy, resource setup, cleanup, dependency checks, diagnostics |
| Variable test input domains      | A spec-governed generator that varies, composes, shrinks, or systematically explores meaningful alternatives               |
| Source-owned vocabulary or shape | The production module, runtime, framework, or protocol package that owns the contract                                      |
| Whole-payload samples            | Inert fixtures read, copied, or passed by path when the complete payload shape matters                                     |
| Curated LLM/eval cases           | Eval case data when generating the case set as JSONL would be wasteful and not tractable                                   |

Judge every binding — variable, constant, fixture parameter, property-generated parameter, alias, or local callback — by the semantic ownership rule in `/test-evidence-standards`. A binding may receive or rename a value an owning source already chose; it may never introduce a case, expected result, configuration choice, setup policy, generator domain, or verdict rule. Those belong in a source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, independently owned oracle, or curated eval case data when generation is wasteful and not tractable. Naming a value or wrapping it in a local function never changes its owner.

Property-based tests require reproducible failures. Use a harness that owns seed selection, run-count policy, and failure diagnostics. Failure output includes the seed and replay path. Seeds and run counts never live in the test file.

</assertion_file_ownership>

<evidence_trap>

Claude can see code and test its shape instead of the behavior that matters.

- **Rejected**: See `OrderProcessor` calling `repository.save()`, create an `InMemoryRepository`, and claim persistence is covered.
- **Required**: Identify persistence as the behavior and test with a real database at the lowest level that proves persistence.

</evidence_trap>

<independent_axes>

Keep evidence, execution pain, and tool choice independent:

- **Assertion type** describes what kind of claim the test proves.
- **Execution level** describes how painful the test is to run.
- **Runner** describes which tool executes the test.

A temporary-directory test can be `L1` when the filesystem is available, setup is trivial, and runtime is cheap. A Playwright test can be `L2` or `L3` depending on whether it uses local infrastructure or remote systems and credentials. Runner never defines level, and level never defines runner.

</independent_axes>

<assertion_types>

Use evidence terms that describe what the test proves:

- `scenario`: one existential interaction within the chosen level
- `mapping`: inputs map to outputs or requests map to actions over a finite source-owned domain
- `conformance`: behavior matches an external or internal contract
- `property`: an invariant holds across an open generated domain
- `compliance`: a required rule or safety boundary rejects a violating case

</assertion_types>

<execution_levels>

Use `L1`, `L2`, and `L3` for execution pain and environment dependence:

- `L1`: almost certainly available, cheap, local, safe, deterministic
- `L2`: real but heavier local infrastructure or setup
- `L3`: remote, shared, credentialed, or network-dependent systems

Examples:

- `L1`: pure logic, temporary files, normal filesystem work, git, repository-required test runners, and standard subprocesses expected on a working machine
- `L2`: local development servers, Docker, browsers, product-specific binaries, full bootstrap or install costs, and other slower or less ubiquitous local dependencies
- `L3`: network access, shared environments, live third-party services, and anything requiring credentials

</execution_levels>

<router>

Route every assertion through all five stages:

| Stage | Outcome                                              | Next step                                                                  |
| ----- | ---------------------------------------------------- | -------------------------------------------------------------------------- |
| 1     | Evidence identified                                  | Stage 2                                                                    |
| 2     | `L2` or `L3` required                                | Use real dependencies at that level. Done.                                 |
| 2     | `L1` appropriate                                     | Stage 3                                                                    |
| 3A    | Pure computation                                     | Test directly at `L1`. No doubles. Done.                                   |
| 3B    | Pure part can be extracted                           | Test pure at `L1`; cover boundary behavior at the right outer level. Done. |
| 3C    | Glue or orchestration code                           | Stage 4                                                                    |
| 4     | Real system is reliable, safe, cheap, and observable | Use the real system at the current level. Done.                            |
| 4     | Real system cannot produce the required evidence     | Stage 5                                                                    |
| 5     | One exception case matches                           | Use the controlled implementation and record the exception. Done.          |
| 5     | No exception matches                                 | Move outward to the lowest real level that proves the behavior. Done.      |

<stage_one>

Answer the three `<pre_test_questions>` before writing the test.

Read the quantifier first:

- A **universal** claim holds over every case (`ALWAYS`, `NEVER`, “for all”, “for every”, “no input”). Its evidence is `mapping`, `conformance`, `compliance`, or `property`; never `scenario`.
- An **existential** claim describes one specific interaction (“given this case, when …, then …”). Its evidence is `scenario`.

Within the universal branch:

- use `mapping` for a deterministic transform over a finite source-owned domain
- use `conformance` for a match against an external or internal contract or protocol
- use `compliance` for a rule exercised against a real violating case or rule oracle
- use `property` for an invariant across an open or infinite input space

For boundary validation, classify by the invalid set: an open or infinite invalid set is `property`; a closed, finite, source-owned invalid set is `mapping`. A hand-picked bag of invalid values establishes neither an open property nor a complete mapping.

</stage_one>

<stage_two>

Choose the level from operational reality:

| Spec promise                                      | Minimum level | Reason                          |
| ------------------------------------------------- | ------------- | ------------------------------- |
| Prices are calculated correctly                   | `L1`          | Pure calculation                |
| User can export data as CSV                       | `L1`          | File I/O with temporary folders |
| CLI processes a product-specific site             | `L2`          | Product-specific binary         |
| Database query returns users                      | `L2`          | Real database required          |
| User completes checkout with a live provider      | `L3`          | Remote provider required        |
| Browser flow works against the live deployed site | `L3`          | Real browser and remote system  |

| Dependency                        | Minimum level |
| --------------------------------- | ------------- |
| None, pure function               | `L1`          |
| Filesystem with temporary folders | `L1`          |
| Standard development tools        | `L1`          |
| Database                          | `L2`          |
| Product-specific binary           | `L2`          |
| External HTTP API or browser API  | `L2` or `L3`  |
| Live third-party service          | `L3`          |
| Real credentials                  | `L3`          |

Test product-owned algorithms, parsers, and rules thoroughly at `L1`. Trust mature library behavior and test product-owned wiring, mappings, invariants, failure handling, and boundaries. Add lower-level evidence when it materially narrows diagnosis. Place confidence where it is achievable: math at `L1`, SQL against a database at `L2`, and live user flows at `L3`.

When evidence lives at `L2` or `L3`, use real dependencies there and stop. Continue to Stage 3 only for `L1` evidence.

</stage_two>

<stage_three>

- **Pure computation**: test directly at `L1` with no doubles.
- **Extractable pure part**: extract and test the computation at `L1`; cover dependency interaction at the correct outer level.
- **Glue or orchestration**: continue to Stage 4 because the behavior is the dependency interaction.

</stage_three>

<stage_four>

Use the real system when it produces the behavior reliably, safely, cheaply, and observably. Continue to Stage 5 when any one of those conditions fails for the evidence required.

</stage_four>

<stage_five>

Only these controlled-implementation exceptions permit avoiding the real dependency:

| Exception                | When                                                                          | Controlled implementation                 |
| ------------------------ | ----------------------------------------------------------------------------- | ----------------------------------------- |
| 1. Failure simulation    | Need timeouts, resets, throttling, full disks, or permission errors           | Stub returning predetermined errors       |
| 2. Interaction protocols | Correctness depends on call sequence or shape                                 | Recording collaborator or spy             |
| 3. Time and concurrency  | Need deterministic clocks, retries, scheduling, races, or debounce            | Fake clock or controllable scheduler      |
| 4. Safety                | Real system charges money, sends mail, or mutates shared administration state | Recording collaborator that does not send |
| 5. Combinatorial cost    | Real dependency makes broad evidence prohibitively expensive                  | Configurable fake preserving the boundary |
| 6. Observability         | Required signal is hidden by the real dependency                              | Spy recording boundary details            |
| 7. Contract probes       | Need controlled verification at a contract boundary                           | Contract stub                             |

If no exception applies, move outward to the lowest real level that proves the behavior.

</stage_five>

</router>

<test_double_taxonomy>

| Type  | Purpose                           | Use for                                     |
| ----- | --------------------------------- | ------------------------------------------- |
| Stub  | Returns predetermined responses   | Failure simulation, safety, contract probes |
| Spy   | Records calls for verification    | Interaction protocols, observability        |
| Fake  | Simplified working implementation | Time control, combinatorial cost            |
| Dummy | Placeholder that is never called  | Satisfying type requirements                |

Framework mocks remain forbidden. Supply a recording collaborator or spy through dependency injection when call recording is required.

</test_double_taxonomy>

<four_part_progression>

| Phase                   | Evidence                                | Confidence gain  |
| ----------------------- | --------------------------------------- | ---------------- |
| 1. Typical cases        | Happy paths and common scenarios        | Baseline         |
| 2. Edge and boundary    | Limits, special values, and error cases | Robustness       |
| 3. Systematic coverage  | Loops, states, and combinations         | Completeness     |
| 4. Property-based tests | Invariants across generated inputs      | Deep correctness |

Small pure functions often need phases 1 and 2. Complex algorithms often need all four. Glue code often needs phase 1 plus the correct outer-level evidence. Treat property-based tests as mandatory candidates for parsers, serializers, mathematical transformations, seed-driven generators, normalization rules, and algorithms with difficult edge cases.

</four_part_progression>

<debuggability>

- Put evidence at the lowest level that proves the claim.
- Prefer direct assertions over indirect side-channel checks.
- Keep setup proportional to the evidence.
- Redesign the test when a failure would not reveal what broke.

</debuggability>

<anti_patterns>

- Writing tests because a layer or file class “should have tests”
- Choosing a label first and searching for evidence to fit it
- Promoting cheap local-real tests into slower schedules because they touch the filesystem, git, or subprocesses
- Treating browser coverage as inherently remote or credentialed
- Treating runner choice as a proxy for cost or realism
- Adding doubles when the real dependency is cheap, deterministic, and observable
- Writing tests that cannot name the production failure they catch

</anti_patterns>

<naming_and_co_location>

Keep tests beside the governing spec and name them for what they prove and how painful they are to run.

Canonical filename model:

- TypeScript and JavaScript: `<subject>.<evidence>.<level>[.<runner>].test.ts`
- Python: `test_<subject>.<evidence>.<level>[.<runner>].py`
- Rust: `<subject>.<evidence>.<level>[.<runner>].rs`
- Go: `<subject>.<evidence>.<level>[.<runner>]_test.go`

Evidence tokens are `scenario`, `mapping`, `conformance`, `property`, and `compliance`. Level tokens are `l1`, `l2`, and `l3`. Omit the runner token for the default runner and add it for a non-default runner.

Examples:

- `dispatch.mapping.l1.test.ts`
- `browser-auth.scenario.l2.playwright.test.ts`
- `test_seeded_generators.property.l1.py`
- `session_token.scenario.l1.rs`
- `login_flow.scenario.l3.tokio.rs`

</naming_and_co_location>

</testing_methodology>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

Abort when `$ARGUMENTS` is empty: "A canonical spec node or ADR/PDR target is required." Otherwise parse it as one canonical target followed by an optional JSON array of exact assertion texts already selected for test. Preserve each array string verbatim; it identifies the untagged spec assertion this workflow may type. Reject malformed JSON or non-string array members before reading the target. A decision target uses decision-rule mode and accepts no assertion-text array.

Check for `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers. If absent, invoke `/understand` and `/contextualize` first.

For a spec target, this loads:

- The target spec node and its assertions
- Ancestor ADRs/PDRs that constrain the testing approach
- Lower-index sibling specs that provide context

For a canonical ADR/PDR target, use decision-rule mode. Require context for the containing node, or `spx/` for a product-level decision, and read only that decision's `### Testing` rules for assertion typing. The implementing specs own executable evidence and evidence links.

</step>

<step name="extract_assertions">

**Step 2: Extract assertions from the spec**

For a spec target, parse the target spec node and extract assertions already selected for `[test]` evidence plus the exact untagged assertions supplied to this invocation as selected test work. Ignore every other untagged assertion; verification-type selection remains outside `/test`. Extract any existing test links from the selected set:

| Type            | Pattern in spec                                    | Test strategy   |
| --------------- | -------------------------------------------------- | --------------- |
| **Scenario**    | `Given ... when ... then ... ([test](...))`        | Example-based   |
| **Mapping**     | `{input} maps to {output} ([test](...))`           | Parameterized   |
| **Conformance** | `{output} conforms to {standard} ([test](...))`    | Tool validation |
| **Property**    | `{invariant} holds for all {domain} ([test](...))` | Property-based  |
| **Compliance**  | `ALWAYS/NEVER: {rule} ([test](...))`               | Violating cases |

Record each assertion with:

- Assertion text
- Assertion type
- Test link (if present) — path and whether it resolves
- Test link status: exists / missing / stale

For a decision target, extract only `### Testing` rules. Apply the complete assertion-type selection from `<testing_methodology>`: the quantifier separates existential scenario evidence from universal evidence, then the universal rule's finite source-owned domain, contract oracle, violating-rule boundary, or open domain selects mapping, conformance, compliance, or property. Record the existing assertion-type tag, if any. Ignore `### Eval` and `### Audit` rules; they remain with their selected specialists.

</step>

<step name="analyze_gaps">

**Step 3: Analyze evidence gaps**

For each assertion:

| Status            | Condition                               | Action                                     |
| ----------------- | --------------------------------------- | ------------------------------------------ |
| **Covered**       | Test link exists and resolves to a file | Verify in Step 4                           |
| **Missing link**  | `[test]` selected with no path          | Must add test evidence link                |
| **Broken link**   | Link present but file doesn't exist     | Must create test file                      |
| **No assertions** | Spec has no typed assertions            | Spec needs work first — do not write tests |

Treat an explicitly supplied untagged test assertion as a missing-link assertion. It proceeds through assertion typing and scaffold generation; an untagged assertion absent from the supplied selected set remains outside this workflow.

For a decision target, skip evidence-link and filename checks. Report a rule as covered when its existing assertion-type tag matches the type selected by the complete methodology procedure, and as needing update when the tag is absent or mismatched.

**Legacy filename check:** For every **Covered** link above, verify the filename encodes assertion type and execution level. A file that provides coverage but lacks canonical naming is an imperfection — the test exists but its classification is opaque.

| Language   | Canonical pattern                                 | Legacy (fails check)                                                    |
| ---------- | ------------------------------------------------- | ----------------------------------------------------------------------- |
| TypeScript | `<subject>.<evidence>.<level>[.<runner>].test.ts` | `*.unit.test.ts`, `*.integration.test.ts`, `*.e2e.test.ts`, `*.spec.ts` |
| Python     | `test_<subject>.<evidence>.<level>[.<runner>].py` | `test_*.py` with no evidence or level segment                           |
| Rust       | `<subject>.<evidence>.<level>[.<runner>].rs`      | `*_test.rs` or `test_*.rs` with no evidence or level segment            |
| Go         | `<subject>.<evidence>.<level>[.<runner>]_test.go` | `*_test.go` with no evidence or level segment                           |

evidence ∈ {scenario, mapping, conformance, property, compliance} — level ∈ {l1, l2, l3}

If any covered link uses a legacy name: flag as imperfection per the global imperfection protocol and surface via AskUserQuestion before proceeding.

Report the evidence gap summary before proceeding.

</step>

<step name="route_methodology">

**Step 4: Route each assertion through the methodology**

For each assertion that needs a test, apply `<testing_methodology>`'s five-stage `<router>`:

0. **Source-contract-first gate** — read the assertion, the existing or planned test, and the code under test; state the production contract the evidence exercises; fix missing source-owned contracts before writing test predicates.
1. **Stage 1** — What evidence does this assertion demand?
2. **Stage 2** — At what execution level does that evidence live? Respect ADRs/PDRs loaded from tree context.
3. **Stages 3–5** — If `L1` is viable, classify the code, check real system viability, and match an exception if needed.

Document the routing decision for each assertion.

In decision-rule mode, stop after assertion-type selection. Execution level, language expression, test files, and evidence links belong to the implementing spec assertion that realizes the rule.

</step>

<step name="generate_scaffolds">

**Step 5: Generate test scaffolds**

For each assertion needing a new test:

1. Determine test pattern from assertion type (Step 2 table).
2. Determine execution level from methodology routing (Step 4).
3. Create the test file in the spec node's `tests/` directory.
4. Name the file using `<naming_and_co_location>`.
5. Scaffold the test structure based on assertion type and language-specific patterns.

Delegate language-specific structure to `/test-go` or `/test-python` or `/test-rust` or `/test-typescript`.

In decision-rule mode, update each `### Testing` rule with exactly one selected assertion-type tag and create no test scaffold. Continue directly to the report step.

**Specified nodes:** If the implementation module doesn't exist yet, test files will fail on import. This is expected — the test is a declaration of what the implementation must satisfy. Add the node's path to `spx/EXCLUDE`. The `spx` CLI skips excluded nodes when running `spx test passing`. Remove the entry when implementation begins. Use `/understand`'s excluded-node guidance for the convention.

</step>

<step name="update_links">

**Step 6: Update spec assertion links**

After creating test files, move each newly typed assertion under its canonical assertion-type heading and update the spec to add `([test](tests/{filename}))` links for each new assertion-test pair. This skill never selects or writes eval or audit evidence.

In decision-rule mode, add no evidence link to the ADR/PDR. The implementing specs own the linked executable evidence.

</step>

<step name="report">

**Step 7: Report evidence summary**

Report which assertions have tests, which do not, and which are stale:

```markdown
| # | Assertion | Type     | Level | Test File | Status  |
| - | --------- | -------- | ----- | --------- | ------- |
| 1 | {text}    | Scenario | l1    | {file}    | Covered |
| 2 | {text}    | Property | l1    | —         | Missing |
```

</step>

</workflow>

<cross_cutting_assertions>

When an assertion lives in an ancestor node, determine where the test evidence should go:

- If the assertion is about behavior that a specific child node implements, the test belongs in that child's `tests/` directory.
- If the assertion spans multiple children, the test belongs in the ancestor's `tests/` directory at a higher level.
- If an ancestor accumulates too many cross-cutting assertions, flag it for `/decompose`; the decomposition workflow owns shared-enabler extraction and index placement.

</cross_cutting_assertions>

<failure_modes>

**Infrastructure encoded the verdict**

- **What happened:** A harness returned booleans whose names and implementations already decided whether each requirement passed, leaving the linked test to assert only that boolean.
- **Why it failed:** The predicate moved out of the linked test, so reversing the linked assertion no longer changed the harness behavior and the spec-to-test evidence chain became indirect.
- **How to avoid:** Infrastructure exposes observations, resources, and recording collaborators. The linked test alone applies assertion APIs and owns the behavioral predicate.

**Implementation logic generated both actual and expected values**

- **What happened:** Expected outputs came from the same table, parser, branch logic, or collaborator verdict method that produced the actual output.
- **Why it failed:** The oracle repeated the implementation; the same defect changed both sides and the test stayed green.
- **How to avoid:** Derive expectations from an independent contract, source-owned finite mapping, generated invariant, or real-system response.

**Test-local bindings laundered domain truth**

- **What happened:** Constants, local functions, fixture parameters, or renamed variables stored expected outputs, boundary bags, runner settings, or source-owned singleton values in the executed test file.
- **Why it failed:** Renaming the declaration preserved test ownership of data and configuration, hiding an invalid seam instead of correcting it.
- **How to avoid:** Move source truth to the production contract, variable domains to generators, execution policy to harnesses, and whole payloads to inert fixtures. Keep only the assertion flow in the test.

**A heading selected the assertion type**

- **What happened:** An `ALWAYS` or `NEVER` rule under a Compliance section was labeled `compliance`, or a universal rule was labeled `scenario`, without examining its quantifier and evidence domain.
- **Why it failed:** Section organization replaced semantic classification, producing an evidence strategy that could not prove the claim.
- **How to avoid:** Read the quantifier first, then select mapping, conformance, compliance, or property from the universal domain, oracle, or violating boundary.

**A finite example bag impersonated stronger evidence**

- **What happened:** A few hand-picked cases were presented as a mapping over a complete domain or as a property over an open domain.
- **Why it failed:** The examples established only those cases; they provided neither source-owned finite completeness nor generated open-domain coverage.
- **How to avoid:** Import the complete finite domain from its source owner for mapping, or use a meaningful shrinking generator for property evidence.

**A mock replaced the behavior under assertion**

- **What happened:** A framework mock, fake repository, monkeypatch, intercepted response, or stub replaced persistence, transport, or another boundary while the test claimed that boundary worked.
- **Why it failed:** The test proved the replacement's configured response instead of production behavior.
- **How to avoid:** Use the real system at the lowest viable level. Permit a controlled implementation only after one Stage 5 exception matches, and preserve the real behavior boundary the assertion claims.

**Tool choice determined execution level**

- **What happened:** Filesystem, subprocess, browser, or runner labels automatically promoted a cheap local test to a heavier level.
- **Why it failed:** Runner identity and dependency category replaced measured execution pain, availability, safety, determinism, and observability.
- **How to avoid:** Classify level from operational reality. Temporary files and standard local tools remain `L1` when cheap and dependable; remote or credentialed systems remain `L3` regardless of runner.

**Property syntax wrapped a constant domain**

- **What happened:** A property framework generated one constant or selected from a copied handful of literals while the test claimed an open-domain invariant.
- **Why it failed:** Framework syntax added no domain variation, shrinking value, or systematic exploration.
- **How to avoid:** Generate a meaningful variable domain with replayable seeds and shrinking, or reclassify the evidence to the finite assertion type it actually supports.

</failure_modes>

<success_criteria>

Testing output is sound when:

- Every decision `### Testing` rule carries exactly one assertion-type tag selected from its quantifier plus the universal claim's domain, contract-oracle, or violating-rule shape, and no executable evidence link.
- Every explicitly supplied untagged test assertion is moved under its selected assertion-type heading and receives one canonical `[test](path)` link; unrelated untagged assertions remain unchanged.
- Every test file name encodes the assertion type and execution level; it includes a runner token only when the canonical model requires one.
- Every test asserts source-coupled behavior with no test-owned data or configuration in the assertion file.
- Every property test uses a meaningful generated domain and reports both the seed and replay path on failure.
- Every test double maps to one of the seven exception cases and preserves the behavior boundary the assertion claims.
- Every spec assertion that receives test evidence links to the evidence file that verifies it.

</success_criteria>
