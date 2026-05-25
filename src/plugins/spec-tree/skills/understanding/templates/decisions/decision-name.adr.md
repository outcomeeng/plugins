# {Decision Name}

## Purpose

{1-3 sentences: what concern this decision governs. State as permanent truth — "This decision governs [scope]" — not as a problem to fix.}

## Context

**Business impact:** {How this decision affects business goals or user outcomes}

**Technical constraints:** {Systems, dependencies, or technical realities that shape this decision}

## Decision

{Primary decision in one sentence.}

## Rationale

{Coherent argument for why this is right given the constraints. Include alternatives considered and why they were rejected.}

## Trade-offs accepted

| Trade-off         | Mitigation / reasoning                      |
| ----------------- | ------------------------------------------- |
| {what's given up} | {why it's acceptable or how it's mitigated} |

## Invariants

Only include if this decision establishes algebraic properties. Omit the section if none apply.

- {invariant — algebraic property that holds for ALL code governed by this ADR}

## Compliance

Only include subsections that apply. Omit empty subsections.

### Recognized by

{Observable patterns indicating code is compliant with this decision}

### MUST

- {rule} — {why this follows from the decision} ([review])

### NEVER

- {prohibition} — {why this violates the decision} ([review])
