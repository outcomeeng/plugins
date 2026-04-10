# Plan: update-spx implementation

Concrete remaining steps to implement the [update-spx enabler](update-spx.md). Remove this file when all deliverables are in place and tests are passing.

## Deliverables

| Artifact                 | Plugin    | Purpose                                                    |
| ------------------------ | --------- | ---------------------------------------------------------- |
| `/updating-spx` (skill)  | spec-tree | Methodology: diff template vs project file, merge strategy |
| `/update-spx` (command)  | spec-tree | User-facing command that invokes the skill                 |
| `spx-updater` (agent)    | spec-tree | Subagent that preloads the skill for autonomous execution  |
| `/understanding` changes | spec-tree | Staleness detection on session start                       |
| `/handoff` changes       | spec-tree | Staleness marker in persistence proposal                   |
