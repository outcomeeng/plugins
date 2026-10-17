---
name: control-positions
description: >-
  ALWAYS invoke this skill when pacing token spend across positions hosted in
  Prowl panes, running one control pass, or installing, checking, stopping, or
  restarting the scheduled position-control job.
argument-hint: "[pass|install|status|stop|restart]"
allowed-tools: Read, Bash(python3 --version), Bash(python3 -B "${CLAUDE_SKILL_DIR}/scripts/control_positions.py":*), {{! tool('ask_user') !}}
---

<objective>

One finite control pass over the positions hosted in Prowl panes, or a checked outcome of the macOS launchd job that starts a pass every thirty minutes.

</objective>

<dependencies>

- Python 3.13 or 3.14; standard library only. Check the interpreter before running.
- Prowl hosting the position panes. A pane Prowl does not list receives no action, so a position in a herdr pane is never touched.
- The sibling `/control-token-spend` and `/operate-prowl` scripts in the same plugin, which the entry point imports by `__file__`-relative paths.
- macOS launchd for scheduling. Any other platform returns an explicit unsupported result.
- Never install dependencies and never invoke a model for these operations.

</dependencies>

<configuration>

One file, `control-positions.toml` under `$XDG_CONFIG_HOME/outcome-engineering/` and defaulting to `~/.config/outcome-engineering/`, holds the operator's settings. A pass rereads it, so a change takes effect at the next pass.

| Setting                       | Effect                                                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Pace per subscription         | Tokens a subscription may spend per pass, divided evenly among that subscription's measured positions.         |
| Subscription of each position | Assigns each position to a pace.                                                                               |
| Skip list                     | Pane titles or worktree paths that receive no action.                                                          |
| Thresholds                    | Compaction at 30% of the window, compaction multiple 1.25, pause multiple 2, weekly ceiling 93% (maximum 95%). |
| `key_authorized`              | Authorizes the Prowl key operation. Without it nothing is paused and the pass reports why.                     |
| `stop_authorized`             | Authorizes `/exit` at the weekly ceiling. Without it nothing is stopped and the pass reports why.              |

An invalid file fails naming the field. Never write or edit this file without the operator's instruction, and never set either authorization on the operator's behalf.

</configuration>

<operations>

Run `python3 -B "${CLAUDE_SKILL_DIR}/scripts/control_positions.py" <operation>` with exactly one operation. An empty request selects `status`.

| Operation | Observable result                                                                                                                                                             |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pass`    | One JSON line listing each report (`kind`, `subject`, `message`) and the positions left `unfinished` when the five-minute bound was reached. Exit 0.                          |
| `install` | Writes the launchd job `engineering.outcome.usage-control.positions` that starts one `pass` every thirty minutes, then prints `succeeded: <detail>` or a failure and exits 1. |
| `status`  | Prints the job's observed state.                                                                                                                                              |
| `stop`    | Stops the job and prints the checked outcome.                                                                                                                                 |
| `restart` | Restarts the job and prints the checked outcome.                                                                                                                              |

Every scheduling operation prints `<status>: <detail>` and exits 1 unless the status is `succeeded`. On a platform other than macOS the status is `unsupported`. An invalid configuration prints `control-positions: invalid configuration: <field>` to standard error and exits non-zero.

Each action a pass takes (compaction, pause, resume, stop) is a durable record under `positions/` in the consumption-control data root and is delivered as consumption-control alerts are. A pass runs no daemon, watcher, or polling loop.

</operations>

<workflow>

<step name="validate">

Resolve the operation from the request. Reject an unsupported interpreter version before running. For `pass`, read the configuration path and state which authorizations it grants before running, because a pass compacts, pauses, and stops positions in live panes. Run `pass` only when the request asks for one.

</step>

<step name="confirm_install">

`install` writes a launch agent under the operator's home directory. Present the absolute destination, `~/Library/LaunchAgents/engineering.outcome.usage-control.positions.plist` expanded to the home directory, through {{! tool('ask_user') !}} and run `install` only after the operator confirms it. Run `status`, `stop`, and `restart` without confirmation.

</step>

<step name="execute">

Run the entry point once with the selected operation. Pass the operation as a single literal argument. After `install` or `restart`, run `status` to confirm the job state.

</step>

<step name="return_evidence">

Return the operation, its printed output verbatim, and the exit code. For a pass, quote each report's message and name each unfinished position. For a failure, name the field, value, or platform the output names and the fix it states.

</step>

</workflow>

<success_criteria>

- The printed output of exactly one operation is returned verbatim with its exit code.
- A launchd job is written only after the operator confirmed its absolute destination.
- No pause or stop is claimed unless the configuration grants its authorization.
- No operation runs a daemon, edits the configuration, or invokes a model.

</success_criteria>
