---
id: 01a1414f-d5bc-7ba8-9c42-10c44b0edcbf
malleability: spec
---

# Position Overrides

PROVIDES the per-position override file and the composition of its settings with the shipped defaults
SO THAT an operation
CAN set its positions, panes, pace, and expectations without editing the shipped skill

## Assertions

- ALWAYS: a position's override file is `.spx/orchestration/<position>.md` in the repository's common Git directory, where `<position>` is the position's display name in lowercase with each space replaced by a hyphen; its TOML front matter between `+++` lines sets keys, read with the standard library's TOML parser, and its Markdown body holds the position's expectations
- ALWAYS: each key the file sets replaces that key's shipped default, a key it omits keeps the default, and an absent file composes the defaults alone
- ALWAYS: the keys and their shipped defaults are `mail.channel`, the mail project of the repository's own common Git directory; `mail.agent`, unset, so mail operations report unavailable; `positions`, empty, each entry naming a position's display name, environment, working directory, mail name, stall minutes, and context percent; `executor_groups`, empty, each naming a label, environment, working-directory prefix, and exclusions; `launchers`, empty, mapping a Product checkout path to the position that launches its Executors; `untouchable_panes`, empty; `advisor`, unset, so forwarding reports unavailable; `interval_seconds`, 1800; `compact_at_percent`, 30; `doorbell_start_delay_seconds`, 300; `pace`, unset, so no pacing applies; and `resume_line`, a line naming `/spec-tree:understand`, the resume note, the expectations, and the mail channel
- ALWAYS: a malformed file or an unknown key stops the skill naming the file, the key, and the reason, and changes nothing
- ALWAYS: the scripts' runtime state, the highest mail id rung per position, each pane's quiet time, and the monitor's last observations, lives under `.spx/orchestration/state/` in the same common Git directory and is never read as configuration
- NEVER: the skill copies expectations or any other file into another worktree; each position reads its own override file, which the resume line names
