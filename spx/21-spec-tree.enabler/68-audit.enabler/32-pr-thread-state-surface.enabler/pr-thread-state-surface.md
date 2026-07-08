# Pull-Request Verification Run State Surface

PROVIDES pull-request audit state through the SPX verification-run persistence mechanism, with pull-request restoration providing prior audit run results at the start of each CI execution
SO THAT CI-side implementation audits
CAN converge across pushes in one pull request without parsing rendered comments, writing `.spx/audits/`, or maintaining a plugin-side PR-thread database

## Assertions

### Compliance

- ALWAYS: pull-request audit runs persist and restore state through the host-backed SPX verification-run mechanism rather than through plugin-side verdict-diff scripts ([audit])
- ALWAYS: prior audit context selectors include audit class, audit kind, stable producer identity, subject path, changed-file partition, language partition, concern partition, and pull-request identity ([audit])
- ALWAYS: the restored prior-context projection preserves open, resolved, reopened, missing-coverage, and unsupported-scope evidence for subsequent auditors in the same merge period ([audit])
- NEVER: pull-request audit state is recovered from rendered comments, delimiter blocks, temporary files, `.spx/audits/`, or any other side surface ([audit])
- NEVER: the absence of a prior pull-request audit run halts the audit; the first run is the empty-prior case ([audit])
