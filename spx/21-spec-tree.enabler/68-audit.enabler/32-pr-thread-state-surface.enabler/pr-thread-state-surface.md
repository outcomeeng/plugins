# Pull-Request Verification Run State Surface

PROVIDES pull-request audit run state through the SPX verification-run persistence mechanism, with individual run projections preserving selector fields for later run-set restoration
SO THAT CI-side implementation audits
CAN record current-run coverage and findings without parsing rendered comments, writing `.spx/audits/`, or maintaining a plugin-side PR-thread database

## Assertions

### Compliance

- ALWAYS: pull-request audit runs persist individual run state through the host-backed SPX verification-run mechanism rather than through plugin-side verdict-diff scripts ([audit])
- ALWAYS: pull-request audit payloads preserve audit class, audit kind, stable producer identity, subject path, changed-file partition, language partition, concern partition, and pull-request identity as selector inputs for the later run-set restoration layer ([audit])
- ALWAYS: when no run-set prior-context projection is available, a pull-request audit run starts from empty prior context and still records complete current-run coverage and findings ([audit])
- NEVER: pull-request audit state is recovered from rendered comments, delimiter blocks, temporary files, `.spx/audits/`, or any other side surface ([audit])
- NEVER: the absence of a prior pull-request audit run halts the audit; the first run is the empty-prior case ([audit])
