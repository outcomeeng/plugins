---
name: wait-for-load
description: >-
  ALWAYS invoke this skill before starting a resource-intensive local command or when host load is high. NEVER calculate or schedule a host-load wait without this skill.
---

<objective>
One terminal record gating the resource-intensive command it guards: the host-wide slot of `spx orchestration lock`, which admits one heavy run per host.
</objective>

<workflow>

1. Run the guarded command as one shell line, identically on every agent harness: pass the command as the argument vector after `--`, with a run id generated for that line, a new UUID each time. Give the call the longest foreground timeout the agent harness allows. Collect the line within the active turn through its process handle until its exit code is observed; the harness does not re-invoke the session when the line exits. The line takes its own approval path.

   ```bash
   spx orchestration lock --run-id <uuid> -- <resource-intensive command>
   ```

2. Collect that one line. Never poll host load, schedule a timer, launch a duplicate guard for the same command, or re-admit the command while the line runs. When the harness hands back a process handle for the line, collect that same handle until its exit code is observed.

3. Read the result per `<lock_result>`.

4. Classify a guarded command's failure only after reading the terminal record of that run: no failure is called flaky, intermittent, or pre-existing before then.

</workflow>

<scope>
Guard a resource-intensive command: a test suite, an eval, a full gate, a compiling build, an install verification. Run a lightweight command without the guard: formatting, a single-file lint, a markdown or link validation, an instruction-block render, a status read. A product's own root instructions may name its heavy commands.
</scope>

<lock_result>
The skill carries no slot, load, wait, or result logic of its own; the guard owns admission, the wait cap, and the terminal record, and its help declares its exit codes. The guard writes its final standard-error line as the terminal record, a JSON document whose `schema` is `spx.orchestration.lock.result.v1`. Accept it only when its `runId` equals the run id passed for that line, and decide from `started` and `status` together, never from the exit code alone.

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

<dependencies>

- the `spx` CLI's `orchestration lock` command

</dependencies>

<testing>
No script ships with this skill and no test covers it; an assertion audit of this skill judges the lock line.
</testing>

<failure_modes>

**Manual delay churn**

- **What happened:** Claude manually selected 1-, 5-, 17-, 20-, and 9-minute delays while waiting for load.
- **Why it failed:** Each wake required another load read, arithmetic pass, and scheduling decision, consuming context and tokens without advancing repository work.
- **How to avoid:** Run the one line so one process owns the complete admission loop.

**Timer-driven host-load checks**

- **What happened:** Claude used timers and repeated 60-second result-collection turns for host-load convergence.
- **Why it failed:** The timer knew elapsed time but did not know readiness, so each re-entry reconstructed context and repeated coordination.
- **How to avoid:** Run the guarded line and collect that one line; never substitute a timer or start another guard while one is still running.

**Heavy commands released together**

- **What happened:** Claude sessions on one host each started a heavy command after the same load dip, and host load reached 98 on 12 cores.
- **Why it failed:** Observing load holds no slot, so Claude sessions that see the same dip start their heavy commands together.
- **How to avoid:** Run every resource-intensive command under `spx orchestration lock` so one host-wide slot admits one heavy run at a time.

**Lost terminal record stopped the work**

- **What happened:** Compaction removed the terminal record before Claude read it, and the workflow stopped for the operator ahead of a lightweight build.
- **Why it failed:** A missing record was treated as an unrecoverable state, and a command that needs no admission was held behind the guard.
- **How to avoid:** Recover the existing invocation and its matching record when a record is lost, never re-run the line, and run lightweight commands without the guard.

</failure_modes>

<success_criteria>

- every resource-intensive command runs as the argument vector of one `spx orchestration lock --run-id <uuid> --` line, and the result is decided from the matching record's `started` and `status` together
- one guard process is active per attempt; no Claude-owned host-load arithmetic, repeated load command, timer, heartbeat, shell sleep, polling loop, duplicate launch, or re-admission is used
- a lock record with `started` false leaves the guarded command unstarted with the terminal record reported, and no unguarded fallback runs
- a lost lock record recovers the existing invocation, starts no new one while its state is unresolved, and reports an unrecoverable outcome as unknown
- a lightweight command runs without the guard
- no guarded command's failure is classified flaky, intermittent, or pre-existing before the terminal record for that run is read

</success_criteria>
