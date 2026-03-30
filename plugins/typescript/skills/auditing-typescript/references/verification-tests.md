# Test Verification Rules

## Rejection Criteria for Tests

| Violation                   | Example                                    | Verdict  |
| --------------------------- | ------------------------------------------ | -------- |
| Uses mocking                | `vi.mock('execa')`                         | REJECTED |
| Tests implementation        | `expect(mockFn).toHaveBeenCalledWith(...)` | REJECTED |
| Wrong level                 | Unit test for Chrome automation            | REJECTED |
| No escalation justification | Level 3 without explanation                | REJECTED |
| Arbitrary test data         | `"test@example.com"` hardcoded             | REJECTED |

## What to Look For

```typescript
// ❌ REJECT: Mocking
vi.mock("execa", () => ({ execa: vi.fn() }));

it("runs command", async () => {
  await runCommand(args);
  expect(execa).toHaveBeenCalled(); // Tests implementation, not behavior
});

// ✅ ACCEPT: Dependency Injection
it("GIVEN valid args WHEN running THEN returns success", async () => {
  const deps: CommandDeps = {
    execa: vi.fn().mockResolvedValue({ exitCode: 0 }),
  };

  const result = await runCommand(args, deps);

  expect(result.success).toBe(true); // Tests behavior
});
```

## Test Organization (Debuggability)

Check for:

- [ ] Test values in separate file or fixtures (not inline anonymous data)
- [ ] Named test categories (`TYPICAL.BASIC` not bare objects)
- [ ] Individual tests for each category (one expect per test)
- [ ] Parametrized tests for systematic coverage (`it.each`)
- [ ] Property-based tests (fast-check) come AFTER named cases

## Test Ordering (Fast Failure)

Check for:

- [ ] Environment/availability checks run first (is tool installed?)
- [ ] Simple operations run before complex ones
- [ ] Infrastructure-dependent tests in separate directories
- [ ] Fast tests before slow tests

## Anti-Patterns to Flag

- ⚠️ Starting with property tests without named cases first → Hard to debug
- ⚠️ Inline test data without names → Not reusable, no context on failure
- ⚠️ Single `it.each` for all cases → Can't set breakpoint on specific case
- ⚠️ `vi.mock()` at module level → Tests implementation, not behavior
