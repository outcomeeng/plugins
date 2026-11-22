---
id: 01a0ebba-5f62-706c-86af-c631392a9d61
malleability: spec
---

# ADR Auditing

PROVIDES an audit methodology verifying ADRs declare well-formed architecture decisions in the settled decision-record form
SO THAT all product-tree projects
CAN eliminate malformed architecture decisions before they accumulate

## Assertions

### Audit: declaration form

- check-order: ALWAYS: check structure, voice, and declaration form with tag validity in order.
- template-is-authority: ALWAYS: judge section structure, atemporal voice, and tag validity from the canonical decision template, never from a transcribed copy of it.
- so-that-property: ALWAYS: verify the SO THAT line names a property of the build that the TO mechanism yields, never an audience and never a restatement of the mechanism.
- type-fits-quantifier: ALWAYS: verify each rule's assertion type, named by its group heading, fits the claim's quantifier per the `/test` router — a universal is never `scenario`; reject a type the router would not produce, without relitigating a choice the router leaves open.
- ungrouped-rule: ALWAYS: a rule under `## Verification` that stands under no typed group heading is a `declaration-form` finding.
- approval-is-not-evidence: NEVER: approval of an ADR declaration establishes that its rules have evidence or that the governed implementation complies.
- no-content-classification: NEVER: classify ADR content as product-behavior-versus-architecture — an ADR's content is architecture by definition; that classification is the PDR audit's concern.

### Audit: context, composition and recording

- record-as-judged: ALWAYS: `/audit-adr` records the root unit as soon as the run starts, each other unit as soon as its judgment completes, and each finding on touched text as soon as it is raised and its unit is recorded, so no unit or finding waits for the judgment of a later unit.
- read-only-context: ALWAYS: before any audit phase, load read-only at the audited snapshot the complete Walk to the Node that holds the ADR — every ancestor spec from the root, at each level along the path every sibling spec and each Decision Record indexed below the child the path continues through, every `ISSUES.md` along the path, the published contracts of the Node's immediate children, the Node's own Decision Records and spec, its Knowledge `index.md` and its Outcome record — then each decision a loaded spec or decision cites from another subtree, once; judge the ADR as the subject, read every other loaded decision for awareness, and take as governing the ADR only a decision that governs it by Index, scope or citation: one at a lower Index than the ADR in its own directory, one at a lower Index than the child the path continues through at an ancestor level, or one that a loaded spec or a governing record cites for it from another subtree; run no command that fetches, rebases, or moves the checkout, so the audit changes no checkout state.
- compose-language-architecture: ALWAYS: compose language-specific ADR concerns by invoking `audit-{lang}-architecture` for the language detected in scope, rather than dispatching a separate language-specific auditor agent.
- language-verdict-consumed: Given a composed language-architecture verdict with malformed fields, a different target, missing required concern rows, or an inconsistent overall result, when the ADR audit consumes it, then the ADR audit run records a `language-result-invalid` finding and accepts no partial concern coverage.
- touched-text-only: ALWAYS: the ADR auditor rejects only on touched text under [the verification PDR](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no touched finding exists.
- run-recording: ALWAYS: `/audit-adr` records its audit through `spx verification run` on a file scope anchored on the ADR path: one root unit with `auditKind` `adr`, one child per audited property and per composed language concern, and every finding. It returns the run token, the run file, and the rendered projection, or a blocked diagnostic when spx refuses a recorded payload or the finish, and the `adr-auditor` wrapper passes the raw target and its run-driver identity and relays them unchanged.

### Evaluate: [structure](evals/structure/eval.toml)

`/audit-adr` audits the ADR `spx/30-task.domain/30-quick-add.capability/15-interpreter.adr.md` in a fixture repository whose `spx/` tree is `versions/4.0/examples/todo-app/80-final/spx/` of `outcomeeng/methodology` at commit `da267d119627814d4a3e391b89aac61caa0a1b5a`, https://github.com/outcomeeng/methodology/tree/da267d119627814d4a3e391b89aac61caa0a1b5a/versions/4.0/examples/todo-app/80-final/spx, with each case's mutation applied to that ADR and the rest of the tree unchanged, and seals an audit run whose terminal status and finding rule the eval compares with the case's.

| Case                                       | Mutation of the baseline ADR                                                                                          | Then                                         |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| well-formed-adr-passes                     | none                                                                                                                  | `approved`, with no finding                  |
| missing-verification-section               | delete the `## Verification` line and every line below it                                                             | `rejected` with a `missing-section` finding  |
| missing-opening-decision-statement         | delete the CONSTRAINS, TO and SO THAT lines                                                                           | `rejected` with a `missing-section` finding  |
| rationale-and-invariants-sections-rejected | insert `## Rationale` and the line `The fallback keeps capture working when the model fails.` above `## Verification` | `rejected` with a `declaration-form` finding |
| so-that-names-an-audience-rejected         | replace the SO THAT line with `SO THAT people adding tasks and support staff share one capture vocabulary`            | `rejected` with a `so-that-property` finding |

### Evaluate: [voice](evals/voice/eval.toml)

`/audit-adr` audits the ADR `spx/30-task.domain/30-quick-add.capability/15-interpreter.adr.md` in the fixture repository of the structure subsection, with each case's mutation applied to that ADR, and seals an audit run whose terminal status and finding rule the eval compares with the case's.

| Case                       | Mutation of the baseline ADR                                                                                                          | Then                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| atemporal-adr-passes       | none                                                                                                                                  | `approved`, with no finding                |
| temporal-opening-statement | append `, which replaced the earlier regular-expression parser` to the TO line                                                        | `rejected` with a `temporal-voice` finding |
| temporal-verification-rule | replace `the deterministic fallback produces` in the `fallback-task` row with `since the outage, the deterministic fallback produces` | `rejected` with a `temporal-voice` finding |

### Evaluate: [tag-validity](evals/tag-validity/eval.toml)

`/audit-adr` audits the ADR `spx/30-task.domain/30-quick-add.capability/15-interpreter.adr.md` in the fixture repository of the structure subsection, with each case's mutation applied to that ADR, and seals an audit run whose terminal status and finding rule the eval compares with the case's.

| Case                                  | Mutation of the baseline ADR                                                                                                                   | Then                                                 |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| valid-form-passes                     | none                                                                                                                                           | `approved`, with no finding                          |
| audit-tag-on-compliance-rule-rejected | append a space and `([audit])` to the `fallback-task` row                                                                                      | `rejected` with an `invalid-tag` finding             |
| bare-mechanism-tag-rejected           | append a space and `([test])` to the `fallback-task` row                                                                                       | `rejected` with an `invalid-tag` finding             |
| eval-tag-on-audit-rule-rejected       | append the heading `### Audit: messages` and the row `- fallback-label: A task the fallback creates carries the label Uninterpreted. ([eval])` | `rejected` with an `invalid-tag` finding             |
| multiple-tags-rejected                | append a space and `([compliance]) ([audit])` to the `fallback-task` row                                                                       | `rejected` with an `invalid-tag` finding             |
| repeated-slug-rejected                | replace the slug `fallback-latency` with `fallback-task`                                                                                       | `rejected` with an `invalid-tag` finding             |
| universal-scenario-group-rejected     | replace `### Test.Compliance: fallback` with `### Test.Scenario: fallback`                                                                     | `rejected` with an `assertion-type-mismatch` finding |
