---
id: 01a0ebba-5f62-706c-86af-c632b5d38e2f
malleability: spec
---

# PDR Auditing

PROVIDES an audit methodology verifying PDRs declare well-formed, observable product decisions
SO THAT all product-tree projects
CAN eliminate malformed product decisions before they accumulate

## Assertions

- ungrouped-draft-rules: Given a PDR with specific ungrouped rules directly under `## Verification`, alone or alongside valid groups, when its declaration is audited, then absent draft groups cause no finding and all other declaration-quality checks remain applicable.
- approval-is-not-evidence: NEVER: approval of a PDR declaration establishes that its ungrouped rules have evidence or that the product exhibits the declared behavior.
- next-form-approved: Given a PDR written in the PDR template's form whose other properties hold, when audited by `/audit-pdr`, then the sealed audit run's terminal status is `approved`. [eval: structure]
- declaration-form: Given a PDR whose opening lacks a GOVERNS paragraph, whose mapping rule is not its own `### Mapping: <slug>` subsection, whose group holds more than seven rules, or that holds text outside its opening, a rule, or a table, when audited by `/audit-pdr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `declaration-form`. [eval: structure]

### Scenarios

- architecture-content: Given a PDR containing architecture content ("use JWT tokens", "store in PostgreSQL"), when audited by `/audit-pdr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `architecture-content` ([eval](evals/structure/eval.toml))
- tooling-surface-observable: Given a PDR for a product whose product document declares its audience operates the product through a command-line, filesystem, or version-control surface, and whose statements describe the CLI, filesystem, or version-control state that audience observes, when audited by `/audit-pdr`, then content classification passes and the statements are not rejected as architecture ([eval](evals/structure/eval.toml))
- tooling-internals: Given a PDR whose statements describe a tool's internal algorithm, in-memory data structure, persisted schema, or library choice that the declared audience never operates, when audited by `/audit-pdr`, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `architecture-content` even for a tooling product ([eval](evals/structure/eval.toml))
- non-observable-behavior: Given a PDR whose CAN RELY ON line names behavior that is not user-observable (the database uses row-level locking), when audited, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `non-observable-property`. [eval: structure]
- temporal-language: Given a PDR with temporal language in the opening or any rule, when audited, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `temporal-language` ([eval](evals/voice/eval.toml))
- invalid-tag: Given a PDR whose `### Testing` rule carries a bare mechanism tag, a tag disagreeing with its subsection, no tag, or more than one tag, when audited, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `invalid-tag` ([eval](evals/tag-validity/eval.toml))
- assertion-type-mismatch: Given a PDR whose rule in a `### Scenario` group states a universal claim (ALWAYS/NEVER), when audited, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `assertion-type-mismatch`. [eval: tag-validity]
- consistency-violation: Given a PDR that contradicts the product document or an ancestor PDR, when audited, then the sealed audit run's terminal status is `rejected` with a finding whose rule is `consistency-violation` ([eval](evals/structure/eval.toml))

### Compliance

- six-content-types: ALWAYS: classify every PDR statement into at least six content types — product behavior, observable non-functional property, technology choice, implementation approach, data structure, performance implementation ([audit])
- audience-grounded-observable: ALWAYS: ground "observable" in the product document's declared audience and interaction surfaces rather than a fixed end-user-application assumption — a statement is product behavior when that audience observes or operates it, so an audience that operates the product through a command-line, filesystem, or version-control surface makes those mechanics product behavior, while the internal algorithm, in-memory data structure, persisted schema, and library choices that audience never operates remain architecture ([audit])
- read-only-context: ALWAYS: load the PDR's context read-only before any audit phase — the product document, then each spec and every decision record on the path from `spx/` to the directory containing the PDR, then every decision a loaded spec or decision cites by full `spx/` path, excluding the PDR under audit — never invoking `/contextualize` or `/sync-base`, so the audit changes no checkout state ([audit])
- classification-first: ALWAYS: check content classification as the first audit phase — a PDR full of architecture content fails regardless of other properties ([audit])
- can-rely-on-observable: ALWAYS: verify the behavior the CAN RELY ON line names is observable and falsifiable from the declared audience's perspective, not the implementation's, and holds at failure and boundary conditions. [audit]
- rule-type-fit: ALWAYS: verify each rule's assertion type, named by its group heading, fits the claim's quantifier per the `/test` router — a universal is never `scenario`; reject a type the router would not produce, without relitigating a choice the router leaves open. [audit]
- unique-slug: ALWAYS: accept an `### Audit` rule tagged `[audit:{rule-slug}]` whose slug is unique within the PDR, or tagged with the pathless `[audit]` that the foundation admits for a toolchain without slug support, and reject a slug that repeats within the PDR as `invalid-tag` ([audit])
- consistency-compared: ALWAYS: compare the PDR against the product document and ancestor PDRs; a contradiction with either is a consistency violation ([audit])
- atemporal: NEVER: approve temporal language in the opening or any rule. [audit]
- touched-text-only: ALWAYS: the PDR auditor rejects only on touched text under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no touched finding exists ([audit])
- run-recording: ALWAYS: `/audit-pdr` records its audit through `spx verification run` on a file scope anchored on the PDR path: one root unit with `auditKind` `pdr`, one child per evidence-model property, and every finding. It returns the run token, the run file, and the rendered projection, or a blocked diagnostic when spx refuses a recorded payload or the finish, and the `pdr-auditor` wrapper passes the raw target and its run-driver identity and relays them unchanged ([audit])
