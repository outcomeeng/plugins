# Host Readiness

PROVIDES bounded host-load readiness observations through silent foreground waiter invocations
SO THAT resource-intensive local workflows
CAN start only when normalized host load is ready and defer safely while it remains above capacity

## Assertions

### Scenarios

- Given normalized host load at or below capacity on the first observation, when the waiter runs, then it emits one terminal `ready` result with `ready: true` and the `ready` exit code without sleeping ([test](tests/test_host_readiness.scenario.l1.py))
- Given normalized host load above capacity that becomes ready within ten minutes, when the waiter runs, then it sleeps and rechecks inside the same process before emitting one terminal `ready` result ([test](tests/test_host_readiness.scenario.l1.py))
- Given normalized host load that remains above capacity for ten minutes, when the waiter reaches its deadline, then it emits one terminal `not_ready` result with `ready: false`, the final observation, and the `not_ready` exit code ([test](tests/test_host_readiness.scenario.l1.py))
- Given a host reporting no positive CPU count, when the waiter observes load, then it emits one terminal `unsupported` result with `ready: false` and the `unsupported` exit code ([test](tests/test_host_readiness.scenario.l1.py))
- Given an interrupt arriving while the waiter sleeps between observations, when the wait is cut short, then it emits one terminal `interrupted` result with `ready: false` and the `interrupted` exit code ([test](tests/test_host_readiness.scenario.l1.py))
- Given a load reader that fails unexpectedly, when the waiter observes load, then it emits one terminal `error` result with `ready: false` and the `error` exit code ([test](tests/test_host_readiness.scenario.l1.py))

### Mappings

- Every terminal status carries both a readiness boolean and an exit code, readiness holding only for `ready` — the status set, the readiness table, and the exit-code table enumerate the same statuses ([test](tests/test_host_readiness.mapping.l1.py))

### Compliance

- ALWAYS: the process exit code for each terminal status is `ready` 0, `error` 1, `unsupported` 2, `not_ready` 3, `interrupted` 130 — the contract a calling workflow branches on, declared here and honored by the waiter's exit-code enum ([audit])
- ALWAYS: a waiter invocation owns every load observation, interval, sleep, and recheck until it emits its terminal result; the agent never polls an active waiter ([audit])
- ALWAYS: only an explicit `not_ready` terminal result permits another waiter invocation, and retries stop when ten invocations or one hour of waiter time is reached, whichever occurs first ([audit])
- NEVER: absent or malformed terminal output permits another waiter invocation or the resource-intensive command; the agent blocks for the operator ([audit])
