# Test Infrastructure

## Purpose

This decision governs where test harnesses, generators, and inert fixtures live, what category of artifact they are, and how the spec tree formalizes their governance. Every spec tree built on this methodology classifies these artifacts as production code, governs them through a mandatory canonical subtree, and places their implementation at a normative per-language path outside `spx/` and outside any `tests/` directory.

## Context

**Business impact:** Tests verify behavior only to the extent that their dependencies are themselves correct. Treating harnesses, generators, and fixtures as throwaway test-folder material leaves them ungoverned — nobody owns their interfaces, nobody audits their failure modes, and their silent drift breaks every downstream test at once. Specifying them as production code closes that gap and makes their quality auditable.

**Technical constraints:** The methodology's canonical filename model `<subject>.<evidence>.<level>[.<runner>]` puts one evidence type per file. The contents of `spx/<node>/tests/` are therefore typed assertion files. Harnesses (mediating module access), generators (producing valid inputs), and fixtures (inert input data) have nothing to assert — they exist to enable assertions. They cannot live inside `spx/<node>/tests/` without violating the per-file evidence model, and they cannot live inside product code without conflating ship-with-product code with test-only code.

## Decision

Test harnesses, generators, and inert fixtures are production code, governed by a mandatory canonical subtree of every spec tree:

- A top-level enabler with slug `infrastructure`.
- Under it, an enabler with slug `testing`.
- Under that, exactly three enabler children with slugs `generators`, `fixtures`, `harnesses`.

The slugs are normative. The methodology never uses the term "support" in the testing context — the category is **infrastructure**.

Implementation lives in a sibling directory to product code, outside `spx/` and outside any `tests/` directory. The per-language path is normative:

| Language       | Product code                | Test-infrastructure production code                                                                                                                                                                                                                                                                              |
| -------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `src/` or product root      | `testing/` at project root, path-mapped to `@testing/`: `@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`                                                                                                                                                                                   |
| **Python**     | `<package>/`                | `<package>_testing/`: `<package>_testing/harnesses/`, `<package>_testing/generators/`, `<package>_testing/fixtures/`. `<package>` is the product's Python package name (the importable identifier used in its `pyproject.toml`); illustrative example: `outcomeeng/` paired with `outcomeeng_testing/`           |
| **Rust**       | `src/` of the product crate | A separate workspace-member crate at `<product>-testing/` (Cargo package name `<product>-testing`, Rust import path `<product>_testing`), declared as a `[dev-dependencies]` entry of consumers; modules `<product>_testing::harnesses::*`, `<product>_testing::generators::*`, `<product>_testing::fixtures::*` |

The Python and Rust rows use a `<package>` / `<product>` placeholder because each product names its test-infrastructure directory after the product's package or crate; the structural rule is uniform across products even when the name is not. TypeScript uses the literal `@testing/` path mapping because the alias is resolved by the project's `tsconfig.json`, not by the package name. When a new language plugin is created, its per-language normative path is added to this table.

## Rationale

Three placement options were considered:

**Inside `tests/` (rejected).** Putting harnesses, helpers, or fixtures in `tests/support/`, `tests/_support/`, `tests/helpers/`, or `tests/conftest.py` mixes ungoverned utility modules into a directory the canonical filename model says contains only typed assertion files. The conflation hides the fact that these modules implement behavior and must be audited as production code; tests that depend on them get false coupling-credit through the harness chain.

**Inside product code (rejected).** Putting harnesses in `src/testing/`, `product/testing/`, or similar mixes test-only code with product-shipping code. Build pipelines, dead-code analysis, bundle minimization, and dependency audits then conflate the two categories. The category boundary becomes implicit and drifts under refactoring.

**Sibling location, named for test-infrastructure purpose (chosen).** A directory sibling to product code, with a name that signals its purpose, gives test-only production code an unambiguous home. The categorization is visible in the file system; build tooling can treat the sibling tree as test-only by path; spec assertions can reference the canonical subtree to govern its behavior; consumers' `[dev-dependencies]` or path mappings keep the directional dependency clear (`tests/* → infrastructure`, never `product/* → infrastructure`).

The choice of slugs is normative because alternates fail. "Support" connotes ungoverned utility code, the opposite of what these artifacts are. "Helpers" / "utilities" / "tools" carry the same connotation. "Test infrastructure" names the production-code category honestly; the leaf slugs `generators`, `fixtures`, `harnesses` are the only three categories the methodology recognizes — every test-infrastructure artifact is one of these.

## Trade-offs accepted

| Trade-off                                                                                    | Mitigation / reasoning                                                                                                                                                                |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Per-language paths must be remembered                                                        | The `standardizing-{lang}-tests` skills document each language's path; consumers do not memorize across languages, they consult the language-specific skill.                          |
| Existing products with `tests/support/`, `tests/fixtures/`, `tests/conftest.py` must migrate | Migration is a file move plus import-path update — a refactor, not a behavior change. The canonical paths are reachable from any existing layout.                                     |
| The methodology mandates a specific subtree shape, not only categories                       | Normative slugs make `/aligning` enforceable: a missing `infrastructure → testing → {generators, fixtures, harnesses}` subtree is a deterministic compliance failure, not a judgment. |
| Rust workspace-member crate requires Cargo workspace configuration                           | Single-crate Rust products that adopt this methodology adopt the workspace layout as a one-time setup; the cost is bounded and pays back the first time test infrastructure changes.  |

## Invariants

- Every test-infrastructure artifact corresponds to a spec node under `<root>/<NN>-infrastructure.enabler/<NN>-testing.enabler/<NN>-{generators|fixtures|harnesses}.enabler/`.
- Every test-infrastructure import in a test file resolves to the language's normative path outside `spx/`.
- The dependency direction is one-way: test files import from test-infrastructure modules; product modules never import test-infrastructure modules.

## Compliance

### Recognized by

- A top-level enabler with slug `infrastructure` exists in the spec tree.
- Under it, an enabler with slug `testing` exists.
- Under that, three enabler children with slugs `generators`, `fixtures`, `harnesses` exist.
- Test-infrastructure implementation lives at the language's normative path (TypeScript `@testing/*`, Python `<package>_testing/*` where `<package>` is the product's Python package name, Rust `<product>_testing::*` from a `<product>-testing` workspace-member crate).
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
