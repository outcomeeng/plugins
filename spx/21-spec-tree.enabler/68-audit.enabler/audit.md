# Audit

PROVIDES implementation-audit orchestration through one spec-tree-owned `implementation-auditor` wrapper agent that records audit coverage, findings, terminal state, and the rendered projection through `spx verification run`
SO THAT all language plugins
CAN contribute code, test, and architecture audit intelligence without shipping per-language auditor agents or plugin-side verdict scripts

## Assertions

### Compliance

- ALWAYS: every programming-language plugin ships its implementation-code audit skill as `audit-{lang}-code` beside its `audit-{lang}-tests` and `audit-{lang}-architecture` concern skills ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- ALWAYS: the `implementation-auditor` wrapper is a thin projection relay that invokes `spec-tree:audit-implementation`, carries the caller's changeset scope and optional advisory live file list, owns no audit policy, and relays the exact `spx verification run` token and rendered projection ([audit])
- ALWAYS: the `spec-tree:audit-implementation` prompt contract requires request validation, one started audit run, language and concern partitioning for every implementation scope, required `audit-{lang}-{code|tests|architecture}` concern dispatch, scope and finding recording through `spx verification run`, missing-skill rejection before dispatch, terminal status derived from accepted evidence, and final projection relay ([audit])
- ALWAYS: each `audit-{lang}-architecture` concern skill accepts composition by `implementation-auditor` for implementation architecture scope and by `adr-auditor` for ADR language-specific architecture concerns ([audit])
- ALWAYS: the published `spx verification run` audit lifecycle accepts implementation-audit input, scope, and finding payloads, extracts the reported `runToken`, records validated scope and finding payloads, finishes with the evidence-derived terminal status, and renders the sealed projection with the authoritative finding count ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- NEVER: implementation-audit orchestration uses plugin-side `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py`; audit payload validation and projection are SPX responsibilities ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- NEVER: the spec-tree plugin ships the retired implementation-audit agents `auditor` or `audit-orchestrator`; implementation audit has one wrapper agent, `implementation-auditor` ([test](tests/test_implementation_audit_contract.compliance.l1.py))

### Audit

- Given a changeset scope with a supported implementation partition, when `implementation-auditor` runs, then it starts one `spx verification run` with `--verification-type audit --scope-type changeset`, extracts the `runToken` from the start JSON locator, records required code, test, and architecture coverage units, records concern findings, finishes the run with the evidence-derived terminal status, and relays the rendered projection ([audit])
- ALWAYS: implementation audits enter through the `implementation-auditor` agent, whose only audit behavior is invoking `spec-tree:audit-implementation` in an isolated verifier context and relaying the rendered `spx verification run` projection ([audit])
- ALWAYS: implementation-audit orchestration records planned or classified coverage units with `spx verification run scope add`, records findings with `spx verification run finding add`, and finishes and renders the run through `spx verification run finish` and `spx verification run render` ([audit])
- ALWAYS: each language implementation partition requires `audit-{lang}-code`, `audit-{lang}-tests`, and `audit-{lang}-architecture`; the old `audit-{lang}` implementation-code skill name is not a valid dispatch target ([audit])
- ALWAYS: producer metadata separates stable producer identity from producer provenance, including the owning plugin version when a concern skill exists, so convergence identity survives plugin version changes ([audit])
- ALWAYS: a gating implementation audit addresses an exact committed changeset head after deterministic verification passes; an implementation audit over modified or untracked files is advisory and cannot satisfy an apply or merge gate ([audit])
- NEVER: implementation-audit orchestration runs deterministic validation, test, or eval commands; those checks remain the main conversation's changeset responsibility and CI's repository responsibility ([audit])
