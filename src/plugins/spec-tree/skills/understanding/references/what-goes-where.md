<overview>

Every artifact in the Spec Tree has a specific purpose. Content placed in the wrong artifact creates confusion and duplication.

| Artifact type           | Purpose                                  | Contains                                     | Verified by                                         |
| ----------------------- | ---------------------------------------- | -------------------------------------------- | --------------------------------------------------- |
| **ADR**                 | GOVERNS how (architecture)               | Decisions, rationale, invariants             | ADR audit                                           |
| **PDR**                 | GOVERNS what (product)                   | Decisions, product properties                | PDR audit                                           |
| **Enabler spec**        | DESCRIBES infrastructure                 | What it provides, assertions                 | Tests                                               |
| **Outcome spec**        | DESCRIBES hypothesis                     | Outcome belief, assertions                   | Tests                                               |
| **Test**                | PROVES assertions                        | Typed assertion files                        | Test runner                                         |
| **Test infrastructure** | PROVIDES harnesses, generators, fixtures | Production code that enables test assertions | Code audit, test evidence audit, architecture audit |
| **Enforcement**         | CONSTRAINS structure                     | Lint rules, AST selectors                    | Tests on the rule                                   |
| **PLAN.md**             | COORDINATES pending steps                | Concrete plan for a node                     | Any agent in the next session                       |
| **ISSUES.md**           | COORDINATES known issues                 | Gaps, bugs, untestable specs                 | Any agent in the next session                       |

ADR vs PDR is decided by content alone — ADR governs how the product is built (architecture, invisible to its users); PDR governs what the product does (behavior its users observe). A decision's **reach** — the nodes it constrains — is set by its tree position (directory and numeric prefix per `ordering-rules.md`) and is identical for an ADR or a PDR at the same index; reach never distinguishes the two, so "it holds tree-wide" or "it's foundational" is not a PDR argument. Because "user-observable" is relative to a product's users, the same concern can be a PDR in one product and an ADR in another: test-infrastructure layout is product behavior for a methodology whose users adopt the tree shape, and architecture for an application whose users never see it.

</overview>

<adr>

**Purpose:** GOVERNS how the product is built — architecture and implementation structure, invisible to the product's users. Not product behavior.

**Contains:**

- Purpose — what concern this decision governs
- Context — business impact and technical constraints
- Decision — the chosen approach in one sentence
- Rationale — why this is right given constraints
- Trade-offs accepted — what was given up and why
- Invariants — algebraic properties that must hold
- Compliance — executable verification criteria (MUST / NEVER rules)

**Does NOT contain:** Outcomes, assertions, test references, or implementation code.

**Verified by:** Architecture audit skills (e.g., `/auditing-typescript-architecture`).

</adr>

<pdr>

**Purpose:** GOVERNS what the product does — behavior the product's users observe. Not how it is built.

**Contains:**

- Purpose — what product behavior this decision governs
- Context — business impact and technical constraints
- Decision — the chosen approach in one sentence
- Rationale — why this is right for users
- Trade-offs accepted — what was given up and why
- Product properties — observable behaviors users can always rely on
- Compliance — product behavior validation criteria (MUST / NEVER rules)

**Does NOT contain:** Outcomes, assertions, test references, or implementation code.

**Verified by:** PDR audit.

</pdr>

<enabler_spec>

**Purpose:** DESCRIBES what infrastructure this node provides to its dependents.

**Opens with:** `PROVIDES ... SO THAT ... CAN ...` — what it offers, who depends on it, what they couldn't do without it.

**Contains:**

- PROVIDES/SO THAT/CAN statement
- Assertions specifying output — what must be true about this infrastructure

**Does NOT contain:** Outcome hypotheses, user behavior claims.

</enabler_spec>

<outcome_spec>

**Purpose:** DESCRIBES a hypothesis connecting a testable output to user behavior change and business impact.

**Contains:**

- Three-part hypothesis: WE BELIEVE THAT [output] WILL [outcome] CONTRIBUTING TO [impact]
- Assertions specifying the output — locally verifiable by tests or review

**Does NOT contain:** Architecture decisions (→ ADR), product decisions (→ PDR), implementation details.

</outcome_spec>

<test_files>

**Purpose:** PROVES that assertions hold.

**Contains:** Typed assertion files only, one assertion type per file, following the canonical pattern `<subject>.<evidence>.<level>[.<runner>]`:

| Level | Suffix shape                | Question                             |
| ----- | --------------------------- | ------------------------------------ |
| 1     | `.<evidence>.l1.test.{ext}` | Is our logic correct?                |
| 2     | `.<evidence>.l2.test.{ext}` | Does it work with real dependencies? |
| 3     | `.<evidence>.l3.test.{ext}` | Does it work for users?              |

Each file imports the module under test — directly or through a test-infrastructure harness — and exercises the behavior its assertions claim.

**Does NOT contain:** Spec content, decision rationale, test harnesses, test generators, or fixtures. Harnesses and generators are test-infrastructure production code with their own home outside `tests/` and outside `spx/` (see `<test_infrastructure>`). Fixtures are inert input files read from disk by path — never imported by executed tests.

</test_files>

<test_infrastructure>

**Purpose:** PROVIDES the harnesses, generators, and inert fixtures that test assertion files depend on.

Test harnesses (modules that mediate access to the system under test), test generators (factories producing valid inputs), and inert fixtures (captured payloads, recorded transcripts, sample documents) are **production code**. They implement behavior, carry their own spec assertions in the spec tree, and pass the same audits as any other production module. They differ from product code only in purpose: they enable test assertions rather than deliver product value.

**Spec-tree governance (natural placement):** Test infrastructure is governed by spec nodes wherever the product's tree naturally places the concern. A shared infrastructure node is valid when category-wide test policy or reusable test substrate is a real product concern. A node-local harness, generator, or fixture can instead be governed by the node whose assertions depend on it, or by a child spec under that node. The categories `harnesses`, `generators`, and `fixtures` are artifact semantics, not mandatory node slugs. Do not create a top-level `infrastructure -> testing -> {generators, fixtures, harnesses}` subtree solely because test infrastructure exists.

**Implementation location (normative per language):** A sibling directory to product code, outside `spx/` and outside any `tests/` directory:

| Language       | Test-infrastructure home                                                                                                                                                                                                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `testing/` at project root, path-mapped to `@testing/`: `@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`                                                                                                                                                                     |
| **Python**     | `<package>_testing/`: `<package>_testing/harnesses/`, `<package>_testing/generators/`, `<package>_testing/fixtures/` — `<package>` is the product's Python package name                                                                                                                            |
| **Rust**       | A workspace-member crate at `<product>-testing/` (Cargo package `<product>-testing`, Rust import path `<product>_testing`), declared as a `[dev-dependencies]` entry of consumers; modules `<product>_testing::harnesses::*`, `<product>_testing::generators::*`, `<product>_testing::fixtures::*` |
| **Go**         | `internal/testinfra/` (package `testinfra` — not `testing`, which collides with the standard library): `internal/testinfra/harnesses/`, `internal/testinfra/generators/`, `internal/testinfra/fixtures/`, imported as `<module>/internal/testinfra/...`                                            |

**The term is "infrastructure", not "support".** "Test support", "test helpers", "test utilities", and "test tools" are anti-terms — they connote ungoverned utility code, the opposite of what these artifacts are.

**Verified by:** Code audit, test evidence audit, architecture audit — the same audit gates that govern product modules.

**Does NOT contain:** Test assertion code (lives in `spx/<node>/tests/`), spec content, or decision rationale.

</test_infrastructure>

<enforcement>

**Purpose:** CONSTRAINS code structure via automated static analysis.

**Contains:** Lint rules (custom rule modules, AST selectors, pattern matchers) registered in the validation pipeline.

**How it differs from tests:** A lint rule walks AST nodes and matches patterns across all files in its glob — it does not import a module or exercise specific behavior.

**Verified by:** A `[test]` that exercises the rule against violating fixtures and asserts the violation is detected. The rule's presence in the validation pipeline is an operational concern, confirmed by the pipeline running green on the codebase.

**Does NOT contain:** Spec content, decision rationale, or test code.

</enforcement>

<coordination_notes>

**Purpose:** Node-local coordination notes. They preserve pending work and known issues so a future session reads them on context load. Both files are committed to git for that one reason — git-tracking carries the coordination across sessions; it does not make the content product truth. They go stale unless acted upon, so treat a coordination note as a fallible input, never as authority: before it steers work, reconcile it against the node's spec, the governing ADRs/PDRs, the assertions, the tests, the implementation, and the current user intent, and act only where it still holds. Prefer amending specs or fixing issues directly when the correction is clear and safe. Session files under `.spx/sessions/` are the only spec-tree artifacts that live outside git; `spx session` shares them across worktrees.

**PLAN.md** — concrete remaining steps for a node. Written when work is interrupted, when an approved plan must persist beyond the current conversation, or when a higher-level declaration creates pending implementation work in the first affected lower node. Commit it; remove completed items in subsequent commits.

**ISSUES.md** — known issues that remain unresolved: spec gaps, contradictions, implementation bugs, untestable assertions. Commit it; remove fixed items and add new ones in subsequent commits.

**Verified by:** Reconcile against the durable layers and current user intent before use. `/contextualizing` reads them automatically; `/pickup` checks for them.

**Does NOT contain:** Spec content (→ spec file), architecture decisions (→ ADR), product decisions (→ PDR).

Higher-level truth belongs in product specs, ADRs, PDRs, and ancestor specs. Lower specs carry declarations that absorb that truth. `PLAN.md` carries the pending implementation steps left after those declarations are aligned.

</coordination_notes>

<flow>

```text
                             ┌──[test]────→ Test
                             │               "does it hold?"
ADR/PDR ──governs──→ Spec ──┤
                             │
                             └──[audit]───→ Human/agent
                                            "does the design follow W?"
```

</flow>

<common_misplacements>

| Content                              | Wrong location             | Correct location                                                           |
| ------------------------------------ | -------------------------- | -------------------------------------------------------------------------- |
| Architecture choice                  | Spec                       | ADR                                                                        |
| Product decision                     | Spec                       | PDR                                                                        |
| Outcome hypothesis                   | ADR                        | Outcome spec                                                               |
| Test reference                       | ADR/PDR                    | Spec assertions                                                            |
| Implementation detail                | Spec                       | Code (not spec)                                                            |
| "How to build it"                    | Spec                       | ADR or code                                                                |
| "What users can rely on"             | Spec                       | PDR                                                                        |
| Enforceable constraint               | `[audit]`                  | `[test]` on the lint rule                                                  |
| Cross-cutting invariant              | Child spec                 | Ancestor spec                                                              |
| Remaining work steps                 | Session file               | PLAN.md in node                                                            |
| Known unresolved issues              | Session file               | ISSUES.md in node                                                          |
| Pending work from higher-level truth | Higher-level decision/spec | PLAN.md in first affected lower node after lower specs align               |
| Child-node enumeration               | Parent spec                | Remove — `/contextualizing` surfaces children; each child describes itself |

</common_misplacements>
