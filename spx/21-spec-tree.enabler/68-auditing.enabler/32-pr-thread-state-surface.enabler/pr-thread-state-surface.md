# Pull-Request Journal State Surface

PROVIDES pull-request audit state through the audit journal backend, with `targetKind=pull-request` and `pullRequestNumber` metadata selecting the PR run set
SO THAT the CI-side `pr-review-orchestrator` agent and any future CI-side caller of `/spec-tree:audit` can iterate auditably across pushes
CAN surface what resolved and what reopened without parsing rendered comments, writing `.spx/audits/`, or maintaining a PR-thread database

## Assertions

### Scenarios

- Given no prior pull-request audit journal run for the same PR, when the audit renders the current verdict, then `resolved` and `reopened` are empty arrays ([test](../tests/test_auditing.scenario.l1.py))
- Given a prior pull-request audit journal run with an open finding and a later run omits that finding, when the audit renders the later verdict, then the finding appears in `resolved` ([test](../tests/test_auditing.scenario.l1.py))
- Given a prior pull-request audit journal run whose `resolved` array contains a finding and a later run reports the same finding again, when the audit renders the later verdict, then the finding appears in `reopened` ([test](../tests/test_auditing.scenario.l1.py))

### Compliance

- ALWAYS: pull-request audit runs stamp `targetKind=pull-request` and `pullRequestNumber` into wrapper metadata before recording the wrapper verdict, so the journal backend can project prior runs for the same PR ([review])
- ALWAYS: resolved and reopened identity is `(file, line, rule, message)`; producer-assigned IDs and severity labels are excluded so regenerated findings match by content ([test](../tests/test_auditing.scenario.l1.py))
- ALWAYS: resolved and reopened arrays are emitted in content-identity order so projections are stable across Python processes ([test](tests/test_audit_orchestrator_cli.scenario.l1.py))
- ALWAYS: the PR comment contains the review prose followed by the audit journal-rendered verdict; the comment is a display projection and never a state record ([review])
- NEVER: pull-request audit state is recovered from rendered comments, delimiter blocks, temporary files, `.spx/audits/`, or any other side surface ([review])
- NEVER: the absence of a prior pull-request audit journal run halts the audit; the first run is the empty-prior case ([test](../tests/test_auditing.scenario.l1.py))
