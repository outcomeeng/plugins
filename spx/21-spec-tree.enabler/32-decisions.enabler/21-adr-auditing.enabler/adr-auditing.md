# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions whose compliance rules carry valid per-rule evidence modes
SO THAT all spec-tree projects
CAN eliminate malformed architecture decisions before they accumulate

## ADR Evidence Model

The audit answers one question: **does this ADR declare a well-formed architecture decision whose compliance rules carry a valid evidence mode?**

Evidence requires three properties checked in order:

1. **Section structure** — the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present; Rationale and Invariants are optional, Invariants only when the decision establishes algebraic properties
2. **Atemporal voice** — the ADR states architecture truth, never history
3. **Per-rule mode validity** — every Compliance MUST/NEVER rule carries exactly one evidence-mode tag naming one of the five claim shapes (scenario, mapping, conformance, property, compliance)

Language-specific ADR concerns — testability-in-Compliance (dependency injection, no-mocking), execution-level accuracy — are out of scope here and stay in `auditing-{lang}-architecture`.

## Per-rule Mode Validity Model

Each Compliance rule carries an evidence-mode tag chosen from the rule's claim shape via `/testing` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit checks the tag is present and matches its subsection; it does not re-derive the mode (mode selection is `/testing`'s authority). A missing tag, a bare mechanism tag (`[review]`/`[test]`), a tag that disagrees with its subsection, or more than one tag is a finding.

## Assertions

### Scenarios

- Given an ADR missing a required section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "missing-section" ([eval](evals/structure/eval.toml))
- Given an ADR with temporal language in any section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given an ADR whose Compliance rule carries a bare mechanism tag instead of a mode tag, when audited by `/audit-adr`, then the verdict is REJECT with finding category "invalid-mode-tag" ([eval](evals/mode-validity/eval.toml))
- Given an ADR where all three properties hold, when audited by `/audit-adr`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check the three properties in order — structure, voice, mode validity — and stop at the first failure ([review])
- ALWAYS: validate each Compliance rule's mode tag against the five modes without re-deriving the mode — mode selection is `/testing`'s authority ([review])
- NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([review])
