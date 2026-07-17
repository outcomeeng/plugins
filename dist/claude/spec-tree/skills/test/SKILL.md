---
name: test
description: ALWAYS invoke this skill before selecting assertion evidence, writing tests, or learning the testing approach.
argument-hint: "[spx/target-node | mode: select-evidence with assertion context]"
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, Bash(git mv:*), AskUserQuestion
---

<objective>
Spec-tree assertion evidence that is correctly selected, canonically named, source-contract-coupled when implemented, and reproducible for property failures.
</objective>

<prerequisite>

**PREREQUISITE**: Read `${CLAUDE_SKILL_DIR}/references/methodology.md` before selecting evidence or writing any test.

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

<selection_only>

When the invocation uses `mode: select-evidence`, supply one assertion at a time in this form:

```text
mode: select-evidence
target: spx/<prospective artifact path>
assertion: <exact assertion or MUST/NEVER rule text>
language: <product implementation language or languages>
source_context: <existing source paths or the planned source contract>
boundary_context: <dependencies, execution environment, and loaded decision constraints>
```

For `select-evidence`:

1. Require live foundation and context markers for the prospective target's parent.
2. Choose `test`, `evaluate`, or `audit` from the live `/understand` `<verification_selection>` rules.
3. For `test`, run all five methodology stages against the assertion, supplied source context, boundary context, and loaded decisions. Select the assertion type from Stage 1 and the lowest justified execution level only after Stages 2–5 establish real-system viability or a named exception. Derive the canonical filename from the target slug, assertion type, level, and language naming rule. If source ownership, language, level, target ownership, or boundary context is unresolved, stop and return that exact unresolved input; never guess.
4. Return exactly these fields:

```text
mode: select-evidence
verification_type: test | evaluate | audit
assertion_type: scenario | mapping | conformance | property | compliance | none
execution_level: l1 | l2 | l3 | none
evidence_form: <exact Markdown form to copy into the artifact>
rationale: <one sentence naming the governing selection rule>
```

The evidence form is artifact-aware:

- A node's deterministic assertion receives `([test](tests/{canonical filename}))`.
- An ADR/PDR deterministic rule receives `([{assertion type}])` under `### Testing`; decision records do not own test-file paths.
- An evaluate result receives `([eval](evals/{rule-slug}/eval.toml))` in a node or `([eval])` in a decision record.
- An audit receives `([audit])`.

Return after selection. Source reads and all five routing stages are part of selection, but repository mutation is not: do not create a test or eval artifact, edit the target spec, or update a link. The normal workflow performs those mutations when `/test` later runs on the authored node.

</selection_only>

<workflow>

The normal workflow below applies when the invocation targets an authored spec node rather than `mode: select-evidence`.

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

If a covered link uses a legacy name, record the imperfection and its planned canonical target. Use AskUserQuestion when the rename changes ownership, scope, cost, risk, or an unresolved product choice. Execute an unambiguous rename only in Step 6 after GATE A passes, then update the spec link in Step 8.

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

</step>

<step name="gate_before_file_creation">

**Step 5 / GATE A — Evidence plan before file creation**

For every planned test file, record `assertion_type`, `execution_level`, `canonical_filename`, `source_contract`, `boundary_or_exception`, and `owner_node`. Pass only when all six values are resolved, the assertion type and level are valid enum values, the filename exactly matches the language's canonical pattern, the owner node determines one unambiguous `tests/` path, and that path does not conflict with an unrelated existing file.

If any check fails, report the failed field and STOP. Do not call Write, Edit, or `git mv` before this gate passes for that file.

</step>

<step name="generate_scaffolds">

**Step 6: Generate test scaffolds**

Execute each GATE A-approved legacy rename with `git mv` before creating new files.

For each assertion needing a new test:

1. Determine test pattern from assertion type (Step 2 table).
2. Determine execution level from methodology routing (Step 4).
3. Create the test file in the spec node's `tests/` directory.
4. Name the file using the canonical model in `${CLAUDE_SKILL_DIR}/references/methodology.md`.
5. Scaffold the test structure based on assertion type and language-specific patterns.

Delegate language-specific structure to `/test-python` or `/test-rust` or `/test-typescript`.

**Specified nodes:** If the implementation module doesn't exist yet, test files will fail on import. This is expected — the test is a declaration of what the implementation must satisfy. Add the node's path to `spx/EXCLUDE`. The `spx` CLI skips excluded nodes when running `spx test passing`. Remove the entry when implementation begins. Use `/understand`'s excluded-node guidance for the convention.

</step>

<step name="gate_before_link_mutation">

**Step 7 / GATE B — Evidence target before spec-link mutation**

For every created or renamed test, require all of these checks to pass: Read succeeds at the recorded path; its basename equals `canonical_filename`; `tests/{canonical_filename}` resolves from the owning spec directory; the file exercises the recorded assertion and source contract; and the delegated language test workflow reports its own required checks complete.

If any check fails, report the failed path or contract and STOP before editing the spec. Never add a link to a missing, misnamed, or unverified target.

</step>

<step name="update_links">

**Step 8: Update spec assertion links**

After creating test files, update the spec to add `([test](tests/{filename}))` links for each new assertion-test pair. Every assertion must link to evidence: `[test]` for automated verification, `[eval]` for LLM-driven behavior that emits a parseable structured verdict, or `[audit]` for semantic constraints requiring agent judgment (`[review]` is the legacy spelling of `[audit]`).

</step>

<step name="report">

**Step 9: Report evidence summary**

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

<unresolved_routing>
What: A test is created after guessing source ownership, execution level, or boundary viability.
Why: The evidence can pass while proving a different contract or exercising the wrong system boundary.
Avoid: Require every GATE A field and stop on the first unresolved value.
</unresolved_routing>

<ambiguous_legacy_rename>
What: A legacy test is renamed even though its owner or canonical target is ambiguous.
Why: The move can break another node's evidence link or silently change assertion ownership.
Avoid: Use `git mv` only after GATE A identifies one owner and one collision-free target; ask the user when ownership or scope remains a product choice.
</ambiguous_legacy_rename>

<selection_only_mutation>
What: `mode: select-evidence` creates an artifact or edits the prospective target.
Why: Authoring-time selection becomes a hidden repository mutation before the artifact exists.
Avoid: Return immediately after the six declared output fields and never enter the normal workflow in selection-only mode.
</selection_only_mutation>

<unreproducible_property_failure>
What: A property test reports a failing case without both its seed and replay path.
Why: The failure cannot be reproduced after shrinking or in another environment.
Avoid: Require non-empty seed and replay fields in the delegated language workflow before GATE B passes.
</unreproducible_property_failure>

</failure_modes>

<success_criteria>

- [ ] A selection-only result contains exactly `mode`, `verification_type`, `assertion_type`, `execution_level`, `evidence_form`, and `rationale`; every enum value is valid, the evidence form matches the artifact kind, and the invocation made zero Write, Edit, or `git mv` calls.
- [ ] Every created or renamed basename equals the `canonical_filename` recorded at GATE A and matches the language's canonical pattern.
- [ ] Read succeeds for every evidence path added to a spec, resolved relative to that spec's directory.
- [ ] Every generated test exercises the source contract recorded at GATE A with no test-owned protocol data or configuration in the assertion file.
- [ ] Every property-test failure report exposes non-empty seed and replay fields, and the delegated language workflow confirms both paths.
- [ ] Every test double names one of the seven exception cases and preserves the recorded behavior boundary.
- [ ] Every spec-link edit changes only the intended assertion's evidence form and points to the GATE B path.

</success_criteria>
