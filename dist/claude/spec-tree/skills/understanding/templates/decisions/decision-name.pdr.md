# {Decision Name}

{The decision, stated directly as permanent truth in 1-3 sentences — what product behavior it governs and what it decides. State user-observable behavior, not implementation. No "Purpose" heading, no preamble.}

## Rationale

{Brief — why this is right for users. Name a rejected alternative only when it sharpens the decision. Omit if self-evident.}

## Product invariants

{Omit if none. Observable user-facing guarantees users can rely on.}

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

Verified by a deterministic test. Each rule carries its claim-shape mode — one of `scenario`, `mapping`, `conformance`, `property`, `compliance` — routed through `/testing`.

- ALWAYS: {rule} ([{mode}])
- NEVER: {prohibition} ([{mode}])
