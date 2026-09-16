# Host Readiness

PROVIDES bounded host-load readiness through one silent foreground waiter invocation chained ahead of the command it guards
SO THAT resource-intensive local workflows
CAN start only when normalized host load is ready, defer while it remains above capacity, and avoid starting together with other waiters on the same host

## Assertions

### Scenarios

- Given normalized host load at or below capacity on the first observation, when the waiter runs, then it emits one terminal `ready` result with `ready: true` and the `ready` exit code without sleeping and without a settle delay ([test](tests/test_host_readiness.scenario.l1.py))
- Given normalized host load above capacity that falls to capacity within four hours, when the waiter runs, then it sleeps and rechecks inside the same process, and after its first ready observation it sleeps a settle delay equal to the elapsed wait modulo the settle window, clamped to the time remaining before the deadline, observes once more, and emits one terminal `ready` result when that confirming observation is at or below capacity with a one-minute average not above the five-minute average by more than the trend tolerance ([test](tests/test_host_readiness.scenario.l1.py))
- Given a confirming observation whose one-minute average exceeds the five-minute average by more than the trend tolerance, when the waiter confirms, then it returns to the wait loop instead of emitting `ready`, and emits `ready` only once a later confirmation holds ([test](tests/test_host_readiness.scenario.l1.py))
- Given a first ready observation whose settle delay exceeds the time remaining before the four-hour deadline, when the waiter settles, then it sleeps only the time remaining, and when that confirming observation is rising it emits one terminal `not_ready` result carrying the rising observation as its final observation with sleeps totalling exactly the bound ([test](tests/test_host_readiness.scenario.l1.py))
- Given normalized host load that remains above capacity for four hours, when the waiter reaches its deadline, then it emits one terminal `not_ready` result with `ready: false`, the final observation, and the `not_ready` exit code ([test](tests/test_host_readiness.scenario.l1.py))
- Given normalized host load whose computed interval is longer than the time left before the four-hour deadline, when the waiter sleeps, then it sleeps only the time remaining and reaches its deadline exactly ([test](tests/test_host_readiness.scenario.l1.py))
- Given a host reporting no positive CPU count, when the waiter observes load, then it emits one terminal `unsupported` result with `ready: false` and the `unsupported` exit code ([test](tests/test_host_readiness.scenario.l1.py))
- Given an interrupt arriving while the waiter sleeps between observations, when the wait is cut short, then it emits one terminal `interrupted` result with `ready: false` and the `interrupted` exit code ([test](tests/test_host_readiness.scenario.l1.py))
- Given a load reader that fails unexpectedly, when the waiter observes load, then it emits one terminal `error` result with `ready: false` and the `error` exit code ([test](tests/test_host_readiness.scenario.l1.py))

### Mappings

- Every terminal status carries both a readiness boolean and an exit code, readiness holding only for `ready` — the status set, the readiness table, and the exit-code table enumerate the same statuses ([test](tests/test_host_readiness.mapping.l1.py))
- Every terminal status maps its one JSON document to standard error with standard output left empty — the status set enumerates the domain, and the exit code follows the status ([test](tests/test_host_readiness.mapping.l1.py))

### Compliance

- ALWAYS: the process exit code for each terminal status is `ready` 0, `error` 1, `unsupported` 2, `not_ready` 3, `interrupted` 130 — the contract a calling workflow branches on, declared here and honored by the waiter's exit-code enum ([audit])
- ALWAYS: a waiter invocation owns every load observation, interval, sleep, settle delay, and confirming observation until it emits its terminal result; the agent never polls an active waiter ([audit])
- ALWAYS: one invocation owns the whole readiness attempt up to its four-hour bound; a `not_ready` result — load above capacity, or a confirmation still failing, at the bound — is terminal for that attempt and the guarded command does not start ([audit])
- ALWAYS: the guarded command follows the waiter on the same shell line joined by `&&`, identically on every agent harness, so the waiter's zero exit is the only thing that starts it; a lost or truncated result re-runs the line and never stops for the operator ([audit])
- NEVER: a guarded command's failure is classified flaky, intermittent, or pre-existing before the waiter's observation for that run is consulted — sustained load above capacity starves short-budgeted operations and produces starvation, not flakiness ([audit])
