# Testing Router

This document decides where evidence lives, what execution level is justified, and when a test double is legitimate.

## Essential Principles

- **No mocking. Ever.** If you feel forced to mock, redesign with dependency injection or test at the level where reality can answer the question.
- **Reality is the oracle.** Prefer real systems whenever they are reliable, safe, cheap enough, and observable enough.
- **Test doubles are exceptions.** The seven exception cases below are the only legitimate uses.
- **Do not skip ahead.** Route every test through all five stages.

---

## Five-Stage Router

Before writing any test, route through all five stages.

| Stage | Outcome                                              | Next Step                                                                           |
| ----- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1     | Evidence identified                                  | Stage 2                                                                             |
| 2     | `L2` or `L3` required                                | Use real dependencies at that level. Done.                                          |
| 2     | `L1` appropriate                                     | Stage 3                                                                             |
| 3A    | Pure computation                                     | Test directly at `L1`. No doubles. Done.                                            |
| 3B    | Can extract the pure part                            | Extract, test pure at `L1`, cover boundary behavior at the right outer level. Done. |
| 3C    | Glue or orchestration code                           | Stage 4                                                                             |
| 4     | Real system works: reliable, safe, cheap, observable | Use the real system at the current level. Done.                                     |
| 4     | Real system does not work for this proof             | Stage 5                                                                             |
| 5     | Exception case matches                               | Use the matching double and record the exception. Done.                             |
| 5     | No exception matches                                 | Move the test outward to the lowest real level that can prove it. Done.             |

### Stage 1: What Evidence Do You Need?

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

### Stage 2: At What Level Does the Evidence Live?

Choose the level from operational reality, not from habit.

#### Factor 1: What Does the Spec Promise?

| Spec promise                                  | Minimum level | Why                             |
| --------------------------------------------- | ------------- | ------------------------------- |
| Prices are calculated correctly               | `L1`          | Pure calculation                |
| User can export data as CSV                   | `L1`          | File I/O with tmp dirs is cheap |
| CLI processes a Hugo site                     | `L2`          | Project-specific binary         |
| Database query returns users                  | `L2`          | Real database required          |
| User can complete checkout with live provider | `L3`          | Remote provider required        |
| Works in Safari against the live site         | `L3`          | Real browser and remote system  |

#### Factor 2: What Dependencies Are Involved?

| Dependency                          | Minimum level |
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

#### Factor 3: How Much Value Does `L1` Add?

| Code type                              | `L1` value                                 |
| -------------------------------------- | ------------------------------------------ |
| Your logic: algorithms, parsers, rules | High - test thoroughly                     |
| Library wiring: Zod, YAML, CLI parsing | Low - trust the library                    |
| Simple orchestration code              | Low - outer-level coverage is often enough |

#### Factor 4: Will Lower-Level Evidence Speed Up Debugging?

| Scenario                                        | Add `L1`? | Reason                                     |
| ----------------------------------------------- | --------- | ------------------------------------------ |
| `L2` database-backed test fails on pricing math | Yes       | `L1` isolates the algorithm                |
| `L2` flag parsing around a mature library fails | No        | Check your usage and boundary              |
| `L3` checkout flow fails                        | Maybe     | Add `L1` if the local logic is complex     |
| `L3` browser clipboard behavior fails           | No        | The evidence lives in the real environment |

#### Factor 5: Where Does Achievable Confidence Live?

| You need to know...              | Achievable at |
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

### Level Definitions

#### `L1`

Almost certainly available, cheap, local, safe, deterministic.

Includes:

- pure logic
- tmp files and normal filesystem work
- git
- repo-required test runners
- standard subprocesses expected on a working machine

#### `L2`

Real but heavier local dependencies.

Includes:

- local dev servers
- Docker
- local browsers
- project-specific binaries
- fresh bootstrap or install costs
- other local dependencies that are materially slower or less ubiquitous

#### `L3`

Remote or credentialed dependencies.

Includes:

- network access
- shared environments
- live third-party systems
- any test that requires credentials

### Stage 3: What Kind of `L1` Code Is This?

#### 3A: Pure computation

Given inputs, compute outputs. No external state, no side effects. Test directly at `L1`. No doubles needed. Done.

#### 3B: Code with dependencies that can be split

Extract the pure part. Test the pure part at `L1`. Test the real boundary at the level where its evidence lives.

#### 3C: Glue or orchestration that cannot be split

The behavior is the interaction with the dependency. Move to Stage 4.

### Stage 4: Can the Real System Produce the Behavior?

| Question                                                | If yes   | If no         |
| ------------------------------------------------------- | -------- | ------------- |
| Reliably? Deterministic and not flaky                   | Continue | Go to Stage 5 |
| Safely? No destructive side effect for normal test runs | Continue | Go to Stage 5 |
| Cheaply? No painful runtime or setup cost               | Continue | Go to Stage 5 |
| Observably? The needed assertions are visible           | Continue | Go to Stage 5 |

If all four answers are yes, use the real system at the current level. Done.

### Stage 5: Which Exception Applies?

Only now may you consider a test double.

| Exception                | When                                                                                | Double type                            |
| ------------------------ | ----------------------------------------------------------------------------------- | -------------------------------------- |
| 1. Failure simulation    | Need specific failures: timeouts, resets, throttling, full disks, permission errors | Stub returning predetermined errors    |
| 2. Interaction protocols | Correctness depends on the sequence or shape of calls                               | Spy that records calls                 |
| 3. Time and concurrency  | Need deterministic control over clocks, retries, scheduling, races, debounce        | Fake clock or controllable scheduler   |
| 4. Safety                | Real system is destructive: charges money, sends mail, mutates shared admin state   | Stub that records but does not execute |
| 5. Combinatorial cost    | The real dependency makes broad evidence prohibitively expensive                    | Configurable fake                      |
| 6. Observability         | The required signal is hidden by the real dependency                                | Spy that records boundary details      |
| 7. Contract probes       | Need controlled verification at a contract boundary                                 | Contract stub                          |

If no exception applies, do not use a double. Move outward to the lowest real level that can prove the behavior.

---

## Test Double Taxonomy

| Double type | Purpose                           | Use for                                     |
| ----------- | --------------------------------- | ------------------------------------------- |
| **Stub**    | Returns predetermined responses   | Failure simulation, safety, contract probes |
| **Spy**     | Records calls for verification    | Interaction protocols, observability        |
| **Fake**    | Simplified working implementation | Time control, combinatorial cost            |
| **Dummy**   | Placeholder that is never called  | Satisfying type requirements                |

Framework mocks stay forbidden. If call recording is required, supply a spy through dependency injection.

---

## Trust the Library

Do not re-prove behavior that a mature parser, validator, or serializer already owns unless your product adds logic around it.

Focus test effort on:

- your orchestration
- your mapping logic
- your invariants
- your failure handling
- your boundary behavior

---

## Randomized and Property-Based Evidence

Use property-based tests when examples are too sparse to give confidence.

Strong candidates include:

- parsers and serializers
- seed-driven generators
- mapping layers with large input spaces
- normalization rules
- algorithmic transformations

Use named invariants. Keep the generators deterministic for the chosen level.

---

## Debuggability Rules

- Add narrower tests only when they shorten debugging time.
- Skip narrower tests when the environment owns the behavior.
- Put evidence at the lowest level that can prove the claim.
- Prefer direct assertions over indirect side-channel checks.
- Keep setup proportional to the proof.
- When an assertion lives only in `L2` or `L3`, do not force an `L1` proof that cannot answer the real question.

---

## Examples

### Clipboard

Clipboard behavior lives in the real browser environment. A local render-only check does not prove the copy action. Use `scenario + L3 + browser runner`.

### Pricing Engine

Complex pricing rules benefit from both:

- `property` or `mapping` checks at `L1` for the calculation logic
- `scenario` checks at `L2` or `L3` for the real flow that consumes the result

### Python CSV Export Script

A Python reporting script that writes CSV output to a temporary directory is still `L1`. The filesystem is cheap and local, and the proof is whether the real file is written with the expected structure. Use the real tmp directory, real file I/O, and a `scenario` or `mapping` test at `L1`.

### Rust Parser and CLI

A Rust manifest parser usually needs two layers of evidence:

- `property + L1` for round-trip or invariant checks on the parser and serializer logic
- `scenario + L2` for the compiled CLI over a real fixture workspace when the proof depends on the binary boundary
