---
name: test-go
description: ALWAYS invoke this skill when writing or fixing tests for Go. NEVER write or repair Go tests without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, Bash(go test:*), Bash(go vet:*), Bash(go build:*), Bash(gofmt:*), Bash(staticcheck:*), Bash(golangci-lint:*)
---

{!% require_skill 'go:go-standards' %!}

{!% require_skill 'go:go-test-standards' %!}

{!% require_skill 'spec-tree:test' %!}

<objective>
Go test files that supply evidence, at the level and assertion type `/test` selects, for a spec-tree node's assertions.
</objective>

<prerequisites>
The `/test` router, `/go-standards`, and `/go-test-standards` are pre-loaded above.

Before writing or revising tests, also check:

1. `spx/local/go.md` at the repository root, if present
2. `spx/local/go-tests.md` at the repository root, if present

</prerequisites>

<mode_detection>
Determine the mode before editing:

| Mode  | Signal                                                                          | Action                                                                                  |
| ----- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Write | An assertion has no linked Go test, or `/verify` routed a new assertion to test | Follow `<workflow>`                                                                     |
| Fix   | An `/audit-go-tests` or `/audit-tests` verdict rejected existing Go evidence    | Follow `<fix_workflow>`, then rerun `<workflow>` steps 5 through 9 on the repaired file |
| Split | A rejected file carries more than one assertion type or execution level         | Separate it into one file per cell, then continue as Fix                                |

</mode_detection>

<fix_workflow>
Map each rejecting finding's property to the remediation it implies before editing:

| Finding property or rule | Remediation                                                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `coupling`               | call the governed function, type, package, or harness-built binary; remove the reassigned function variable or generated mock |
| `falsifiability`         | replace the severed seam with a hand-written implementation of the same interface; assert on observations                     |
| `alignment`              | exercise every clause of the assertion; match the evidence method to the assertion type                                       |
| `coverage`               | drive execution into the assertion-relevant path; remove `t.Skip` on a mandatory dependency                                   |
| `oracle-independence`    | derive the expectation from the spec, an exported constant of another package, an external schema, or a fixture               |
| `declarations`           | move the chosen data, expectation, or runner setting to its owner: source contract, generator, harness, or fixture            |
| `predicate-ownership`    | move the comparison and the `testing.T` failure call back into the `Test*` function or its subtest                            |
| `extraction_target`      | move the harness, generator, or fixture resolver into `internal/testinfra/`                                                   |
| `filename_policy`        | rename to `<subject>.<evidence>.<level>[.<runner>]_test.go`; add the `//go:build` constraint an `l2` or `l3` file needs       |

</fix_workflow>

<workflow>
1. Load the governing spec context before editing any co-located `spx/.../tests/` file.
2. Map each assertion to the assertion type and level chosen by `/test`.
3. Apply the `/test` source-contract-first gate: read the assertion, the existing or planned test, and the Go code under test; state the production contract the evidence exercises.
4. If the source does not expose the typed constant set, constructor, interface boundary, parser entry point, registry, schema, or observable behavior the assertion needs, fix the source contract before writing test predicates.
5. Use the `<router_mapping>` and examples in `/go-test-standards` to choose the Go implementation shape.
6. Keep every predicate and `testing.T` failure call in the linked `Test*` function or its `t.Run` subtest. Permit `:=`, `var`, `const`, closure, and property-generated parameters that only receive actual results, source contracts, generated values, harness observations, callback inputs, resource handles, or fixture paths; reject bindings that choose data, expectations, configuration, setup policy, generator domains, fixture contents, or verdict rules. A `t.Helper()` mark never moves a predicate into infrastructure.
7. Keep test infrastructure — harnesses, generators, and inert fixtures — in the canonical `internal/testinfra/` location prescribed by `/go-test-standards`. A repo-local overlay may route to a governing product spec or decision that explicitly amends this contract; the overlay does not redefine the location itself.
8. Put `//go:build l2` or `//go:build l3` on the first line of every Level 2 or Level 3 file, so `go test ./...` runs Level 1 alone.
9. Run the repository's Go validation commands before reporting the tests complete, or the fallback sequence `gofmt -l .`, `go vet ./...`, the repository's linter, and `go test -race ./...`. `allowed-tools` preapproves only the listed raw-tool fallbacks; a repository-canonical wrapper outside those patterns uses the runtime's normal per-call approval path, and a fallback is never selected merely to avoid that approval.

</workflow>

<router_mapping>
After running through `/test`, use the canonical mapping in `/go-test-standards`:

| Router Decision       | Go implementation summary                                                                |
| --------------------- | ---------------------------------------------------------------------------------------- |
| Stage 2 -> Level 1    | pure functions, `t.TempDir()`, hand-written interface implementations, in-cycle binaries |
| Stage 2 -> Level 2    | local services, containers, installed binaries                                           |
| Stage 2 -> Level 3    | remote APIs, deployed workflows, browser automation, shared environments                 |
| Stage 3A              | direct pure-function tests                                                               |
| Stage 3B              | extracted pure function plus outer boundary evidence                                     |
| Stage 5 exceptions    | controlled implementations that preserve the real seam                                   |
| compile-time contract | toolchain-oracle evidence                                                                |
| universal invariant   | property-based evidence through the `rapid` harness                                      |

</router_mapping>

<reference_guides>
All Go test examples are owned by `/go-test-standards`:

- `/go-test-standards` `<level_1_patterns>`
- `/go-test-standards` `<property_and_compile_time_patterns>`
- `/go-test-standards` `<level_2_patterns>`
- `/go-test-standards` `<level_3_patterns>`
- `/go-test-standards` `references/level-1.md`
- `/go-test-standards` `references/level-2.md`
- `/go-test-standards` `references/level-3.md`

</reference_guides>

<success_criteria>
Go test work is complete when:

- `/test` chose the assertion type and target level first
- the source-contract-first gate was applied before test predicates were written or repaired
- `/go-standards` and `/go-test-standards` were loaded before test code was written
- the test shape follows the canonical Go test standard and repo-local overlays
- executed `Test*` functions and subtests own every predicate and `testing.T` failure call
- test-file bindings introduce no case data, expectation, configuration, setup policy, generator domain, fixture content, or verdict rule
- controlled implementations preserve coupling to the real seam
- property claims use property-based testing through the harness
- compile-time claims use toolchain-oracle evidence
- Level 2 and Level 3 files carry their build constraint
- the repository's Go validation commands pass, or the fallback sequence in step 9 passes, with any unavailable tool named explicitly

</success_criteria>
