# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions whose compliance rules carry valid per-rule evidence types
SO THAT all spec-tree projects
CAN eliminate malformed architecture decisions before they accumulate

## ADR Evidence Model

The audit answers one question: **does this ADR declare a well-formed architecture decision whose compliance rules carry a valid evidence type?**

Evidence requires three properties checked in order:

1. **Section structure** — the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present; Rationale and Invariants are optional, Invariants only when the decision establishes algebraic properties
2. **Atemporal voice** — the ADR states architecture truth, never history
3. **Per-rule tag validity and evidence-type fit** — every rule under `## Verification` carries exactly one tag valid for its subsection: `### Testing` rules carry one of the five evidence types (scenario, mapping, conformance, property, compliance), `### Eval` rules carry `[eval]`, and `### Audit` rules carry `[audit]`; and a `### Testing` rule's evidence type fits the claim's quantifier — a universal (ALWAYS/NEVER) is never `scenario`

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are out of scope here and stay in `auditing-{lang}-architecture`.

## Per-rule Tag Validity Model

A `### Testing` rule's evidence-type tag is chosen from the rule's claim shape via `/testing` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). `/testing` selects the type; the audit verifies the selection is correct against the claim's shape — the decisive check is the quantifier: a universal claim (ALWAYS/NEVER) is never `scenario`, because a scenario proves one case and cannot establish a claim about every case. The audit does not relitigate a choice the router leaves open between equally-valid types. A missing tag, a bare mechanism tag (`[review]`/`[test]`), a tag that disagrees with its subsection, more than one tag, or an evidence type the `/testing` router would not produce for the claim is a finding.

## Assertions

### Scenarios

- Given an ADR missing a required section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "missing-section" ([eval](evals/structure/eval.toml))
- Given an ADR with temporal language in any section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given an ADR whose Compliance rule carries a bare mechanism tag instead of an evidence-type tag, when audited by `/audit-adr`, then the verdict is REJECT with finding category "invalid-mode-tag" ([eval](evals/mode-validity/eval.toml))
- Given an ADR whose `### Testing` rule tags a universal claim (ALWAYS/NEVER) as `scenario`, when audited by `/audit-adr`, then the verdict is REJECT with finding category "evidence-type-mismatch" ([eval](evals/mode-validity/eval.toml))
- Given an ADR where all three properties hold, when audited by `/audit-adr`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check structure, voice, and tag validity in order ([review])
- ALWAYS: verify each `### Testing` rule's evidence type fits the claim's quantifier per the `/testing` router — a universal is never `scenario`; reject a type the router would not produce, without relitigating a choice the router leaves open ([review])
- NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([review])
