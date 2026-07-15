# Audit

PROVIDES implementation-audit orchestration through one spec-tree-owned `implementation-auditor` wrapper agent that records audit coverage, findings, terminal state, and the rendered projection through `spx verification run`
SO THAT all language plugins
CAN contribute code, test, and architecture audit intelligence without shipping per-language auditor agents or plugin-side verdict scripts

## Assertions

### Scenarios

- Given the pinned published SPX CLI and source-owned implementation-audit payload contracts, when the verification-run lifecycle records scope and finding evidence and finishes with the evidence-derived status, then it returns monotonic evidence sequences and a sealed projection carrying the authoritative finding count ([test](tests/test_implementation_audit_contract.scenario.l1.py))

### Compliance

- ALWAYS: every programming-language plugin ships its implementation-code audit skill as `audit-{lang}-code` beside its `audit-{lang}-tests` and `audit-{lang}-architecture` concern skills ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- ALWAYS: the `implementation-auditor` wrapper is a thin projection relay that invokes `spec-tree:audit-implementation`, carries the caller's changeset scope and optional advisory live file list, owns no audit policy, and relays the exact `spx verification run` token and rendered projection ([audit])
- ALWAYS: the `spec-tree:audit-implementation` prompt contract requires request validation, one audit run started before concern analysis, language and concern partitioning for every implementation scope, required `audit-{lang}-{code|tests|architecture}` concern dispatch, scope and finding recording through `spx verification run` with the published audit payload field names, missing-skill rejection before dispatch, terminal status derived from accepted evidence, final projection relay, and complete blocked-command relay carrying the run token when started, exact command, payload source and key, exit code, and stderr ([audit])
- ALWAYS: each `audit-{lang}-architecture` concern skill accepts composition by `implementation-auditor` for implementation architecture scope and by the artifact-type auditor that governs decision records for ADR language-specific architecture concerns ([audit])
- NEVER: implementation-audit orchestration uses plugin-side `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py`; audit payload validation and projection are SPX responsibilities ([audit])
- NEVER: the spec-tree plugin ships implementation-audit agents named `auditor` or `audit-orchestrator`; implementation audit has one wrapper agent, `implementation-auditor` ([test](tests/test_implementation_audit_contract.compliance.l1.py))
