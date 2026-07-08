# Verification Run State Surface

PROVIDES audit state as an SPX verification-run projection keyed by audit verification type, changeset scope, coverage units, producer identity, and finding content
SO THAT local audit runs and pull-request audit runs
CAN carry open, resolved, reopened, missing-coverage, and unsupported-scope evidence across audit iterations without a plugin-side state file, lock file, verdict script, or rendered-comment database

## Assertions

### Compliance

- ALWAYS: audit state persistence and projection go through `spx verification run` commands, with no plugin-side audit state file or verdict script ([test](../tests/test_implementation_audit_contract.compliance.l1.py))
- ALWAYS: prior audit context is selected by audit class, audit kind, stable producer identity, subject path, changed-file partition, language partition, and concern partition so repeated runs in one merge period converge on the same audit units ([audit])
- ALWAYS: resolved and reopened finding identity excludes producer-assigned IDs and producer provenance version, so regenerated findings match by stable producer identity plus content ([audit])
- NEVER: audit state is written to `.spx/audits/`, a lock file, a path inside `spx/`, or any other tracked product directory ([test](../tests/test_implementation_audit_contract.compliance.l1.py))
- NEVER: audit state is recovered by parsing rendered PR comments; rendered comments are display projections, not the state source ([audit])
