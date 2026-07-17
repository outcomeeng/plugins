# Verification Run State Surface

PROVIDES individual audit-run state as an SPX verification-run projection keyed by audit verification type, changeset scope, coverage units, producer identity, producer provenance, prior-context selector fields, and finding content
SO THAT local audit runs
CAN record current-run coverage, findings, terminal state, and run-set selector inputs without a plugin-side state file, lock file, verdict script, or rendered-comment database

## Assertions

### Compliance

- ALWAYS: each authored and generated implementation-audit runtime directory contains exactly `SKILL.md`, with no plugin-side script, state file, lock file, or other runtime artifact ([test](tests/test_implementation_audit_runtime.compliance.l1.py))
- ALWAYS: implementation-audit orchestration directs persistence and projection through `spx verification run`; the plugin runtime records no audit state of its own ([audit])
- NEVER: implementation-audit orchestration directs a verifier to write state to `.spx/audits/`, a lock file, a path inside `spx/`, or another tracked product directory ([audit])
- ALWAYS: implementation-audit orchestration directs each verifier to preserve audit class, audit kind, stable producer identity, subject path, changed-file partition, language partition, concern partition, and producer provenance in SPX scope and finding payloads so run-set projection selects prior audit context without parsing rendered output ([audit])
- ALWAYS: implementation-audit orchestration treats the terminal status and authoritative finding count in the SPX-rendered individual-run projection as the audit result ([audit])
- NEVER: audit state is recovered by parsing rendered PR comments; rendered comments are display projections, not the state source ([audit])
