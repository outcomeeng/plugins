---
name: reviewing-tests
disable-model-invocation: true
description: >-
  Foundational test review methodology. Loaded by /reviewing-python-tests and /reviewing-typescript-tests, not invoked directly.
---

<objective>
Determine if tests provide genuine evidence that assertions are fulfilled through adversarial review. Reject tests that can pass while assertions remain unfulfilled.

**THE ADVERSARIAL QUESTION:**

> How could these tests pass while the assertion remains unfulfilled?

If you can answer that question, the tests are **REJECTED**.

</objective>

<quick_start>
**PREREQUISITE**: Reference `/testing` for methodology (5 stages, 5 factors, 7 exceptions).

This is a foundational skill. Language-specific skills (`/reviewing-python-tests`, `/reviewing-typescript-tests`) load this first and add language-specific phases.

Review protocol has 4 foundational phases — stop at first rejection:

1. **Spec structure validation** — Assertion format, test links exist, level appropriateness
2. **Evidentiary integrity** — Adversarial test, dependency handling, harness verification
3. **Lower-level assumptions** — Spec hierarchy, atemporal voice, integration boundaries
4. **ADR/PDR compliance** — Decision record constraint verification

Language-specific skills add:

5. **Property-based testing** — Language-specific tooling and patterns
6. **Test quality** — Language-specific conventions and anti-patterns

When reporting findings, cite source skills:

- "Per /testing Stage 2 Factor 2, database dependency requires Level 2"
- "Per /reviewing-tests Phase 1.1, assertion type must match test strategy"

</quick_start>

<verdict>
There is no middle ground. No "mostly good." No "acceptable with caveats."

- **APPROVED**: Tests provide genuine evidence for all assertions at appropriate levels
- **REJECT**: Any deficiency, missing link, silent skip, or evidentiary gap

A missing comma is REJECT. A philosophical disagreement about test structure is REJECT. If it's not APPROVED, it's REJECT.

</verdict>

<context>
This skill protects the test suite from phantom evidence. A single evidentiary gap means CI can go green while promised assertions remain unfulfilled. The cost of false approval is infinite; the cost of false rejection is rework.

</context>

<review_protocol>
Execute these phases IN ORDER. Stop at first REJECT.

<phase name="spec_structure_validation">
For each assertion in the spec, verify:

**1.1 Assertion Format**

Assertions MUST use one of five typed formats. No code in specs.

| Type            | Quantifier                     | Test strategy   | Format pattern                                     |
| --------------- | ------------------------------ | --------------- | -------------------------------------------------- |
| **Scenario**    | There exists (this case works) | Example-based   | `Given ... when ... then ... ([test](...))`        |
| **Mapping**     | For all over finite set        | Parameterized   | `{input} maps to {output} ([test](...))`           |
| **Conformance** | External oracle                | Tool validation | `{output} conforms to {standard} ([test](...))`    |
| **Property**    | For all over type space        | Property-based  | `{invariant} holds for all {domain} ([test](...))` |
| **Compliance**  | ALWAYS/NEVER rules             | Review or test  | `ALWAYS/NEVER: {rule} ([review]/[test](...))`      |

```markdown
<!-- ✅ CORRECT: Typed assertions with inline test links -->

### Scenarios

- Given a parser configured for strict mode, when invalid input is provided, then a ParseError is raised ([test](tests/test_parser_unit.ext))

### Properties

- Serialization is deterministic: same input always produces the same output ([test](tests/test_serialize_unit.ext))

### Compliance

- ALWAYS: signal writes use non-blocking assignment — PDR-12 two-phase tick ([review](../../12-simulation-execution.pdr.md))
```

<!-- ❌ REJECT: Code in spec -->

```
def test_parser():
    parser = Parser(strict=True)
    ...
```

**If spec contains code examples**: REJECT. Specs are durable; code drifts.

**Assertion type must match test strategy:**

| Assertion Type | Required Test Pattern      | REJECT if                                    |
| -------------- | -------------------------- | -------------------------------------------- |
| Scenario       | Example-based tests        | Missing concrete inputs/outputs              |
| Mapping        | Parameterized tests        | Only example-based (not all cases covered)   |
| Property       | Property-based framework   | Only example-based (must use property-based) |
| Conformance    | Tool validation            | Manual checks instead of tool                |
| Compliance     | `[review]` or `[test]` tag | No tag indicating verification method        |

**1.2 Test File Linkage**

**Inline test links are contractual.** Every `([test](...))` link in an assertion must resolve to an actual file. Stale links = REJECT.

Specs may use either format:

- **Inline links** (spec-tree format): `([test](tests/test_parser_unit.ext))` embedded in assertions
- **Test Files tables** (spx-legacy format): Separate table with File/Level/Harness columns

Both are contractual — every link must resolve.

This is distinct from the **Analysis section** (stories only), which documents the agent's codebase examination. Analysis references may diverge from implementation as understanding deepens — do NOT reject specs for stale Analysis references.

**Check:**

1. Link syntax is valid Markdown: `[test](path)` or `[display](path)`
2. Linked file EXISTS at specified path
3. Level matches filename convention (language-specific — see language skill)

```bash
# Verify linked files exist (extract paths from inline links or tables)
ls -la {container}/tests/{linked_file}
```

**If link is broken or file missing**: REJECT.

**1.3 Level Appropriateness**

Evidence lives at specific levels. Verify each assertion is tested at the correct level:

| Evidence Type              | Minimum Level | Example                                  |
| -------------------------- | ------------- | ---------------------------------------- |
| Pure computation/algorithm | 1             | Protocol timing, math correctness        |
| Component interaction      | 2             | TX→RX loopback, multi-entity simulation  |
| Project-specific binary    | 2             | Verilator lint, external tool invocation |
| Real credentials/services  | 3             | Cloud APIs, payment providers            |

**If assertion is tested at wrong level**: REJECT.

**If story-level assertion appears in feature spec**: Note as structural issue (stories should be created), but continue review.

**GATE 1**: Before proceeding to Phase 2, verify:

- [ ] All assertions use typed format (Scenario/Mapping/Conformance/Property/Compliance — no code in specs)
- [ ] Assertion type matches test strategy (Property assertions use property-based framework, Mapping uses parameterized tests, etc.)
- [ ] All test file links resolve (inline or table — ran `ls` for each)
- [ ] All assertions tested at appropriate level

If any check fails, STOP and REJECT with detailed findings.

</phase>

<phase name="evidentiary_integrity">
For each test file, verify it provides genuine evidence.

**2.1 The Adversarial Test**

Ask: **How could this test pass while the assertion remains unfulfilled?**

| Scenario                                                   | Verdict |
| ---------------------------------------------------------- | ------- |
| Test asserts something other than what assertion specifies | REJECT  |
| Test uses hardcoded values that happen to match            | REJECT  |
| Test doesn't actually exercise the code path               | REJECT  |
| Test mocks the thing it's supposed to verify               | REJECT  |
| Test can pass with broken implementation                   | REJECT  |

**2.2 Dependency Availability**

**CRITICAL: Missing dependencies MUST FAIL, not skip.**

Search for silent skip patterns (use language-specific grep patterns from the language skill).

**Evaluate each skip:**

| Pattern                                      | Verdict                                          |
| -------------------------------------------- | ------------------------------------------------ |
| Skip on required project dependency          | **REJECT** - Required dependency must fail       |
| Skip on test infrastructure (property lib)   | **REJECT** - Test infrastructure must be present |
| Skip on platform (`sys.platform`, `os.type`) | REVIEW - May be legitimate                       |
| Skip on CI environment variable              | REVIEW - What is being skipped?                  |

**The Silent Skip Problem:**

Tests that silently skip on required dependencies allow CI to go green with zero verification. This is evidentiary fraud.

**If tests silently skip on required dependencies**: REJECT.

**2.3 Harness Verification**

If assertion specifies a harness:

1. Harness must exist and be specified (in `spx/` or project test infrastructure)
2. Harness must have its own tests
3. Harness failures must cause test failures, not skips

**If harness is referenced but doesn't exist or isn't tested**: REJECT.

**GATE 2**: Before proceeding to Phase 3, verify:

- [ ] Each test file reviewed for adversarial test (can it pass while assertion fails?)
- [ ] Searched for skip patterns, evaluated each found
- [ ] Any harnesses referenced have been verified to exist

If any check fails, STOP and REJECT with detailed findings.

</phase>

<phase name="lower_level_assumptions">
Features assume stories have tested what can be tested at story level. Capabilities assume features have done their job.

**3.1 Check for Lower-Level Specs**

```bash
# For a feature, check if stories exist
ls -d {feature_path}/*-*.story/ 2>/dev/null

# For a capability, check if features exist
ls -d {capability_path}/*-*.feature/ 2>/dev/null
```

**3.2 Evaluate Assumptions**

| Scenario                              | Action                                                            |
| ------------------------------------- | ----------------------------------------------------------------- |
| Lower-level specs exist with tests    | Verify assumptions align                                          |
| Lower-level specs exist without tests | Note gap, continue review                                         |
| Lower-level specs don't exist         | Note structural issue, evaluate if tests are appropriately coarse |

**Key principle**: Specs are DURABLE. They DEMAND assertions. A spec must NEVER say "stories are pending" or "tests will be added later." If lower-level decomposition is needed, those specs should exist.

**If spec contains language about missing/pending specs**: REJECT. Specs are not working documents.

**Atemporal voice** (Durable Map Rule): Specs state product truth. They NEVER narrate code history, current state, or migration plans. Any temporal language is a REJECTION — no section gets a pass.

**Temporal patterns to reject in specs:**

- "The current `module.py` has..." — narrates code state
- "The file `deprecated/old.py` does not exist" — narrates filesystem state
- "We need to replace..." / "We need to migrate..." — narrates a plan, not a truth
- "Currently X uses..." — snapshot that expires
- "The existing implementation..." — references code, not architecture
- "X has accumulated without..." — narrates drift
- "Previously..." / "Before this..." — there is no before

Code that doesn't conform to a spec is discovered through code review and test coverage analysis — the spec itself never names files to delete or code to replace.

**3.3 Integration Test Assumptions**

For integration tests (Level 2), verify they don't duplicate story-level evidence:

| Integration Test Should    | Integration Test Should NOT              |
| -------------------------- | ---------------------------------------- |
| Verify component contracts | Re-test algorithm correctness            |
| Verify interoperation      | Exhaustively test edge cases             |
| Assume story tests passed  | Provide coarse coverage of unit concerns |

**If integration tests are doing story-level work because stories don't exist**: Note as structural issue. Tests may be legitimately coarse in transitional state, but this should be flagged.

**GATE 3**: Before proceeding to Phase 4, verify:

- [ ] Checked for lower-level specs (stories within features, features within capabilities)
- [ ] No temporal language in spec — no "pending", "will be added", "currently", "the existing", references to specific files to delete
- [ ] Integration tests are not duplicating unit-level work

If any check fails, STOP and REJECT with detailed findings.

</phase>

<phase name="decision_record_compliance">
Check test code against decision records.

**4.1 Identify Applicable ADRs/PDRs**

```bash
# Find decision records referenced in spec
grep -oE '\[.*?\]\(.*?\.(adr|pdr)\.md\)' {spec_file}

# Find ADRs/PDRs in ancestry
ls {capability_path}/*.adr.md {capability_path}/*.pdr.md 2>/dev/null
ls {feature_path}/*.adr.md {feature_path}/*.pdr.md 2>/dev/null
```

**4.2 Verify Compliance**

For each decision record, extract constraints and verify test code follows them. Use grep to search test files for violation patterns.

**If tests violate ADR/PDR constraints**: REJECT.

**GATE 4**: Before proceeding to language-specific phases, verify:

- [ ] Identified all applicable ADRs/PDRs (spec references + ancestry)
- [ ] Searched test files for each decision-record constraint
- [ ] No ADR/PDR violations found

If any check fails, STOP and REJECT with detailed findings.

</phase>

</review_protocol>

<failure_modes>
Failures from actual usage:

**Failure 1: Approved tests with silent skips**

- What happened: Agent saw test output with all tests passing, approved
- Why it failed: Tests had skip decorators for required dependencies — CI went green with zero verification
- How to avoid: ALWAYS search for skip patterns in Phase 2.2. Any skip on a required dependency is automatic REJECT

**Failure 2: Missed broken test links**

- What happened: Agent checked link syntax but didn't verify files exist
- Why it failed: Spec had inline test link but file was named differently
- How to avoid: Run `ls -la {container}/tests/{file}` for EVERY linked file in Phase 1.2. Don't trust link syntax alone.

**Failure 3: Approved tests that mocked the SUT**

- What happened: Agent searched for one mocking pattern but tests used another variant
- Why it failed: Grep pattern didn't catch all mocking variants
- How to avoid: Use complete grep pattern for ALL mocking variants in the language

**Failure 4: Missed ADR constraint violation**

- What happened: Agent found ADRs but didn't systematically check each constraint
- Why it failed: ADR imposed a constraint but tests violated it
- How to avoid: For EACH ADR constraint, write and run a grep command. Document what you searched for.

**Failure 5: Compared coverage at wrong granularity**

- What happened: Agent saw low coverage for one story and flagged as insufficient
- Why it failed: Multiple stories share one implementation file; per-story coverage is meaningless
- How to avoid: Always compare coverage at the implementation file level, not story level

**Failure 6: Temporal language approved as "observation"**

- What happened: Agent noticed temporal language in spec Context section but approved it as "style concern, not violation"
- Why it failed: Atemporal voice applies to ALL sections. No section gets a pass — Context, Purpose, Assertions, all must state permanent truth.
- How to avoid: Any temporal language in any spec section is REJECT. No exceptions. "The current X..." is never acceptable.

</failure_modes>

<output_format>
<approve_template>

```markdown
## Test Review: {container_path}

### Verdict: APPROVED

All assertions have genuine evidentiary coverage at appropriate levels.

### Assertions Verified

| # | Assertion | Type   | Level | Test File | Evidence Quality |
| - | --------- | ------ | ----- | --------- | ---------------- |
| 1 | {name}    | {type} | {N}   | {file}    | Genuine          |

### ADR/PDR Compliance

| Decision Record | Status    |
| --------------- | --------- |
| {name}          | Compliant |
```

</approve_template>

<reject_template>

```markdown
## Test Review: {container_path}

### Verdict: REJECT

{One-sentence summary of primary rejection reason}

### Rejection Reasons

| # | Category | Location    | Issue   | Required Fix |
| - | -------- | ----------- | ------- | ------------ |
| 1 | {cat}    | {file:line} | {issue} | {fix}        |

### Detailed Findings

#### {Category}: {Issue Title}

**Location**: `{file}:{line}`

**Problem**: {Detailed explanation of why this is a rejection}

**Evidence**:
```

{Code snippet or grep output showing the issue}

```
**Required Fix**: {Specific action to resolve}

---

### How Tests Could Pass While Assertion Fails

{Explain the evidentiary gap — how could these tests go green while the promised assertion remains unfulfilled?}
```

</reject_template>

</output_format>

<rejection_triggers>
Quick reference for common rejection triggers:

| Category            | Trigger                                                                      | Verdict |
| ------------------- | ---------------------------------------------------------------------------- | ------- |
| **Spec Structure**  | Code examples in spec                                                        | REJECT  |
| **Spec Structure**  | Assertion type doesn't match test strategy (Property without property tests) | REJECT  |
| **Spec Structure**  | Missing or broken test file links (inline or table)                          | REJECT  |
| **Spec Structure**  | Language about "pending" specs                                               | REJECT  |
| **Spec Structure**  | Temporal language ("currently", "the existing", file references)             | REJECT  |
| **Level**           | Assertion tested at wrong level                                              | REJECT  |
| **Dependencies**    | Skip on required dependency                                                  | REJECT  |
| **Dependencies**    | Harness referenced but missing                                               | REJECT  |
| **Decision Record** | Test violates ADR/PDR constraint                                             | REJECT  |
| **Evidentiary**     | Test can pass with broken impl                                               | REJECT  |

Language-specific skills add additional triggers (mocking patterns, type annotations, property testing requirements).

</rejection_triggers>

<success_criteria>
Task is complete when:

- [ ] Verdict is APPROVED or REJECT (no middle ground)
- [ ] All 4 foundational phases executed in order (or stopped at first REJECT)
- [ ] All gates passed (or documented why gate failed)
- [ ] Each rejection reason has file:line location
- [ ] Evidentiary gap explained (how tests could pass while assertion fails)
- [ ] Output follows specified format (APPROVED or REJECT template)

</success_criteria>

<cardinal_rule>
**If you can explain how the tests could pass while the assertion remains unfulfilled, the tests are REJECTED.**

Your job is to protect the test suite from phantom evidence. A rejected review that catches an evidentiary gap is worth infinitely more than an approval that lets one through.

</cardinal_rule>
