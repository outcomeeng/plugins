# Audit

PROVIDES implementation-audit orchestration through one spec-tree-owned `implementation-auditor` wrapper agent that records audit coverage, findings, terminal state, and the rendered projection through `spx verification run`
SO THAT all language plugins
CAN contribute code, test, and architecture audit intelligence without shipping per-language auditor agents or plugin-side verdict scripts

## Assertions

- ALWAYS: the `spec-tree:audit-implementation` prompt contract admits only `audited`, `not-applicable`, `missing-skill`, or `unsupported` as a required coverage unit's final status, and requires a run that reaches none of those to return the blocked diagnostic naming the concrete failed operation or absent prerequisite ([audit])
- ALWAYS: the `spec-tree:audit-implementation` prompt contract requires reconciliation before the run finishes — every planned unit carries a final status and every recorded finding references an accepted unit — and continues the run when reconciliation fails ([audit])
- ALWAYS: the `spec-tree:audit-implementation` prompt contract requires each subject body to be inspected completely from the resolved base-to-head scope, re-issuing a truncated or partial read in bounded ranges until the body is complete ([audit])
- ALWAYS: the `spec-tree:audit-implementation` prompt contract requires each concern's governing standards and the audited repository's declared `spx/local/` overlays to load before a finding is accepted ([audit])
- NEVER: the `spec-tree:audit-implementation` prompt contract admits remaining work, elapsed time, context pressure, or unfinished reading as a cause for ending a run, or derives a subject body from a single commit's patch rather than the resolved base-to-head scope ([audit])

### Scenarios

- Given a feature branch whose local base lags its remote-tracking base, when implementation-audit scope discovery receives `HEAD`, then it returns the full remote-base and feature commit identities and only the feature's changed paths ([test](tests/test_implementation_scope.scenario.l1.py))
- Given a nonexistent repository path, when implementation-audit scope discovery receives it through `--repo`, then it returns an unsuccessful scope-resolution diagnostic naming that path, without scope JSON or a Python traceback ([test](tests/test_implementation_scope.scenario.l1.py))
- Given the pinned published SPX CLI and source-owned implementation-audit payload contracts, when the verification-run lifecycle records scope and finding evidence and finishes with the evidence-derived status, then it returns monotonic evidence sequences and a sealed projection carrying the authoritative finding count ([test](tests/test_implementation_audit_contract.scenario.l3.py))
- Given a verification run carrying a recorded blocking finding, when the lifecycle finishes with an approving terminal status, then the finish fails rather than sealing a terminal status the recorded evidence contradicts ([test](tests/test_implementation_audit_contract.scenario.l3.py))

### Compliance

- ALWAYS: every programming-language plugin ships its implementation-code audit skill as `audit-{lang}-code` beside its `audit-{lang}-tests` and `audit-{lang}-architecture` concern skills ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- ALWAYS: `implementation-auditor` is the only implementation-audit wrapper agent; no `auditor`, `audit-orchestrator`, or language-specific auditor agent exists ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- ALWAYS: every typed `implementation-auditor` run records implementation-audit input, scope, findings, terminal state, and a sealed rendered projection through the published `spx verification run` lifecycle ([audit])
- ALWAYS: the `implementation-auditor` wrapper is a thin projection relay that invokes `spec-tree:audit-implementation` with the caller's raw scope selector, supplies its own run-driver producer identity as internal request data, owns no audit policy, and relays the exact `spx verification run` token and rendered projection; the invoked skill discovers repository, governing nodes, verification context, and the complete live file set for an explicitly advisory target ([audit])
- ALWAYS: the `spec-tree:audit-implementation` prompt contract requires request validation including generic run-driver identity, one audit run started before concern analysis, implementation-language recognition through installed `code-{lang}` skills, required `audit-{lang}-{code|tests|architecture}` concern dispatch for each recognized implementation partition, exclusion of artifact classes outside implementation-audit ownership from missing-skill coverage, scope and finding recording through `spx verification run` with the published audit payload field names, missing-skill rejection before dispatch, terminal status derived from accepted evidence, final projection relay, and complete blocked-command relay carrying the run token when started, exact command, payload source and key, exit code, and stderr ([audit])
- ALWAYS: each `audit-{lang}-architecture` concern skill accepts composition by `implementation-auditor` for implementation architecture scope and by the artifact-type auditor that governs decision records for ADR language-specific architecture concerns ([audit])
- NEVER: implementation-audit orchestration uses plugin-side `verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, `journal_emit.py`, or `audit_orchestrator.py`; audit payload validation and projection are SPX responsibilities ([audit])
- NEVER: the spec-tree plugin ships implementation-audit agents named `auditor` or `audit-orchestrator`; implementation audit has one wrapper agent, `implementation-auditor` ([test](tests/test_implementation_audit_contract.compliance.l1.py))
- NEVER: a programming-language plugin ships the retired aggregate `audit-{lang}` skill beside its `audit-{lang}-{code|tests|architecture}` concern trio ([test](tests/test_implementation_audit_contract.compliance.l1.py))
