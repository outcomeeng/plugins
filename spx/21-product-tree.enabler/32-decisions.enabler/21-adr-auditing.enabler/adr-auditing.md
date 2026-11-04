---
id: 01a0ebba-5f62-706c-86af-c631392a9d61
malleability: spec
---

# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions in authoring or routed verification form
SO THAT all product-tree projects
CAN eliminate malformed architecture decisions before they accumulate

## Assertions

- language-verdict-consumed: Given a composed language-architecture verdict with malformed fields, a different target, missing required concern rows, or an inconsistent overall result, when the ADR audit consumes it, then the ADR audit run records a `language-result-invalid` finding and accepts no partial concern coverage.
- ungrouped-draft-rules: Given an ADR with specific ungrouped rules directly under `## Verification`, alone or alongside valid groups, when its declaration is audited, then absent draft groups cause no finding and all other declaration-quality checks remain applicable.
- untagged-routed-rule: Given an ADR with an untagged rule inside a routed verification subsection, when audited, then the run records an `invalid-tag` finding against that rule.
- approval-is-not-evidence: NEVER: approval of an ADR declaration establishes that its ungrouped rules have evidence or that the governed implementation complies.

### Scenarios

- missing-section: Given an ADR without a `## Verification` section, when audited by `/audit-adr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `missing-section` ([eval](evals/structure/eval.toml))
- temporal-voice: Given an ADR with temporal language in the opening or any rule, when audited by `/audit-adr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `temporal-voice` ([eval](evals/voice/eval.toml))
- bare-mechanism-tag: Given an ADR whose `### Testing` compliance-type rule carries a bare mechanism tag instead of an assertion-type tag, when audited by `/audit-adr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `invalid-tag` ([eval](evals/tag-validity/eval.toml))
- universal-as-scenario: Given an ADR whose rule in a `### Scenario` group states a universal claim (ALWAYS/NEVER), when audited by `/audit-adr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `assertion-type-mismatch` ([eval](evals/tag-validity/eval.toml))
- all-properties-hold: Given an ADR written in the ADR template's form whose other properties hold, when audited by `/audit-adr`, then the sealed audit run's terminal status is `approved` ([eval](evals/structure/eval.toml))

### Compliance

- check-order: ALWAYS: check structure, voice, and declaration form with tag validity in order ([audit])
- template-is-authority: ALWAYS: judge section structure, atemporal voice, and tag validity from the canonical decision template, never from a transcribed copy of it ([audit])
- compose-language-architecture: ALWAYS: compose language-specific ADR concerns by invoking `audit-{lang}-architecture` for the language detected in scope, rather than dispatching a separate language-specific auditor agent ([audit])
- type-fits-quantifier: ALWAYS: verify each rule's assertion type, named by its group heading, fits the claim's quantifier per the `/test` router — a universal is never `scenario`; reject a type the router would not produce, without relitigating a choice the router leaves open ([audit])
- audit-tag: ALWAYS: accept an `### Audit` rule tagged `[audit:{rule-slug}]` whose slug is unique within the ADR, or tagged with the pathless `[audit]` that the foundation admits for a toolchain without slug support, and reject a slug that repeats within the ADR as `invalid-tag` ([audit])
- so-that-property: ALWAYS: verify the SO THAT line names a property of the build that the TO mechanism yields, never an audience and never a restatement of the mechanism. [audit]
- touched-text-only: ALWAYS: the ADR auditor rejects only on touched text under [the verification PDR](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no touched finding exists ([audit])
- run-recording: ALWAYS: `/audit-adr` records its audit through `spx verification run` on a file scope anchored on the ADR path: one root unit with `auditKind` `adr`, one child per audited property and per composed language concern, and every finding. It returns the run token, the run file, and the rendered projection, or a blocked diagnostic when spx refuses a recorded payload or the finish, and the `adr-auditor` wrapper passes the raw target and its run-driver identity and relays them unchanged ([audit])
- no-content-classification: NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern ([audit])
