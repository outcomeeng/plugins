<overview>

Every artifact in the Spec Tree has a specific purpose. Content placed in the wrong artifact creates confusion and duplication.

| Artifact type    | Purpose                    | Contains                         | Verified by       |
| ---------------- | -------------------------- | -------------------------------- | ----------------- |
| **ADR**          | GOVERNS how (architecture) | Decisions, rationale, invariants | ADR audit         |
| **PDR**          | GOVERNS what (product)     | Decisions, product invariants    | PDR audit         |
| **Enabler spec** | DESCRIBES infrastructure   | What it provides, assertions     | Tests             |
| **Outcome spec** | DESCRIBES hypothesis       | Outcome belief, assertions       | Tests             |
| **Test**         | PROVES assertions          | Test code                        | Test runner       |
| **Enforcement**  | CONSTRAINS structure       | Lint rules, AST selectors        | Tests on the rule |
| **PLAN.md**      | DEFERS remaining steps     | Concrete plan for a node         | Next agent        |
| **ISSUES.md**    | DEFERS known issues        | Gaps, bugs, untestable specs     | Next agent        |

</overview>

<adr>

**Purpose:** GOVERNS how things are built. Constrains architecture, not product behavior.

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

**Purpose:** GOVERNS what the product does. Establishes product decisions that must hold across a subtree.

**Contains:**

- Purpose — what product behavior this decision governs
- Context — business impact and technical constraints
- Decision — the chosen approach in one sentence
- Rationale — why this is right for users
- Trade-offs accepted — what was given up and why
- Product invariants — observable behaviors users can always rely on
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

**Contains:** Test code organized by level:

| Level       | Suffix                    | Question                             |
| ----------- | ------------------------- | ------------------------------------ |
| Unit        | `.unit.test.{ext}`        | Is our logic correct?                |
| Integration | `.integration.test.{ext}` | Does it work with real dependencies? |
| E2E         | `.e2e.test.{ext}`         | Does it work for users?              |

**Does NOT contain:** Spec content, decision rationale, or anything other than test code.

</test_files>

<enforcement>

**Purpose:** CONSTRAINS code structure via automated static analysis.

**Contains:** Lint rules (custom rule modules, AST selectors, pattern matchers) registered in the validation pipeline.

**How it differs from tests:** A lint rule walks AST nodes and matches patterns across all files in its glob — it does not import a module or exercise specific behavior.

**Verified by:** A `[test]` that exercises the rule against violating fixtures and asserts the violation is detected. The rule's presence in the validation pipeline is an operational concern, confirmed by the pipeline running green on the codebase.

**Does NOT contain:** Spec content, decision rationale, or test code.

</enforcement>

<escape_hatches>

**Purpose:** Non-durable node-local files left by `/handoff` for the next agent. They are escape hatches, not homes — prefer amending specs or fixing issues directly.

**PLAN.md** — concrete remaining steps for a node. Written when work is interrupted. Remove when all steps are complete.

**ISSUES.md** — known issues that were deferred: spec gaps, implementation bugs, untestable assertions. Remove fixed items, add new ones.

**Verified by:** `/contextualizing` reads them automatically. `/pickup` checks for them.

**Does NOT contain:** Spec content (→ spec file), architecture decisions (→ ADR), product decisions (→ PDR).

</escape_hatches>

<flow>

```text
                             ┌──[test]────→ Test
                             │               "does it hold?"
ADR/PDR ──governs──→ Spec ──┤
                             │
                             └──[review]───→ Human/agent
                                             "does the design follow W?"
```

</flow>

<common_misplacements>

| Content                  | Wrong location | Correct location                                                           |
| ------------------------ | -------------- | -------------------------------------------------------------------------- |
| Architecture choice      | Spec           | ADR                                                                        |
| Product decision         | Spec           | PDR                                                                        |
| Outcome hypothesis       | ADR            | Outcome spec                                                               |
| Test reference           | ADR/PDR        | Spec assertions                                                            |
| Implementation detail    | Spec           | Code (not spec)                                                            |
| "How to build it"        | Spec           | ADR or code                                                                |
| "What users can rely on" | Spec           | PDR                                                                        |
| Enforceable constraint   | `[review]`     | `[test]` on the lint rule                                                  |
| Cross-cutting invariant  | Child spec     | Ancestor spec                                                              |
| Remaining work steps     | Session file   | PLAN.md in node                                                            |
| Known deferred issues    | Session file   | ISSUES.md in node                                                          |
| Child-node enumeration   | Parent spec    | Remove — `/contextualizing` surfaces children; each child describes itself |

</common_misplacements>
