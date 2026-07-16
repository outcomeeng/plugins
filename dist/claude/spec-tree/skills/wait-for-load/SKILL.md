---
name: wait-for-load
description: >-
  ALWAYS invoke this skill before starting a resource-intensive local command or when host load is high. NEVER calculate or schedule a host-load wait without this skill.
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/wait_for_load.py")
---

<objective>
A terminal host-readiness result produced by one silent foreground process that owns load observation, interval selection, sleeping, and rechecking.
</objective>

<workflow>
1. Run this command exactly once before the resource-intensive local command:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/wait_for_load.py"
```

2. Collect that process's completion. When the harness returns a running-process handle, continue collecting the same process; never re-read host load, calculate another interval, schedule a timer, or start a second waiter.
3. Read the exit status and the one terminal JSON document:
   - Exit zero with `status: "ready"` and `ready: true` permits the resource-intensive command.
   - A nonzero exit reports `unsupported`, `interrupted`, or `error`; stop the resource-intensive command and report that terminal JSON.

</workflow>

<input_output>
The waiter accepts no arguments. It reads the host's 1-, 5-, and 15-minute load averages and logical CPU count through Python's standard library.

It emits nothing while waiting. Immediately before exit it writes exactly one compact JSON document to standard output containing the initial and final observations, readiness, terminal status, wait-cycle count, and elapsed wait. It stores no intermediate observation history and imposes no total wait ceiling.
</input_output>

<dependencies>
- Python 3.13 or 3.14 as the supported window; syntax remains compatible with Python 3.9 or newer
- `os.getloadavg()` and a positive `os.cpu_count()` result
- Python standard library only; no repository-local package, subprocess, file, or network dependency

</dependencies>

<error_handling>

| Terminal status | Exit | Meaning                                                | Action                               |
| --------------- | ---: | ------------------------------------------------------ | ------------------------------------ |
| `ready`         |    0 | All three normalized averages are at or below capacity | Start the resource-intensive command |
| `unsupported`   |    2 | Load averages or CPU count are unavailable             | Stop and report the terminal JSON    |
| `interrupted`   |  130 | The foreground wait received an interruption           | Stop and report the terminal JSON    |
| `error`         |    1 | An internal operation failed                           | Stop and report the terminal JSON    |

</error_handling>

<testing>
Release verification covers these controlled boundaries without wall-clock delay:

- immediate readiness with zero waits
- two high-load observations followed by readiness, producing two sleeps of at least 60 seconds
- unavailable CPU count producing `unsupported` and exit 2
- interrupted sleep producing `interrupted` and exit 130
- load-reader failure producing `error` and exit 1
- unexpected arguments producing `error` and exit 1 with an actionable message
- complete silence before one terminal JSON document
- no subprocess or file creation
- byte-identical generated runtime copies

</testing>

<failure_modes>
**Manual delay churn**

- **What happened:** Claude manually selected 1-, 5-, 17-, 20-, and 9-minute delays while waiting for load.
- **Why it failed:** Each wake required another load read, arithmetic pass, and scheduling decision, consuming context and tokens without advancing repository work.
- **How to avoid:** Run the waiter once so one process owns the complete readiness loop.

**Timer-driven host-load checks**

- **What happened:** Claude used runtime timers and repeated 60-second result-collection turns for host-load convergence.
- **Why it failed:** The timer knew elapsed time but did not know readiness, so each re-entry reconstructed context and repeated coordination.
- **How to avoid:** Collect the same waiter process until its terminal JSON arrives; never substitute a timer or a new waiter.

</failure_modes>

<success_criteria>

- exactly one waiter process owns every host-load observation, interval, sleep, and recheck
- no stdout or stderr output appears before the terminal JSON document
- the resource-intensive command starts only after exit zero with `status: "ready"` and `ready: true`
- nonzero results stop the resource-intensive command and remain machine-readable
- no agent-owned host-load arithmetic, repeated load command, timer, heartbeat, shell sleep, or polling loop is used

</success_criteria>
