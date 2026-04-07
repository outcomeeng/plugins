<!-- Test file naming varies by language. See spx/CLAUDE.md for conventions.
     TypeScript: tests/{slug}.unit.test.ts    tests/{slug}.integration.test.ts    tests/{slug}.e2e.test.ts
     Python:     tests/test_{slug}.unit.py     tests/test_{slug}.integration.py    tests/test_{slug}.e2e.py
     Tables below use logical names. Resolve to actual filenames when instantiating. -->

# Capability: [Capability Name]

## Purpose

[What this capability delivers and why it matters to users.]

## Success Metric

- **Baseline**: [Current measurable state]
- **Target**: [Expected improvement]
- **Measurement**: [How progress will be tracked]

## Requirements

[Prose description of functional and quality requirements. Constraints and invariants that tests must verify.]

## Test Strategy

| Component       | Level | Harness       | Rationale                              |
| --------------- | ----- | ------------- | -------------------------------------- |
| [Component 1]   | 1     | -             | [Why this level is minimum sufficient] |
| [Component 2]   | 2     | [harness-ref] | [Why this level is minimum sufficient] |
| [Full workflow] | 3     | e2e-harness   | [Why E2E verification is needed]       |

### Escalation Rationale

- **1 → 2**: [What confidence does Level 2 add that Level 1 cannot provide?]
- **2 → 3**: [What confidence does Level 3 add that Level 2 cannot provide?]

## Outcomes

### 1. [Primary user journey]

```gherkin
GIVEN [full environment with real services]
WHEN [complete user workflow]
THEN [value delivered to user]
```

| File       | Level | Harness                                                                     |
| ---------- | ----- | --------------------------------------------------------------------------- |
| {slug}.e2e | 3     | [e2e-harness](spx/NN-test-infrastructure.capability/NN-e2e-harness.feature) |

---

### 2. [Alternative scenario]

```gherkin
GIVEN [alternative preconditions]
WHEN [user action]
THEN [expected behavior]
```

| File           | Level | Harness                                                                     |
| -------------- | ----- | --------------------------------------------------------------------------- |
| {slug}-alt.e2e | 3     | [e2e-harness](spx/NN-test-infrastructure.capability/NN-e2e-harness.feature) |

---

## Architectural Constraints

| ADR                              | Constraint                               |
| -------------------------------- | ---------------------------------------- |
| [adr-NN_name](../adr-NN_name.md) | [What constraint this ADR imposes]       |
| [pdr-NN_name](../pdr-NN_name.md) | [What product behavior this PDR governs] |
