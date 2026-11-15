# Agent guide

Before any other step, read methodology 4.0 in the main checkout of the methodology repository, `/Users/shz/Code/outcomeeng/methodology/methodology/versions/4.0/methodology/`, starting at `index.md`. Pull that checkout before you read it. Methodology 4.0 governs all work in this repository.

Run `/hold-position resume` when a session starts, and `/hold-position hand-off` before its context is cleared. Use no other installed skill. Where a skill and methodology 4.0 differ, methodology 4.0 holds.

When a Position needs an answer from the Operator and the orchestration file sets `operator_available = true`, it asks through AskUserQuestion. This holds however many earlier questions the Operator dismissed.

A Position stops working only to hand off, or for an answer it cannot settle itself. Before it stops, it asks the Operator through AskUserQuestion when the orchestration file sets `operator_available = true`, and otherwise mails its overseer.

Work is done only when it is merged into `main` on origin.

## Product commands

- `just check-full`: the full deterministic gate the pull-request check runs.
