---
name: reviewing-typescript-tests
description: >-
  ALWAYS invoke this skill when reviewing TypeScript tests for evidentiary value and spec compliance.
  NEVER review tests without this skill.
---

<objective>
TypeScript-specific test review. Extends `/reviewing-tests` with TypeScript testing patterns, property-based testing requirements, and TypeScript code quality checks.

</objective>

<quick_start>
**PREREQUISITE**: Read these skills first — they are the law:

- `/reviewing-tests` — Foundational review protocol (Phases 1–4: spec structure, evidentiary integrity, lower-level assumptions, ADR/PDR compliance)
- `/testing` — Methodology (5 stages, 5 factors, 7 exceptions)
- `/standardizing-typescript` — TypeScript code standards

Execute the 4 foundational phases from `/reviewing-tests` first, then continue with the TypeScript-specific phases below.

**TypeScript-specific grep patterns** for foundational Phase 2 (evidentiary integrity):

```bash
# Find silent skips (REJECT if on required deps)
grep -rn "it.skip\|describe.skip\|test.skip\|skipIf" {test_dir}

# Find mocking (any = REJECT)
grep -rn "vi.mock\|vi.spyOn\|jest.mock\|jest.spyOn\|sinon\.\|stub(" {test_dir}
```

**TypeScript filename conventions** for foundational Phase 1.2 (test file linkage):

| Level | Filename suffix        | Example                       |
| ----- | ---------------------- | ----------------------------- |
| 1     | `.unit.test.ts`        | `uart-tx.unit.test.ts`        |
| 2     | `.integration.test.ts` | `uart-tx.integration.test.ts` |
| 3     | `.e2e.test.ts`         | `uart-tx.e2e.test.ts`         |

When reporting findings, cite source skills:

- "Per /reviewing-tests Phase 1.1, assertion type must match test strategy"
- "Per /standardizing-typescript, all functions must have explicit return types"

</quick_start>

<typescript_phases>
Execute these AFTER completing the 4 foundational phases from `/reviewing-tests`.

<phase name="property_based_testing">
Property-based testing is **MANDATORY** for code types that have algebraic properties:

| Code Type               | Required Property        | Framework                |
| ----------------------- | ------------------------ | ------------------------ |
| Parsers                 | `parse(format(x)) == x`  | fast-check / `fc.assert` |
| Serialization           | `decode(encode(x)) == x` | fast-check / `fc.assert` |
| Mathematical operations | Algebraic properties     | fast-check / `fc.assert` |
| Complex algorithms      | Invariant preservation   | fast-check / `fc.assert` |

**5.1 Identify Applicable Code Types**

```bash
# Find parsers and serializers
grep -rn "function parse\|function encode\|function decode\|function serialize\|function deserialize" {src_dir}
grep -rn "export.*parse\|export.*encode\|export.*decode\|export.*serialize" {src_dir}

# Check if tests have property-based coverage
grep -rn "fc.assert\|fc.property\|from 'fast-check'\|from \"fast-check\"" {test_dir}
```

**5.2 Evaluate Coverage**

For each identified parser/serializer/math operation:

| Found                                        | Verdict    |
| -------------------------------------------- | ---------- |
| `fc.assert(fc.property(...))` with roundtrip | PASS       |
| Only example-based tests                     | **REJECT** |
| No tests at all                              | **REJECT** |

**Example rejection:**

```typescript
// ❌ REJECT: Parser with only example-based tests
it("parses simple JSON", () => {
  const result = parse("{\"key\": \"value\"}");
  expect(result).toEqual({ key: "value" });
});

// Missing: fc.assert + roundtrip property
```

**5.3 Verify Property Quality**

Property tests must test meaningful properties, not just "doesn't throw":

```typescript
// ❌ REJECT: Trivial property (only tests "doesn't throw")
it("handles arbitrary strings", () => {
  fc.assert(
    fc.property(fc.string(), (text) => {
      parse(text); // No assertion — just checks it doesn't throw
    }),
  );
});

// ✅ ACCEPT: Meaningful roundtrip property
it("roundtrips valid values", () => {
  fc.assert(
    fc.property(validJsonArbitrary(), (value) => {
      expect(parse(format(value))).toEqual(value);
    }),
  );
});
```

**GATE 5**: Before proceeding to Phase 6, verify:

- [ ] Identified all parsers, serializers, math operations, complex algorithms in code under test
- [ ] Ran grep for `fc.assert` / `fc.property` patterns in test files
- [ ] Each applicable code type has property-based tests with meaningful properties

If any check fails, STOP and REJECT with detailed findings.

</phase>

<phase name="typescript_test_quality">
Verify tests follow TypeScript testing patterns per `/standardizing-typescript`.

**6.1 Type Safety**

```bash
# Find any type assertions that bypass safety
grep -rn "as any\|@ts-ignore\|@ts-expect-error" {test_dir}
```

`as any` in test code is **REJECT** — tests should use concrete types. `@ts-expect-error` with explanation is acceptable only when testing error paths of third-party libraries.

**6.2 No Mocking**

```bash
# Find mocking patterns (comprehensive)
grep -rn "vi.mock\|vi.spyOn\|vi.fn()\|jest.mock\|jest.spyOn\|jest.fn()\|sinon\.\|createStub\|stub(" {test_dir}
```

**Any mocking = REJECT.** Use dependency injection, interface implementations, or stub classes instead.

Legitimate alternatives (NOT mocking):

| Pattern                       | Acceptable? | Why                                                  |
| ----------------------------- | ----------- | ---------------------------------------------------- |
| Interface + stub class        | Yes         | Real implementation of interface, no behavior faking |
| `vi.useFakeTimers()`          | Yes         | Exception 3 from /testing (time/concurrency)         |
| Spy class with call recording | Yes         | Exception 2 from /testing (interaction protocols)    |
| `vi.mock("module")`           | **REJECT**  | Replaces real module with fake                       |
| `vi.spyOn(obj, "method")`     | **REJECT**  | Intercepts real method                               |

**6.3 Return Types**

```bash
# Find test helper functions missing return types
grep -rn "function " {test_dir} | grep -v ": \w"
```

All helper functions in test files should have explicit return types per `/standardizing-typescript`.

**6.4 Test Organization**

- [ ] Test names use `it("verb phrase", ...)` describing the scenario
- [ ] Assertions verify outcomes, not implementation details
- [ ] `beforeEach`/`afterEach` clean up resources (temp dirs, servers)
- [ ] No hardcoded ports, paths, or environment-specific values
- [ ] Imports are explicit (no `import *`)

**GATE 6 (FINAL)**: Before issuing verdict, verify:

- [ ] No `as any` or `@ts-ignore` in test code
- [ ] No mocking patterns found (`vi.mock`, `vi.spyOn`, `jest.mock`, etc.)
- [ ] Helper functions have return types
- [ ] Test organization checklist passes

If all gates passed (foundational 1–4 + TypeScript 5–6), issue APPROVED. Otherwise, REJECT with detailed findings.

</phase>

</typescript_phases>

<concrete_examples>
**Example 1: APPROVED verdict**

Reviewing `spx/01-config/03-parser.story/`

Phase 1 checks (from /reviewing-tests):

```bash
$ grep -A 5 "^### Scenarios" parser.story.md
### Scenarios

- Given a config file with nested sections, when parsed, then all section values are accessible by dotted path ([test](tests/config-parser.unit.test.ts))

$ ls -la tests/config-parser.unit.test.ts
-rw-r--r-- 1 user group 3421 Jan 15 10:23 tests/config-parser.unit.test.ts
✓ File exists, Level 1 matches .unit.test.ts suffix
```

Phase 2 checks (from /reviewing-tests, using TypeScript grep patterns):

```bash
$ grep -rn "it.skip\|describe.skip\|test.skip" tests/
(no results)
✓ No silent skips

$ grep -rn "vi.mock\|vi.spyOn\|jest.mock" tests/
(no results)
✓ No mocking
```

Phase 5 checks (TypeScript-specific):

```bash
$ grep -rn "fc.assert\|fc.property" tests/
tests/config-parser.unit.test.ts:45:    fc.assert(fc.property(validConfigArb(), (config) => {
✓ Property-based test for parser roundtrip
```

Phase 6 checks (TypeScript-specific):

```bash
$ grep -rn "as any\|@ts-ignore" tests/
(no results)
✓ No type safety bypasses
```

**Verdict: APPROVED** - All assertions have genuine evidentiary coverage at appropriate levels.

---

**Example 2: REJECT verdict**

Reviewing `spx/02-api/05-auth.feature/`

Phase 2 finds mocking:

```bash
$ grep -rn "vi.mock\|vi.spyOn" tests/
tests/auth.integration.test.ts:8:vi.mock("../src/database", () => ({ query: vi.fn() }))
```

**Verdict: REJECT**

| # | Category | Location                   | Issue                      | Required Fix                                  |
| - | -------- | -------------------------- | -------------------------- | --------------------------------------------- |
| 1 | Mocking  | auth.integration.test.ts:8 | vi.mock on database module | Use real database with test harness (Level 2) |

**How Tests Could Pass While Assertion Fails:**

Database module is entirely replaced with a fake. Tests verify behavior against a fake database that always succeeds. Real database could have schema mismatches, connection failures, or constraint violations that the mocked tests will never catch.

</concrete_examples>

<rejection_triggers>
Quick reference — includes both foundational triggers (from `/reviewing-tests`) and TypeScript-specific triggers:

| Category            | Trigger                                                                   | Verdict | Source             |
| ------------------- | ------------------------------------------------------------------------- | ------- | ------------------ |
| **Spec Structure**  | Code examples in spec                                                     | REJECT  | /reviewing-tests   |
| **Spec Structure**  | Assertion type doesn't match test strategy (Property without `fc.assert`) | REJECT  | /reviewing-tests   |
| **Spec Structure**  | Missing or broken test file links (inline or table)                       | REJECT  | /reviewing-tests   |
| **Spec Structure**  | Language about "pending" specs                                            | REJECT  | /reviewing-tests   |
| **Spec Structure**  | Temporal language ("currently", "the existing", file references)          | REJECT  | /reviewing-tests   |
| **Level**           | Assertion tested at wrong level                                           | REJECT  | /reviewing-tests   |
| **Dependencies**    | `it.skip` / `describe.skip` on required dependency                        | REJECT  | /reviewing-tests   |
| **Dependencies**    | Harness referenced but missing                                            | REJECT  | /reviewing-tests   |
| **Decision Record** | Test violates ADR/PDR constraint                                          | REJECT  | /reviewing-tests   |
| **Evidentiary**     | Test can pass with broken impl                                            | REJECT  | /reviewing-tests   |
| **Property-Based**  | Parser without `fc.assert` roundtrip test                                 | REJECT  | TypeScript Phase 5 |
| **Property-Based**  | Serializer without `fc.assert` roundtrip test                             | REJECT  | TypeScript Phase 5 |
| **Property-Based**  | Math operation without property tests                                     | REJECT  | TypeScript Phase 5 |
| **TypeScript**      | `as any` or `@ts-ignore` in test code                                     | REJECT  | TypeScript Phase 6 |
| **TypeScript**      | Mocking (`vi.mock`, `vi.spyOn`, `jest.mock`)                              | REJECT  | TypeScript Phase 6 |

</rejection_triggers>

<success_criteria>
Task is complete when:

- [ ] Verdict is APPROVED or REJECT (no middle ground)
- [ ] All 4 foundational phases from `/reviewing-tests` executed
- [ ] Both TypeScript-specific phases (5–6) executed
- [ ] Property-based test coverage verified for parsers/serializers/math/algorithms
- [ ] Each rejection reason has file:line location
- [ ] Evidentiary gap explained (how tests could pass while assertion fails)
- [ ] Output follows format from `/reviewing-tests` (APPROVED or REJECT template)

</success_criteria>
