---
name: direct-positions
description: >-
  ALWAYS invoke this skill when directing positions across Products: resuming the directing session after a compaction, observing, waking, or steering a position's pane, or reading a position's mail. NEVER instruct, compact, restart, or reload a position's pane without this skill.
argument-hint: "[resume | observe | wake | steer <position> | compact <position> | restart <position> | reload <position>]"
allowed-tools: Read, Write, {{! tool('use_skill') !}}, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/direction.py":*)
---

Use skill `coding-agents:operate-herdr` for every pane operation on a position whose `environment` is `herdr`.

Use skill `coding-agents:operate-prowl` for every pane operation on a position whose `environment` is `prowl`.

Use skill `coding-agents:operate-agent-mail` for every mail operation.

<objective>
A report of each configured position's observed state, each action taken on its pane or mail with the authority that permitted it, and each action stopped for an absent definition or grant, produced by one directing pass.
</objective>

<essential_principles>

- Run every operation through `python3 "${CLAUDE_SKILL_DIR}/scripts/direction.py" <subcommand> --position "<directing position display name>"`; it resolves the common Git directory through the agent-mail adapter and the invocation checkout through Git, and prints one JSON result.
- Every value this skill acts on comes from the composed configuration in `<configuration>`. Name no person, mail name, Product, pane, worktree path, date, or incident that the configuration does not supply.
- Reach every pane through `coding-agents:operate-herdr` or `coding-agents:operate-prowl`, by the position's `environment`, and every mail operation through `coding-agents:operate-agent-mail`. Construct no raw environment or mail command, and name no path into the plugin cache.
- Read a pane's last prompt and context fill from the environment skill's result. When the result omits either, report it unavailable and act on neither. Read no harness transcript file.
- Never believe a report unchecked: confirm a position's claim against its pane or its mail before relaying it or acting on it.

</essential_principles>

<configuration>

A position's override file is `.spx/orchestration/<position>.md` in the repository's common Git directory, which `git rev-parse --git-common-dir` returns. `<position>` is the position's display name in lowercase with each space replaced by a hyphen. The file is optional.

The file's TOML front matter between `+++` lines sets keys, parsed as TOML. Its Markdown body holds the position's expectations, including any operator grant with its bounds. Each key the file sets replaces that key's default; each key it omits keeps the default; an absent file composes the defaults alone.

| Key                            | Default                                                                                                           |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `mail.channel`                 | the mail project of the repository's own common Git directory                                                     |
| `mail.agent`                   | unset; every mail operation reports unavailable                                                                   |
| `positions`                    | empty; each entry names a display name, environment, working directory, mail name, stall minutes, context percent |
| `executor_groups`              | empty; each entry names a label, environment, working-directory prefix, and exclusions                            |
| `launchers`                    | empty; maps a Product checkout path to the position that launches its Executors                                   |
| `untouchable_panes`            | empty                                                                                                             |
| `advisor`                      | unset; forwarding reports unavailable                                                                             |
| `interval_seconds`             | 1800                                                                                                              |
| `compact_at_percent`           | 30                                                                                                                |
| `doorbell_start_delay_seconds` | 300                                                                                                               |
| `pace`                         | unset; no pacing applies                                                                                          |
| `resume_line`                  | a line naming `/spec-tree:understand`, the resume note, the expectations, and the mail channel                    |

A malformed file or an unknown key stops the skill with a message naming the file, the key, the value found, and the accepted form, and changes nothing.

The skill only reads the override file; it writes nothing into the common Git directory. Runtime state lives under `.spx/orchestration/state/` in the invocation checkout, the top-level directory of the checkout the skill runs from: the highest mail id rung per position in `rungs.json`, each pane's quiet time in `quiet.json`, the monitor's last observations in `observations.json`, and the resume note in `resume-note.md`. The `compose` result prints the absolute `stateDirectory` and `resumeNote`. Never read it as configuration. Copy no expectations or other file into another worktree; each position reads its own override file, which the `resume_line` names.

</configuration>

<authority>

A position acts only when the declared methodology chapter defines the action for that position, or when an operator grant in the composed configuration names the action with its bounds. Read the methodology declaration in `spx.config.yaml` and the chapter it names before the first action of a pass. Act only within the authority the defining source establishes. When neither source establishes an action, stop that action and report the absent definition and the absent grant.

</authority>

<pane_guards>

Send no prompt, key, compaction, restart, or reload to:

- a pane in `untouchable_panes`;
- a pane whose last prompt the environment skill shows came from the operator;
- a pane that waits at a question or approval screen.

Report such a pane with its screen quoted verbatim and take no other action on it. The guards bar input into a pane only; forwarding a stalled guarded pane's screen to `advisor` by mail is the controller's one action on it.

</pane_guards>

<scripts>

| Subcommand   | Effect                                                                                                                                                                                                                                                                                                                                      | Extra arguments                                                                                                                      |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `compose`    | prints the composed configuration                                                                                                                                                                                                                                                                                                           | none                                                                                                                                 |
| `roster`     | resolves each position and executor-group pane through its environment adapter                                                                                                                                                                                                                                                              | none                                                                                                                                 |
| `monitor`    | one monitor pass                                                                                                                                                                                                                                                                                                                            | none                                                                                                                                 |
| `doorbell`   | one doorbell pass                                                                                                                                                                                                                                                                                                                           | `--authority <source>`                                                                                                               |
| `controller` | one report-only controller pass: forwards a stalled position's question, with the guarded pane's screen verbatim, to `advisor` and reports forwarding `unavailable` for a stalled position while `advisor` is unset, reports positions over `compact_at_percent` as `compact-recommended` and reports `pace`; it compacts and paces nothing | `--authority <source>`                                                                                                               |
| `inbox`      | prints the unread records of one mail name                                                                                                                                                                                                                                                                                                  | `--recipient <mail name>`, which defaults to `mail.agent`                                                                            |
| `send`       | sends one record from `mail.agent`                                                                                                                                                                                                                                                                                                          | `--authority <source>`, `--recipient`, `--kind`, `--correlation`, `--subject`, `--body-file <file written in the scratch directory>` |
| `act`        | sends a prompt, `/compact`, a restart, or a reload to one pane after the guards pass                                                                                                                                                                                                                                                        | `--target <position or pane>`, `--operation`, `--text`, `--authority <source>`                                                       |

Every subcommand exits 0 with its JSON result, or exits 1 with `status` `stopped` or `unavailable` and a `detail`; a malformed override file or unknown key stops it naming the file and key before any change. Each pass result carries `rearmAfterSeconds`, which `<passes>` uses to re-arm. A pane's last prompt and context fill print `unavailable` while the environment adapters report neither, and the scripts act on neither. `--authority` names the methodology chapter or operator grant that permits the action; without it `act`, `send`, the doorbell, and the controller stop before any prompt, mail, forward, or compaction, naming the subcommand, the absent definition, the absent grant, and the argument to pass. Restart is available for herdr sessions only, and relaunches the same agent kind with no launch arguments. A missing `--target`, `--operation`, `--recipient`, `--subject`, or `--correlation`, an unreadable `--body-file`, or a target that names no single pane stops the subcommand with a `detail` naming the argument and listing the valid positions, panes, or operations.

Test record: `direction_core.py` and `direction.py` are exercised by the position-direction mapping tests with a stubbed mail adapter and no live pane. The tests cover default and override composition, malformed and unknown-key files with every unknown key reported, pane guards, quiet time, atomic state writes, runtime state and the resume note placed in the invocation checkout apart from the override file in the common Git directory, an absent authority on `act`, `send`, the doorbell, and the controller, a guarded `act` target, an absent `act` target or operation, and absent `send` arguments, the located reason for an unresolved pane, wrong-typed override values, restart without launch arguments, the report-only controller forwarding a stalled guarded pane's screen, and each stated default that reports unavailable: an unset `advisor` on the controller, an unset `mail.agent` on the doorbell, `inbox`, and `send`, and an unset `pace`. They leave no state beyond the pytest temporary directory.

</scripts>

<passes>

The monitor, the doorbell, and the controller are passes. Each pass runs once, writes its observations to the state directory, and ends. The monitor pass writes `quiet.json` and `observations.json`, and the doorbell pass writes `rungs.json` and `quiet.json`. No pass loops, waits for its next pass, or outlives this session. After a pass ends, re-arm the next one through a session-scoped harness capability: the harness monitor for the monitor pass, and a bounded background run whose exit the harness reports for the doorbell and controller passes. A harness without such a capability runs each pass at the next step boundary.

- **Monitor pass.** For each position in `positions` and each group in `executor_groups`, read the pane through its environment skill. Record quiet time and context fill. Report a pane quiet for its stall minutes or filled past its context percent.
- **Doorbell pass.** After `doorbell_start_delay_seconds`, list each position's unread mail through `coding-agents:operate-agent-mail` for the `mail.agent` identity. For a position whose highest unread id exceeds its recorded rung and whose pane is idle, send one prompt through the position's environment skill that tells it to read its mail, then record the new rung. Skip every pane `<pane_guards>` excludes.
- **Controller pass.** Run with `--authority`. The pass reports only: it forwards a stalled position's question to `advisor` when set, and reports forwarding `unavailable` naming the `advisor` key and the override file to set it in when unset, with the screen of a guarded pane quoted verbatim since the guards bar input into a pane and never mail, marks each position over `compact_at_percent` `compact-recommended`, and reports `pace`. It compacts and paces nothing; run `act` with `--operation compact` and the authority that permits it for each recommended position. Recommend compaction for no pane `<pane_guards>` excludes.

</passes>

<arguments>

The first word of the argument selects the mode:

| Argument             | Steps that run                     |
| -------------------- | ---------------------------------- |
| none, or `resume`    | `compose_configuration`, `resume`  |
| `observe`            | `compose_configuration`, `observe` |
| `wake <position>`    | `compose_configuration`, `act`     |
| `steer <position>`   | `compose_configuration`, `act`     |
| `compact <position>` | `compose_configuration`, `act`     |
| `restart <position>` | `compose_configuration`, `act`     |
| `reload <position>`  | `compose_configuration`, `act`     |

Every mode ends at `record`. A mode that needs `<position>` and receives none, or a name the roster lacks, stops and lists the roster's labels.

</arguments>

<workflow>

<step name="compose_configuration">
Run `compose` per `<scripts>`; it resolves the common Git directory, reads the override file of the directing position, and composes it with the defaults per `<configuration>`. Stop on a malformed file. The step writes nothing.
</step>

<step name="resume">
Run this step first in a fresh session and after every compaction. Read the resume note under the state directory, the composed expectations, and the unread mail of `mail.agent` on `mail.channel`. Run the composed `resume_line`. Re-arm the monitor, doorbell, and controller passes. Dispose of each unread mail through the matching step below.
</step>

<step name="observe">
Run `monitor` per `<scripts>`. For each pane the pass flags, read the pane again before acting and check the claim against its mail.
</step>

<step name="act">
For `wake`, `steer`, `compact`, `restart`, and `reload`, check `<authority>` and `<pane_guards>` first. Then run `act` per `<scripts>` with the authority that permits it; it reaches the pane through the position's environment adapter. For a message to a position, Use skill `coding-agents:message-agents`. After a restart or reload, read the pane and confirm the position is up before reporting it.
</step>

<step name="record">
Write the resume note at the absolute `resumeNote` path the `compose` result printed: the time, the last mail handled, each position's observed state, each action in flight with its next trigger, and each operator rule given since the last note. Report the pass outcome to the operator by position display name.
</step>

</workflow>

<failure_modes>

**Claude acted on an unconfirmed report.** A position's mail claimed a Change had merged, and Claude relayed it before checking. Confirm the claim against the position's pane or the store before relaying it.

**Claude typed into a pane that waited at an approval screen.** A prompt sent to wake an idle pane answered a pending approval. Read the pane first and send nothing when it shows a question or approval.

**Claude kept directing after a compaction without its notes.** The session lost its roster and mail rungs. Run `resume` first and read the resume note before any other step.

</failure_modes>

<success_criteria>

- The composed configuration names every value the pass acted on, and the pass names no person, mail name, Product, pane, path, date, or incident from outside it.
- Every pane operation and mail operation went through `coding-agents:operate-herdr`, `coding-agents:operate-prowl`, or `coding-agents:operate-agent-mail`.
- No input went into an untouchable pane, an operator-prompted pane, or a pane at a question or approval screen.
- Every action carries the methodology chapter or operator grant that permitted it; every other action stopped naming the absent definition and the absent grant.
- Each pass ended after one run and was re-armed through a harness capability or deferred to the next step boundary.
- Every state file and the resume note were written under the invocation checkout, and nothing was written into the common Git directory.
- The resume note records the state a post-compaction session needs.

</success_criteria>
