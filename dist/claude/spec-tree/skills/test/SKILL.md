---
name: test
description: ALWAYS invoke this skill before writing tests or when learning the testing approach.
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, Bash(git mv:*)
---

<objective>
Spec-tree assertion tests that are canonically named, evidence-routed, source-contract-coupled, and reproducible for property failures.
</objective>

<prerequisite>

**PREREQUISITE**: Read `${CLAUDE_SKILL_DIR}/references/methodology.md` before writing any test.

That local reference contains:

- non-negotiable testing rules and evidence standards
- the split between test configuration, test data, harnesses, generators, fixtures, and eval cases
- property-based seed and replay requirements
- the pre-test questions and the evidence trap
- the separation between assertion type, execution level, and runner
- the 4-part progression
- the 5-stage router with stop conditions
- the 5 factors, the 7 exception cases, and key examples
- the naming and co-location contract

Then follow the spec-tree workflow below.

</prerequisite>

<evidence_design_gate>

Record one assertion-to-evidence row per assertion, then one clause row per independently falsifiable clause. Score every field before scaffolding or repair:

| Check                        | PASS                                                                                                                                                                                 | FAIL                                                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| Clause inventory             | Every independently falsifiable clause has one row                                                                                                                                   | Any claim in the assertion has no row                                                                         |
| Assertion routing            | The row names the assertion type, verification type, linked evidence file, and language                                                                                              | Type, lane, link, or language is absent or inferred from existing test shape                                  |
| Required evidence form       | The row names the language-standard form and every type-specific obligation                                                                                                          | The planned form is generic or omits a required mapping, property, conformance, scenario, or compliance shape |
| Exercised path               | The row names the source path the evidence executes                                                                                                                                  | The path is absent, adjacent, or replaced                                                                     |
| Coupling trace               | The row traces the linked evidence through infrastructure to assertion-relevant source behavior                                                                                      | Coupling is structural, type-only, partial, severed, or untraced                                              |
| Observable result            | The row names an assertion-relevant observable                                                                                                                                       | The observation is structural, trivial, or unrelated                                                          |
| Independent oracle           | The expected result comes from outside the behavior under test                                                                                                                       | The behavior under test produces its own expected result                                                      |
| Passing-while-false mutation | A concrete source mutation makes the clause false and must fail the evidence                                                                                                         | No concrete mutation is named, or the evidence survives it                                                    |
| Relevant-path coverage       | Reading the source and evidence shows execution reaches every assertion-relevant branch                                                                                              | An assertion-relevant branch has no exercised route                                                           |
| Distrust sweep               | When any existing evidence proves only a subpart, every linked test, harness, generator, fixture, source contract, oracle, and assertion-relevant implementation path is inventoried | A subpart trigger exists and any evidence-chain artifact is uninspected                                       |
| Source-contract readiness    | Source-owned vocabulary and observable behavior exist in production contracts                                                                                                        | Test predicates would need copied values, hidden data, or replaced behavior                                   |

The gate is `PASS` only when every row passes every check. Any failed check blocks scaffolding and repair. Fix the source contract or evidence design, then score the complete matrix again.

</evidence_design_gate>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

Check for `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers. If absent, invoke `/understand` and `/contextualize` first.

This loads:

- The target spec node and its assertions
- Ancestor ADRs/PDRs that constrain the testing approach
- Lower-index sibling specs that provide context

</step>

<step name="extract_assertions">

**Step 2: Extract assertions from the spec**

Parse the target spec node. Extract all typed assertions and their test links:

| Type            | Pattern in spec                                    | Test strategy        |
| --------------- | -------------------------------------------------- | -------------------- |
| **Scenario**    | `Given ... when ... then ... ([test](...))`        | Example-based        |
| **Mapping**     | `{input} maps to {output} ([test](...))`           | Parameterized        |
| **Conformance** | `{output} conforms to {standard} ([test](...))`    | Tool validation      |
| **Property**    | `{invariant} holds for all {domain} ([test](...))` | Property-based       |
| **Compliance**  | `ALWAYS/NEVER: {rule} ([audit]/[test]/[eval])`     | Audit, test, or eval |

Record each assertion with:

- Assertion text
- Assertion type
- Verification type and language-standard evidence form
- Test link (if present) — path and whether it resolves
- Test link status: exists / missing / stale
- Coupling path from evidence through infrastructure to assertion-relevant source
- Type-specific obligations and relevant source branches

</step>

<step name="analyze_gaps">

**Step 3: Analyze evidence gaps**

For each assertion:

| Status            | Condition                                     | Action                                     |
| ----------------- | --------------------------------------------- | ------------------------------------------ |
| **Covered**       | Test link exists and resolves to a file       | Verify in Step 4                           |
| **Missing link**  | No `([test])`, `([eval])`, or `([audit])` tag | Must add evidence link                     |
| **Broken link**   | Link present but file doesn't exist           | Must create test file                      |
| **No assertions** | Spec has no typed assertions                  | Spec needs work first — do not write tests |

**Legacy filename check:** For every **Covered** link above, verify the filename encodes assertion type and execution level. A file that provides coverage but lacks canonical naming is an imperfection — the test exists but its classification is opaque.

| Language   | Canonical pattern                                 | Legacy (fails check)                                                    |
| ---------- | ------------------------------------------------- | ----------------------------------------------------------------------- |
| TypeScript | `<subject>.<evidence>.<level>[.<runner>].test.ts` | `*.unit.test.ts`, `*.integration.test.ts`, `*.e2e.test.ts`, `*.spec.ts` |
| Python     | `test_<subject>.<evidence>.<level>[.<runner>].py` | `test_*.py` with no evidence or level segment                           |
| Rust       | `<subject>.<evidence>.<level>[.<runner>].rs`      | `*_test.rs` or `test_*.rs` with no evidence or level segment            |

evidence ∈ {scenario, mapping, conformance, property, compliance} — level ∈ {l1, l2, l3}

If any covered link uses a legacy name, derive its canonical name from the assertion type, execution level, and optional runner; rename the tracked file with `git mv`, update every spec link to the new path, and continue only after all links resolve. Canonical naming is a safe local repair, never an operator question.

Report the evidence gap summary before proceeding.

</step>

<step name="route_methodology">

**Step 4: Route each assertion through the methodology**

For every assertion, including assertions with existing linked evidence, apply the methodology from `${CLAUDE_SKILL_DIR}/references/methodology.md` in this order:

0. **Assertion-to-evidence matrix** — record the assertion type, verification type, linked file, language-standard evidence form, type-specific obligations, coupling path, relevant source branches, and one independently falsifiable row per clause with its exercised path, observable result, independent oracle, and passing-while-false mutation.
1. **Full-chain distrust trigger** — if existing evidence proves only a subpart, inspect every clause, linked test, harness, generator, fixture, source contract, oracle, and assertion-relevant implementation path before designing a repair.
2. **Source-contract-first gate** — read the assertion, the existing or planned test, and the code under test; state the production contract the evidence exercises; fix missing source-owned contracts before writing test predicates.
3. **Stage 1** — What evidence does this assertion demand?
4. **Stage 2** — At what execution level does that evidence live? Respect ADRs/PDRs loaded from tree context.
5. **Stages 3–5** — If `L1` is viable, classify the code, check real system viability, and match an exception if needed.

Document the routing decision for each assertion.

Do not proceed to scaffolding or repair until every assertion has a complete matrix, every clause has a concrete failing mutation, every language-standard evidence form is satisfied by design, and the complete evidence chain has been inspected after any distrust trigger.

Apply `<evidence_design_gate>`. Stop this step with `FAIL` when any check fails. Step 5 starts only from a recorded `PASS` for every assertion.

</step>

<step name="generate_scaffolds">

**Step 5: Generate test scaffolds**

For each assertion needing a new test:

1. Determine test pattern from assertion type (Step 2 table).
2. Determine execution level from methodology routing (Step 4).
3. Create the test file in the spec node's `tests/` directory.
4. Name the file using the canonical model in `${CLAUDE_SKILL_DIR}/references/methodology.md`.
5. Scaffold the test structure based on assertion type and language-specific patterns.

Delegate language-specific structure to `/test-python` or `/test-rust` or `/test-typescript`.

**Specified nodes:** If the implementation module doesn't exist yet, test files will fail on import. This is expected — the test is a declaration of what the implementation must satisfy. Add the node path relative to `spx/` to `spx/EXCLUDE`; never write the leading `spx/` segment into an entry. Record the exact missing production owner and the focused RED diagnostics. The `spx` CLI skips excluded nodes when running `spx test passing`. Report the test-evidence audit as deferred because the assertion-relevant production path is not inspectable. Remove the entry when implementation begins, bring the normal deterministic gates to passing, and dispatch the test-evidence audit only then. Use `/understand`'s excluded-node guidance for the convention.

</step>

<step name="update_links">

**Step 6: Update spec assertion links**

Before changing a spec link, rescore `<evidence_design_gate>` against the written test and its complete infrastructure chain. Update the link only when every clause still passes and every passing-while-false mutation necessarily fails the written evidence.

After creating test files, update the spec to add `([test](tests/{filename}))` links for each new assertion-test pair. Every assertion must link to evidence: `[test]` for automated verification, `[eval]` for LLM-driven behavior that emits a parseable structured verdict, or `[audit]` for semantic constraints requiring agent judgment (`[review]` is the legacy spelling of `[audit]`).

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

For a specified node, also report the relative `spx/EXCLUDE` entry, exact missing production owner, RED diagnostics, and `test-evidence audit: deferred until implementation exists`.

</step>

</workflow>

<cross_cutting_assertions>

When an assertion lives in an ancestor node, determine where the test evidence should go:

- If the assertion is about behavior that a specific child node implements, the test belongs in that child's `tests/` directory.
- If the assertion spans multiple children, the test belongs in the ancestor's `tests/` directory at a higher level.
- If an ancestor accumulates too many cross-cutting assertions, flag it for `/decompose`; the decomposition workflow owns shared-enabler extraction and index placement.

</cross_cutting_assertions>

<failure_modes>

**Failure: Claude renamed a legacy test from its filename alone.**

What happened: Claude saw a non-canonical linked filename, guessed the evidence type and execution level from the old name, ran `git mv`, and repaired only the link in the target assertion. Another spec still referenced the old path, or the guessed destination collided with evidence for a different assertion.

Why it failed: A legacy filename does not establish its own classification or ownership. The assertion, methodology routing, and complete set of spec references determine the canonical destination.

How to avoid: Derive the destination from the linked assertion's evidence type, routed execution level, and runner; search all spec links to the old path; check that the destination is absent or is the same evidence; run `git mv`; update every referencing spec link; then verify that the old path is absent and every new link resolves before continuing.

</failure_modes>

<success_criteria>

Testing output is sound when:

- A recorded assertion-to-evidence matrix names every assertion's type, verification lane, linked file, required language form, type-specific obligations, coupling path, and relevant source branches, plus one row for every independently falsifiable clause.
- Every matrix row names an exercised source path, assertion-relevant observable, independent oracle, and concrete passing-while-false mutation.
- Every assertion records `<evidence_design_gate>` as `PASS` before scaffolding and again before spec-link mutation.
- Every subpart trigger has a complete inventory of linked tests, harnesses, generators, fixtures, source contracts, oracles, and assertion-relevant implementation paths.
- Every test file name encodes the assertion type and execution level; it includes a runner token only when the canonical model requires one.
- Every test asserts source-coupled behavior with no test-owned data or configuration in the assertion file.
- Every property test uses a meaningful generated domain and reports both the seed and replay path on failure.
- Every test double maps to one of the seven exception cases and preserves the behavior boundary the assertion claims.
- Every spec assertion that receives test evidence links to the evidence file that verifies it.
- A specified-node report records its exclusion, missing owner, RED diagnostics, and deferred audit; no test-evidence audit is dispatched until implementation makes the full chain inspectable.

</success_criteria>
