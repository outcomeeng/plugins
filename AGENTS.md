# Agent guide

Before any other step, read methodology 4.0 in the main checkout of the methodology repository, `/Users/shz/Code/outcomeeng/methodology/methodology/versions/4.0/methodology/`, starting at `index.md`. Pull that checkout before you read it. Methodology 4.0 governs all work in this repository.

Run `/hold-position resume` when a session starts, and `/hold-position hand-off` before its context is cleared. Use no other installed skill, except the pane skills an overseer uses to read, prompt, clear and resume the panes of the Positions it oversees: `coding-agents:operate-prowl` and `coding-agents:operate-herdr`. Where a skill and methodology 4.0 differ, methodology 4.0 holds.

A Position stops working only to hand off, or for an answer it cannot settle itself. Before it stops, it mails its overseer.

Work is done only when it is merged into `main` on origin.

## Product commands

- `just check-full`: the full deterministic gate the pull-request check runs.
