# Verification Run State Surface

PROVIDES individual audit-run state as an SPX verification-run projection keyed by audit verification type, changeset scope, coverage units, producer identity, producer provenance, prior-context selector fields, and finding content
SO THAT local audit runs
CAN record current-run coverage, findings, terminal state, and run-set selector inputs without a plugin-side state file, lock file, verdict script, or rendered-comment database

## Assertions

### Conformance

- The implementation-audit state surface conforms to SPX ownership: persistence and projection go through `spx verification run`, and the plugin runtime carries no audit state file or verdict script ([test](tests/test_verification_run_state_surface.conformance.l1.py))
- The implementation-audit state locations conform to the tracked-state boundary: no audit state is written to `.spx/audits/`, a lock file, a path inside `spx/`, or another tracked product directory ([test](tests/test_verification_run_state_surface.conformance.l1.py))

### Compliance

- ALWAYS: audit scope and finding payloads preserve audit class, audit kind, stable producer identity, subject path, changed-file partition, language partition, concern partition, and producer provenance so a later run-set projection can select prior audit context without parsing rendered output ([audit])
- ALWAYS: individual audit-run projection derives terminal status and authoritative finding count from accepted scope and finding evidence in that run ([audit])
- NEVER: audit state is recovered by parsing rendered PR comments; rendered comments are display projections, not the state source ([audit])
