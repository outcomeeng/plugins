# Audit Tests Delivery

PROVIDES the Spec Tree plugin's `audit-tests` skill and `test-evidence-auditor` wrapper implementing the portable test-evidence audit methodology
SO THAT the main conversation and implementation-audit composition
CAN dispatch isolated test-evidence verdicts through one shared skill contract

## Assertions

### Compliance

- ALWAYS: `audit-tests` implements `spx/31-outcomeeng.enabler/31-verification.enabler/31-audit-verification.enabler/54-audit-tests.enabler/audit-tests.md` without redefining its testability, evidence-quality, ownership, or assertion-placement rules ([audit])
- ALWAYS: given successful required language-concern composition, the language-neutral `audit-tests` skill inspects every artifact in a non-Python evidence chain before approval, rejects unsourced protocol vocabulary in imported test infrastructure, and identifies the transitive artifact and required ownership target in its structured verdict ([eval](evals/full-chain-ownership/eval.toml))
- ALWAYS: the Codex runtime rendering of `audit-tests` satisfies the same non-Python full-chain ownership verdict contract as the shared authored skill ([eval](evals/full-chain-ownership-codex/eval.toml))
- ALWAYS: `audit-tests` is reached only by dispatching the `test-evidence-auditor` agent; the main conversation does not invoke the audit skill in place ([audit])
- ALWAYS: `audit-tests` invokes contextualization on the target spec node before audit analysis and composes the applicable language test-audit concern ([audit])
- NEVER: `audit-tests` runs the project's test, coverage, validation, or eval commands — deterministic verification completes before dispatch ([audit])
