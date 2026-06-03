# {Decision Name}

{The decision, stated directly as permanent truth in 1-3 sentences — what it governs and what it decides. No "Purpose" heading, no "this decision governs" preamble.}

## Rationale

{Brief — why this is right given the constraints. Name a rejected alternative only when it sharpens the decision. Omit if self-evident.}

## Invariants

{Omit if none. Algebraic properties that hold for all code governed by this ADR.}

## Verification

Each rule is an ALWAYS guarantee or a NEVER boundary, under the one subsection naming how it is verified. Include only the subsections that apply.

### Audit

Verified by an auditing skill's judgment against this decision — the subject (a Spec Tree decision, spec, skill, or agent) admits no deterministic test or graded eval.

- ALWAYS: {rule} ([audit])
- NEVER: {prohibition} ([audit])

### Eval

Verified by graded LLM behavior over curated cases — the subject is a skill, agent, or classifier whose output has a parseable contract.

- ALWAYS: {rule} ([eval])
- NEVER: {prohibition} ([eval])

### Testing

Verified by a deterministic test. Each rule carries its evidence type — one of `scenario`, `mapping`, `conformance`, `property`, `compliance` — routed through `/testing`.

- ALWAYS: {rule} ([{evidence type}])
- NEVER: {prohibition} ([{evidence type}])
