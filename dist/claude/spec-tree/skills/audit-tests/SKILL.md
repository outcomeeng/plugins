---
name: audit-tests
description: >-
  Test-evidence audit methodology preloaded by the test-evidence-auditor agent.
  Dispatch test-evidence-auditor to audit test evidence against spec assertions;
  the main conversation reaches this audit only through that agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<dispatch_gate>

This audit runs in the test-evidence-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the test-evidence-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on whether a spec node's tests provide genuine evidence its assertions are fulfilled — APPROVED, or REJECTED with each finding naming the assertion, the failed property, and the evidentiary gap. Four properties must hold, checked in strict order: coupling (the test exercises codebase behavior, not authored prose), falsifiability (a named mutation breaks it), alignment (it exercises the asserted behavior), and coverage (measured deltas). A test missing any property has zero evidentiary value regardless of code quality.

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/evidence-model.md`

</objective>

<essential_principles>

**COUPLING FIRST.**

A test that imports nothing from the codebase will pass forever regardless of what any file contains. Check imports before anything else. This is not a heuristic — it is a prerequisite.

**RUN COVERAGE, DON'T GUESS.**

Read the product's CLAUDE.md for the test and coverage command. Run coverage without the test (baseline), then with the test. Report actual deltas per source file. Never reason about what paths a test "probably" covers.

**NO MECHANICAL DETECTION.**

Mocking patterns, skip patterns, type annotations — these are linting concerns (SemGrep, ESLint). The auditor evaluates evidence quality, not code quality signals.

Cross-file literal validation is TypeScript-only. The base audit and non-TypeScript wrappers must not require `spx validation literal`; TypeScript wrappers may run it as an optional preliminary check.

**BINARY VERDICT.**

APPROVED or REJECTED. No middle ground. If any property is missing for any assertion, REJECTED.

</essential_principles>

<constraints>

- NEVER modify the tests under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS measure coverage by running the project's coverage command (baseline, then with the test) — never estimate which paths a test covers.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every REJECT finding.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the tests for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualize` on the spec node whose tests are being audited. This loads the spec's assertions, ancestor ADRs/PDRs, and the full hierarchy context.

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

**Compliance assertions with `[audit]` tags** (or the legacy `[review]`) are verified by agent judgment, not by tests. Skip them in the test evidence audit.

</step>

<step name="audit_coupling">

**Step 3a: Coupling**

Read the test file's import statements. Classify each import:

| Import source                                  | Classification             |
| ---------------------------------------------- | -------------------------- |
| Test framework (vitest, pytest, jest)          | Framework — does not count |
| Node modules / pip packages                    | Library — does not count   |
| Codebase path (relative import, product alias) | Codebase — counts          |

**Zero codebase imports → REJECT — "no coupling" (tautology).**

If codebase imports exist, classify using the coupling taxonomy in `${CLAUDE_SKILL_DIR}/references/evidence-model.md`:

| Category           | Definition                                                                                 | Verdict                                         |
| ------------------ | ------------------------------------------------------------------------------------------ | ----------------------------------------------- |
| Direct             | Test imports the module under test                                                         | Proceed                                         |
| Indirect           | Test imports a harness wrapping the module                                                 | Proceed — verify harness has real coupling      |
| Transitive         | Test imports a consumer of the module                                                      | Proceed — verify test level matches             |
| Laundered indirect | Imports a test-support module that exists only to expose hardcoded values back to the test | REJECT — laundering                             |
| False              | Imports module but never calls assertion-relevant functions                                | REJECT                                          |
| Partial            | Calls functions but on wrong inputs or wrong code paths                                    | REJECT                                          |
| None               | Test imports only its test framework                                                       | REJECT — tautology                              |
| Prose-coupling     | Reads an authored prose/doc body and asserts its content                                   | REJECT — couples to authored text, not behavior |

Coupling means exercising executable **behavior**, never reading a document's content. A test whose "subject" is an authored prose or documentation artifact — a skill body, a spec body, a prompt, any text the product authors and maintains — that the test reads and asserts substrings of is NOT behavioral coupling, even when that artifact is the thing the assertion names. The text passes whatever it literally contains; no code runs. This holds full-chain: a harness that exposes the authored path as a constant, or a reader helper that performs the read inside test infrastructure, does not convert a prose assertion into behavioral coupling — follow the read to its source and classify by what is ultimately exercised.

**A test whose evidence is reading an authored prose or documentation body and asserting on its content → REJECT — "prose-coupling."** The claim verifies that prose was authored, not that code behaves; its verification type belongs in `[eval]` (a graded judgment over a producer's structured verdict) or `[audit]` (a semantic constraint), and the spec assertion is retagged accordingly. Reading an authored *source-code* file for a structural lint that exercises a rule is not prose-coupling; the discriminator is whether the subject is authored prose/documentation or executable behavior.

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

**Exception**: Test doubles used under the 7 legitimate exception cases from the `/test` methodology are not "coupling severed." The auditor must identify which exception applies and verify the double type matches. See the exception cross-reference in `${CLAUDE_SKILL_DIR}/references/evidence-model.md`.

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

Read the product's CLAUDE.md, package.json, pyproject.toml, or Justfile. Find the test and coverage command.

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

If the product has no coverage tooling configured: note as a finding but do not REJECT solely for this. The other three properties still apply.

</step>

<step name="compose_language">

**Step 3e: Compose language-specific test-evidence concerns**

The four evidence properties above are language-neutral. Language-specific test-evidence concerns — the per-language check IDs and extraction targets named in `<verdict_format>` — are owned by the language test audit skill, not by this one.

Detect the test language from the node's scope — infer it from the file extension of the test files linked from the assertions (`.py` → python, `.ts`/`.tsx` → typescript, `.rs` → rust); on mixed extensions, prefer the one with the most linked files. When a language is in scope and an `audit-{lang}-tests` skill exists for it, invoke that skill via the Skill tool. It returns a verdict in this same row schema (`gate-0-deterministic`, `gate-1-assertion`, `gate-2-architectural`) carrying language-specific check IDs. **Merge its findings into the matching rows by `name`** — append, never replace — and emit one merged verdict. When no language is in scope or no matching skill exists, skip composition.

</step>

<step name="verdict">

**Step 4: Issue verdict**

Scan all findings across all assertions, including any folded in from the composed language audit. If any assertion has a property failure: **REJECTED.**

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical schema in `${CLAUDE_SKILL_DIR}/../audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The composing audit workflow records and renders the verdict through the audit journal path. Skills never hand-format markdown verdicts.

The skill's `overall` is `PASS` iff every applicable gate row is `PASS`; `FAIL` if any gate is `FAIL`; `UNKNOWN` if a gate could not be evaluated. Findings within each row carry severity `REJECT` for blocking findings (these are what flip a row to `FAIL`), `WARNING` or `INFO` for non-blocking observations.

```json
{
  "schema_version": 1,
  "skill": "audit-tests",
  "target": "<spec-node-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    {
      "name": "gate-0-deterministic",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": [
        {
          "id": "f-001",
          "file": "<path>",
          "line": null,
          "rule": "<check-id>",
          "severity": "REJECT",
          "message": "<one-line>"
        }
      ]
    },
    {
      "name": "gate-1-assertion",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": [
        {
          "id": "f-002",
          "file": "<test-file>",
          "line": null,
          "rule": "<assertion-id-or-property-name>",
          "severity": "REJECT",
          "message": "<one-line evidentiary gap>"
        }
      ]
    },
    {
      "name": "gate-2-architectural",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": [
        {
          "id": "f-003",
          "file": "<test-file>",
          "line": null,
          "rule": "<duplication-pattern>",
          "severity": "REJECT",
          "message": "<extraction target>: <nearest common test-support location>"
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Gate-skipped rows use `status: "UNKNOWN"`. Skills with no Gate 0 or Gate 2 omit those rows from the verdict. Language-specific test audit skills inherit this shape — they add language-specific check IDs and extraction targets to the findings but do not change the row names or schema.

</verdict_format>

<failure_modes>

**Failure 1: Accepted a tautological test file**

Claude approved a test file that imported only vitest. It declared OKLCH color constants and verified they satisfied contrast thresholds — pure math with zero connection to any CSS file, theme, or component. The tests pass if the entire codebase is deleted. Claude was distracted by clean types, good structure, and comprehensive scenarios, and never checked the imports.

How to avoid: Step 3a checks imports FIRST. Zero codebase imports = instant REJECT.

**Failure 2: Accepted mocking as legitimate coupling**

Claude saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. The real module never ran.

How to avoid: Step 3b checks for mocking AFTER confirming coupling. Import + mock = coupling severed.

**Failure 3: Guessed coverage instead of measuring**

Claude said "this test covers the parser's edge cases" based on reading the test code. The test exercised paths already fully covered by other tests and added zero new coverage.

How to avoid: Step 3d runs the actual coverage command. Report numbers, not impressions.

**Failure 4: Distracted by code quality signals**

Claude spent the entire audit checking for `as any`, verifying return types, and searching for skip patterns. The test had perfect TypeScript quality and zero evidentiary value. Quality signals are linting concerns, not audit concerns.

How to avoid: Essential principles — no mechanical detection. Check the four evidence properties only.

**Failure 5: Approved a prose-body substring test as direct coupling**

Claude audited a test that read an authored skill body and asserted that policy substrings were present, and rated coupling PASS — "direct coupling to the artifact; the text is the thing under test" — and falsifiability PASS — "removing the clause from the skill body breaks the test." The test exercises no code; only an edit to the authored prose falsifies it, so it carries no behavioral evidence, yet the four-property model rationalized it as conformance.

How to avoid: Step 3a — after identifying what a test reads, classify by whether the subject is executable behavior or authored prose/documentation, not by whether the path resolves to a repository file. A read of an authored prose or documentation body asserted for its content is prose-coupling → REJECT, however the path is resolved and whatever harness mediates the read.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every assertion's tests were judged on all four evidence properties with none skipped — coupling, falsifiability, alignment, and coverage; when a language is in scope, the composed `/audit-{lang}-tests` rows are judged too (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every gate row carrying its determination, with no assertion left unevaluated.
- Each REJECT finding is falsifiable: it names the assertion, the failed property, and the evidentiary gap — and for a pass-while-assertion-fails risk, how the test could pass while the assertion is unfulfilled.
- Coverage deltas are measured from the coverage command, never estimated; the same node yields the same verdict.

</success_criteria>
