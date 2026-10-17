---
name: control-positions
description: >-
  ALWAYS invoke this skill when pacing token spend across positions hosted in
  Prowl panes, running one control pass, or installing, checking, stopping, or
  restarting the scheduled position-control job.
argument-hint: "[pass|install|status|stop|restart]"
allowed-tools: Read, Bash(python3 --version), Bash(python3 -B "${CLAUDE_SKILL_DIR}/scripts/control_positions.py":*), AskUserQuestion
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

Every numeric setting accepts only a finite number above zero, within its maximum; zero, a negative number, `nan`, `inf`, and `-inf` each fail. An invalid file fails naming the field. Never write or edit this file without the operator's instruction, and never set either authorization on the operator's behalf.

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

Each action a pass takes (compaction, pause, resume, stop) is a durable record under `positions/` in the consumption-control data root and is delivered as consumption-control alerts are. A pass also keeps its cross-pass state in `control-positions-state.json` in that root. The root is `~/Library/Application Support/Outcome Engineering/usage-control` expanded to the home directory, outside the invocation checkout. A pass runs no daemon, watcher, or polling loop.

A pass ends within five minutes: it caps each Prowl command at the time left in that bound, so a command started just before the bound cannot extend the pass. Before it measures a position's tokens, a pass collects the consumption-control accounting itself, so it does not depend on the consumption-control job having collected beforehand. The measurement runs only when its longest duration, two 30-second limits, fits in the time left; otherwise the position's pace is reported as unmeasured with a note that the measurement was skipped, and the position is not marked unfinished. An unusable or changed consumption-control accounting interface also leaves the position's pace unmeasured and the pass continues. For any position with an unmeasured pace, only context compaction and the weekly ceiling apply. A paused position resumes with `continue` only on a measurement: a measured spend under its share, or a readable accounting source that reports its history complete and holds no session for its worktree in the window (an incomplete history leaves the pace unmeasured), which a paused position's lack of requests makes the ordinary case and which the record states as its basis. A skipped or failed measurement, or a subscription with no configured pace, leaves the position paused and reports its pace as unmeasured.

</operations>

<workflow>

<step name="validate">

Resolve the operation from the request. Reject an unsupported interpreter version before running. For `pass`, read the configuration path and state which authorizations it grants before running, because a pass compacts, pauses, and stops positions in live panes. Run `pass` only when the request asks for one, and only after `confirm_writes`.

</step>

<step name="confirm_writes">

`pass` writes records and state under the consumption-control data root, and the job `install` creates writes there every thirty minutes; `install` also writes a launch agent. Both lie under the operator's home directory, outside the invocation checkout. Present each absolute destination, expanded to the home directory, through AskUserQuestion and run the operation only after the operator confirms it:

- For `pass`: `~/Library/Application Support/Outcome Engineering/usage-control`.
- For `install`: `~/Library/LaunchAgents/engineering.outcome.usage-control.positions.plist`, and the data root above, which the scheduled passes write.

One confirmation covers one operation; the next `pass` or `install` asks again. Run `status`, `stop`, and `restart` without confirmation.

</step>

<step name="execute">

Run the entry point once with the selected operation. Pass the operation as a single literal argument. After `install` or `restart`, run `status` to confirm the job state.

</step>

<step name="return_evidence">

Return the operation, its printed output verbatim, and the exit code. For a pass, quote each report's message and name each unfinished position. For a failure, name the field, value, or platform the output names and the fix it states.

</step>

</workflow>

<script_tests>

The four bundled scripts were tested together through the entry point `control_positions.py`, with the Prowl and launchd collaborators and the clock replaced by recorded stand-ins and the data root and launch-agent directory in a temporary directory removed when each test ended. The production token source was also run against a real consumption-control accounting database that the test built in a temporary directory from a transcript written for a worktree. No test touched a live pane, the real data root, or the real `~/Library/LaunchAgents`.

| Script                  | Tested with                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Expected output and error cases                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `control_positions.py`  | Passes over one to three positions at context use at and above 30%, spend at 1.25 and 2 times the share over consecutive passes, and weekly use at the ceiling; a skip-listed pane; a herdr pane; a pass past the five-minute bound; a Prowl command starting just before the bound; a position whose token measurement does not fit in the time left; a token source returning nothing; the production token source against a real accounting database built from a transcript for a worktree, before and after a further transcript, for a worktree with no transcript and for a window with none; ten changes to the accounting interface | Compaction, pause, resume, and stop actions match the thresholds; skipped and herdr positions receive no action; unfinished positions are named; no polling loop; a ceiling above 95% is rejected before any action; the pass ends within five minutes even when a command starts just before the bound; a skipped measurement reports the pace as unmeasured with a note and does not mark the position unfinished; the worktree's tokens are measured after the source collects the accounting itself; each changed accounting interface leaves the pace unmeasured, the pass completes, and only context compaction and the ceiling apply |
| `positions_config.py`   | `XDG_CONFIG_HOME` set and unset; every scalar field given an invalid value; `nan`, `inf`, and `-inf` for every numeric setting and for a subscription's pace; a changed file between two passes; `key_authorized` and `stop_authorized` each absent                                                                                                                                                                                                                                                                                                                                                                                          | The path resolves under `outcome-engineering/`; an invalid or non-finite field fails naming it before any action; the change applies at the next pass; an unauthorized pause or stop is withheld with its reason                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `positions_schedule.py` | `install`, `status`, `stop`, and `restart` on `darwin`, then `linux` and `win32`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | The job labelled `engineering.outcome.usage-control.positions` starts a pass every 1800 seconds with no keep-alive; other platforms return `unsupported` and write no launch agent                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `positions_store.py`    | Passes that take several actions; a record number already on disk; a state file written and read back                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | One numbered file per action holding the position, measurement, threshold, and reason; an existing record is never replaced; the state survives to the next pass                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

</script_tests>

<success_criteria>

- The printed output of exactly one operation is returned verbatim with its exit code.
- A pass runs, and a launchd job is written, only after the operator confirmed each absolute destination.
- No pause or stop is claimed unless the configuration grants its authorization.
- No operation runs a daemon, edits the configuration, or invokes a model.

</success_criteria>
