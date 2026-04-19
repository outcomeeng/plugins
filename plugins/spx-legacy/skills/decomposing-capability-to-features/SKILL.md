---
name: decomposing-capability-to-features
description: >-
  ALWAYS invoke this skill when breaking down a capability into features.
  NEVER decompose capabilities without this skill.
---

<objective>
Transform Capability specs into well-scoped Feature specs. Each feature is a significant vertical slice that can be implemented in at most 7 atomic stories.
</objective>

<prerequisite>
**READ FIRST**: `/understanding-outcome-decomposition`

You must understand:

- Feature = significant vertical slice (at most 7 stories)
- Features don't list story outcomes (Principle 11)
- The tree can start small (1 feature) and grow organically

</prerequisite>

<quick_start>

1. Read the capability spec completely
2. Identify significant vertical slices of the capability
3. Each slice must be implementable in ≤7 atomic stories
4. Create feature specs with BSP numbering based on dependencies
5. Start small—a single feature is valid

</quick_start>

<workflow>

## Step 1: Analyze Capability for Vertical Slices

Read the capability and ask: **"What significant slices make up this product ability?"**

| Look for                       | Examples                                  |
| ------------------------------ | ----------------------------------------- |
| Distinct user-facing functions | "Login", "Registration", "Password Reset" |
| Separable workflows            | "Import", "Export", "Transform"           |
| Independent subsystems         | "Parser", "Generator", "Validator"        |
| Logical groupings              | "CRUD operations", "Search", "Reports"    |

## Step 2: Apply the 7-Story Test

**Critical constraint: Each feature must be implementable in ≤7 atomic stories.**

```
FOR each potential feature:
    Estimate: How many atomic stories would this need?

    IF > 7 stories:
        Split into multiple features
    ELSE:
        Valid feature scope
```

### Signs a Feature is Too Large

- You're listing more than 7 distinct behaviors
- The feature name includes "and" (e.g., "Login and Registration")
- You can't describe it in one sentence
- It spans multiple user personas

### Signs a Feature is Too Small

- It's really just 1-2 stories
- It doesn't provide significant standalone value
- It's an implementation detail, not user-facing

**Note:** A small feature (1-2 stories) is valid—it can grow. But consider if it's really a story.

## Step 3: Consider Starting Small

**A single feature is valid.** The capability grows organically.

```
21-auth.capability/
└── 21-login.feature/         ← Start with one
    └── 21-basic-login.story/
```

Later:

```
21-auth.capability/
├── 21-login.feature/
├── 37-registration.feature/  ← Added
└── 54-password-reset.feature/ ← Added
```

## Step 4: Determine BSP Ordering

**Lower BSP = dependency.** Features with lower BSP must be done before higher BSP features.

| Pattern                           | BSP Strategy        |
| --------------------------------- | ------------------- |
| Foundation (shared types, config) | Low BSP (10-20)     |
| Core functionality                | Mid BSP (21-50)     |
| Dependent features                | Higher BSP (54-80)  |
| Polish/improvements               | Highest BSP (76-99) |

### Parallel Features (Same BSP)

Features with the same BSP can be worked on in parallel:

```
21-auth.capability/
├── 21-login.feature/          ← Depends on nothing
├── 37-registration.feature/   ← Same BSP = parallel
├── 37-password-reset.feature/ ← Same BSP = parallel
└── 54-oauth.feature/          ← Depends on login (21) and reg (37)
```

## Step 5: Write Feature Specs

For each feature, create:

```
spx/NN-{cap}.capability/NN-{slug}.feature/
├── {slug}.feature.md
└── tests/                 # Created when starting implementation
```

### Feature Spec Structure

Use the template from `/managing-spx`:

```markdown
# Feature: {Name}

## Purpose

{What this significant slice delivers and why it matters}

## Requirements

{Prose focused on this feature's scope}

## Test Strategy

{Overview of testing approach—can include multiple levels}

## Outcomes

{Feature-level outcomes, if any—remember Principle 11}

## Architectural Constraints

{ADRs and PDRs that constrain this feature}
```

**Critical: Principle 11 - Correctly Understood**

Features MUST have their own outcomes. Principle 11 means features don't list outcomes that ARE stories (atomic implementation units).

**Features KEEP these outcomes:**

```markdown
## Outcomes

### 1. Complete login flow works end-to-end ← KEEP (integration)

### 2. Failed logins are rate-limited ← KEEP (integration)

### 3. Session tokens are securely generated ← KEEP (quality gate)
```

**Features MOVE these to stories:**

```markdown
### 4. Parse credentials from request ← MOVE TO STORY (atomic)

### 5. Validate password against hash ← MOVE TO STORY (atomic)

### 6. Create session record ← MOVE TO STORY (atomic)
```

**The test:** Does this outcome require multiple pieces working together (integration) or is it a single atomic behavior (story)?

**⚠️ WARNING:** Do NOT remove all outcomes from features. Features need integration outcomes and quality gates.

## Step 6: Validate Decomposition

For each feature:

```
□ Is a significant vertical slice
□ Can be implemented in ≤7 stories
□ Has clear boundaries with sibling features
□ BSP reflects dependencies
□ Does NOT list story-level outcomes (Principle 11)
```

</workflow>

<examples>

## Example 1: Auth Capability → Features

**Capability:** "Identity and Authentication Management"

**Analysis:**

| Slice                  | Stories needed | Valid feature? |
| ---------------------- | -------------- | -------------- |
| "Login"                | ~4-5           | YES            |
| "Registration"         | ~3-4           | YES            |
| "Password Reset"       | ~3             | YES            |
| "OAuth Integration"    | ~5-6           | YES            |
| "Complete Auth System" | ~15+           | NO - too large |

**Result:**

```
21-auth.capability/
├── 21-login.feature/
├── 37-registration.feature/
├── 54-password-reset.feature/
└── 76-oauth.feature/
```

## Example 2: SPI Peripherals Capability → Features

**Capability:** "SPI Peripheral Support"

**Analysis:**

| Slice                         | Stories needed | Valid feature?    |
| ----------------------------- | -------------- | ----------------- |
| "SPI Master"                  | ~3             | YES               |
| "SPI Slave"                   | ~3             | YES               |
| "SPI Configuration"           | ~2             | YES (small is OK) |
| "Complete SPI with all modes" | ~10+           | NO - split        |

**Result:**

```
21-spi-peripherals.capability/
├── 21-spi-master.feature/      # Mode 0-3, clock gen
├── 37-spi-slave.feature/       # Response handling
└── 54-spi-integration.feature/ # Master-slave together
```

## Example 3: Feature Too Large - How to Split

**Original:** "User Management" with 12 identified stories

**Split by concern:**

```
BEFORE:
21-user-management.feature/  ← Too large (12 stories)

AFTER:
21-user-crud.feature/        ← 4 stories
37-user-roles.feature/       ← 4 stories
54-user-preferences.feature/ ← 4 stories
```

**Split by workflow:**

```
BEFORE:
21-document-processing.feature/  ← Too large

AFTER:
21-document-import.feature/
37-document-transform.feature/
54-document-export.feature/
```

</examples>

<the_spi_mistake>

## The SPI Anti-Pattern (What NOT to Do)

Claude created this feature spec with 5 outcomes:

| Outcome                           | Type         | Action              |
| --------------------------------- | ------------ | ------------------- |
| 1. SPI master transmits in mode 0 | Atomic       | MOVE to story       |
| 2. SPI modes 1-3 verified         | Atomic       | MOVE to story       |
| 3. SPI slave responds             | Atomic       | MOVE to story       |
| 4. Master-slave loopback works    | Integration  | **KEEP in feature** |
| 5. Lint-clean HDL                 | Quality gate | **KEEP in feature** |

**Correct result - feature KEEPS outcomes 4-5:**

```markdown
# Feature: Serial SPI (AFTER decomposition)

## Outcomes

### 1. Master-slave loopback works end-to-end

GIVEN SPI master and slave connected via loopback
WHEN master sends 0xAB
THEN slave receives 0xAB AND master receives slave response

### 2. Generated HDL passes lint

GIVEN configured SPI components
WHEN Verilog is generated
THEN Verilator lint passes with zero warnings
```

**Directory structure:**

```
22-serial-spi.feature/
├── serial-spi.feature.md     # Keeps integration + quality outcomes
├── 10-spi-master.story/      # Former outcomes 1-2 (atomic)
└── 20-spi-slave.story/       # Former outcome 3 (atomic)
```

**⚠️ WRONG:** Removing ALL outcomes from the feature. Features MUST keep integration and quality gate outcomes.

**The decision test:**

- "SPI master mode 0" - single component, testable in isolation → STORY
- "Master-slave loopback" - requires BOTH master AND slave → FEATURE
- "Lint-clean HDL" - quality gate, cross-cutting verification → FEATURE

</the_spi_mistake>

<anti_patterns>

## What NOT to Create as Features

| Anti-pattern             | Why wrong    | Fix                 |
| ------------------------ | ------------ | ------------------- |
| "Login and Registration" | Two features | Split               |
| "Parse Config"           | Too small    | Story               |
| Feature with 12 stories  | Too large    | Split into features |

## What NOT to Do When Decomposing

| Anti-pattern                     | Why wrong                          | Correct action                           |
| -------------------------------- | ---------------------------------- | ---------------------------------------- |
| Remove ALL outcomes from feature | Features need integration outcomes | KEEP integration + quality gate outcomes |
| Keep ALL outcomes in feature     | Atomic outcomes should be stories  | MOVE only atomic outcomes to stories     |

## Signals You're at Wrong Level

| Signal                        | Problem                    |
| ----------------------------- | -------------------------- |
| >7 stories needed             | Feature too large          |
| Name includes "and"           | Probably multiple features |
| Outcomes are atomic behaviors | Should be stories          |
| 1 story with no room to grow  | Might just be a story      |

</anti_patterns>

<success_criteria>

Decomposition complete when:

- [ ] Each feature is a significant vertical slice
- [ ] Each feature needs ≤7 stories
- [ ] BSP ordering reflects dependencies
- [ ] Features KEEP integration and quality gate outcomes
- [ ] Features MOVE atomic outcomes to stories
- [ ] Structure can grow organically

</success_criteria>
