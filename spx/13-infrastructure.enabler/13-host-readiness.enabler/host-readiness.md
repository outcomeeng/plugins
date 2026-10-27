---
id: 01a173ca-e226-7d04-8019-50121c12ff0e
malleability: spec
---

# Host Readiness

PROVIDES each resource-intensive local command one host-wide turn through the `spx orchestration lock` guard
SO THAT resource-intensive local workflows from every session on one host
CAN avoid starting together

## Assertions

### Scenarios

- Given a guard that reaches its wait cap, when the record reads `started` false and `status` `not_ready` with exit 3, then the skill reports `not_ready`, the command never started, and the skill starts no new attempt without operator direction ([audit])
- Given a guarded command that exits 3, when the record reads `started` true, `status` `completed`, and `childExitCode` 3, then the skill reports the command's own exit code 3 and never `not_ready` ([audit])
- Given a guard that started its command, when the record reads `started` true with a `signal` in place of `childExitCode` or a `status` other than `completed`, then the skill reports the `status` and the `signal` or `childExitCode` as the record carries them, never `not_ready` and never success, and starts no new attempt without operator direction ([audit])
- Given a guard whose standard error ends without a terminal record, when the line exits, then the skill reports `interrupted` with an unknown outcome, never `not_ready` and never success, and starts no new invocation on its own ([audit])
- Given a terminal record lost from the agent's view by compaction or an output cap, when the agent resumes, then it recovers the existing invocation — its tool or process handle and the terminal record whose `runId` matches — and starts no new invocation while that invocation's state is unresolved; when the invocation's terminal exit is known but its record cannot be recovered, the skill reports the outcome unknown, and a later run follows the recovered outcome's own rule or the operator's direction ([audit])
- Given a terminal record that reads `started` false with a status other than `not_ready`, such as the guard's unsupported-platform status, when the line ends, then the skill reports that status with the command unstarted and runs no unguarded fallback ([audit])
- Given a guarded command that runs a nested `/wait-for-load` line, when the nested line ends, then the skill takes the nested command's exit code as that line's result and expects no terminal record from it ([audit])

### Compliance

- ALWAYS: `/wait-for-load` runs every resource-intensive command as the argument vector after `--` in `spx orchestration lock --run-id <id> -- <command>`, with a run id the agent generates for that line; the skill carries no slot, load, wait, or result logic of its own ([audit])
- NEVER: the `/wait-for-load` skill ships a script, reads a lock switch, or chains a command behind a host-load waiter; the guard admits every resource-intensive command on every repository ([audit])
- ALWAYS: the Claude rendering of `/wait-for-load` tells the caller to give the lock line the longest foreground timeout the harness allows, and that a call the harness moves to the background when that timeout elapses re-invokes the session when the line exits, so that re-invocation is the only collection the line needs ([audit])
- ALWAYS: the Codex rendering of `/wait-for-load` tells the caller to give the lock line the longest foreground timeout the harness allows and to collect the line within the active turn through its process handle until its exit code is observed ([audit])
- NEVER: the Codex rendering of `/wait-for-load` tells the caller that the harness re-invokes the session when the line exits ([audit])
- ALWAYS: the skill reads the guard's final standard-error line as the terminal record whose `schema` is `spx.orchestration.lock.result.v1` and whose `runId` equals the run id it passed, and decides from `started` and `status` together, never from the exit code alone ([audit])
- ALWAYS: one guard invocation owns the attempt from launch to terminal exit; the agent may collect that invocation's tool or process handle until its terminal exit, and never polls host load on its own, schedules a replacement timer, launches a duplicate guard for the same command, or re-admits the command while that invocation runs ([audit])
- NEVER: a guarded command's failure is classified flaky, intermittent, or pre-existing before the guard's terminal record for that run is read ([audit])
- ALWAYS: a lightweight command — formatting, a single-file lint, a markdown or link validation, an instruction-block render, a status read — runs without the guard ([audit])
