# {Decision Name}

## Purpose

{1-3 sentences: what product behavior this decision governs. State as permanent truth — "This decision governs [scope]" — not as a gap to fill.}

## Context

**Business impact:** {How this decision affects business goals or user outcomes}

**Technical constraints:** {Systems, dependencies, or technical realities that shape this decision}

## Decision

{Primary decision in one sentence.}

## Rationale

{Coherent argument for why this is right for users. Include alternatives considered and why they were rejected.}

## Trade-offs accepted

| Trade-off         | Mitigation / reasoning                      |
| ----------------- | ------------------------------------------- |
| {what's given up} | {why it's acceptable or how it's mitigated} |

## Product invariants

Only include if this decision establishes observable user-facing guarantees. Omit the section if none apply.

- {observable user-facing behavior} — {why users can rely on this}

## Compliance

Only include subsections that apply. Omit empty subsections.

Each MUST/NEVER rule carries a single evidence-mode tag `([{mode}])` — one of `scenario`, `mapping`, `conformance`, `property`, or `compliance` — chosen by routing the rule's claim shape through `/testing`. The mode is the minimum evidence the downstream spec assertion that enforces the rule must carry; it is a claim-shape classification, not a test reference, so it carries no path.

### Recognized by

{Observable product behavior indicating compliance with this decision}

### MUST

- {product behavior rule} — {why this follows from the decision} ([{mode}])

### NEVER

- {prohibited product behavior} — {why this violates the decision} ([{mode}])
