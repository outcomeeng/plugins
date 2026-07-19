<operational_effectiveness_examples>
Examples of operational effectiveness issues to flag:

<example name="unverifiable_success_criteria">
❌ Flag as critical for complex skills. A `/apply` skill writing:

```text
<success_criteria>Outcome is complete when:
- Every assertion has evidence
- Required audits are approved
- Tests and validation pass</success_criteria>
```

**Why it fails**: "Every assertion has evidence" — verified how? "Required audits are approved" — which verdict field records approval? "Tests and validation pass" — which commands?

✅ Should be:

```text
<success_criteria>Outcome is complete when:

- `spx validation markdown` exits 0 after every assertion receives its declared `[test](...)`, `[eval](...)`, or `[audit]` evidence form.
- The structured verdict from each required artifact auditor records `APPROVED` for the exact committed subject.
- The target repository's declared node-test command exits 0 for every changed node.
- The target repository's declared changeset validation command exits 0.</success_criteria>
```

**Why it works**: Each criterion names the command or structured verdict that establishes the result, without relying on an adjective or undocumented control-flow markup.
</example>

<example name="missing_failure_modes">
❌ Flag as recommendation for complex skills:
Skill has detailed workflow but no `<failure_modes>` section.

**Why it matters**: Claude will repeat mistakes that prior runs did not preserve. Failure modes capture hard-won operational knowledge.

✅ A `/audit-tests` skill should include:

```text
<failure_modes>Failures from actual usage:

**Failure 1: Approved a test with zero codebase imports**
- What happened: Claude reviewed `tests/colors.scenario.l1.test.ts` and classified its coupling as Direct because the file sits next to the spec it claims to verify. The test imported only `vitest` and asserted on a constant declared inside the test file itself.
- Why it failed: Co-location is structural, not evidential. A test with zero codebase imports has no coupling to the module under test — it asserts on values it controls. Any change to the real module is invisible to this test.
- How to avoid: enumerate codebase imports before judging coupling. Zero codebase imports → REJECT regardless of file location.

**Failure 2: Missed mock-severed coupling**
- What happened: Claude saw `import { database } from "../src/database"` at the top of a test and classified the coupling as Direct. Two lines later the file called `vi.mock("../src/database", () => ({ query: vi.fn().mockResolvedValue([]) }))`.
- Why it failed: `vi.mock` (and `mock.patch`, `respx.mock`, and similar) replaces the module before any test code runs. The import statement is syntactic; the runtime coupling is severed. Schema changes, query bugs, and connection failures in the real `database` module are all invisible to this test.
- How to avoid: After listing imports, scan the file for module-replacement primitives. Each match severs coupling for the named import. Unless one of the seven exception cases in `/test` methodology applies, REJECT.</failure_modes>
```

**Why it works**: Future runs retain the past mistake without repeating it, and each entry names a concrete signal in the file (an import, a `vi.mock` call) the next auditor can search for.
</example>

<example name="abstract_vs_concrete_examples">
❌ Flag as recommendation. An `/audit-tests` skill writing:

```text
<success_criteria>Audit verdict reflects test quality accurately.</success_criteria>
```

**Why it fails**: "Reflects accurately" is unfalsifiable. What does the verdict look like? How does Claude know its output matches the expected shape?

✅ Should be:

```text
<success_criteria>Audit verdict conforms to the auditor's declared structured output and reports a verdict per assertion. Concrete example:

Spec assertion:
  Given a tree with one failing child, when status is computed, parent reports failing
  ([test](tests/status-rollup.scenario.l1.test.ts))

Test file imports:
  import { computeStatus } from "../../src/status";
  import { describe, expect, it } from "vitest";

Test body:
  const tree = makeTree({ children: [{ status: "failing" }] });
  expect(computeStatus(tree)).toBe("failing");

Audit verdict for this assertion:
  Coupling: Direct (imports `computeStatus` from `../../src/status`)
  Falsifiability: mutation "computeStatus returns 'passing' for failing children" fails the test at line N
  Alignment: test sets up one failing child, calls computeStatus, asserts "failing" — matches the assertion
  Coverage: src/status.ts baseline 65.1% → with test 83.5% (+18.4%)
  Verdict: APPROVED — four properties satisfied.

Output shape: one structured assertion row recording the assertion path, evidence properties, findings, and `APPROVED` verdict.</success_criteria>
```

**Why it works**: Claude can compare its actual verdict to the example line-for-line — same field names, same shape, same expected values for a known input — and detect a mismatch before emitting.
</example>

<example name="procedural_without_operational">
❌ Flag as critical for complex skills. Example shape:

A `/decompose` skill has a 450-line `<workflow>` covering concern boundaries, node-type selection, ordering evidence, and sparse index assignment — but the operational sections look like this:

```text
<success_criteria>Decomposition is complete when child nodes have been created.</success_criteria>
```

No validation command, observable output check, or `<failure_modes>` grounded in actual usage. The procedural side is exhaustive; the operational side is a single unfalsifiable sentence.

**Pattern**: Heavy procedural, light operational leaves Claude knowing how to act without evidence that the result succeeded.

**Why it matters**: Claude, following the workflow, produces child nodes that compile and lint clean, then closes the turn. The defects appear later — a child node typed as enabler when it should be outcome, indices that collide with future siblings because Claude picked `21` and `22` instead of sparse `21` and `32`, a concern boundary that cuts across an ADR rule. Each is a separate skill rerun to repair.

✅ Balanced skill has roughly equal investment in:

- Procedural content — workflow, steps, commands.
- Operational content — `<success_criteria>` with verification commands or boolean output checks, `<failure_modes>` naming concrete signals to inspect, and a worked example showing input → expected output for a known case.

For a skill that makes durable changes, treat the imbalance as critical when its declared success cannot be established from the named commands, structured outputs, or boolean checks.
</example>
</operational_effectiveness_examples>
