---
id: 01a173ca-e226-7d04-8019-50121c12ff0e
malleability: spec
---

# Host Readiness

PROVIDES each resource-intensive local command one host-wide turn through the `spx orchestration lock` guard where the repository's lock switch is on, and bounded host-load readiness through the waiter where it is off
SO THAT resource-intensive local workflows from every session on one host
CAN avoid starting together

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
- Given a guard that reaches its wait cap, when the record reads `started` false and `status` `not_ready` with exit 3, then the skill reports `not_ready`, the command never started, and the skill starts no new attempt without operator direction ([audit])
- Given a guarded command that exits 3, when the record reads `started` true, `status` `completed`, and `childExitCode` 3, then the skill reports the command's own exit code 3 and never `not_ready` ([audit])
- Given a guard that started its command, when the record reads `started` true with a `signal` in place of `childExitCode` or a `status` other than `completed`, then the skill reports the `status` and the `signal` or `childExitCode` as the record carries them, never `not_ready` and never success, and starts no new attempt without operator direction ([audit])
- Given a guard whose standard error ends without a terminal record, when the line exits, then the skill reports `interrupted` with an unknown outcome, never `not_ready` and never success, and starts no new invocation on its own ([audit])
- Given a terminal record lost from the agent's view by compaction or an output cap, when the agent resumes, then it recovers the existing invocation — its tool or process handle and the terminal record whose `runId` matches — and starts no new invocation while that invocation's state is unresolved; when the invocation's terminal exit is known but its record cannot be recovered, the skill reports the outcome unknown, and a later run follows the recovered outcome's own rule or the operator's direction ([audit])
- Given a terminal record that reads `started` false with a status other than `not_ready`, such as the guard's unsupported-platform status, when the line ends, then the skill reports that status with the command unstarted and runs no unguarded fallback ([audit])
- Given a guarded command that runs a nested `/wait-for-load` line, when the nested line ends, then the skill takes the nested command's exit code as that line's result and expects no terminal record from it ([audit])

### Mappings

- Every terminal status carries both a readiness boolean and an exit code, readiness holding only for `ready` — the status set, the readiness table, and the exit-code table enumerate the same statuses ([test](tests/test_host_readiness.mapping.l1.py))
- Every terminal status maps its one JSON document to standard error with standard output left empty — the status set enumerates the domain, and the exit code follows the status ([test](tests/test_host_readiness.mapping.l1.py))

### Compliance

- ALWAYS: the process exit code for each terminal status is `ready` 0, `error` 1, `unsupported` 2, `not_ready` 3, `interrupted` 130 — the contract a calling workflow branches on, declared here and honored by the waiter's exit-code enum ([audit])
- ALWAYS: a waiter invocation owns every load observation, interval, sleep, settle delay, and confirming observation until it emits its terminal result; the agent never polls an active waiter ([audit])
- ALWAYS: one invocation owns the whole readiness attempt up to its four-hour bound; a `not_ready` result — load above capacity, or a confirmation still failing, at the bound — is terminal for that attempt and the guarded command does not start ([audit])
- ALWAYS: `/wait-for-load` reads its lock switch from `spx/local/wait-for-load.md` at the repository root; the switch is on only when that overlay holds the line `orchestration-lock: on`, and an absent overlay, an overlay without that line, or any other value leaves it off ([audit])
- ALWAYS: with the lock switch on, `/wait-for-load` runs a resource-intensive command as the argument vector after `--` in `spx orchestration lock --run-id <id> -- <command>`, with a run id the agent generates for that line, and starts no waiter; the skill carries no slot, load, wait, or result logic of its own for that line ([audit])
- ALWAYS: with the lock switch off, `/wait-for-load` chains the resource-intensive command behind the host-load waiter on one shell line joined by `&&`, identically on every agent harness, so the waiter's zero exit is the only thing that starts it; a lost or truncated waiter result re-runs the line and never stops for the operator ([audit])
- ALWAYS: with the lock switch off, the Claude rendering of `/wait-for-load` tells the caller to give the chained line the longest foreground timeout the harness allows, and that a call the harness moves to the background when that timeout elapses re-invokes the session when the line exits, so that re-invocation is the only collection the line needs ([audit])
- ALWAYS: with the lock switch off, the Codex rendering of `/wait-for-load` tells the caller to give the chained line the longest foreground timeout the harness allows and to collect the line within the active turn through its process handle until its exit code is observed ([audit])
- NEVER: with the lock switch off, the Codex rendering of `/wait-for-load` tells the caller that the harness re-invokes the session when the line exits ([audit])
- NEVER: with the lock switch off, a guarded command's failure is classified flaky, intermittent, or pre-existing before the waiter's observation for that run is consulted — sustained load above capacity starves short-budgeted operations and produces starvation, not flakiness ([audit])
- ALWAYS: the skill reads the guard's final standard-error line as the terminal record whose `schema` is `spx.orchestration.lock.result.v1` and whose `runId` equals the run id it passed, and decides from `started` and `status` together, never from the exit code alone ([audit])
- ALWAYS: one guard invocation owns the attempt from launch to terminal exit; the agent may collect that invocation's tool or process handle until its terminal exit, and never polls host load on its own, schedules a replacement timer, launches a duplicate guard for the same command, or re-admits the command while that invocation runs ([audit])
- ALWAYS: a lightweight command — formatting, a single-file lint, a markdown or link validation, an instruction-block render, a status read — runs with neither the guard nor the waiter, whatever the lock switch ([audit])
