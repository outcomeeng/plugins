<!-- Test file naming varies by language. See spx/CLAUDE.md for conventions.
     TypeScript: tests/{slug}.unit.test.ts    tests/{slug}.integration.test.ts    tests/{slug}.e2e.test.ts
     Python:     tests/test_{slug}.unit.py     tests/test_{slug}.integration.py    tests/test_{slug}.e2e.py
     Tables below use logical names. Resolve to actual filenames when instantiating. -->

# Story: [Story Name]

## Purpose

[What this story delivers and why it matters.]

## Outcomes

### 1. [Outcome name] (Scenario)

```gherkin
GIVEN [precondition]
WHEN [action]
THEN [expected result]
AND [additional assertion]
```

#### Test Files

| File        | Level | Harness |
| ----------- | ----- | ------- |
| {slug}.unit | 1     | -       |

#### Analysis

*Implementation may diverge as understanding deepens.*

| File            | Intent         |
| --------------- | -------------- |
| `src/path/file` | [What changes] |
| `src/path/new`  | [What it does] |

| Constant                         | Intent                    |
| -------------------------------- | ------------------------- |
| `src/path/constants::CONST_NAME` | [Why using existing]      |
| `src/path/constants::NEW_CONST`  | [Why new constant needed] |

| Config Parameter | Test Values      | Expected Behavior   |
| ---------------- | ---------------- | ------------------- |
| `ENV_VAR`        | `unset`, `value` | [Behavior for each] |

---

### 2. [Outcome name] (Property)

**Property:** For all [variable] ∈ [domain], [predicate holds].

**Domain:** [description of the value space]

**Test:** [property-based test framework call]

#### Test Files

| File               | Level | Harness                                                                 |
| ------------------ | ----- | ----------------------------------------------------------------------- |
| {slug}.integration | 2     | [harness-name](spx/NN-test-infrastructure.capability/NN-{name}.feature) |

#### Analysis

*Implementation may diverge as understanding deepens.*

| File            | Intent         |
| --------------- | -------------- |
| `src/path/file` | [What changes] |

| Constant                       | Intent |
| ------------------------------ | ------ |
| `src/path/constants::EXISTING` | [Why]  |

*No configuration for this outcome.*

---

## Architectural Constraints

| ADR                              | Constraint                               |
| -------------------------------- | ---------------------------------------- |
| [adr-NN_name](../adr-NN_name.md) | [What constraint this ADR imposes]       |
| [pdr-NN_name](../pdr-NN_name.md) | [What product behavior this PDR governs] |
