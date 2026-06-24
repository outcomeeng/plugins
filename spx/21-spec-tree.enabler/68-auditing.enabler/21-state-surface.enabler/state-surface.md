# Journal State Surface

PROVIDES audit state as a projection over the `spx journal --type audit` run set, keyed by the run target metadata and rendered from the sealed journal prefix
SO THAT local audit runs and pull-request audit runs share one durable state contract
CAN carry open, resolved, and reopened findings across audit iterations without a separate state file, state-file lock, or rendered-comment database

## Assertions

### Scenarios

- Given an audit run with no prior journal run for the same target, when the projection renders the current verdict, then `resolved` and `reopened` are empty arrays ([test](../tests/test_auditing.scenario.l1.py))
- Given a prior journal run with an open finding and a later run omits that finding, when the projection renders the later verdict, then the finding appears in `resolved` ([test](../tests/test_auditing.scenario.l1.py))
- Given a prior journal run whose `resolved` array contains a finding and a later run reports the same finding again, when the projection renders the later verdict, then the finding appears in `reopened` ([test](../tests/test_auditing.scenario.l1.py))
- Given two branch labels whose slug values collide in the same state directory, when `branch_slug` derives a label for the later branch, then it appends a hash suffix so caller-owned local projections can keep distinct names ([test](../tests/test_auditing.scenario.l1.py))

### Compliance

- ALWAYS: the journal backend owns persistence and concurrency for audit runs; the `/audit` skill records the wrapper verdict on the audit journal and renders state from the sealed prefix ([review])
- ALWAYS: resolved and reopened identity is `(file, line, rule, message)`; producer-assigned IDs and severity labels are excluded so regenerated findings match by content ([test](../tests/test_auditing.scenario.l1.py))
- NEVER: audit state is written to `.spx/audits/`, a lock file, a path inside `spx/`, or any other tracked product directory ([review])
- NEVER: audit state is recovered by parsing rendered PR comments; rendered comments are display projections, not the state source ([review])
