---
id: 01931c2a-9d4e-7f1a-8c6b-2e5d7a9f0b41
---

# Task

OWNS the task vocabulary — title, due date, completion, and the rules that relate them
SO THAT every capability, interface, and surface that handles tasks
CAN speak one meaning of a task instead of each defining its own

## Assertions

### Mapping: completion-state

A task's completion state maps to exactly one of open or done; no third state exists.

| Case | State |
| ---- | ----- |
| open | open  |
| done | done  |

### Property: due-date

- due-date-is-a-date: A due date is always a calendar date in the task owner's zone, never an instant.

### Compliance: identity

- stable-identity: ALWAYS: a task keeps its identity across edits to title, date, and completion — consumers hold the id, never the title.

### Audit

- field-ownership: NEVER: a capability or surface introduces a task field this domain does not define.
