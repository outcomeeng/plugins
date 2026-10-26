---
name: wait-for-load
description: >-
  ALWAYS invoke this skill before starting a resource-intensive local command or when host load is high. NEVER calculate or schedule a host-load wait without this skill.
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/wait_for_load.py")
---

<objective>
One terminal result gating the resource-intensive command it guards: the host-wide slot of `spx orchestration lock` where the repository's lock switch is on, the host-load waiter where it is off.
</objective>

<workflow>

1. Read the lock switch from `spx/local/wait-for-load.md` at the repository root. The switch is on only when that overlay holds the line `orchestration-lock: on`. An absent overlay, an overlay without that line, or any other value leaves it off. A nested line reads the same switch as the outer line.

2. Run the guarded command as one shell line in the form the switch selects, identically on every agent harness. Give the call the longest foreground timeout the agent harness allows. A harness that moves a long call to the background when that timeout elapses re-invokes the session when the line exits, and that re-invocation is the only collection the line needs. The line takes its own approval path.

   Switch on: pass the command as the argument vector after `--`, with a run id generated for that line, a new UUID each time, and start no waiter:

   ```bash
   spx orchestration lock --run-id <uuid> -- <resource-intensive command>
   ```

   Switch off: chain the command behind the waiter with `&&`:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/wait_for_load.py" && <resource-intensive command>
   ```

3. Collect that one line. Never re-read host load, compute an interval, schedule a timer, poll, launch a duplicate guard or waiter for the same command, or re-admit the command while the line runs. When the harness hands back a process handle for the line, collect that same handle until its exit code is observed.

4. Read the result by the line form, per `<lock_result>` or `<waiter_result>`.

5. Classify a guarded command's failure only after reading the result of that run. With the switch off, sustained load above capacity starves short-budgeted operations and produces starvation, not flakiness, so no failure is called flaky, intermittent, or pre-existing before the waiter's observation for that run is read.

</workflow>

<scope>
Guard a resource-intensive command: a test suite, an eval, a full gate, a compiling build, an install verification. Run a lightweight command with neither the lock nor the waiter, whatever the switch: formatting, a single-file lint, a markdown or link validation, an instruction-block render, a status read. A product's own root instructions may name its heavy commands.
</scope>

<lock_result>
The skill carries no slot, load, wait, or result logic of its own for a lock line; the guard owns admission, the wait cap, and the terminal record. The guard writes its final standard-error line as the terminal record, a JSON document whose `schema` is `spx.orchestration.lock.result.v1`. Accept it only when its `runId` equals the run id passed for that line, and decide from `started` and `status` together, never from the exit code alone.

| Record                                                                                     | Report                                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `started` false, `status` `not_ready`, exit 3 (wait cap reached)                           | `not_ready`; the command never started; start no new attempt without operator direction                                                                                                   |
| `started` true, `status` `completed`                                                       | The command's own result by `childExitCode`; a `childExitCode` of 3 is the command's exit 3, never `not_ready`                                                                            |
| `started` true, `status` other than `completed`, or a `signal` in place of `childExitCode` | The `status` and the `signal` or `childExitCode` as the record carries them; the command started, so never `not_ready` and never success; start no new attempt without operator direction |
| `started` false, any other `status`, such as unsupported platform                          | That status with the command unstarted; run no unguarded fallback                                                                                                                         |
| Standard error ends with no terminal record                                                | `interrupted` with an unknown outcome, never `not_ready` and never success; start no new invocation on its own                                                                            |

A guarded command that itself runs a nested `/wait-for-load` line takes the nested command's exit code as that line's result and expects no terminal record from the nested line.

A terminal record lost from view, by compaction or an output cap, never re-runs the line. Recover the existing invocation: its tool or process handle and the terminal record whose `runId` matches. Start no new invocation while that invocation's state is unresolved. When its terminal exit is known but its record cannot be recovered, report the outcome unknown; a later run follows the recovered outcome's own rule or the operator's direction.
</lock_result>

<waiter_result>
The waiter writes exactly one JSON document to standard error immediately before it exits, and standard output stays empty, so the guarded command's own output and exit code follow the document untouched. Exit 0 means the guarded command started; every other exit means it did not, and `<error_handling>` names the action for each terminal status. A lost or truncated result, whether by compaction or by an output cap, means the guarded command ran only if the waiter exited zero, so re-run the same line. Never stop for the operator over a missing result.
</waiter_result>

<input_output>
The lock line accepts the command as its argument vector and emits the terminal record described in `<lock_result>`.

The waiter accepts no arguments. It reads the host's 1-, 5-, and 15-minute load averages and logical CPU count through Python's standard library.

It emits nothing while waiting, and one invocation owns the whole attempt, bounded at four hours. A first observation with all three normalized averages at or below capacity starts the guarded command at once. Otherwise the waiter sleeps a load-derived interval of at least sixty seconds and rechecks; on its first ready observation it sleeps a settle delay equal to the elapsed wait modulo 180 seconds, clamped to the time left before the four-hour bound, observes once more, and starts only when that observation is still at or below capacity and its one-minute load has not risen past its five-minute load by more than half a core. A rising one-minute load means other work just started, so the waiter returns to its loop. Waiters that began waiting at different moments on one host therefore start at different moments, and a load dip does not release them together.

Immediately before exit it writes exactly one compact JSON document to standard error containing the initial and final observations, readiness, terminal status, wait-cycle count, and elapsed wait, plus an `error` object carrying the type and message on an `error`, `unsupported`, or `interrupted` result. It stores no intermediate observation history. A ready result after one wait and a settle delay reads, with its keys sorted and its floats shortened here:

```text
{"final":{"cpu_count":12,"load":[4.5,4.7,4.9],"normalized":[0.375,0.392,0.408]},"initial":{"cpu_count":12,"load":[14.2,11.8,9.6],"normalized":[1.183,0.983,0.8]},"ready":true,"status":"ready","wait_cycles":1,"waited_seconds":120.0}
```

</input_output>

<dependencies>

- the waiter: Python 3.13 or 3.14 as the supported window, with 3.13 as the floor; `os.getloadavg()` and a positive `os.cpu_count()` result; Python standard library only, with no repository-local package, subprocess, file, or network dependency
- the lock line: the `spx` CLI's `orchestration lock` command

</dependencies>

<error_handling>

Waiter terminal statuses:

| Terminal status | Exit | Meaning                                                   | Action                                                                                            |
| --------------- | ---: | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `ready`         |    0 | A confirmed observation is at or below capacity           | The guarded command starts on the same line                                                       |
| `not_ready`     |    3 | No confirmed ready observation within the four-hour bound | The attempt is over; report the terminal JSON and start no new attempt without operator direction |
| `unsupported`   |    2 | Load averages or CPU count are unavailable                | The guarded command does not start; report the JSON                                               |
| `interrupted`   |  130 | The foreground wait received an interruption              | The guarded command does not start; report the JSON                                               |
| `error`         |    1 | An internal operation failed, or an argument was given    | The guarded command does not start; report the JSON                                               |

Lock-line outcomes are in `<lock_result>`.

</error_handling>

<testing>
Release verification of the waiter covers these controlled boundaries without wall-clock delay:

- immediate readiness with zero waits and no settle delay
- a wait followed by a settle delay of the elapsed time modulo the settle window and a confirming observation
- a rising confirming observation returning the waiter to its loop before a later confirmation succeeds
- load held above capacity through the four-hour bound, producing `not_ready`, exit 3, the last observation, and sleeps totalling exactly the bound
- an interval longer than the time left clamped to the remainder
- a settle delay longer than the time left clamped to the remainder, with a rising confirmation at the bound producing `not_ready`
- unavailable CPU count producing `unsupported` and exit 2
- interrupted sleep producing `interrupted` and exit 130
- load-reader failure producing `error` and exit 1
- every terminal status writing its one document to standard error with standard output empty

The lock line has no test; an assertion audit of this skill judges it.
</testing>

<failure_modes>

**Manual delay churn**

- **What happened:** Claude manually selected 1-, 5-, 17-, 20-, and 9-minute delays while waiting for load.
- **Why it failed:** Each wake required another load read, arithmetic pass, and scheduling decision, consuming context and tokens without advancing repository work.
- **How to avoid:** Run the one line so one process owns the complete admission loop.

**Timer-driven host-load checks**

- **What happened:** Claude used timers and repeated 60-second result-collection turns for host-load convergence.
- **Why it failed:** The timer knew elapsed time but did not know readiness, so each re-entry reconstructed context and repeated coordination.
- **How to avoid:** Run the guarded line and collect that one line; never substitute a timer or start another guard or waiter while one is still running.

**Waiters released together**

- **What happened:** Claude sessions on one host each started a heavy command behind a waiter at 03:30Z after the same load dip, and host load reached 98 on 12 cores.
- **Why it failed:** A waiter observes load and holds no slot, so Claude sessions that see the same dip start their heavy commands together.
- **How to avoid:** Where the lock switch is on, run the command under `spx orchestration lock` so one host-wide slot admits one heavy run at a time.

**Parser stage between the waiter and the command**

- **What happened:** Claude wrote the waiter's output through a parser stage and chained the command after the parser, as in `wait_for_load.py | python3 -c '...' && just check`.
- **Why it failed:** The `&&` bound to the parser's exit code, not the waiter's, so a not-ready result let the command start, and the terminal document was consumed instead of shown.
- **How to avoid:** Chain the command directly after the waiter. The document is on standard error and needs no parser.

**Lost waiter result stopped the work**

- **What happened:** Compaction removed the waiter's terminal JSON before Claude read it, and the workflow stopped for the operator ahead of a lightweight build.
- **Why it failed:** A missing result was treated as an unrecoverable state, and a command that needs no admission was held behind the waiter.
- **How to avoid:** Re-run the same waiter line when a result is lost, and run lightweight commands without the waiter or the lock.

</failure_modes>

<success_criteria>

- the lock switch is read from `spx/local/wait-for-load.md`, and only the line `orchestration-lock: on` turns it on
- with the switch on, the command runs as the argument vector of one `spx orchestration lock --run-id <uuid> --` line with no waiter, and the result is decided from the matching record's `started` and `status` together
- with the switch off, the guarded command starts only on the waiter's zero exit in the same shell line, identically on every agent harness
- one guard or waiter process is active per attempt; no Claude-owned host-load arithmetic, repeated load command, timer, heartbeat, shell sleep, polling loop, duplicate launch, or re-admission is used
- a nonzero waiter exit, or a lock record with `started` false, leaves the guarded command unstarted with the terminal result reported, and no unguarded fallback runs
- a lost waiter result re-runs the waiter line; a lost lock record recovers the existing invocation, starts no new one while its state is unresolved, and reports an unrecoverable outcome as unknown
- a lightweight command runs with neither the lock nor the waiter
- with the switch off, no guarded command's failure is classified flaky, intermittent, or pre-existing before the waiter's observation for that run is read

</success_criteria>
