---
name: test
description: ALWAYS invoke this skill before writing tests or when learning the testing approach.
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, {{! tool('ask_user') !}}
---

Invoke the `spec-tree:test-evidence-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop before writing test evidence.

<objective>
Spec-tree assertion tests that are canonically named, evidence-routed, source-contract-coupled, and reproducible for property failures.
</objective>

<shared_standards>

Apply the complete predicate-seam, semantic-binding, case-provenance, oracle-independence, and assertion-type litmus rules loaded from `/test-evidence-standards` for every verification type. Load the execution-level and runner methodology only when Step 4 selects `[test]` evidence.

</shared_standards>

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
- Test link (if present) — path and whether it resolves
- Test link status: exists / missing / stale

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
| Python     | `test_<subject>.<evidence>.<level>.py`            | `test_*.py` with no evidence or level segment                           |
| Rust       | `<subject>.<evidence>.<level>[.<runner>].rs`      | `*_test.rs` or `test_*.rs` with no evidence or level segment            |

evidence ∈ {scenario, mapping, conformance, property, compliance} — level ∈ {l1, l2, l3}

If any covered link uses a legacy name: flag as imperfection per the global imperfection protocol and surface via {{! tool('ask_user') !}} before proceeding.

Report the evidence gap summary before proceeding.

</step>

<step name="route_methodology">

**Step 4: Route each assertion through the methodology**

Select the verification type before execution-level or runner concerns. When at least one assertion needs `[test]` evidence, read `${CLAUDE_SKILL_DIR}/references/methodology.md` exactly once, then apply its 5-stage router to every `[test]` assertion:

0. **Source-contract-first gate** — read the assertion, the existing or planned test, and the code under test; state the production contract the evidence exercises; fix missing source-owned contracts before writing test predicates.
1. **Stage 1** — What evidence does this assertion demand?
2. **Stage 2** — At what execution level does that evidence live? Respect ADRs/PDRs loaded from tree context.
3. **Stages 3–5** — If `L1` is viable, classify the code, check real system viability, and match an exception if needed.

Document the routing decision for each assertion.

Assertions routed to `[eval]` or `[audit]` do not load the test execution-level and runner methodology.

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

**Specified nodes:** If the implementation module doesn't exist yet, test files will fail on import. This is expected — the test is a declaration of what the implementation must satisfy. Add the node's path to `spx/EXCLUDE`. The `spx` CLI skips excluded nodes when running `spx test passing`. Remove the entry when implementation begins. Use `/understand`'s excluded-node guidance for the convention.

</step>

<step name="update_links">

**Step 6: Update spec assertion links**

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

</step>

</workflow>

<cross_cutting_assertions>

When an assertion lives in an ancestor node, determine where the test evidence should go:

- If the assertion is about behavior that a specific child node implements, the test belongs in that child's `tests/` directory.
- If the assertion spans multiple children, the test belongs in the ancestor's `tests/` directory at a higher level.
- If an ancestor accumulates too many cross-cutting assertions, flag it for `/decompose`; the decomposition workflow owns shared-enabler extraction and index placement.

</cross_cutting_assertions>

<failure_modes>

**Execution-level methodology loaded for every evidence route.**

What happened: Claude loaded `${CLAUDE_SKILL_DIR}/references/methodology.md` before selecting `[test]`, `[eval]`, or `[audit]` evidence.

Why it failed: the reference governs test execution levels and runners, so loading it for eval and audit routes made progressive disclosure unconditional and spent context on rules those routes never consume.

How to avoid: keep `/test-evidence-standards` eager for every route, then read the execution-level methodology exactly once only when Step 4 selects at least one `[test]` assertion.

</failure_modes>

<success_criteria>

Testing output is sound when:

- Every test file name encodes the assertion type and execution level; it includes a runner token only when the canonical model requires one.
- Every test keeps all predicates and assertion API calls in the linked test function or callback; infrastructure exposes observations without verdict logic.
- Every test-file binding introduces no test-owned data, expectation, configuration, setup policy, or verdict rule.
- Every case and oracle passes the assertion-type litmus questions from `/test-evidence-standards`.
- Every property test uses a meaningful generated domain and reports both the seed and replay path on failure.
- Every test double maps to one of the seven exception cases and preserves the behavior boundary the assertion claims.
- Every spec assertion that receives test evidence links to the evidence file that verifies it.

</success_criteria>
