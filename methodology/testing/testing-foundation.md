# Testing Philosophy

## The Overarching Question

> **What evidence do I need to convince the user that my code correctly implements the specification?**

Every test exists to answer this question. Tests are not bureaucracy or checkbox items - they are **evidence** that your code works.

---

## Tests Serve Three Purposes

At the time of writing code, create tests for ALL future scenarios:

| Purpose              | What It Means                     | Example                                                    |
| -------------------- | --------------------------------- | ---------------------------------------------------------- |
| **Code quickly**     | Fast feedback loop while building | Run Level 1 tests in <1 second to verify logic as you code |
| **Evidence quickly** | Prove the spec is implemented     | Show user that acceptance criteria are met                 |
| **Debug quickly**    | Find bugs when regressions occur  | Named test cases point directly to the broken behavior     |

The 4-part progression (below) organizes tests to serve all three purposes simultaneously.

---

## Key Principle: Find the Right Test Combination

**Not "bottom up always"** - instead, find the combination of tests across levels that provides the best tradeoff for your situation.

### The Question Per Outcome

For every **functional assertion** or **quality constraint** in your work item, ask:

> **How can this be proven, and which combination of tests at which levels provides the adequate tradeoff between:**
>
> 1. **Effort** - How costly is this test to write, run, and maintain?
> 2. **Insight** - What does a passing test actually prove? What does a failure reveal?
> 3. **Assumptions** - What hidden assumptions does this test surface or validate?
> 4. **Protection** - How well does this test guard against future regressions?

### The Three Dimensions

Every test level offers different tradeoffs across three orthogonal dimensions:

#### 1. Detection: What Bugs Can This Level Find?

Each level has a **different lens** - not progressively broader, but genuinely different:

| Level  | Detects                                                      | Cannot Detect                                                                                                                         |
| ------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| **L1** | Algorithmic bugs, edge cases, invariant violations           | Race conditions (no concurrency), integration mismatches (only uses standard dependencies like temp directories, build tools and git) |
| **L2** | Race conditions, integration mismatches, contract violations | Pure logic bugs (hidden in the stack), graphical UX issues (only command line / terminal UI)                                          |
| **L3** | Workflow breaks, UX failures, real-world edge cases          | Algorithmic bugs (hidden deep in call stack), intermittent race conditions (not enough stress)                                        |

**Example insights**: L1 property-based tests catch algorithmic bugs that L3 almost never detects. L2 randomized harnesses catch race conditions that L1 can't see and L3 rarely triggers.

#### 2. Validity: What Does a Passing Test Prove?

| Level  | A Passing Test Proves                           | False Confidence Risk                                                                           |
| ------ | ----------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **L1** | The isolated logic is correct for tested inputs | Low - tests exactly what it claims; limited only by input coverage                              |
| **L2** | Components integrate correctly with the harness | Medium - depends on harness breadth of randomization and fidelity to production                 |
| **L3** | The workflow succeeds in the test environment   | High - can pass while feature is broken in production (env differences, timing, browser quirks) |

**Key insight**: L3's passing test is the least trustworthy signal. "E2E tests pass" does not mean "it's logically and algorithmically correct", "it will work at scale", or "it works for users."

#### 3. Cost: What Investment Does This Level Require?

| Aspect          | L1                          | L2                                             | L3                                             |
| --------------- | --------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| **Upfront**     | Low (no setup, just code)   | Medium (harnesses, fixtures, containers)       | High (real env, credentials, test accounts)    |
| **Per-run**     | Milliseconds                | Seconds to minutes                             | Minutes to hours                               |
| **Maintenance** | Low (stable, deterministic) | Medium (harness evolution, dependency updates) | High (brittle to UI changes, flaky, env drift) |

**Key insight**: A test that's cheap to write can be expensive to maintain. Poorly designed tests at all levels become "tests you're afraid to touch."

### Where Evidence Can Live

Some outcomes can be proven at multiple levels; others require specific levels:

| Outcome                             | Can Be Proven At | Best Combination                                  |
| ----------------------------------- | ---------------- | ------------------------------------------------- |
| Algorithm correctness               | Level 1          | L1 with property-based testing                    |
| Parser handles grammar              | Level 1          | L1 typical + edges + properties                   |
| Database query returns correct data | Level 2 minimum  | L2 integration; L1 only if query logic is complex |
| CLI binary behaves correctly        | Level 2 minimum  | L2 with fixture files                             |
| API contract is honored             | Level 2 or 3     | L2 against test server; L3 against staging        |
| Clipboard works in browsers         | Level 3 only     | L3 in real browser; L1 tests prove nothing        |
| Payment flow completes              | Level 3 only     | L3 with test credentials                          |
| Full user workflow succeeds         | Level 3 only     | L3 happy path + critical edges                    |

### The Clipboard Example

Consider a "copy to clipboard" React component. What combination proves it works?

**Level 1 unit test**: Component renders without errors

- **Insight**: None about clipboard functionality
- **Assumptions surfaced**: None - clipboard API not exercised
- **Protection**: None for the actual feature
- **Verdict**: Waste of effort for this assertion

**Level 3 E2E test**: Actually copies text in real browser

- **Insight**: Full - proves the feature works as users experience it
- **Assumptions surfaced**: Browser compatibility, permissions, HTTPS requirements
- **Protection**: High - catches real-world regressions
- **Verdict**: Essential for this assertion

**Best combination**: Skip L1/L2 entirely, write L3 tests in target browsers.

### The Pricing Engine Example

Consider a complex pricing calculation with discounts, taxes, and promotions.

**Level 2 only**: Integration test creates order, checks total

- **Insight**: Knows IF total is wrong, not WHERE
- **Assumptions surfaced**: Database behavior, but not calculation edge cases
- **Protection**: Catches that something broke, but debugging is hard
- **Verdict**: Necessary but insufficient

**Level 1 + Level 2**: Unit tests for calculation + integration test for flow

- **Insight**: L1 shows exactly which rule is broken; L2 confirms it works end-to-end
- **Assumptions surfaced**: L1 surfaces edge cases (negative prices, overflow); L2 surfaces integration assumptions
- **Protection**: L1 catches logic regressions instantly; L2 catches integration regressions
- **Verdict**: Right combination for complex logic

**Best combination**: L1 with all 4 parts (typical, edges, systematic, property-based) + L2 for integration.

---

## Add Lower Levels for Debuggability

When Level 2 or 3 is required for evidence, add Level 1 tests ONLY if:

1. **The code is complex** - Your logic (algorithms, parsers, rule engines), not library wiring
2. **Debugging will be hard** - When the higher-level test fails, will you know where to look? Will you be able to inspect the logic of your code without writing ad hoc tests?
3. **Property-based testing adds value** - Would testing with generated inputs find edge cases?

### The Debuggability Question

> When this Level 2/3 test fails, will a Level 1 test help me find the bug faster?

| Scenario                                        | Add Level 1? | Reason                                        |
| ----------------------------------------------- | ------------ | --------------------------------------------- |
| Integration test fails on a complex algorithm   | YES          | Level 1 isolates the algorithm                |
| Integration test fails on argparse flag parsing | NO           | Trust argparse; check your usage              |
| E2E test fails on payment flow                  | MAYBE        | If payment calculation logic is complex, yes  |
| E2E test fails on clipboard                     | NO           | It's a browser API call, nothing to unit test |

---

## Five Factors Determine Test Level

When deciding what tests to write, consider:

### 1. What the Spec Promises

The acceptance criteria drive the minimum test level:

- "User can export data as CSV" → Level 1 with temp directory (file I/O is Level 1)
- "User can complete checkout" → Level 3 (real payment provider)
- "CLI processes Hugo site" → Level 2 (project-specific binary)
- "Prices are calculated correctly" → Level 1 (pure calculation)

### 2. Dependencies Involved

| Dependency                 | Minimum Level |
| -------------------------- | ------------- |
| None (pure function)       | Level 1       |
| File system (temp dirs)    | Level 1       |
| Database                   | Level 2       |
| External HTTP API          | Level 2       |
| Project-specific binary    | Level 2       |
| Browser API                | Level 3       |
| Third-party service (live) | Level 3       |

### 3. Code Complexity

| Code Type                                   | Level 1 Value                |
| ------------------------------------------- | ---------------------------- |
| **Your logic** (algorithms, parsers, rules) | HIGH - test thoroughly       |
| **Library wiring** (argparse, Zod, YAML)    | LOW - trust the library      |
| **Simple glue code**                        | LOW - covered by integration |

### 4. Debuggability Needs

Ask: "When a bug is reported, how will I find it?"

- Complex business logic → Level 1 helps isolate
- Simple CRUD → Integration test points to the operation
- Browser behavior → Can only debug in browser

### 5. Where Achievable Confidence Lives

Some guarantees can ONLY be proven at certain levels:

| You want to know...           | Achievable at |
| ----------------------------- | ------------- |
| Your math is correct          | Level 1       |
| Your SQL is valid             | Level 2       |
| The API accepts your requests | Level 2       |
| Users can complete the flow   | Level 3       |
| It works in Safari            | Level 3       |

---

## Trust the Library

Libraries like argparse, yargs, Zod, pydantic, and js-yaml are battle-tested. Instead of verifying that they work by mocking or faking dependencies at level 1, test whether your integration works as designed with a proper test harness at level 2.

### What NOT to Test

```python
# DON'T test that argparse parses flags
def test_verbose_flag_is_parsed():
    args = parser.parse_args(["--verbose"])
    assert args.verbose is True  # Tests argparse, not your code


# DON'T test that Zod validates schemas
def test_zod_rejects_invalid_email():
    result = schema.safeParse({"email": "invalid"})
    assert result.success is False  # Tests Zod, not your code
```

### What TO Test

```python
# DO test YOUR logic that uses the parsed result
def test_verbose_mode_produces_detailed_output():
    output = run_command(verbose=True)
    assert "DEBUG:" in output  # Tests your behavior


# DO test YOUR business rules, not validation
def test_user_with_valid_email_can_register():
    user = register(email="valid@example.com")
    assert user.id is not None  # Tests your registration logic
```

### Implicit Library Testing via Integration

For boundary validation, use randomized fixtures at Level 2:

1. Generate diverse inputs using seeded randomization
2. Pass them through your integration tests
3. If validation fails unexpectedly, the test catches it
4. You've tested the schema implicitly without writing "does Zod reject X?" tests

### How to Design Randomized Test Harnesses

Randomized Test Harnesses are key to maximize insight per effort spent and uncover assumptions that might be hidden by using hardcoded values.

Always ask yourself first: what is the data structure that describes the fixture. For example, when working with a directory tree, the data structure is a directed acyclic graph (DAG). So your harness should NOT generate directories and files but rather a DAG, which you can test at level 2. Only then should your test harness turn the DAG into an actual directory tree in a temporary directory.

### Seeding Generated Test Data

As you will read in the next subsection, generating test data is crucial for dependable testing that unravels hidden assumptions. All randomized tests should be seeded but the seed should be derived from the system time (i.e., be different every time) and be shown when a test fails so it can be rerun with the same seed.

This way, we maximize the variety of randomized test data while still providing the possibility to reproduce test runs that fail.

---

## The 4-Part Progression

For organizing tests at any level to serve all three purposes (code/evidence/debug):

### Part 0: Shared Test Values File

Create a `module.test-values.ts` file with named, typed test data:

```typescript
export const TYPICAL = {
  BASIC: { input: "simple", expected: 42 },
  COMPLEX: { input: "with-flags", expected: 100 },
} as const;

export const EDGES = {
  EMPTY: { input: "", expected: 0 },
  MAX: { input: "x".repeat(1000), expected: "ERROR" },
} as const;
```

**Why**: Reusable, named, type-safe. Single source of truth for test data.

### Part 1: Named Typical Cases

One `it()` per category, using Part 0 data:

```typescript
describe("GIVEN typical inputs", () => {
  it("WHEN processing BASIC input THEN returns expected", () => {
    const { input, expected } = TYPICAL.BASIC;
    expect(process(input)).toBe(expected);
  });
});
```

**Why**: When test fails, you know EXACTLY which case. Set breakpoint, inspect `TYPICAL.BASIC`.

**Serves**: Code quickly (fast feedback), Debug quickly (immediate isolation)

### Part 2: Named Edge Cases

One `it()` per boundary condition:

```typescript
describe("GIVEN boundary conditions", () => {
  it("WHEN processing EMPTY input THEN handles correctly", () => {
    const { input, expected } = EDGES.EMPTY;
    expect(process(input)).toBe(expected);
  });
});
```

**Why**: Each boundary is independently debuggable. Failures point to specific conditions.

**Serves**: Evidence quickly (proves edge handling), Debug quickly (boundary isolation)

### Part 3: Systematic Coverage Loop

Loop discovers missing categories:

```typescript
describe("GIVEN all known cases", () => {
  it("WHEN testing all THEN pass", () => {
    for (const [name, testCase] of Object.entries(TYPICAL)) {
      expect(process(testCase.input)).toBe(testCase.expected);
    }
  });
});
```

**Why**: Should ONLY fail if Parts 1-2 missed a category. Inspect `name` at breakpoint to discover what's missing.

**Serves**: Evidence quickly (comprehensive), Debug quickly (reveals gaps)

### Part 4: Generated/Property-Based

Progress from controlled generation to full property-based:

```typescript
describe("GIVEN generated inputs", () => {
  // Controlled: seeded randomization
  it("WHEN testing 10 samples THEN all pass", async () => {
    await withTestEnv(async ({ seeded }) => {
      for (let i = 0; i < 10; i++) {
        const input = seeded.gen.string({ length: 5 });
        expect(process(input)).toBeDefined();
      }
    });
  });

  // Full property-based
  it("WHEN testing property THEN always holds", async () => {
    await withTestEnv(async ({ fcAssert }) => {
      fcAssert(
        fc.property(fc.string(), (input) => {
          return process(input) !== null;
        }),
      );
    });
  });
});
```

**Why**: Reproducible via `TEST_SEED`. Escalate from debuggable loops to comprehensive properties.

**Serves**: Evidence quickly (finds unexpected cases), Debug quickly (seed enables reproduction)

---

## Level Breadth

The 4-part progression applies at each level, but with different breadth:

| Level                     | Typical Parts      | Why                                     |
| ------------------------- | ------------------ | --------------------------------------- |
| **Level 1** (Unit)        | All 4 parts        | Cheapest - can afford full breadth      |
| **Level 2** (Integration) | Parts 1-2, maybe 3 | More expensive - focus on key scenarios |
| **Level 3** (E2E)         | Part 1 only        | Most expensive - critical flows only    |

### Example Breakdown

For a "user registration" feature:

**Level 3** (E2E - Part 1 only):

- `test_complete_signup_workflow` - One test for the happy path

**Level 2** (Integration - Parts 1-2):

- `test_user_repository_saves_user` (typical)
- `test_email_service_sends_welcome` (typical)
- `test_duplicate_email_rejected` (edge)

**Level 1** (Unit - All 4 parts):

- Part 0: `VALID_EMAILS`, `INVALID_EMAILS`, `PASSWORDS` test values
- Part 1: Named typical validation cases
- Part 2: Named edge cases (empty, too long, unicode)
- Part 3: Loop over all known patterns
- Part 4: Property-based testing of validation rules

---

## Anti-Patterns

### Testing Library Behavior

```python
# BAD: Tests argparse, not your code
def test_flag_parsing():
    assert parser.parse_args(["--verbose"]).verbose is True
```

**Instead**: Test YOUR behavior that depends on the flag.

### Bottom-Up When Evidence Lives Higher

```python
# BAD: Writing Level 1 tests for clipboard
def test_clipboard_component_renders():
    render(<CopyButton />)
    expect(screen.getByRole('button')).toBeInTheDocument()
    # Proves nothing about clipboard!
```

**Instead**: Write Level 3 test that actually verifies clipboard works.

### Skipping Debuggability for Complex Logic

```python
# BAD: Only integration test for complex algorithm
def test_pricing_integration(database):
    order = create_order(items=[...])
    assert order.total == 157.42
    # When this fails, where's the bug?
```

**Instead**: Add Level 1 tests for the pricing calculation so failures are isolated.

### Anonymous Test Data

```python
# BAD: Magic numbers, no names
def test_processing():
    assert process("abc") == 42
    assert process("xyz") == 100
    # What do "abc" and "xyz" represent?
```

**Instead**: Use Part 0 named test values with meaningful category names.

---

## Summary

1. **Ask**: What evidence do I need to prove this spec is implemented?
2. **Find**: At what level does that evidence actually live?
3. **Test there**: Don't write lower-level tests if they prove nothing
4. **Add lower levels**: Only for debuggability of complex logic
5. **Organize**: Use the 4-part progression for maximum value
6. **Trust libraries**: Don't test argparse, Zod, etc.

The goal is not "passing tests" or "high coverage" - it's **justified confidence that your code works in the real world**.

---

## Test Infrastructure

Keep test infrastructure separate from tests. Language-specific skills define concrete paths for your ecosystem, but the categories are universal:

### 1. Test Environment Context Managers

Shared utilities (like `withTestEnv`) that handle:

- Seeding and reproducibility
- Temp directory lifecycle
- Environment variable isolation
- Shared setup/teardown across test suites

### 2. Containerized Services

Local databases, dev servers, message queues for integration tests. Managed via docker-compose or similar.

### 3. Fixtures

Named test values (TYPICAL, EDGES) - static data collections for the 4-part progression.

### 4. Generators

Randomized data generation with seeding for reproducibility. Always derive seed from system time; show seed on failure for reproduction.

---

## Co-located Tests (Outcome Engineering Framework)

Tests stay with their specs permanently. No graduation.

| Location                     | Level indicated by | Purpose                       |
| ---------------------------- | ------------------ | ----------------------------- |
| `spx/.../tests/`             | Filename suffix    | All tests, co-located         |
| `*.unit.test.{ts,py}`        | Level 1            | Pure logic, DI                |
| `*.integration.test.{ts,py}` | Level 2            | Real dependencies via harness |
| `*.e2e.test.{ts,py}`         | Level 3            | Full system with credentials  |

**The invariant**: All tests in `spx/.../tests/` MUST NOT PASS unless the spec has been implemented completely. Node state is derived from test results — passing tests mean the node is Passing, failing tests mean Failing. No stored status file; reality is the oracle.

**No graduation**: Tests remain co-located with their specs regardless of nesting depth. Descendant tests stay in their own node's `tests/` directory, addressed by filename path rather than promoted to an ancestor.

---

## When You Don't Know: Stop and Ask

### For Level 2 Tests

If you cannot describe the test harness for a dependency, STOP and ask:

> I need to write integration tests for [dependency].
>
> To proceed, I need to know:
>
> 1. What test harness exists or should I build?
> 2. How do I start/stop/reset it?
> 3. Where are fixture files or seed data?
> 4. What environment variables configure it?

### For Level 3 Tests

If you do not have explicit information about test credentials and accounts, STOP and ask:

> I need to write end-to-end tests that use [external service].
>
> To proceed, I need to know:
>
> 1. Where are the test credentials stored?
> 2. What test accounts/environments exist?
> 3. Are there rate limits or quotas?
> 4. How do I reset test data between runs?

Do not guess. Do not assume. Ask.

---

## Checklist Before Declaring Tests Complete

- [ ] Evidence exists at the level where it can be proven
- [ ] No mocking anywhere—use DI with real implementations, or test at appropriate level
- [ ] Level 2 harnesses are documented
- [ ] Level 3 credentials are documented (not hardcoded)
- [ ] Tests verify behavior, not implementation
- [ ] Regression tests all pass
