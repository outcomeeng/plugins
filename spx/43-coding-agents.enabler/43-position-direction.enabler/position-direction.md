---
id: 01a1414f-d5a1-71dd-9a0d-7606b4ee6f35
malleability: spec
---

# Position Direction

PROVIDES the Director skill `/direct-positions` and its scripts for the roster, panes, monitor, doorbell, controller, mail, pane compaction, restart, and reload
SO THAT a session directing positions across Products
CAN observe, wake, and steer them and resume after compaction without operation-specific skill text

The skill reaches panes through the environment adapters of `spx/43-coding-agents.enabler/18-herdr-environment.enabler/herdr-environment.md` and `spx/43-coding-agents.enabler/18-prowl-environment.enabler/prowl-environment.md`, and mail through the adapter of `spx/43-coding-agents.enabler/18-agent-mail.enabler/agent-mail.md`. It sends the message records that `spx/43-coding-agents.enabler/21-agent-communication.enabler/agent-communication.md` declares.

## Assertions

### Mappings

- ALWAYS: every mail request `/direct-positions` sends carries the composed `mail.channel` as its `repository` when the configuration sets one and carries none otherwise ([test](tests/test_direction.mapping.l1.py))

### Compliance

- ALWAYS: `/direct-positions` resumes a directing session after every compaction from its own resume note, the configuration its override file and the shipped defaults compose, and its unread mail ([audit])
- NEVER: the skill or a script names one operation's people, mail names, Products, panes, worktree paths, dates, or incidents; each such value comes from the composed configuration ([audit])
- ALWAYS: the monitor, the doorbell, and the controller each run one bounded pass per invocation and exit, and each rendering of the skill arms the next pass after it handles the result under the arming rule `bounded-background-wait` of [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md); the Claude rendering arms the monitor through the harness monitor and the doorbell and the controller as bounded background runs collected on the completion notice; the Codex rendering, which offers no monitor tool, runs the monitor pass at the next step boundary and runs the doorbell and the controller as foreground runs collected within the active turn or moved to the next step boundary; no script loops, waits for its next pass, or outlives the session that started it ([audit])
- ALWAYS: every pane read, prompt, key, compaction, restart, and reload runs through the coding-agents environment adapters, and every mail operation through the agent-mail adapter, each reached by a `__file__`-relative import inside the plugin; no script constructs a raw environment or mail command or names a path into the plugin cache ([audit])
- ALWAYS: a script that reports a mail name's records lists its unjudged records through the agent-mail capability's list operation, and no script reads or acknowledges a record on a position's behalf ([audit])
- NEVER: a script types into, compacts, restarts, or reloads a pane the configuration marks untouchable, a pane whose last prompt the environment adapter shows came from the operator, or a pane that waits at a question or approval screen ([audit])
- NEVER: a script reads a harness transcript file; a pane's last prompt and context fill come from the environment adapters or are reported unavailable ([audit])
- ALWAYS: a position acts only when the declared methodology chapter defines it or an operator grant in the composed configuration names it with its bounds, and only within the authority that source establishes; an action that neither source establishes stops and names the absent definition and the absent grant ([audit])
- ALWAYS: the Director ranks a Change the Product's Maintainer confirmed at Proposed for its Frame ahead of the Product's other Proposed Changes ([audit])
- ALWAYS: the Director answers each question a refining position sends because no assumption can defend an answer, and takes it to the operator only when the answer adds intent or settles an open product question ([audit])
- ALWAYS: a restart that relaunches a position's agent session obtains from SPX's `spx verification run paths` the canonical write paths of the verification runs that session records, supplies each path through the harness's supported parent-session permission configuration, preserves the operator's approval policy, and runs a permission preflight of the session's effective native child policy before its first verification round, stopping with a configuration error naming each path the policy denies ([audit:relaunch-write-paths])
