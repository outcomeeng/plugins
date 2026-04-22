# Testing Methodology Reference

This file is the local methodology payload for the `testing` skill. Keep it self-contained inside the plugin.

## Non-negotiable rules

- No mocking. Ever.
- Reality is the oracle. Prefer real systems whenever they are cheap, deterministic, safe, and observable enough to prove the behavior.
- Test doubles are exceptions, not defaults. The seven exception cases in Stage 5 are the only legitimate reasons to avoid the real dependency.
- Route every assertion through all five stages. Do not skip ahead.
- Name tests by subject, evidence mode, execution level, and optional runner.

## Why tests exist

Every test should serve at least one of these purposes:

1. **Prove behavior**: confirm that a requirement, scenario, or invariant holds in production-relevant execution.
2. **Catch failures early**: detect concrete breakages before users, operators, or downstream systems see them.
3. **Improve debugging economics**: place evidence at the lowest level that can prove the claim so diagnosis is fast when something breaks.

If a test serves none of these purposes, delete it.

## Before you write any test

Every test must answer these questions:

1. What production behavior could be wrong?
2. If this test passes, what does it prove about the real system?
3. What failure would this catch before users see it?

If you cannot answer all three, stop.

## The evidence trap

Agents often skip the evidence question. They see code and decide to test the shape of the code instead of the behavior that matters.

- **Wrong**: See `OrderProcessor` calling `repository.save()`, create an `InMemoryRepository`, and claim persistence is covered.
- **Right**: Ask what evidence is needed, realize the question is whether orders persist correctly, then test with a real database at the lowest level that can prove persistence.

## Separate the axes

Do not collapse evidence, execution pain, and tool choice into one label.

- **Evidence mode** describes what kind of proof the test provides.
- **Execution level** describes how painful the test is to run.
- **Runner** describes which tool executes the test.

Examples:

- A temporary-directory test can still be `L1` when the machine almost certainly has a filesystem, the setup cost is trivial, and the runtime is cheap.
- A Playwright test can be `L2` or `L3` depending on whether it uses only local infrastructure or requires remote systems and credentials.

The runner does not define the level, and the level does not define the runner.

## Evidence modes

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
- `L2`: local dev servers, Docker, browsers, project-specific binaries, full bootstrap or install costs, and other real local dependencies that are slower or less ubiquitous
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
| 4     | Real system does not work for this proof             | Stage 5                                                                             |
| 5     | Exception case matches                               | Use the appropriate double and record the exception. DONE.                          |
| 5     | No exception matches                                 | Move the test outward to the lowest real level that can prove it. DONE.             |

### Stage 1: What evidence do you need?

Answer these questions before writing the test:

1. What behavior could actually fail for users, operators, or downstream systems?
2. If this test passes, what does that prove about the real system?
3. What concrete failure would reach production without this test?

Use the evidence mode that matches the proof:

- `scenario` for user-visible or workflow-visible behavior
- `mapping` for deterministic input-output or request-action transforms
- `conformance` for contracts and protocol boundaries
- `property` for invariants across a large input space
- `compliance` for rules, boundaries, and safety constraints

### Stage 2: At what level does that evidence live?

Choose the level from operational reality, not from habit.

**Factor 1: What does the spec promise?**

| Spec Promise                                    | Minimum Level | Why                             |
| ----------------------------------------------- | ------------- | ------------------------------- |
| "Prices are calculated correctly"               | `L1`          | Pure calculation                |
| "User can export data as CSV"                   | `L1`          | File I/O with tmp dirs is cheap |
| "CLI processes a Hugo site"                     | `L2`          | Project-specific binary         |
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
| Project-specific binary             | `L2`          |
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

| You Need to Know...              | Achievable At |
| -------------------------------- | ------------- |
| Your math is correct             | `L1`          |
| Your SQL is valid                | `L2`          |
| The API accepts your requests    | `L2` or `L3`  |
| Users can complete the live flow | `L3`          |

Decision:

- Evidence lives at `L3` -> use the real environment there.
- Evidence lives at `L2` -> use real dependencies there.
- Evidence lives at `L1` -> go to Stage 3.

If the proof lives at `L2` or `L3`, stop. Use the real dependencies at that level.

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

Only now may you use a test double. Match a specific exception.

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

| Phase                   | What You Are Testing                | Confidence Gain  |
| ----------------------- | ----------------------------------- | ---------------- |
| 1. Typical cases        | Happy paths and common scenarios    | Baseline         |
| 2. Edge and boundary    | Limits, special values, error cases | Robustness       |
| 3. Systematic coverage  | Loops, states, combinations         | Completeness     |
| 4. Property-based tests | Invariants across generated inputs  | Deep correctness |

Simple utilities often need phases 1 and 2. Complex algorithms often need all four. Glue code often needs phase 1 plus the correct outer-level proof.

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
- Keep setup proportional to the proof.
- Redesign the test if a failure would not tell you what broke.

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
