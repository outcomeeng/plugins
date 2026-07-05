# Testing Methodology Reference

This file is the local methodology payload for the `test` skill. Keep it self-contained inside the plugin.

## Table of contents

- [Non-negotiable rules](#non-negotiable-rules)
- [Why tests exist](#why-tests-exist)
- [Before writing any test](#before-writing-any-test)
- [Source-contract-first gate](#source-contract-first-gate)
- [Test files own assertions, not data or configuration](#test-files-own-assertions-not-data-or-configuration)
- [The evidence trap](#the-evidence-trap)
- [Separate the axes](#separate-the-axes)
- [Assertion types](#assertion-types)
- [Execution levels](#execution-levels)
- [Five-stage router](#five-stage-router)
- [Test double taxonomy](#test-double-taxonomy)
- [Trust the library when it already owns the problem](#trust-the-library-when-it-already-owns-the-problem)
- [Four-part progression](#four-part-progression)
- [Debuggability rules](#debuggability-rules)
- [Anti-patterns](#anti-patterns)
- [Naming and co-location](#naming-and-co-location)

## Non-negotiable rules

- No mocking. Ever.
- Reality is the oracle. Prefer real systems whenever they are cheap, deterministic, safe, and observable enough to prove the behavior.
- Test doubles are exceptions, not defaults. The seven exception cases in Stage 5 are the only legitimate reasons to avoid the real dependency.
- Route every assertion through all five stages. Do not skip ahead.
- Name tests by subject, assertion type, execution level, and optional runner.
- Derive the assertion type from the shape of the assertion, never from the section a rule appears in. A MUST/NEVER rule under a `## Compliance` heading does not imply the `compliance` assertion type.
- This skill is the single authority for selecting an assertion's verification type and assertion type. A decision-record author routes each rule through it to record the assertion type its `### Testing` rule carries; a test author routes each spec assertion through it to select the assertion type. No agent hand-picks either.

## Why tests exist

Every test should serve at least one of these purposes:

1. **Prove behavior**: confirm that a requirement, scenario, or invariant holds in production-relevant execution.
2. **Catch failures early**: detect concrete breakages before users, operators, or downstream systems see them.
3. **Improve debugging economics**: place evidence at the lowest level that can prove the claim so diagnosis is fast when something breaks.

If a test serves none of these purposes, delete it.

## Before writing any test

Every test must answer these questions:

1. What production behavior could be wrong?
2. If this test passes, what does it prove about the real system?
3. What failure would this catch before users see it?

If all three cannot be answered, stop.

## Source-contract-first gate

Before writing or repairing evidence, read the spec assertion, the existing or planned test, and the code under test. State the production contract the test will exercise:

- source-owned values: protocol tokens, status values, command names, route names, schema fields, rule identifiers, message identifiers, registries, constructors, typed factories, or public vocabulary
- observable behavior: pure functions, constructors, dataclasses, enums, schemas, protocols, typed collaborators, emitted artifacts, or side-effect boundaries
- oracle: expected output derived from the input, an independent reference, a source-owned contract, or a real system response

If the source does not expose the contract the assertion needs, fix the source contract first. Do not patch test predicates around a reviewer example, copy literals into tests, hide domain values in fixtures or generators, or mock away behavior the assertion claims to verify.

## Test files own assertions, not data or configuration

An executed test file is a typed assertion file. It owns the assertion flow: arrange the behavior through imported source contracts or infrastructure, execute the behavior, and assert the outcome. It does not own reusable values or execution policy.

Use these ownership rules before writing the test:

| Concern                          | Owner                                                                                                                      |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Test configuration               | A spec-governed harness: run counts, property seeds, retry policy, resource setup, cleanup, dependency checks, diagnostics |
| Variable test input domains      | A spec-governed generator that varies, composes, shrinks, or systematically explores meaningful alternatives               |
| Source-owned vocabulary or shape | The production module, runtime, framework, or protocol package that owns the contract                                      |
| Whole-payload samples            | Inert fixtures read, copied, or passed by path when the complete payload shape matters                                     |
| Curated LLM/eval cases           | Eval case data when generating the case set as JSONL would be wasteful and not tractable                                   |

Do not create variables, constants, fixture parameters, or property-generated parameters in the executed test file. Every value or configuration choice those bindings would carry belongs in a source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, or curated eval case data when generation is wasteful and not tractable. Local functions are rejected when they own runner settings, boundary bags, expected outputs, fixture paths, generated domains, reusable setup, diagnostics, harness behavior, or source-owned singleton shapes. Naming a value or wrapping it in a local function does not make it evidence. A renamed test-local declaration is still owned by the wrong layer.

Property-based tests need reproducible failures. Use a harness that owns seed selection, run-count policy, and failure diagnostics. The failure output must include the seed and replay path so the failing generated case can be reproduced. Do not put seeds or run counts in the test file; amortize those choices in the harness.

## The evidence trap

Agents often skip the evidence question. They see code and decide to test the shape of the code instead of the behavior that matters.

- **Wrong**: See `OrderProcessor` calling `repository.save()`, create an `InMemoryRepository`, and claim persistence is covered.
- **Right**: Ask what evidence is needed, realize the question is whether orders persist correctly, then test with a real database at the lowest level that can prove persistence.

## Separate the axes

Do not collapse evidence, execution pain, and tool choice into one label.

- **Assertion type** describes what kind of claim the test proves.
- **Execution level** describes how painful the test is to run.
- **Runner** describes which tool executes the test.

Examples:

- A temporary-directory test can still be `L1` when the machine almost certainly has a filesystem, the setup cost is trivial, and the runtime is cheap.
- A Playwright test can be `L2` or `L3` depending on whether it uses only local infrastructure or requires remote systems and credentials.

The runner does not define the level, and the level does not define the runner.

## Assertion types

Use evidence terms that describe what the test proves:

- `scenario`: an end-to-end behavior within the chosen level
- `mapping`: inputs map to outputs or requests map to actions
- `conformance`: behavior matches an external or internal contract
- `property`: an invariant holds across many generated cases
- `compliance`: required rules, boundaries, or safety constraints hold

## Execution levels

Use `L1`, `L2`, and `L3` to describe execution pain and environment dependence.

- `L1`: almost certainly available, cheap, local, safe, deterministic
- `L2`: real but heavier local infrastructure or setup
- `L3`: remote, shared, credentialed, or network-dependent systems

Examples:

- `L1`: pure logic, tmp files, normal filesystem work, git, repo-required test runners, and standard subprocesses expected on a working machine
- `L2`: local dev servers, Docker, browsers, product-specific binaries, full bootstrap or install costs, and other real local dependencies that are slower or less ubiquitous
- `L3`: network access, shared environments, live third-party services, and anything requiring credentials

## Five-stage router

Before writing any test, route through all five stages.

| Stage | Outcome                                              | Next Step                                                                           |
| ----- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1     | Evidence identified                                  | Stage 2                                                                             |
| 2     | `L2` or `L3` required                                | Use real dependencies at that level. DONE.                                          |
| 2     | `L1` appropriate                                     | Stage 3                                                                             |
| 3A    | Pure computation                                     | Test directly at `L1`. No doubles. DONE.                                            |
| 3B    | Can extract the pure part                            | Extract, test pure at `L1`, cover boundary behavior at the right outer level. DONE. |
| 3C    | Glue or orchestration code                           | Stage 4                                                                             |
| 4     | Real system works: reliable, safe, cheap, observable | Use the real system at the current level. DONE.                                     |
| 4     | Real system does not work for this evidence          | Stage 5                                                                             |
| 5     | Exception case matches                               | Use the appropriate double and record the exception. DONE.                          |
| 5     | No exception matches                                 | Move the test outward to the lowest real level that can prove it. DONE.             |

### Stage 1: What evidence is needed?

Answer these questions before writing the test:

1. What behavior could actually fail for users, operators, or downstream systems?
2. If this test passes, what does that prove about the real system?
3. What concrete failure would reach production without this test?

**Quantifier first.** Read whether the claim is universal or existential before anything else — it bounds the assertion type:

- A **universal** claim holds over every case (ALWAYS / NEVER / "for all" / "for every" / "no input"). Its evidence is `mapping`, `conformance`, `compliance`, or `property` — never `scenario`. A scenario proves one case passes; it cannot establish a claim about every case.
- An **existential** claim describes one specific interaction ("given this case, when …, then …"). Its evidence is `scenario`.

Within the universal branch, pick by what the evidence proves:

- `mapping` for a deterministic input-output transform over a finite, source-owned domain
- `conformance` for a match against an external or internal contract or protocol
- `compliance` for a rule exercised against violating cases (a real violating fixture or rule oracle)
- `property` for an invariant across an open or infinite input space

The assertion type follows what the claim proves, not the heading it sits under. A rule in a decision record's `## Compliance` section is classified here by its claim shape — it does not inherit the `compliance` assertion type from the section title, and an ALWAYS/NEVER rule is a universal, so it never takes `scenario`.

**Boundary-validation routing (a universal special case).** An assertion that rejects values outside a predicate is universal; route it by the structure of the invalid set:

- The invalid set is open or infinite — arbitrary strings, identifiers, timestamps, keys, generated names — so the assertion type is `property`. The evidence generates values from across the space outside the predicate.
- The invalid set is closed, finite, and source-owned — enum variants, a defined protocol set, registry members — so the assertion type is `mapping`. The evidence parameterizes over every source-owned invalid member.

One rule yields one assertion type. A `property`-floor rule is not satisfied by a finite mapping over a hand-picked subset of an open space: a hand-picked bag of invalid values is neither the property's generated domain nor the mapping's complete source-owned set.

### Stage 2: At what level does that evidence live?

Choose the level from operational reality, not from habit.

**Factor 1: What does the spec promise?**

| Spec Promise                                    | Minimum Level | Why                             |
| ----------------------------------------------- | ------------- | ------------------------------- |
| "Prices are calculated correctly"               | `L1`          | Pure calculation                |
| "User can export data as CSV"                   | `L1`          | File I/O with tmp dirs is cheap |
| "CLI processes a Hugo site"                     | `L2`          | Product-specific binary         |
| "Database query returns users"                  | `L2`          | Real database required          |
| "User can complete checkout with live provider" | `L3`          | Remote provider required        |
| "Works in Safari against the live site"         | `L3`          | Real browser and remote system  |

**Factor 2: What dependencies are involved?**

| Dependency                          | Minimum Level |
| ----------------------------------- | ------------- |
| None, pure function                 | `L1`          |
| File system with tmp dirs           | `L1`          |
| Standard dev tools: git, node, curl | `L1`          |
| Database                            | `L2`          |
| External HTTP API                   | `L2` or `L3`  |
| Product-specific binary             | `L2`          |
| Browser API                         | `L2` or `L3`  |
| Live third-party service            | `L3`          |
| Real credentials                    | `L3`          |

**Factor 3: How much value does `L1` add?**

| Code Type                              | `L1` Value                                 |
| -------------------------------------- | ------------------------------------------ |
| Your logic: algorithms, parsers, rules | High - test thoroughly                     |
| Library wiring: Zod, YAML, CLI parsing | Low - trust the library                    |
| Simple orchestration code              | Low - outer-level coverage is often enough |

**Factor 4: Will lower-level evidence speed up debugging?**

| Scenario                                        | Add `L1`? | Reason                                 |
| ----------------------------------------------- | --------- | -------------------------------------- |
| `L2` database-backed test fails on pricing math | Yes       | `L1` isolates the algorithm            |
| `L2` flag parsing around a mature library fails | No        | Check your usage and boundary          |
| `L3` checkout flow fails                        | Maybe     | Add `L1` if the local logic is complex |

**Factor 5: Where does achievable confidence live?**

| What to Know                     | Achievable At |
| -------------------------------- | ------------- |
| Your math is correct             | `L1`          |
| Your SQL is valid                | `L2`          |
| The API accepts your requests    | `L2` or `L3`  |
| Users can complete the live flow | `L3`          |

Decision:

- Evidence lives at `L3` -> use the real environment there.
- Evidence lives at `L2` -> use real dependencies there.
- Evidence lives at `L1` -> go to Stage 3.

If the evidence lives at `L2` or `L3`, stop. Use the real dependencies at that level.

### Stage 3: What kind of `L1` code is this?

**3A: Pure computation**

Given inputs, compute outputs. No external state, no side effects. Test directly at `L1`. No doubles needed. DONE.

**3B: Code with dependencies, but the pure part can be extracted**

Extract the computation from the dependency interaction. Test the pure part at `L1`, and cover the boundary behavior at the right outer level. DONE.

**3C: Glue or orchestration code**

The behavior is the interaction with the dependency. Go to Stage 4.

### Stage 4: Can the real system produce the behavior?

| Question                                                | If YES   | If NO         |
| ------------------------------------------------------- | -------- | ------------- |
| Reliably? Deterministic and not flaky                   | Continue | Go to Stage 5 |
| Safely? No destructive side effect for normal test runs | Continue | Go to Stage 5 |
| Cheaply? No painful runtime or setup cost               | Continue | Go to Stage 5 |
| Observably? The needed assertions are visible           | Continue | Go to Stage 5 |

If all four answers are yes, use the real system at the current level. DONE.

### Stage 5: Which exception applies?

Only now may a test double be used. Match a specific exception.

| Exception                | When                                                                                | Double Type                            |
| ------------------------ | ----------------------------------------------------------------------------------- | -------------------------------------- |
| 1. Failure simulation    | Need specific failures: timeouts, resets, throttling, full disks, permission errors | Stub returning predetermined errors    |
| 2. Interaction protocols | Correctness depends on the sequence or shape of calls                               | Spy that records calls                 |
| 3. Time and concurrency  | Need deterministic control of clocks, retries, scheduling, races, debounce          | Fake clock or controllable scheduler   |
| 4. Safety                | Real system is destructive: charges money, sends mail, mutates shared admin state   | Stub that records but does not execute |
| 5. Combinatorial cost    | The real dependency makes broad evidence prohibitively expensive                    | Configurable fake                      |
| 6. Observability         | The required signal is hidden by the real dependency                                | Spy that records boundary details      |
| 7. Contract probes       | Need controlled verification at a contract boundary                                 | Contract stub                          |

If no exception applies, do not use a double. Move outward to the lowest real level that can prove the behavior.

## Test double taxonomy

| Double Type | Purpose                           | Use For                                     |
| ----------- | --------------------------------- | ------------------------------------------- |
| **Stub**    | Returns predetermined responses   | Failure simulation, safety, contract probes |
| **Spy**     | Records calls for verification    | Interaction protocols, observability        |
| **Fake**    | Simplified working implementation | Time control, combinatorial cost            |
| **Dummy**   | Placeholder that is never called  | Satisfying type requirements                |

Framework mocks stay forbidden. If call recording is required, supply a spy through dependency injection.

## Trust the library when it already owns the problem

Do not re-prove behavior that a well-scoped library already owns unless your product adds logic around it.

Focus test effort on:

- your orchestration
- your mapping logic
- your invariants
- your failure handling
- your boundary behavior

## Four-part progression

| Phase                   | What Is Being Tested                | Confidence Gain  |
| ----------------------- | ----------------------------------- | ---------------- |
| 1. Typical cases        | Happy paths and common scenarios    | Baseline         |
| 2. Edge and boundary    | Limits, special values, error cases | Robustness       |
| 3. Systematic coverage  | Loops, states, combinations         | Completeness     |
| 4. Property-based tests | Invariants across generated inputs  | Deep correctness |

Small pure functions often need phases 1 and 2. Complex algorithms often need all four. Glue code often needs phase 1 plus the correct outer-level evidence.

Property-based tests are mandatory candidates for:

- parsers and serializers
- mathematical transformations
- seed-driven generators
- normalization rules
- algorithms with edge cases that are hard to enumerate

## Debuggability rules

A good test failure narrows the search space.

- Put evidence at the lowest level that can prove the claim.
- Prefer direct assertions over indirect side-channel checks.
- Keep setup proportional to the evidence.
- Redesign the test if a failure would not reveal what broke.

## Anti-patterns

Avoid these patterns:

- Writing tests because a layer or file class "should have tests"
- Choosing a label first and then searching for evidence to fit it
- Promoting cheap local-real tests into slower schedules just because they touch the filesystem, git, or subprocesses
- Treating browser coverage as inherently remote or credentialed
- Treating runner choice as a proxy for cost or realism
- Adding doubles when the real dependency is already cheap, deterministic, and observable
- Writing tests that cannot name the failure they would catch

## Naming and co-location

Keep tests next to the governing spec work, and name them for what they prove and how painful they are to run.

Canonical filename model:

- TypeScript and JavaScript: `<subject>.<evidence>.<level>[.<runner>].test.ts`
- Python: `test_<subject>.<evidence>.<level>[.<runner>].py`
- Rust: `<subject>.<evidence>.<level>[.<runner>].rs`
- Go: `<subject>.<evidence>.<level>[.<runner>]_test.go` (Go recognizes a test file only by the `_test.go` suffix, so the test marker is the suffix, not a `.test.` segment)

Canonical evidence tokens:

- `scenario`
- `mapping`
- `conformance`
- `property`
- `compliance`

Canonical level tokens:

- `l1`
- `l2`
- `l3`

Canonical runner rule:

- Omit the runner token for the default runner.
- Add an explicit token for non-default runners.
- `playwright` is the explicit non-default runner example.

Examples:

- `dispatch.mapping.l1.test.ts`
- `browser-auth.scenario.l2.playwright.test.ts`
- `test_seeded_generators.property.l1.py`
- `session_token.scenario.l1.rs`
- `login_flow.scenario.l3.tokio.rs`
- `context_bar.property.l1_test.go`
