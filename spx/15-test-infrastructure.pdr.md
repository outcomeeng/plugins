# Test Infrastructure

## Purpose

This decision governs what every product built on the Spec Tree methodology observably presents for its test code: where harnesses, generators, and inert fixtures live; what category of artifact they are; and what shape the spec tree takes to govern them. Methodology users — developers and agents building products against this methodology — see this as a guarantee about the product's own surface: every spec tree has the same canonical subtree for test infrastructure, and every implementation home is at a path users can predict from the product's language.

## Context

**Business impact:** Methodology users decide where to put a new harness, generator, or fixture every time they extend their product. If the methodology leaves that decision to local convention, every product invents its own answer, audits cannot detect drift, and skill-driven workflows generate guidance that contradicts itself across languages. A single canonical answer turns the decision into a lookup and makes the methodology's product surface uniform.

**Technical constraints:**

- The canonical filename model `<subject>.<evidence>.<level>[.<runner>]` declares one evidence type per test file. The contents of `spx/<node>/tests/` are typed assertion files. Harnesses, generators, and inert fixtures have nothing to assert — they exist to enable assertions — and cannot share that directory without violating the per-file evidence model.
- Test infrastructure is production code: it implements behavior, has interfaces consumers depend on, and breaks every downstream test if it drifts. It cannot live with shipping product code without conflating the two categories under build tools, dead-code analysis, and bundle minimization.
- Methodology users are language-diverse. The same product behavior must hold whether the product is TypeScript, Python, or Rust; per-language paths must be predictable from each language's package conventions.

## Decision

Every spec tree governed by this methodology presents a canonical test-infrastructure subtree at the top level. Methodology users observe and rely on this shape:

- A top-level enabler with slug `infrastructure`.
- Under it, an enabler with slug `testing`.
- Under that, exactly three enabler children with slugs `generators`, `fixtures`, `harnesses`.

The slugs are normative. The methodology never uses the term "support" in the testing context — the category methodology users see and reference is **infrastructure**.

Test-infrastructure implementations live in a sibling directory to product code, outside `spx/` and outside any `tests/` directory. The per-language path methodology users can expect:

| Language       | Product code                | Test-infrastructure home                                                                                                                                                                                                                                                                                    |
| -------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `src/` or product root      | `testing/` at project root, path-mapped to `@testing/`: `@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`                                                                                                                                                                              |
| **Python**     | `<package>/`                | `<package>_testing/`: `<package>_testing/harnesses/`, `<package>_testing/generators/`, `<package>_testing/fixtures/`. `<package>` is the product's Python package name (the importable identifier used in its `pyproject.toml`); illustrative example: `outcomeeng/` paired with `outcomeeng_testing/`      |
| **Rust**       | `src/` of the product crate | A separate workspace-member crate at `<product>-testing/` (Cargo package `<product>-testing`, Rust import path `<product>_testing`), declared as a `[dev-dependencies]` entry of consumers; modules `<product>_testing::harnesses::*`, `<product>_testing::generators::*`, `<product>_testing::fixtures::*` |

The Python and Rust rows use `<package>` / `<product>` placeholders because each product names its test-infrastructure directory after its own package or crate — the structural rule is uniform across products even when the name is not. TypeScript uses the literal `@testing/` path mapping because the alias is resolved by `tsconfig.json`, not by package name. When a new language plugin is created, its per-language normative path is added to this table.

## Rationale

Methodology users rely on three predictable properties: where to find a harness, generator, or fixture; what category of artifact it is; and how to add a new one. The decision above gives each property a single answer that holds across products.

**Why a sibling directory, not inside `tests/`.** Putting harnesses or fixtures in `tests/support/`, `tests/_support/`, `tests/helpers/`, or `tests/conftest.py` would mix ungoverned utility modules into a directory the canonical filename model declares contains only typed assertion files. Methodology users would lose the per-file evidence guarantee — and the harness chain in test-audit findings would carry false coupling credit.

**Why a sibling directory, not inside product code.** Putting harnesses in `src/testing/`, `product/testing/`, or similar would put test-only code on the build path. Methodology users would see their bundle minimization, dead-code analysis, and dependency audits conflate the two categories; the category boundary would become implicit and drift under refactoring.

**Why these slugs are normative.** Alternates fail to convey what the artifacts are. "Support" connotes ungoverned utility code — the opposite of production-code status. "Helpers" / "utilities" / "tools" carry the same connotation. Methodology users encountering "test infrastructure" know they are looking at production code that the spec tree governs; methodology users encountering "test support" reasonably assume they are looking at glue they can rewrite at will. The leaf slugs `generators`, `fixtures`, `harnesses` are the only three categories the methodology recognizes — every test-infrastructure artifact is exactly one of these.

## Trade-offs accepted

| Trade-off                                                                                    | Mitigation / reasoning                                                                                                                                                                |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Methodology users must remember a different path per language                                | The `standardizing-{lang}-tests` skill for each language documents that language's path; users consult one skill, not memorize three. The path is predictable from package naming.    |
| Existing products with `tests/support/`, `tests/fixtures/`, `tests/conftest.py` must migrate | Migration is a file move plus import-path update — a refactor, not a behavior change. Methodology users perform it once when they adopt this decision; the new paths are stable.      |
| The methodology mandates a specific subtree shape, not only categories                       | Normative slugs make `/aligning` enforceable: a missing `infrastructure → testing → {generators, fixtures, harnesses}` subtree is a deterministic compliance failure, not a judgment. |
| Rust workspace-member crate requires Cargo workspace configuration                           | Single-crate Rust products adopt the workspace layout as a one-time setup; the cost is bounded and pays back the first time test infrastructure changes.                              |

## Product invariants

- For every test-infrastructure artifact in any product built on this methodology, a corresponding spec node exists under `<root>/<NN>-infrastructure.enabler/<NN>-testing.enabler/<NN>-{generators|fixtures|harnesses}.enabler/`. Methodology users can derive a node path from the artifact, and vice versa.
- For every test file (matching `<subject>.<evidence>.<level>[.<runner>]`) that imports a test-infrastructure module, the import resolves to the language's normative path outside `spx/`. Methodology users can scan a test's imports and know whether each one is governed by this PDR.
- The dependency direction is one-way: test files import from test-infrastructure modules; product modules never import test-infrastructure modules. Methodology users can rely on a product's shipping code containing no references to its test infrastructure.

## Compliance

### Recognized by

- A top-level enabler with slug `infrastructure` exists in the spec tree.
- Under it, an enabler with slug `testing` exists.
- Under that, three enabler children with slugs `generators`, `fixtures`, `harnesses` exist.
- Test-infrastructure implementation lives at the language's normative path (TypeScript `@testing/*`, Python `<package>_testing/*`, Rust `<product>_testing::*` from a `<product>-testing` workspace-member crate).
- Test files in `spx/<node>/tests/` follow the canonical filename pattern `<subject>.<evidence>.<level>[.<runner>]` and contain only typed assertion code.

### MUST

- Every spec tree governed by this methodology contains the canonical subtree `infrastructure → testing → {generators, fixtures, harnesses}` with these exact slugs ([review])
- Test harness, generator, and fixture implementations live at the language's normative path outside `spx/` and outside any `tests/` directory ([review])
- Spec assertions for test-infrastructure artifacts pass the same code audit, test evidence audit, and architecture audit as any other production-code node ([review])
- The methodology — across skills, references, templates, and audit findings — uses the term "infrastructure" for this category and never "support" ([review])

### NEVER

- A `tests/` directory at any level of any spec tree contains a test harness, generator, fixture, or any non-test-assertion code — `tests/` contains only typed assertion files matching `<subject>.<evidence>.<level>[.<runner>]` ([review])
- The terms "test support", "test helpers", "test utilities", or "test tools" appear in the methodology, the language standards, or the audit skills as governing categories — these are anti-terms ([review])
- A test-infrastructure module is imported into a product module — the dependency direction is `tests → infrastructure`, never `product → infrastructure` ([review])
- A test file declares a value inside the test file itself and asserts against it as if it were a domain truth — this is the No Coupling tautology defined in `/auditing-tests` evidence-model.md and is rejected wherever it appears ([review])
