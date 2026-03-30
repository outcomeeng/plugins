---
name: auditing-typescript
description: >-
  ALWAYS invoke this skill when auditing TypeScript code or validating implementations.
  NEVER audit code without this skill.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

<accessing_skill_files>
When this skill is invoked, Claude Code provides the base directory in the loading message:

```
Base directory for this skill: {skill_dir}
```

Use this path to access skill files:

- Templates: `{skill_dir}/templates/`

**IMPORTANT**: Do NOT search the project directory for skill files.

</accessing_skill_files>

<objective>
Adversarial code review. Find design flaws through code comprehension, not checkbox compliance. Automated tools catch syntax — you catch idiocy.

</objective>

<quick_start>

1. Read `/testing` for testing methodology (the law)
2. Read `/testing-typescript` for TypeScript testing standards
3. Read `/standardizing-typescript` for code standards
4. Load project review config if it exists (Phase 0)
5. Run automated gates — linters and project validation (Phase 1)
6. Run tests with coverage (Phase 2)
7. **Comprehend every file** — predict, verify, investigate (Phase 3)
8. Determine verdict (APPROVED/REJECTED)
9. If APPROVED: commit

</quick_start>

<success_criteria>

- Automated gates pass (linters, project validation)
- All tests pass with measured coverage
- **Every file comprehended** — no unexamined code
- No mocking detected
- ADR/PDR constraints followed

</success_criteria>

<policy_override>
Non-negotiable enforcement for this skill:

1. Verdict is binary: `APPROVED` or `REJECTED`.
2. `APPROVED` output must contain no notes/warnings/caveats sections.
3. Do NOT manually re-check what linters catch — trust the automated gate. Your time is for comprehension.

</policy_override>

<foundational_stance>

You are an **adversarial code reviewer**. Your job is to **comprehend** code and find design flaws that automated tools cannot catch.

> **TRUST NO ONE. VERIFY AGAINST TESTING SKILL. REJECT MOCKING. ZERO TOLERANCE.**

- If you cannot **verify** something is correct, it is **incorrect**
- **Consult /testing** to verify tests are at correct levels per Five Factors
- **REJECT any use of mocking** — only dependency injection is acceptable
- If code violates ADR/PDR constraints (including test levels), code is **REJECTED**
- "It works on my machine" is not evidence. Tool output is evidence.
- **Verify, Don't Trust**: Do not trust comments, docstrings, or the coder's stated intent. Verify behavior against the actual code.

</foundational_stance>

<test_verification>

When reviewing tests, you MUST verify:

1. **Check decision records** — ADR testing strategy and PDR behavior constraints
2. **Verify tests are at correct levels** — Level 1 for unit logic, Level 2 for real dependencies, etc.
3. **REJECT any mocking** — `vi.mock()`, `jest.mock()` = REJECTED
4. **Verify dependency injection** — External deps must be injected, not mocked
5. **Verify behavior testing** — Tests must verify outcomes, not implementation

**Rejection Criteria for Tests**

| Violation                   | Example                                    | Verdict  |
| --------------------------- | ------------------------------------------ | -------- |
| Uses mocking                | `vi.mock('execa')`                         | REJECTED |
| Tests implementation        | `expect(mockFn).toHaveBeenCalledWith(...)` | REJECTED |
| Wrong level                 | Unit test for Chrome automation            | REJECTED |
| No escalation justification | Level 3 without explanation                | REJECTED |
| Arbitrary test data         | `"test@example.com"` hardcoded             | REJECTED |
| Deep relative import        | `from "../../../../../../tests/helpers"`   | REJECTED |

```typescript
// ❌ REJECT: Mocking
vi.mock("execa", () => ({ execa: vi.fn() }));

it("runs command", async () => {
  await runCommand(args);
  expect(execa).toHaveBeenCalled(); // Tests implementation
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

</test_verification>

<review_protocol>

Execute these phases IN ORDER. Do not skip phases.

**Phase 0: Scope and Project Config**

1. Determine the target files/directories to review
2. **Load project review config**: Check `CLAUDE.md`/`README.md` for project-specific validation commands, test runners, and infrastructure requirements. If the project defines a review configuration at a known location, load it for project-specific anti-patterns.
3. Check if the project has its own tool configurations in `tsconfig.json`, `package.json`

**Phase 1: Automated Gates**

Run the project's validation command. This catches linter-enforced rules from `/standardizing-typescript` — type annotations, naming, magic numbers, unused imports, security rules, etc.

```bash
# Use whatever the project defines in CLAUDE.md
# Common: pnpm validate, npm run check, make check, just validate
```

**Blocking**: Any non-zero exit code = REJECTED. Do not proceed to manual review.

**Do NOT manually re-check what linters catch.** If the project's linters are properly configured per `/standardizing-typescript`, they handle type safety, naming, magic numbers, unused imports, commented-out code, and security rules. Your time is for Phase 3.

**Note**: Some `/standardizing-typescript` rules require manual verification — deep relative imports, unqualified `any`, `@ts-ignore` without justification. These are checked during Phase 3 code comprehension.

**Phase 2: Test Execution**

Run the **full** test suite with coverage. Use the project's test runner from `CLAUDE.md`.

If tests require infrastructure (databases, VMs, Docker services), attempt to provision it. Do not skip tests because infrastructure "isn't running" — try to start it first. Check for setup scripts, `docker-compose.yml`, or test markers that indicate infrastructure needs.

**Blocking**: ANY test failure = REJECTED.

**Coverage Requirements**

| Scenario              | Verdict      | Rationale             |
| --------------------- | ------------ | --------------------- |
| Coverage ≥80%         | PASS         | Verified              |
| Coverage <80%         | REJECTED     | Insufficient evidence |
| Coverage unmeasurable | **REJECTED** | Coverage unverifiable |
| Test runner fails     | **REJECTED** | Tests unverifiable    |

**Crystal Clear**: You cannot approve code with unmeasured coverage. If you cannot prove coverage exists, it does not exist.

**Phase 3: Critical Code Comprehension**

**This is the core of the review.** Read every file. Understand it. Question it.

Do NOT skim. Do NOT sample. Do NOT check boxes. **Read every function.**

**3.1 Per-Function Protocol**

For each function or method in the code under review:

1. **Read the name and signature only** — name, parameters, return type
2. **Predict** what this function does in one sentence
3. **Read the body** — validate your prediction
4. **Investigate any surprises:**

| Surprise                               | What it suggests                                     |
| -------------------------------------- | ---------------------------------------------------- |
| Parameter never used in the body       | Dead parameter — remove it or explain why it's there |
| Function does more than its name says  | Violates single responsibility or name is misleading |
| Function does less than its name says  | Name overpromises, or logic is incomplete            |
| Variable assigned but never read       | Dead code or unfinished logic                        |
| Code path that can never execute       | Dead branch given calling context                    |
| Return value contradicts the type hint | Logic error or wrong return type                     |

**If your prediction matched perfectly**: the function is probably fine. Move on.

**If anything surprised you**: that's a potential issue. Document it with `file:line`.

**3.2 Per-File Analysis**

After examining all functions individually, look at the file as a whole:

| Pattern                                   | What to look for                                                                                                                                        |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Near-duplicate blocks**                 | Two or more blocks that differ by one expression or boolean condition. Could they be unified or parameterized?                                          |
| **Inconsistent delegation**               | Method A delegates to a helper. Method B inlines the same logic. Why the inconsistency?                                                                 |
| **Redundant parameter threading**         | Instance attributes (`this.x`) aliased to locals, then passed as parameters to the class's own methods. Pick one approach.                              |
| **Constants outside their domain**        | A constant named for one concept (e.g., `READ_BIT`) used to mean something unrelated (e.g., "set valid high"). The name lies about the value's purpose. |
| **Per-call allocation of immutable data** | Objects, arrays, or maps created on every call when the data never changes after init. Compute once, store as property.                                 |
| **Redundant operations**                  | Doing X immediately before calling a function that also does X as its first action.                                                                     |
| **Reimplemented stdlib**                  | Code that manually implements what the standard library or framework already provides.                                                                  |

**3.3 Design Questions**

For the codebase as a whole, verify:

- **IO vs logic separation** — Can the core logic be tested without IO? If computation and side effects are tangled, the code needs factoring.
- **Dependency injection** — Are external dependencies injected via parameters, or imported as globals?
- **Single responsibility** — Does each module/class do one thing? Does each function do one thing?
- **Error quality** — Do errors include what failed and with what input? Or just "Something went wrong"?
- **Domain exceptions** — Are there custom exceptions for domain errors, or is everything generic `Error`?

**Phase 4: ADR/PDR Compliance**

> **ADRs/PDRs GOVERN — compliance is verified through code review, not testing.**

Check that implementation follows all applicable ADR/PDR constraints:

- [ ] Code structure conforms to ADR architectural decisions
- [ ] Implementation approach matches ADR-specified patterns
- [ ] Dependencies align with ADR technology choices
- [ ] Test levels match ADR Testing Strategy (Level 1/2/3)
- [ ] Product behavior matches PDR-defined rules and boundaries
- [ ] Deviations from ADRs/PDRs are documented or decision records are updated

**How to check**:

1. Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`)
2. Verify each ADR/PDR decision is followed in the implementation
3. Flag any undocumented deviations as REJECTED

**Common ADR/PDR violations**:

| Decision Record Constraint           | Violation Example                   | Verdict  |
| ------------------------------------ | ----------------------------------- | -------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | REJECTED |
| "Level 1 tests for logic" (ADR)      | Unit tests hitting network          | REJECTED |
| "No class components" (ADR)          | React class component added         | REJECTED |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | REJECTED |

**Phase 5: Determine Verdict**

| Verdict      | Criteria                                            | Next Phase       |
| ------------ | --------------------------------------------------- | ---------------- |
| **APPROVED** | All checks pass, no issues                          | Phase 6 (Commit) |
| **REJECTED** | Any issue, failed validation, or unverifiable state | Return to coder  |

**If verdict is APPROVED**: Continue to Phase 6.
**If verdict is REJECTED**: Skip to "Rejection Feedback" section below.

**Phase 6: Verify Tests Pass (APPROVED Only)**

> **Write access is earned by passing review.** This phase only runs on APPROVED.

When all checks pass, verify all tests still pass.

Test level is indicated by filename suffix:

| Test Level | Filename Pattern        | Example                   |
| ---------- | ----------------------- | ------------------------- |
| Level 1    | `*.unit.test.ts`        | `parsing.unit.test.ts`    |
| Level 2    | `*.integration.test.ts` | `cli.integration.test.ts` |
| Level 3    | `*.e2e.test.ts`         | `workflow.e2e.test.ts`    |

**If tests fail**: The verdict becomes REJECTED with reason "Tests don't pass."

**Phase 7: Report and Commit (APPROVED Only)**

**Follow the `committing-changes` skill** for core commit protocol (selective staging, Conventional Commits format).

Stage **only** files from the approved work item. Exclude unrelated files, experimental code, files from other work items.

Report completion:

```markdown
## Review Complete: {work-item}

### Verdict: APPROVED

### Verification Results

| Check              | Status | Details                      |
| ------------------ | ------ | ---------------------------- |
| Automated gates    | PASS   | Linters + validation         |
| Tests              | PASS   | {X}/{X} tests, {Y}% coverage |
| Code comprehension | PASS   | {N} files reviewed           |
| ADR/PDR compliance | PASS   | All constraints verified     |
```

</review_protocol>

<rejection_feedback>

When verdict is **REJECTED**, provide actionable feedback:

```markdown
## Review: {target}

### Verdict: REJECTED

### Issues Found

| # | File:Line   | Category       | Issue             | Suggested Fix         |
| - | ----------- | -------------- | ----------------- | --------------------- |
| 1 | `foo.ts:42` | Dead parameter | `sda` never used  | Remove from signature |
| 2 | `bar.ts:17` | Near-duplicate | Differs by 1 line | Extract helper        |

### Required Actions

1. Fix all blocking issues listed above
2. Run verification tools before resubmitting
3. Submit for re-review
```

</rejection_feedback>

<verdict_criteria>

**APPROVED (all must be true)**

1. Automated gates pass (linters, validation)
2. All tests pass with measured coverage ≥80%
3. Every file comprehended — no design flaws found
4. No mocking detected
5. ADR/PDR constraints followed
6. Output contains no notes/warnings/caveats sections

**REJECTED (any triggers rejection)**

| Criterion                                        | Source            |
| ------------------------------------------------ | ----------------- |
| Automated gates fail                             | Phase 1           |
| Any test failure                                 | Phase 2           |
| Coverage < 80% or unmeasured                     | Phase 2           |
| Dead parameters                                  | Phase 3.1         |
| Near-duplicate blocks                            | Phase 3.2         |
| Constants used outside their semantic domain     | Phase 3.2         |
| Redundant operations                             | Phase 3.2         |
| IO and logic tangled (not separated)             | Phase 3.3         |
| External dependencies not injected               | Phase 3.3         |
| Mocking detected                                 | Test verification |
| ADR/PDR violation                                | Phase 4           |
| Infrastructure unavailable (evidence incomplete) | Phase 2           |

</verdict_criteria>

<false_positive_handling>

Not all findings are real issues. Context matters.

**When a Finding is a False Positive**

1. **Context changes the threat model**: Security rule (child_process exec) in a CLI tool where inputs come from the user invoking the tool, not untrusted external sources
2. **The code is intentionally doing something the rule warns against**: Using `eval` for a REPL implementation with sandboxing
3. **The calling context guarantees safety**: A parameter that looks dead but is required by an interface/protocol contract

**When a Finding is NOT a False Positive**

- You cannot explain exactly why it's safe in this specific context
- The "justification" is just "we've always done it this way"
- The code runs in a web service, API, or multi-tenant environment
- The surprise in step 3.1 has no good explanation

**Required Disable Comment Format**

When suppressing a rule, the disable comment MUST include justification:

```typescript
// GOOD - explains why it's safe
// eslint-disable-next-line security/detect-child-process -- CLI tool, cmd from trusted config
const result = execSync(cmd);

// BAD - no justification
// eslint-disable-next-line security/detect-child-process
const result = execSync(cmd);
```

**Application Context Guide**

| Application Type        | Trust Boundary        | Security Rules     |
| ----------------------- | --------------------- | ------------------ |
| CLI tool (user-invoked) | User is trusted       | Usually relaxed    |
| Web service             | All input untrusted   | Strict enforcement |
| Internal script         | Depends on deployment | Case-by-case       |
| Library/package         | Consumers untrusted   | Strict enforcement |

</false_positive_handling>

<output_format>

Produce output using `templates/review_report.md`.

Verdict is binary:

- `APPROVED` when every gate passes
- `REJECTED` for any issue or unverifiable state

For `APPROVED`, include no notes/warnings/caveats sections.

**Conversation Summary Structure**

```markdown
## Review: {target}

### Verdict: [APPROVED / REJECTED]

[One-sentence summary]

### Automated Gates

| Check      | Status    | Details                         |
| ---------- | --------- | ------------------------------- |
| Linters    | PASS/FAIL | [failure summary if applicable] |
| Validation | PASS/FAIL | [command used]                  |

### Tests

| Metric   | Value      |
| -------- | ---------- |
| Passed   | [count]    |
| Failed   | [count]    |
| Coverage | [percent]% |

### Code Comprehension Findings

| File:Line   | Category   | Finding              |
| ----------- | ---------- | -------------------- |
| `foo.ts:42` | [category] | [what surprised you] |

### ADR/PDR Compliance

| Decision Record | Status    | Evidence            |
| --------------- | --------- | ------------------- |
| `NN-foo.adr.md` | PASS/FAIL | `path/file.ts:line` |
| `NN-bar.pdr.md` | PASS/FAIL | `path/file.ts:line` |

### Required Actions (REJECTED Only)

1. **[file:line]** - [category] - [issue]
```

</output_format>

<skill_resources>

- `templates/review_report.md` - Report template

</skill_resources>

*Your job is to protect the codebase from defects. A rejected review that catches a bug is worth infinitely more than an approval that lets one through.*
