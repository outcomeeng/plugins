<operational_effectiveness_examples>
Examples of operational effectiveness issues to flag:

<example name="unverifiable_success_criteria">
❌ Flag as critical for complex skills. A `/applying` skill writing:

```xml
<success_criteria>Outcome is complete when:
- All assertions have tests
- Audit gates green
- Coverage acceptable</success_criteria>
```

**Why it fails**: "All assertions have tests" — verified how? "Audit gates green" — which gates, what does green look like? "Coverage acceptable" — what threshold?

✅ Should be:

```xml
<success_criteria>Outcome is complete when:

- Every assertion in `<spec>.md` has a `[test]` or `[review]` link resolving to an existing file (verify: count of `\[test\]\(tests/` plus `\[review\]` matches the assertion bullet count)
- Architecture audit verdict is APPROVED for every ADR touched this turn (verify: each `<audit_verdict>` XML output has `<verdict>APPROVED</verdict>` and three `<gate status="PASS">` entries; `spx validation audit-verdict` exits 0)
- Test evidence audit verdict is APPROVED for every assertion (verify: same XML schema check; per-assertion `<verdict>APPROVED</verdict>` present)
- Code audit verdict is APPROVED (verify: same XML schema check)
- All tests pass: `just test` exits 0
- Coverage delta is non-negative on assertion-relevant source files (verify: see the `coverage_protocol` procedure in `/auditing-tests` references)</success_criteria>
```

**Why it works**: Each criterion names the file or command that produces the evidence, and each "green" is defined by a concrete output shape (`<verdict>APPROVED</verdict>`) rather than an adjective.
</example>

<example name="missing_verification_gates">
❌ Flag as critical for multi-step skills. A `/applying` skill writing:

```xml
<workflow>1. Load context with `/contextualizing`
2. Author the spec
3. Write tests for assertions
4. Write implementation code
5. Run audits</workflow>
```

**Why it fails**: No stop points. Agent can write implementation before tests, or skip the architecture audit between spec and code. A failure at step 5 leaves the agent guessing which prior step introduced the defect.

✅ Should be:

```xml
<workflow>1. Load context with `/contextualizing` for the target node.

**GATE 0**: Before authoring, verify:
- [ ] `<SPEC_TREE_FOUNDATION>` marker present in session
- [ ] `<SPEC_TREE_CONTEXT>` manifest names every ancestor ADR/PDR
If gate fails, re-run `/understanding` and `/contextualizing` before continuing.

2. Author the spec with typed assertions (`/authoring`).
3. Author any ADR the spec depends on (`/architecting-<lang>`).

**GATE 1**: Before writing tests, verify:
- [ ] Architecture audit (`/auditing-<lang>-architecture`) returns APPROVED for every ADR touched
- [ ] PDR audit (`/audit-pdr`) returns APPROVED if a PDR governs this subtree
If a higher-layer artifact rejects, fix it before descending — the spec depends on the decision, not the other way around.

4. Write tests driven by spec assertions (`/testing`).

**GATE 2**: Before writing implementation, verify:
- [ ] Test audit (`/auditing-tests`) returns APPROVED per assertion
- [ ] Every test file uses canonical naming `<subject>.<evidence>.<level>[.<runner>]`
If gate fails, fix tests before writing implementation — code derives from tests, never the reverse.

5. Write implementation (`/coding-<lang>`).

**GATE 3**: Before closing the outcome, verify:
- [ ] Code audit (`/auditing-<lang>`) returns APPROVED
- [ ] `just test` exits 0
- [ ] `spx validation audit-verdict` exits 0 on every emitted verdict
If gate fails, do not commit.</workflow>
```

**Why it works**: Each gate names the artifact it depends on, the skill that produces the verdict, and the failure handling. A defect surfaces at the first gate after its introducing step, not five steps downstream.
</example>

<example name="missing_failure_modes">
❌ Flag as recommendation for complex skills:
Skill has detailed workflow but no `<failure_modes>` section.

**Why it matters**: Agents will make the same mistakes that previous agents made. Failure modes capture hard-won operational knowledge.

✅ A `/auditing-tests` skill should include:

```xml
<failure_modes>Failures from actual usage:

**Failure 1: Approved a test with zero codebase imports**
- What happened: Agent reviewed `tests/colors.scenario.l1.test.ts` and classified its coupling as Direct because the file sits next to the spec it claims to verify. The test imported only `vitest` and asserted on a constant declared inside the test file itself.
- Why it failed: Co-location is structural, not evidential. A test with zero codebase imports has no coupling to the module under test — it asserts on values it controls. Any change to the real module is invisible to this test.
- How to avoid: Step 1 of coupling verification (see `evidence-model.md`) is to enumerate codebase imports. Zero codebase imports → REJECT regardless of file location.

**Failure 2: Missed mock-severed coupling**
- What happened: Agent saw `import { database } from "../src/database"` at the top of a test and classified the coupling as Direct. Two lines later the file called `vi.mock("../src/database", () => ({ query: vi.fn().mockResolvedValue([]) }))`.
- Why it failed: `vi.mock` (and `mock.patch`, `respx.mock`, and similar) replaces the module before any test code runs. The import statement is syntactic; the runtime coupling is severed. Schema changes, query bugs, and connection failures in the real `database` module are all invisible to this test.
- How to avoid: After listing imports, scan the file for module-replacement primitives. Each match severs coupling for the named import. Unless one of the seven exception cases in `/testing` methodology applies, REJECT.</failure_modes>
```

**Why it works**: Future agents learn from past mistakes without repeating them, and each entry names a concrete signal in the file (an import, a `vi.mock` call) the next auditor can search for.
</example>

<example name="abstract_vs_concrete_examples">
❌ Flag as recommendation. An `/auditing-tests` skill writing:

```xml
<success_criteria>Audit verdict reflects test quality accurately.</success_criteria>
```

**Why it fails**: "Reflects accurately" is unfalsifiable. What does the verdict look like? How does the agent know its output matches the expected shape?

✅ Should be:

```xml
<success_criteria>Audit verdict conforms to `audit-verdict.xsd` and reports a verdict per assertion. Concrete example:

Spec assertion:
  Given a tree with one failing child, when status is computed, parent reports failing
  ([test](tests/status-rollup.scenario.l1.test.ts))

Test file imports:
  import { computeStatus } from "../../src/status";
  import { describe, expect, it } from "vitest";

Test body:
  const tree = makeTree({ children: [{ status: "failing" }] });
  expect(computeStatus(tree)).toBe("failing");

Audit verdict for this assertion (Gate 1 finding shape):
  Coupling: Direct (imports `computeStatus` from `../../src/status`)
  Falsifiability: mutation "computeStatus returns 'passing' for failing children" fails the test at line N
  Alignment: test sets up one failing child, calls computeStatus, asserts "failing" — matches the assertion
  Coverage: src/status.ts baseline 65.1% → with test 83.5% (+18.4%)
  Verdict: APPROVED — four properties satisfied.

Output shape (full verdict): `<assertion>` element with `<verdict>APPROVED</verdict>` and one `<finding>` per evaluated step.</success_criteria>
```

**Why it works**: The agent can compare its actual verdict to the example line-for-line — same field names, same shape, same expected values for a known input — and detect a mismatch before emitting.
</example>

<example name="procedural_without_operational">
❌ Flag as critical for complex skills. Example shape:

A `/decomposing` skill has a 450-line `<workflow>` covering concern boundaries, node-type selection, ordering evidence, and sparse index assignment — but the operational sections look like this:

```xml
<success_criteria>Decomposition is complete when child nodes have been created.</success_criteria>
```

No `<verification_gates>`, no `<failure_modes>`. The procedural side is exhaustive; the operational side is a single unfalsifiable sentence.

**Pattern**: Heavy procedural, light operational = agents know HOW to act but not WHETHER they succeeded.

**Why it matters**: An agent following the workflow produces child nodes that compile and lint clean, then closes the turn. The defects appear later — a child node typed as enabler when it should be outcome, indices that collide with future siblings because the agent picked `21` and `22` instead of sparse `21` and `32`, a concern boundary that cuts across an ADR rule. Each is a separate skill rerun to repair.

✅ Balanced skill has roughly equal investment in:

- Procedural content — workflow, steps, commands.
- Operational content — `<success_criteria>` with verification commands, `<verification_gates>` between irreversible steps, `<failure_modes>` naming concrete signals to grep for, and a worked example showing input → expected output for a known case.

The auditor calibration: count lines or tokens in procedural vs. operational sections. If procedural exceeds operational by more than 3:1 and the skill makes durable changes (writes files, creates nodes, opens PRs), the imbalance is critical.
</example>
</operational_effectiveness_examples>
