---
name: test
description: ALWAYS invoke this skill before writing tests or when learning the testing approach.
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, AskUserQuestion
---

<objective>
Spec-tree assertion tests whose evidence architecture is approved before mutation, canonically named, source-contract-coupled, and reproducible for property failures.
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

Before creating or changing an executed test file, emit one structured evidence-design row per assertion. No test-file mutation is allowed until every row has `status: "PROCEED"` and the packet has `mutation_allowed: true`.

Each row determines:

- assertion id, exact assertion text, quantifier, and finite or open/composable domain;
- independent oracle and a concrete way the proposed evidence could pass while the assertion remained false;
- assertion type and execution level;
- source-contract, harness, generator, and fixture requirements;
- property seed, replay, and failure-diagnostic ownership;
- reference validity by role.

Open or composable domains default to a variable generator or property evidence. Reject a constant-only generator with `insufficient-domain-variation`. A property design without harness-owned seed, replay input, and failure diagnostics stops with `missing-replay-harness`. Expected output derived from the implementation under test stops with `missing-independent-oracle`.

An inert whole-payload fixture is an operator-approved exception. Before requesting approval, state why the complete payload shape is material, why variable generation or property evidence is infeasible or wasteful, which state-space coverage is surrendered, which harness owns setup, cleanup, seed policy, replay, and diagnostics, and the recommended generator or property alternative. Use `AskUserQuestion` with the recommended variable-evidence path first, fixture approval second, and pause/inspect third. Approval applies only to the named assertion and payload role. A module, constant bag, copied protocol value, expected-output file, or finite substitute for an open domain is never an approvable fixture.

Validate references before emitting a row:

1. A local artifact reference is a Markdown link whose target is a product-root-relative path. Reject prose-only names, inline-code paths, absolute paths, `file://` URIs, targets beginning with `/` or `./`, traversal segments, and backslashes.
2. Resolve the target from the product root and require an existing file whose kind matches the declared role.
3. A governing reference targets the exact assertion-bearing spec file or full ADR/PDR path under `spx/`. A node directory, bare node name, or implementation file fails governance.
4. A source contract, harness, generator, or fixture requires the governing reference and, when implementation exists, a second link to that implementation. An implementation link is mandatory secondary traceability and never sufficient by itself.
5. A `[test]` reference targets the exact co-located typed test file. An `[eval]` reference targets the exact `eval.toml`. An external conformance authority uses its stable canonical URL or identifier together with a product-root-relative Markdown link to the local spec or full decision that adopts it. A seed, replay token, or run token remains a verbatim source-emitted value and pairs with product-root-relative Markdown links to its owning harness or journal implementation and exact governing spec or full decision.
6. Planned infrastructure with no implementation links its governing spec, records implementation as absent, and stops dependent test-file authoring. Never manufacture a broken implementation link.

Emit this JSON contract:

```json
{
  "status": "PROCEED | STOP | OPERATOR_DECISION_REQUIRED",
  "mutation_allowed": false,
  "rows": [
    {
      "assertion_id": "<id>",
      "evidence_shape": "SCENARIO | MAPPING | CONFORMANCE | PROPERTY | COMPLIANCE | FIXTURE",
      "reference_status": "VALID | INVALID | MISSING",
      "fixture_status": "NOT_REQUIRED | APPROVAL_REQUIRED | APPROVED"
    }
  ],
  "findings": [
    { "rule": "<rule>", "assertion_id": "<id>" }
  ]
}
```

Set `mutation_allowed` true only with `status: "PROCEED"`, valid references, an independent oracle, sufficient domain variation, replayable property evidence, and every fixture decision resolved.

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

Then execute `<evidence_design_gate>` and report its packet before any Step 5 mutation. Stop when the packet blocks or requests operator approval.

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

<success_criteria>

Testing output is sound when:

- The evidence-design packet was emitted before test-file mutation, every row proceeded, and any fixture exception has scoped operator approval.
- Every local artifact reference passed role, path-shape, existence, target-kind, and governance-pairing validation.
- Every test file name encodes the assertion type and execution level; it includes a runner token only when the canonical model requires one.
- Every test asserts source-coupled behavior with no test-owned data or configuration in the assertion file.
- Every property test uses a meaningful generated domain and reports both the seed and replay path on failure.
- Every test double maps to one of the seven exception cases and preserves the behavior boundary the assertion claims.
- Every spec assertion that receives test evidence links to the evidence file that verifies it.

</success_criteria>
