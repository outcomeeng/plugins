# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions whose compliance rules carry valid per-rule evidence types
SO THAT all spec-tree projects
CAN eliminate malformed architecture decisions before they accumulate

## ADR Evidence Model

The audit answers one question: **does this ADR declare a well-formed architecture decision whose compliance rules carry a valid evidence type?**

Evidence requires three properties checked in order:

1. **Section structure** — the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present; Rationale and Invariants are optional, Invariants only when the decision establishes algebraic properties
2. **Atemporal voice** — the ADR states architecture truth, never history
3. **Per-rule tag validity** — every rule under `## Verification` carries exactly one tag valid for its subsection: `### Testing` rules carry one of the five evidence types (scenario, mapping, conformance, property, compliance), `### Eval` rules carry `[eval]`, and `### Audit` rules carry `[audit]`

Language-specific ADR concerns — testability-in-Compliance (dependency injection, no-mocking), execution-level accuracy — are out of scope here and stay in `auditing-{lang}-architecture`.

## Per-rule Tag Validity Model

A `### Testing` rule's evidence-type tag is chosen from the rule's claim shape via `/testing` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit checks the tag is present and matches its subsection; it does not re-derive the evidence type (evidence-type selection is `/testing`'s authority). A missing tag, a bare mechanism tag (`[review]`/`[test]`), a tag that disagrees with its subsection, or more than one tag is a finding.

## Assertions

### Scenarios

- Given an ADR missing a required section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "missing-section" ([eval](evals/structure/eval.toml))
- Given an ADR with temporal language in any section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given an ADR whose Compliance rule carries a bare mechanism tag instead of an evidence-type tag, when audited by `/audit-adr`, then the verdict is REJECT with finding category "invalid-mode-tag" ([eval](evals/mode-validity/eval.toml))
- Given an ADR where all three properties hold, when audited by `/audit-adr`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check structure, voice, and tag validity in order ([review])
- ALWAYS: validate each rule's tag against its subsection without re-deriving the evidence type — evidence-type selection is `/testing`'s authority ([review])
- NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([review])
