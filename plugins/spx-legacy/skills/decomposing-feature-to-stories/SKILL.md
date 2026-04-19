---
name: decomposing-feature-to-stories
description: >-
  ALWAYS invoke this skill when breaking down a feature into stories.
  NEVER decompose features without this skill.
---

<objective>
Transform Feature specs into well-scoped Story specs by identifying which outcomes are atomic (should become stories) vs integration-level (should stay in feature). Each story is an atomic implementation unit—something that can be understood, implemented, and tested as a single coherent piece, expressible as structured outcomes (Scenario, Mapping, Conformance, or Property).

**⚠️ CRITICAL:** Do NOT remove all outcomes from the feature. Features MUST keep their integration outcomes and quality gates. Only MOVE atomic outcomes to stories.

**OUTCOMES, NOT TASKS.** Stories are OUTCOMES (states that should exist), not tasks (things to do).
</objective>

<prerequisite>
**READ FIRST**: `/understanding-outcome-decomposition`

You must understand:

- Story = atomic implementation unit (expressible as structured outcomes)
- Feature should have ≤7 stories
- Stories prove themselves through passing tests
- The tree can start small (1 story) and grow organically

</prerequisite>

<quick_start>

1. Read the feature spec completely
2. Identify atomic pieces—each expressible as a structured outcome
3. Each story should be implementable as a single coherent unit
4. Create story specs with BSP numbering based on dependencies
5. Aim for ≤7 stories (if more, feature may need splitting)

</quick_start>

<workflow>

## Step 0: Sort Feature Outcomes into KEEP vs MOVE

**Before creating stories, classify each existing feature outcome:**

| Outcome type              | Action              | Example                        |
| ------------------------- | ------------------- | ------------------------------ |
| Integration scenario      | **KEEP in feature** | "Master-slave loopback works"  |
| Quality gate              | **KEEP in feature** | "Lint-clean HDL generated"     |
| End-to-end workflow       | **KEEP in feature** | "Complete login flow works"    |
| Atomic component behavior | **MOVE to story**   | "SPI master mode 0 works"      |
| Single isolated operation | **MOVE to story**   | "Parse credentials from input" |

**The test:** Does this outcome require multiple pieces working together?

- YES → KEEP in feature (integration)
- NO → MOVE to story (atomic)

**⚠️ Do NOT remove all outcomes from the feature.** Features need their integration and quality gate outcomes.

## Step 1: Analyze Feature for Atomic Pieces

Read the feature and ask: **"What atomic behaviors make up this feature?"**

| Look for           | Examples                                          |
| ------------------ | ------------------------------------------------- |
| Distinct behaviors | "Parse input", "Validate data", "Generate output" |
| User actions       | "Submit form", "Click button", "View result"      |
| Processing steps   | "Load file", "Transform data", "Save result"      |
| Error handling     | "Handle invalid input", "Recover from failure"    |

**Key test:** Can each piece be expressed as a structured outcome?

The most common type is a Scenario (Gherkin), but consider all four outcome types:

- **Scenario** (∃): Specific case with Given/When/Then
- **Mapping** (∀ finite): Every member of an enumerable set produces expected output
- **Conformance**: Output satisfies an external tool or standard
- **Property** (∀ infinite): Universal statement holds across a domain

If you can't write a clear structured outcome, the piece isn't well-defined enough.

## Step 2: Verify Atomicity

**An atomic story can be implemented as a single coherent unit.**

For each potential story, ask:

```
□ Can I write a clear structured outcome for this?
□ Can I implement this without partial states?
□ Does it have clear acceptance criteria?
□ Is it a single concern, not multiple behaviors bundled?
```

### Signs a Story is Too Large

- You're describing multiple distinct behaviors
- The Gherkin has many unrelated THEN clauses
- Implementation would require multiple PRs
- You keep saying "and also..."

### Signs a Story is Too Small

- It's really part of another story's implementation
- It has no user-visible behavior
- It's a technical detail, not a behavior
- You can't write a meaningful structured outcome for it

## Step 3: Check the 7-Story Limit

**If you identify >7 stories, the feature may be too large.**

```
IF stories > 7:
    Consider: Is this really one feature?
    Options:
    - Split feature into multiple features
    - Combine related stories
    - Re-scope the feature
```

## Step 4: Determine BSP Ordering

**Lower BSP = dependency.** Stories with lower BSP must be done before higher BSP stories.

| Pattern                    | BSP Strategy        |
| -------------------------- | ------------------- |
| Foundation (types, config) | Low BSP (10-20)     |
| Core behavior              | Mid BSP (21-50)     |
| Dependent behavior         | Higher BSP (54-80)  |
| Edge cases, polish         | Highest BSP (76-99) |

### Parallel Stories (Same BSP)

Stories with the same BSP can be worked on in parallel:

```
21-login.feature/
├── 21-parse-credentials.story/    ← Foundation
├── 37-validate-password.story/    ← Same BSP = parallel
├── 37-check-account-status.story/ ← Same BSP = parallel
└── 54-create-session.story/       ← Depends on validation (37)
```

## Step 5: Write Story Specs

For each story, create:

```
spx/.../NN-{slug}.feature/NN-{slug}.story/
├── {slug}.story.md
└── tests/                 # Created when starting implementation
```

### Story Spec Structure

Use the template from `/managing-spx`:

```markdown
# Story: {Name}

## Purpose

{What this atomic unit delivers and why it matters}

## Outcomes

### 1. {Outcome name}

\`\`\`gherkin
GIVEN {precondition}
WHEN {action}
THEN {expected result}
AND {additional assertion}
\`\`\`

#### Test Files

| File                                    | Level | Harness |
| --------------------------------------- | ----- | ------- |
| [{slug}.unit](tests/{slug}.unit.test.*) | 1     | -       |

#### Analysis

*Implementation may diverge as understanding deepens.*

| File              | Intent         |
| ----------------- | -------------- |
| `src/path/file.*` | {What changes} |

| Constant                | Intent |
| ----------------------- | ------ |
| `src/constants.*::NAME` | {Why}  |

| Config Parameter | Test Values      | Expected Behavior |
| ---------------- | ---------------- | ----------------- |
| `ENV_VAR`        | `unset`, `value` | {Behavior}        |

---

### 2. {Second outcome if needed}

{Same structure}

---

## Architectural Constraints

{ADRs and PDRs that constrain this story}
```

**Note:** Stories have an **Analysis** section that proves Claude examined the codebase. This is unique to stories.

## Step 6: Validate Decomposition

For each story:

```
□ Is expressible as structured outcomes
□ Is atomic—implementable as single unit
□ Has clear acceptance criteria
□ BSP reflects dependencies
□ Total stories ≤7 (if more, reconsider feature scope)
```

</workflow>

<examples>

## Example 1: Login Feature → Stories

**Feature:** "Password-based Login"

**Analysis:**

| Atomic behavior                    | Outcome possible?  | Story?  |
| ---------------------------------- | ------------------ | ------- |
| Parse username/password from input | YES                | YES     |
| Validate password against hash     | YES                | YES     |
| Check account isn't locked         | YES                | YES     |
| Create session token               | YES                | YES     |
| Return auth response               | YES                | YES     |
| Handle invalid credentials         | Part of validation | COMBINE |

**Result (5 stories):**

```
21-login.feature/
├── 21-parse-credentials.story/
├── 37-validate-password.story/
├── 37-check-account-status.story/
├── 54-create-session.story/
└── 76-auth-response.story/
```

## Example 2: SPI Master Feature → Stories (Corrected)

**Feature:** "SPI Master"

**Wrong approach (what Claude did):**
Put all outcomes in the feature spec.

**Correct approach:**

| Atomic behavior                | Story?                           |
| ------------------------------ | -------------------------------- |
| SPI master transmits in mode 0 | YES - `21-mode0-transmit.story/` |
| SPI modes 1-3 timing           | COMBINE with mode 0 OR separate  |
| Clock generation               | Part of mode stories OR separate |

**Result:**

```
21-spi-master.feature/
├── 21-mode0.story/         # Mode 0 transmit/receive
├── 37-mode1.story/         # Mode 1 (or combine modes)
├── 37-mode2.story/
├── 37-mode3.story/
└── 54-clock-config.story/  # Clock divider configuration
```

**OR (if modes are similar):**

```
21-spi-master.feature/
├── 21-basic-transfer.story/  # Core transfer logic
├── 37-mode-config.story/     # Mode 0-3 configuration
└── 54-clock-config.story/    # Clock divider
```

## Example 3: Too Many Stories - Feature Needs Splitting

**Original:** "Document Processing" with 12 potential stories

**Problem:** >7 stories indicates feature too large.

**Solution:** Split feature first:

```
BEFORE:
21-document-processing.feature/
├── (12 stories...)

AFTER:
21-document-import.feature/
├── 21-parse-format.story/
├── 37-validate-schema.story/
└── 54-store-document.story/

37-document-transform.feature/
├── 21-apply-rules.story/
├── 37-validate-output.story/
└── 54-handle-errors.story/

54-document-export.feature/
├── 21-format-output.story/
├── 37-write-file.story/
└── 54-verify-export.story/
```

</examples>

<level_of_abstraction>

## Level of Abstraction Depends on Context

The same behavior can be one story or multiple:

**Simple auth system:**

```
21-login.feature/
└── 21-login-flow.story/  # Everything in one
```

**Complex auth system:**

```
21-login.feature/
├── 21-parse-credentials.story/
├── 37-validate-password.story/
├── 37-check-mfa.story/
├── 54-check-account-status.story/
├── 54-audit-login.story/
├── 76-create-session.story/
└── 87-return-response.story/
```

**How to decide:**

| Factor      | Fewer stories         | More stories          |
| ----------- | --------------------- | --------------------- |
| Complexity  | Simple logic          | Complex logic         |
| Team size   | Solo dev              | Multiple devs         |
| Risk        | Low risk              | High risk             |
| Testability | Easy to test together | Need isolated testing |

**Rule of thumb:** Start with fewer stories. Split when you need to.

</level_of_abstraction>

<anti_patterns>

## What NOT to Create as Stories

**OUTCOMES, NOT TASKS.** Stories are states that should exist, not things to do.

| Anti-pattern               | Why wrong          | Correct approach                                            |
| -------------------------- | ------------------ | ----------------------------------------------------------- |
| "ADR compliance"           | Task, not outcome  | ADR compliance is verified BY stories, not a separate story |
| "Refactor to use X"        | Task, not outcome  | The outcome is the behavior; refactoring is HOW             |
| "Write tests"              | Meta task          | Tests are PROOF of outcomes                                 |
| "Fix bug in Y"             | Task framing       | Outcome: "Edge case Y handled correctly"                    |
| "The login feature"        | Feature, not story | Keep as feature                                             |
| Multiple behaviors bundled | Not atomic         | Split into stories                                          |

**The ADR Compliance Anti-Pattern:**

WRONG:

```
21-cordic-rotate.story/     # Rotate mode works
37-cordic-vector.story/     # Vector mode works
76-adr-compliance.story/    # ← NOT A STORY - this is a task
```

RIGHT:

```
21-cordic-rotate.story/     # Rotate mode works (ADR-compliant by design)
37-cordic-vector.story/     # Vector mode works (ADR-compliant by design)
# ADR compliance is verified by each story's tests
# May also be a feature-level quality gate outcome
```

**ADR compliance IS an outcome** — verified through tests. But "make code comply with ADR" is a TASK, not an outcome.

## Signals You're at Wrong Level

| Signal                              | Problem                      |
| ----------------------------------- | ---------------------------- |
| Can't express as structured outcome | Not well-defined             |
| Multiple GIVEN/WHEN/THEN sets       | Multiple stories             |
| "And also..." in description        | Multiple stories             |
| No user-visible behavior            | May be implementation detail |
| Need >7 stories                     | Feature too large            |

</anti_patterns>

<outcome_quality>

## Writing Good Outcomes

Outcomes must be specific and testable regardless of type.

### Scenario (most common)

```gherkin
# GOOD
GIVEN an SPI master configured for mode 0 (CPOL=0, CPHA=0)
WHEN data 0xAB is transmitted
THEN SCLK idles low before transmission
AND data is sampled on rising edge
AND data is shifted on falling edge
AND MOSI outputs 0xAB MSB-first

# BAD (vague)
GIVEN SPI master
WHEN data is sent
THEN it works correctly
```

### Mapping

```markdown
# GOOD — finite set, each row verifiable

| IR Expression | Expected Verilog |
| ------------- | ---------------- |
| `Add(a, b)`   | `a + b`          |
| `Sub(a, b)`   | `a - b`          |
| `Neg(a)`      | `-a`             |

# BAD — no expected output

| IR Expression |
| ------------- |
| `Add(a, b)`   |
```

### Conformance

```markdown
# GOOD — external oracle is specific

Conforms to: Verilator 5.x --lint-only
Predicate: Zero warnings, zero errors

# BAD — no verifiable predicate

Conforms to: "industry standards"
```

### Property

```markdown
# GOOD — domain and predicate are precise

Property: For all (signal_type, width, op) ∈ SignalType × [1..64] × ArithOp,
op(signal_type(width), signal_type(width)).type == int.
Test: @given(signal_types(), widths(), arith_ops())

# BAD — no testable predicate

Property: Arithmetic works for all types
```

**The outcome quality test:**

- Can someone implement tests from this outcome alone?
- Is every assertion verifiable?
- Does the outcome type match the quantifier intent?

</outcome_quality>

<success_criteria>

Decomposition complete when:

- [ ] Feature KEEPS integration and quality gate outcomes
- [ ] Only atomic outcomes are MOVED to stories
- [ ] Each story is expressible as structured outcomes
- [ ] Each story is atomic and implementable as single unit
- [ ] Total stories ≤7 (or feature needs splitting)
- [ ] BSP ordering reflects dependencies
- [ ] Analysis section proves codebase examination
- [ ] Stories have clear acceptance criteria

</success_criteria>
