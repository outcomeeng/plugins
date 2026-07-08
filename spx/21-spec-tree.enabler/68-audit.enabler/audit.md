# Audit

PROVIDES implementation-audit orchestration through one spec-tree-owned `implementation-auditor` wrapper agent that records audit coverage, findings, terminal state, and the rendered projection through `spx verification run`
SO THAT all language plugins
CAN contribute code, test, and architecture audit intelligence without shipping per-language auditor agents or plugin-side verdict scripts

## Assertions

### Compliance

- ALWAYS: every programming-language plugin ships its implementation-code audit skill as `audit-{lang}-code` beside its `audit-{lang}-tests` and `audit-{lang}-architecture` concern skills ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- NEVER: implementation-audit orchestration uses plugin-side `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py`; audit payload validation and projection are SPX responsibilities ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- NEVER: the spec-tree plugin ships the retired implementation-audit agents `auditor` or `audit-orchestrator`; implementation audit has one wrapper agent, `implementation-auditor` ([test](tests/test_implementation_audit_contract.compliance.l1.py))

### Audit

- Given a changeset scope with a supported implementation partition, when `implementation-auditor` runs, then it starts one `spx verification run` with `--verification-type audit --scope-type changeset`, records required code, test, and architecture coverage units, records concern findings, finishes the run, and relays the rendered projection ([audit])
- ALWAYS: implementation audits enter through the `implementation-auditor` agent, whose only audit behavior is invoking `spec-tree:audit` in an isolated verifier context and relaying the rendered `spx verification run` projection ([audit])
- ALWAYS: implementation-audit orchestration records planned or classified coverage units with `spx verification run scope add`, records findings with `spx verification run finding add`, and finishes and renders the run through `spx verification run finish` and `spx verification run render` ([audit])
- ALWAYS: each language implementation partition requires `audit-{lang}-code`, `audit-{lang}-tests`, and `audit-{lang}-architecture`; the old `audit-{lang}` implementation-code skill name is not a valid dispatch target ([audit])
- ALWAYS: producer metadata separates stable producer identity from producer provenance, including the owning plugin version when a concern skill exists, so convergence identity survives plugin version changes ([audit])
- NEVER: implementation-audit orchestration runs deterministic validation, test, or eval commands; those checks remain the main conversation's changeset responsibility and CI's repository responsibility ([audit])
