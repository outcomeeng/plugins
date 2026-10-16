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

### Compliance

- ALWAYS: `/direct-positions` resumes a directing session after every compaction from its own resume note, the configuration its override file and the shipped defaults compose, and its unread mail ([audit])
- NEVER: the skill or a script names one operation's people, mail names, Products, panes, worktree paths, dates, or incidents; each such value comes from the composed configuration ([audit])
- ALWAYS: the monitor, the doorbell, and the controller each run one bounded pass per invocation and exit; the skill re-arms the next pass through a session-scoped harness capability, the harness monitor for the monitor and a bounded background run whose exit the harness reports for the doorbell and the controller, and no script loops, waits for its next pass, or outlives the session that started it ([audit])
- ALWAYS: every pane read, prompt, key, compaction, restart, and reload runs through the coding-agents environment adapters, and every mail operation through the agent-mail adapter, each reached through its own command line from a `__file__`-relative path inside the plugin; no script constructs a raw environment, mail, or Git command, derives the mail project key from Git state, or names a path into the plugin cache ([audit])
- NEVER: a script types into, compacts, restarts, or reloads a pane the configuration marks untouchable, a pane whose last prompt the environment adapter shows came from the operator, or a pane that waits at a question or approval screen ([audit])
- NEVER: a script reads a harness transcript file; a pane's last prompt and context fill come from the environment adapters or are reported unavailable ([audit])
- ALWAYS: a position acts only when the declared methodology chapter defines it or an operator grant in the composed configuration names it with its bounds, and only within the authority that source establishes; an action that neither source establishes stops and names the absent definition and the absent grant ([audit])
