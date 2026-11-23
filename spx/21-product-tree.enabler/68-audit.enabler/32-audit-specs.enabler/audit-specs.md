---
id: 01a0ebba-5f66-7099-bada-7c732ce43af8
malleability: spec
---

# Audit Specs

PROVIDES an audit methodology that verifies a spec node's rows stand under group headings naming their verification types, carry no tag, and fit the type their heading names — including that a claim about authored prose or documentation content never stands under a `Test.` heading
SO THAT all product-tree projects
CAN eliminate malformed node specs and stop prose-bound claims from masquerading as behavioral test evidence before they accumulate

## Assertions

### Audit: properties checked

- property-order: ALWAYS: `/audit-specs` checks section structure, atemporal voice, and per-row heading fitness in that order
- section-structure: ALWAYS: section structure holds when the node carries the opening and front matter its canonical kind template requires and a nonempty `## Assertions` section whose every row stands under a group heading naming its verification type — `Test.Scenario`, `Test.Mapping: <slug>`, `Test.Conformance`, `Test.Property`, `Test.Compliance`, `Evaluate: <slug>`, `Probe`, or `Audit`; a variant follows its parent's kind, and an admitted prior enabler or outcome form keeps its three-clause opening
- heading-names-type: ALWAYS: `/audit-specs` reads each group heading as the verification type of its rows, so `### Audit` heads audit rows and `### Test.Compliance` heads compliance tests, and finds a tag on a row an `invalid-tag` finding
- heading-fitness: ALWAYS: a row's claim fits the type its heading names; under a `Test.` heading the assertion type fits the claim's quantifier, a universal never standing under `Test.Scenario`, judged against the `/test` router without relitigating a choice it leaves open
- slug-link-fitness: ALWAYS: a row's slug links an artifact only in the directory its heading's type names — `tests/` for a `Test.` heading, `evals/` for `Evaluate`, `probes/` for `Probe` — and an `Audit` row links none; a row whose evidence does not exist yet stands with its plain slug and draws no finding
- prose-coupling: ALWAYS: a claim whose subject is authored prose or documentation content standing under a `Test.` heading is a `prose-coupling` finding, whether the would-be evidence reads the authored artifact directly or through test infrastructure; its verification belongs under `Evaluate` or `Audit`
- approval-not-evidence: NEVER: approval of a spec declaration establishes evidence completeness, implementation correctness, or Passing state for a row whose slug links no evidence
- no-architecture-classification: NEVER: classify a node's content as architecture-versus-product-behavior — that classification is the decision-record audits' concern, not the node audit's

### Audit: finding rules

- temporal-voice-rejected: ALWAYS: a spec node with temporal language in any section yields a sealed audit run whose terminal status is `rejected` with a finding whose rule is `temporal-voice`
- evidence-type-mismatch: ALWAYS: a universal claim standing under `Test.Scenario` yields a sealed audit run whose terminal status is `rejected` with a finding whose rule is `evidence-type-mismatch`

### Audit: audit run

- read-only-context: ALWAYS: before any audit phase, `/audit-specs` loads read-only at the audited snapshot the complete Walk to the target spec node as the work — every ancestor spec from the root, at each level along the path every sibling spec and each Decision Record indexed below the child the path continues through, every `ISSUES.md` along the path, the published contracts of the target's immediate children, the target's own Decision Records and spec, its Knowledge `index.md` and its Outcome record — then each decision a loaded spec or decision cites from another subtree, once; it runs no command that fetches, rebases, or moves the checkout, so the audit changes no checkout state
- caller-independent: ALWAYS: `/audit-specs` names no caller and stays invocable on its own; the Author's agent session produces a verdict by dispatching the audit to a separate Verifier's agent session rather than grading its own work in place, per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md)
- touched-text-only: ALWAYS: the spec auditor rejects only on touched text under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no touched finding exists
- run-recording: ALWAYS: `/audit-specs` records its audit through `spx verification run` on a file scope anchored on the node spec path: one root unit with `auditKind` `spec`, one child per declaration-quality property, and every finding. It returns the run token, the run file, and the rendered projection, or a blocked diagnostic when spx refuses a recorded payload or the finish, and the `spec-auditor` wrapper passes the raw target and its run-driver identity and relays them unchanged
- record-as-judged: ALWAYS: `/audit-specs` records the root unit as soon as the run starts, each other unit as soon as its judgment completes, and each finding on touched text as soon as it is raised and its unit is recorded, so no unit or finding waits for the judgment of a later unit

### Evaluate: [structure](evals/structure/eval.toml)

`/audit-specs` audits the spec `spx/30-task.domain/30-quick-add.capability/quick-add.spec.md` in a fixture repository whose `spx/` tree is `versions/4.0/examples/todo-app/80-final/spx/` of `outcomeeng/methodology` at commit `da267d119627814d4a3e391b89aac61caa0a1b5a`, https://github.com/outcomeeng/methodology/tree/da267d119627814d4a3e391b89aac61caa0a1b5a/versions/4.0/examples/todo-app/80-final/spx, with each case's mutation applied to that spec and the rest of the tree unchanged, and reports its sealed run's terminal status and finding rules, which the eval compares with the case's expected status and rule.

| Case               | Mutation of the baseline spec                                                                          | Terminal status | Finding rule             |
| ------------------ | ------------------------------------------------------------------------------------------------------ | --------------- | ------------------------ |
| conforming         | none                                                                                                   | approved        | none                     |
| missing-section    | delete the `## Assertions` line and every line below it                                                | rejected        | missing-section          |
| malformed-kind     | replace the PROVIDES line with `PROVIDES one-line natural-language task capture SO THAT every surface` | rejected        | malformed-kind-statement |
| heading-mismatch   | replace `### Test.Scenario: capture` with `### Test.Compliance: capture`                               | rejected        | heading-mismatch         |
| untagged-audit-row | delete every group under `## Assertions` except `### Audit: messages`                                  | approved        | none                     |
| tagged-audit-row   | append a space and `([audit])` to the `reject-message` row                                             | rejected        | invalid-tag              |
