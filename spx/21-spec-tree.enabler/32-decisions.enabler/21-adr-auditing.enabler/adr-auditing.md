# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions in authoring or routed verification form
SO THAT all spec-tree projects
CAN eliminate malformed architecture decisions before they accumulate

## ADR Evidence Model

The audit answers one question: **does this ADR declare a well-formed architecture decision whose rules conform to their declaration form?**

Evidence requires three properties checked in order:

1. **Section structure** — the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present; Rationale and Invariants are optional, Invariants only when the decision establishes algebraic properties
2. **Atemporal voice** — the ADR states architecture truth, never history
3. **Per-rule declaration form and tag fitness** — untagged rules directly under `## Verification` are authoring declarations awaiting selection; every rule in a routed subsection carries exactly one valid tag: `### Testing` rules carry one of the five assertion types (scenario, mapping, conformance, property, compliance), `### Eval` rules carry `[eval]`, and `### Audit` rules carry `[audit]`; a `### Testing` rule's assertion type fits the claim's quantifier — a universal (ALWAYS/NEVER) is never `scenario`

Section structure, atemporal voice, and tag validity are judged from the canonical decision template (`spx/21-spec-tree.enabler/21-templates.enabler`), never a transcribed copy of it. Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed by invoking `audit-{lang}-architecture` for the language detected in scope; that skill carries only those language-specific concerns and never re-judges structure, voice, or tags.

## Per-rule Tag Validity Model

A `### Testing` rule's assertion-type tag is chosen from the rule's claim shape via `/test` after `/verify` selects test (see `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md`). `/test` selects the assertion type; the audit verifies the selection is correct against the claim's shape — the decisive check is the quantifier: a universal claim (ALWAYS/NEVER) is never `scenario`, because a scenario proves one case and cannot establish a claim about every case. The audit does not relitigate a choice the router leaves open between equally-valid types. A missing tag inside a routed subsection, a bare mechanism tag (`[review]`/`[test]`), a tag that disagrees with its subsection, more than one tag, or an assertion type the `/test` router would not produce for the claim is a finding. Untagged rules directly under `## Verification` receive declaration-quality checks without a missing-tag finding; their approval establishes no evidence result.

## Assertions

- Given an ADR with specific untagged rules directly under `## Verification`, alone or alongside valid routed subsections, when its declaration is audited, then absent draft tags and subsections cause no finding and all other declaration-quality checks remain applicable.
- Given an ADR with an untagged rule inside a routed verification subsection, when audited, then the verdict rejects that rule as `invalid-tag`.
- NEVER: approval of an ADR declaration establishes that its untagged rules have evidence or that the governed implementation complies.

### Scenarios

- Given an ADR missing a required section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "missing-section" ([eval](evals/structure/eval.toml))
- Given an ADR with temporal language in any section, when audited by `/audit-adr`, then the verdict is REJECT with finding category "temporal-voice" ([eval](evals/voice/eval.toml))
- Given an ADR whose `### Testing` compliance-type rule carries a bare mechanism tag instead of an assertion-type tag, when audited by `/audit-adr`, then the verdict is REJECT with finding category "invalid-tag" ([eval](evals/tag-validity/eval.toml))
- Given an ADR whose `### Testing` rule tags a universal claim (ALWAYS/NEVER) as `scenario`, when audited by `/audit-adr`, then the verdict is REJECT with finding category "assertion-type-mismatch" ([eval](evals/tag-validity/eval.toml))
- Given an ADR where all three properties hold, when audited by `/audit-adr`, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: check structure, voice, and tag validity in order ([audit])
- ALWAYS: judge section structure, atemporal voice, and tag validity from the canonical decision template, never from a transcribed copy of it ([audit])
- ALWAYS: compose language-specific ADR concerns by invoking `audit-{lang}-architecture` for the language detected in scope, rather than dispatching a separate language-specific auditor agent ([audit])
- ALWAYS: verify each `### Testing` rule's assertion type fits the claim's quantifier per the `/test` router — a universal is never `scenario`; reject a type the router would not produce, without relitigating a choice the router leaves open ([audit])
- NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([audit])
