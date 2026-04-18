---
name: auditing-tests
description: >-
  ALWAYS invoke this skill when auditing test evidence quality, after writing tests for a spec node,
  or before closing an outcome.
---

<objective>

Audit whether tests provide genuine evidence that spec assertions are fulfilled. Four properties must hold — coupling, falsifiability, alignment, coverage — checked in strict order. A test missing any property has zero evidentiary value regardless of code quality.

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/evidence-model.md`

</objective>

<quick_start>

**PREREQUISITE**: Invoke `/contextualizing` on the target spec node before auditing.

1. Extract assertions and linked test files from the spec
2. For each test file, check in order: coupling → falsifiability → alignment → coverage
3. First property failure = REJECT for that assertion (skip remaining properties)
4. All four properties hold for all assertions = APPROVED

**Coupling is the gate.** If a test imports nothing from the codebase, skip all other checks — it is a tautology.

</quick_start>

<essential_principles>

**COUPLING FIRST.**

A test that imports nothing from the codebase will pass forever regardless of what any file contains. Check imports before anything else. This is not a heuristic — it is a prerequisite.

**RUN COVERAGE, DON'T GUESS.**

Read the project's CLAUDE.md for the test and coverage command. Run coverage without the test (baseline), then with the test. Report actual deltas per source file. Never reason about what paths a test "probably" covers.

**NO MECHANICAL DETECTION.**

Mocking patterns, skip patterns, type annotations — these are linting concerns (SemGrep, ESLint). The auditor evaluates evidence quality, not code quality signals.

**BINARY VERDICT.**

APPROVED or REJECT. No middle ground. If any property is missing for any assertion, REJECT.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualizing` on the spec node whose tests are being audited. This loads the spec's assertions, ancestor ADRs/PDRs, and the full hierarchy context.

Do not proceed without `<SPEC_TREE_CONTEXT>` marker.

</step>

<step name="map_assertions">

**Step 2: Map assertions to test files**

Read the spec's Assertions section. For each assertion, extract:

| Field          | Extract                                                  |
| -------------- | -------------------------------------------------------- |
| Assertion text | The claim being tested                                   |
| Assertion type | Scenario / Mapping / Conformance / Property / Compliance |
| Test link      | Path from `([test](path))`                               |
| Link status    | File exists or missing                                   |

**Missing test file = finding.** Record it and continue to next assertion.

**Compliance assertions with `[review]` tags** are verified by human/agent judgment, not by tests. Skip them in the test evidence audit.

</step>

<step name="audit_coupling">

**Step 3a: Coupling**

Read the test file's import statements. Classify each import:

| Import source                                  | Classification             |
| ---------------------------------------------- | -------------------------- |
| Test framework (vitest, pytest, jest)          | Framework — does not count |
| Node modules / pip packages                    | Library — does not count   |
| Codebase path (relative import, project alias) | Codebase — counts          |

**Zero codebase imports → REJECT — "no coupling" (tautology).**

If codebase imports exist, classify using the coupling taxonomy in `${CLAUDE_SKILL_DIR}/references/evidence-model.md`:

| Category   | Definition                                                  | Verdict                                    |
| ---------- | ----------------------------------------------------------- | ------------------------------------------ |
| Direct     | Test imports the module under test                          | Proceed                                    |
| Indirect   | Test imports a harness wrapping the module                  | Proceed — verify harness has real coupling |
| Transitive | Test imports a consumer of the module                       | Proceed — verify test level matches        |
| False      | Imports module but never calls assertion-relevant functions | REJECT                                     |
| Partial    | Calls functions but on wrong inputs or wrong code paths     | REJECT                                     |

</step>

<step name="audit_falsifiability">

**Step 3b: Falsifiability**

For each codebase import, name a concrete mutation to the imported module that would cause this test to fail. Write it down:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed result
Impact: "parses nested sections" fails — expect(result.section.key) throws
```

**Cannot name a mutation for any import → REJECT — "unfalsifiable."**

Check for mocking. If the test imports a module then replaces it with a mock, the coupling is severed:

```typescript
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn() }));
// Real database.query never runs — coupling severed
```

**Import + mock = REJECT — "coupling severed."**

**Exception**: Test doubles used under the 7 legitimate exception cases from the `/testing` methodology are not "coupling severed." The auditor must identify which exception applies and verify the double type matches. See the exception cross-reference in `${CLAUDE_SKILL_DIR}/references/evidence-model.md`.

</step>

<step name="audit_alignment">

**Step 3c: Alignment**

Read the spec assertion text. Read the test's expect/assert statements. Answer:

1. Does the test exercise the exact behavior the assertion describes?
2. Could the spec assertion be unfulfilled while the test passes?

If yes to question 2: **REJECT — "misaligned."**

Check assertion-type-to-strategy alignment:

| Assertion type | Required test strategy                            | REJECT if                 |
| -------------- | ------------------------------------------------- | ------------------------- |
| Scenario       | Example-based with Given/When/Then inputs         | Missing concrete scenario |
| Mapping        | Parameterized over input set                      | Only one example tested   |
| Property       | Property-based framework (fast-check, Hypothesis) | Only example-based        |
| Conformance    | Tool or schema validation                         | Manual check              |

</step>

<step name="audit_coverage">

**Step 3d: Coverage**

Read the project's CLAUDE.md, package.json, pyproject.toml, or Justfile. Find the test and coverage command.

1. Run coverage **excluding** the test file under audit — this is the baseline
2. Run coverage **including** the test file under audit
3. Compare coverage of the source files relevant to the assertion

Report actual numbers:

```text
Baseline: src/config-parser.ts — 43.2%
With test: src/config-parser.ts — 67.8%
Delta: +24.6% — new coverage ✓
```

**Interpret the delta:**

- **Positive delta**: The test covers new lines or branches. ✓
- **Zero delta, baseline < 100%**: REJECT — "no coverage increase." Uncovered paths exist and the test doesn't hit them.
- **Zero delta, baseline = 100%**: Coverage is saturated — no uncovered paths exist. Annotate as `saturated` in the verdict table. The test's evidentiary value comes from the other three properties.

Coverage measures execution breadth (which lines and branches are hit), not assertion strength. A property-based test that exercises fully-covered code with a broader input domain adds genuine evidence that coverage cannot measure.

If the project has no coverage tooling configured: note as a finding but do not REJECT solely for this. The other three properties still apply.

</step>

<step name="verdict">

**Step 4: Issue verdict**

Scan all findings across all assertions. If any assertion has a property failure: **REJECT.**

</step>

</audit_workflow>

<verdict_format>

**Approved:**

```text
Audit: {spec-node-path}
Verdict: APPROVED

| # | Assertion | Coupling | Falsifiability | Alignment | Coverage | Verdict |
|---|-----------|----------|----------------|-----------|----------|---------|
| 1 | {text}    | Direct   | {mutation}     | ✓         | +{n}%    | PASS    |
```

**Rejected:**

```text
Audit: {spec-node-path}
Verdict: REJECT

| # | Assertion | Property Failed | Finding | Detail |
|---|-----------|-----------------|---------|--------|
| 1 | {text}    | Coupling        | no coupling | Imports only vitest |

How tests could pass while assertions fail:
{Explain the evidentiary gap for each rejected assertion}
```

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Three reviewers approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. The tests pass if the entire codebase is deleted. Every reviewer was distracted by clean types, good structure, and comprehensive scenarios. None checked the imports.

How to avoid: Step 3a checks imports FIRST. Zero codebase imports = instant REJECT.

**Failure 2: Accepted mocking as legitimate coupling**

Reviewer saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. The real module never ran.

How to avoid: Step 3b checks for mocking AFTER confirming coupling. Import + mock = coupling severed.

**Failure 3: Guessed coverage instead of measuring**

Reviewer said "this test covers the parser's edge cases" based on reading the test code. The test exercised paths already fully covered by other tests and added zero new coverage.

How to avoid: Step 3d runs the actual coverage command. Report numbers, not impressions.

**Failure 4: Distracted by code quality signals**

Reviewer spent the entire audit checking for `as any`, verifying return types, and searching for skip patterns. The test had perfect TypeScript quality and zero evidentiary value. Quality signals are linting concerns, not audit concerns.

How to avoid: Essential principles — no mechanical detection. Check the four evidence properties only.

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] `/contextualizing` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] All assertions extracted from spec with types and test links
- [ ] Each test file: coupling checked (imports classified)
- [ ] Each test file: falsifiability checked (mutations named)
- [ ] Each test file: alignment checked (assertion-to-test match verified)
- [ ] Each test file: coverage checked (actual deltas from coverage command)
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has assertion reference, failed property, finding category, detail
- [ ] For REJECT: "how tests could pass while assertions fail" explained

</success_criteria>
