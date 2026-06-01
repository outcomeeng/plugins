# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions whose compliance rules carry valid per-rule evidence modes and flow into spec assertions with sufficient evidence
SO THAT all spec-tree projects
CAN eliminate malformed or unenforced architecture decisions before they accumulate

## ADR Evidence Model

The audit answers one question: **does this ADR declare an enforceable architecture decision whose rules are both routed to a valid evidence mode and enforced downstream at or above that mode?**

Evidence requires four properties checked in order:

1. **Section structure** — the ADR carries the required sections (Purpose, Context, Decision, Rationale, Trade-offs, Compliance); Invariants only when algebraic properties hold
2. **Atemporal voice** — the ADR states architecture truth, never history
3. **Per-rule mode validity** — every Compliance MUST/NEVER rule carries exactly one evidence-mode tag naming one of the five claim shapes (scenario, mapping, conformance, property, compliance)
4. **Downstream sufficiency** — every Compliance rule resolves to a spec assertion in the governed subtree whose evidence meets or exceeds the rule's declared mode

Language-specific ADR concerns — testability-in-Compliance (dependency injection, no-mocking), execution-level accuracy — are out of scope here and stay in `auditing-{lang}-architecture`.

## Per-rule Mode Validity Model

Each Compliance rule names the minimum evidence mode its downstream enforcement must carry, chosen from the rule's claim shape via `/testing` (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). The audit checks the tag is present and names one of the five modes; it does not re-derive the mode (mode selection is `/testing`'s authority). A missing tag, a tag naming a bare mechanism (`[review]`/`[test]`/`[eval]`) instead of a mode, or more than one tag is a finding.

## Downstream Sufficiency Model

For each Compliance rule the auditor finds the spec assertion(s) enforcing it in the governed subtree and compares the assertion's evidence against the rule's declared mode. Presence alone is insufficient: a `property`-floor rule enforced only by a `scenario` assertion is a finding (`insufficient-evidence-mode`), not a judgment call. A rule with no downstream assertion is `unenforced-rule`.

## Assertions

### Scenarios

- Given an ADR missing a required section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "missing-section" ([eval](evals/structure/eval.toml))
- Given an ADR with temporal language in any section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given an ADR whose Compliance rule carries a bare mechanism tag instead of a mode tag, when audited by `/audit-adr`, then the verdict is REJECT with finding category "invalid-mode-tag" ([eval](evals/mode-validity/eval.toml))
- Given an ADR whose `property`-floor Compliance rule resolves only to a `scenario` spec assertion, when audited by `/audit-adr`, then the verdict is REJECT with finding category "insufficient-evidence-mode" ([eval](evals/mode-floor/eval.toml))
- Given an ADR whose Compliance rule has no downstream spec assertion, when audited by `/audit-adr`, then the verdict is REJECT with finding category "unenforced-rule" ([eval](evals/mode-floor/eval.toml))
- Given an ADR where all four properties hold, when audited by `/audit-adr`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check the four properties in order — structure, voice, mode validity, downstream sufficiency — and stop at the first failure ([review])
- ALWAYS: validate each Compliance rule's mode tag against the five modes without re-deriving the mode — mode selection is `/testing`'s authority ([review])
- NEVER: approve an ADR whose Compliance rule resolves to a downstream assertion below the rule's declared mode — sufficiency, not mere presence, is the bar ([review])
- NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([review])
