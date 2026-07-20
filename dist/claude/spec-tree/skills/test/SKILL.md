---
name: test
description: >-
  ALWAYS invoke this skill before writing or repairing deterministic tests for
  a spec assertion, selecting a decision Testing rule's assertion type, or when
  learning the testing approach.
argument-hint: <full-spx-node-or-decision-path> [selected-assertions-json-array]
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, AskUserQuestion
---

<objective>
Spec-tree assertion tests and decision Testing rules that are canonically assertion-typed, source-contract-coupled, language-routed, and reproducible where executable evidence exists.
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

<workflow>

<step name="load_context">

**Step 1: Load tree context**

Abort when `$ARGUMENTS` is empty: "A canonical spec node or ADR/PDR target is required." Otherwise parse it as one canonical target followed by an optional JSON array of exact assertion texts already selected for test. Preserve each array string verbatim; it identifies the untagged spec assertion this workflow may type. Reject malformed JSON or non-string array members before reading the target. A decision target uses decision-rule mode and accepts no assertion-text array.

Check for `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers. If absent, invoke `/understand` and `/contextualize` first.

For a spec target, this loads:

- The target spec node and its assertions
- Ancestor ADRs/PDRs that constrain the testing approach
- Lower-index sibling specs that provide context

For a canonical ADR/PDR target supplied by `/verify`, use decision-rule mode. Require context for the containing node, or `spx/` for a product-level decision, and read only that decision's `### Testing` rules for assertion typing. The implementing specs own executable evidence and evidence links.

</step>

<step name="extract_assertions">

**Step 2: Extract assertions from the spec**

For a spec target, parse the target spec node and extract assertions already selected for `[test]` evidence plus the exact untagged assertions supplied to this invocation as selected test work. Ignore every other untagged assertion; verification-type selection remains outside `/test`. Extract any existing test links from the selected set:

| Type            | Pattern in spec                                    | Test strategy   |
| --------------- | -------------------------------------------------- | --------------- |
| **Scenario**    | `Given ... when ... then ... ([test](...))`        | Example-based   |
| **Mapping**     | `{input} maps to {output} ([test](...))`           | Parameterized   |
| **Conformance** | `{output} conforms to {standard} ([test](...))`    | Tool validation |
| **Property**    | `{invariant} holds for all {domain} ([test](...))` | Property-based  |
| **Compliance**  | `ALWAYS/NEVER: {rule} ([test](...))`               | Violating cases |

Record each assertion with:

- Assertion text
- Assertion type
- Test link (if present) — path and whether it resolves
- Test link status: exists / missing / stale

For a decision target, extract only `### Testing` rules. Apply the complete assertion-type selection from the loaded methodology prerequisite: the quantifier separates existential scenario evidence from universal evidence, then the universal rule's finite source-owned domain, contract oracle, violating-rule boundary, or open domain selects mapping, conformance, compliance, or property. Record the existing assertion-type tag, if any. Ignore `### Eval` and `### Audit` rules; they remain with their selected specialists.

</step>

<step name="analyze_gaps">

**Step 3: Analyze evidence gaps**

For each assertion:

| Status            | Condition                               | Action                                     |
| ----------------- | --------------------------------------- | ------------------------------------------ |
| **Covered**       | Test link exists and resolves to a file | Verify in Step 4                           |
| **Missing link**  | `[test]` selected with no path          | Must add test evidence link                |
| **Broken link**   | Link present but file doesn't exist     | Must create test file                      |
| **No assertions** | Spec has no typed assertions            | Spec needs work first — do not write tests |

Treat an explicitly supplied untagged test assertion as a missing-link assertion. It proceeds through assertion typing and scaffold generation; an untagged assertion absent from the supplied selected set remains outside this workflow.

For a decision target, skip evidence-link and filename checks. Report a rule as covered when its existing assertion-type tag matches the type selected by the complete methodology procedure, and as needing update when the tag is absent or mismatched.

**Legacy filename check:** For every **Covered** link above, verify the filename encodes assertion type and execution level. A file that provides coverage but lacks canonical naming is an imperfection — the test exists but its classification is opaque.

| Language   | Canonical pattern                                 | Legacy (fails check)                                                    |
| ---------- | ------------------------------------------------- | ----------------------------------------------------------------------- |
| TypeScript | `<subject>.<evidence>.<level>[.<runner>].test.ts` | `*.unit.test.ts`, `*.integration.test.ts`, `*.e2e.test.ts`, `*.spec.ts` |
| Python     | `test_<subject>.<evidence>.<level>[.<runner>].py` | `test_*.py` with no evidence or level segment                           |
| Rust       | `<subject>.<evidence>.<level>[.<runner>].rs`      | `*_test.rs` or `test_*.rs` with no evidence or level segment            |

evidence ∈ {scenario, mapping, conformance, property, compliance} — level ∈ {l1, l2, l3}

If any covered link uses a legacy name: flag as imperfection per the global imperfection protocol and surface via AskUserQuestion before proceeding.

Report the evidence gap summary before proceeding.

</step>

<step name="route_methodology">

**Step 4: Route each assertion through the methodology**

For each assertion that needs a test, apply the 5-stage router from `${CLAUDE_SKILL_DIR}/references/methodology.md`:

0. **Source-contract-first gate** — read the assertion, the existing or planned test, and the code under test; state the production contract the evidence exercises; fix missing source-owned contracts before writing test predicates.
1. **Stage 1** — What evidence does this assertion demand?
2. **Stage 2** — At what execution level does that evidence live? Respect ADRs/PDRs loaded from tree context.
3. **Stages 3–5** — If `L1` is viable, classify the code, check real system viability, and match an exception if needed.

Document the routing decision for each assertion.

In decision-rule mode, stop after assertion-type selection. Execution level, language expression, test files, and evidence links belong to the implementing spec assertion that realizes the rule.

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

In decision-rule mode, update each `### Testing` rule with exactly one selected assertion-type tag and create no test scaffold. Continue directly to the report step.

**Specified nodes:** If the implementation module doesn't exist yet, test files will fail on import. This is expected — the test is a declaration of what the implementation must satisfy. Add the node's path to `spx/EXCLUDE`. The `spx` CLI skips excluded nodes when running `spx test passing`. Remove the entry when implementation begins. Use `/understand`'s excluded-node guidance for the convention.

</step>

<step name="update_links">

**Step 6: Update spec assertion links**

After creating test files, move each newly typed assertion under its canonical assertion-type heading and update the spec to add `([test](tests/{filename}))` links for each new assertion-test pair. This skill never selects or writes eval or audit evidence.

In decision-rule mode, add no evidence link to the ADR/PDR. The implementing specs own the linked executable evidence.

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

<success_criteria>

Testing output is sound when:

- Every decision `### Testing` rule carries exactly one assertion-type tag selected from its quantifier plus the universal claim's domain, contract-oracle, or violating-rule shape, and no executable evidence link.
- Every explicitly supplied untagged test assertion is moved under its selected assertion-type heading and receives one canonical `[test](path)` link; unrelated untagged assertions remain unchanged.
- Every test file name encodes the assertion type and execution level; it includes a runner token only when the canonical model requires one.
- Every test asserts source-coupled behavior with no test-owned data or configuration in the assertion file.
- Every property test uses a meaningful generated domain and reports both the seed and replay path on failure.
- Every test double maps to one of the seven exception cases and preserves the behavior boundary the assertion claims.
- Every spec assertion that receives test evidence links to the evidence file that verifies it.

</success_criteria>
