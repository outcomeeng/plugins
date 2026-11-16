---
id: 01931c2a-6e7b-7c4d-9a1f-3b2e8d5f6a70
malleability: verification
---

# Quick Add

PROVIDES capture of a task from one line of natural text, including a due date when the text names one
SO THAT every interface and surface that captures tasks
CAN record a task without leaving what they were doing

## Assertions

### Test.Mapping: relative-dates

Relative date words map to dates: "today", "tomorrow", and weekday names resolve against the capture time.

| Case     | Date                      |
| -------- | ------------------------- |
| today    | the capture date          |
| tomorrow | the day after the capture |
| weekday  | the next such weekday     |

### Test.Scenario: capture

- dated-capture:
  - Given the text "buy milk tomorrow"
  - When it is captured
  - Then a task titled "buy milk" exists with tomorrow's date
- undated-capture:
  - Given text with no date
  - When it is captured
  - Then the task has no due date
  - And no error is raised

### Test.Property: capture

- capture-idempotent: Capture is idempotent on its parsed form: capturing the parsed title and date again produces an equal task.

### Test.Compliance: capture

- capture-event: ALWAYS every capture emits the `task_captured` event the capture-rate source reads — the outcome record's condition is unreadable without it.

### Probe: quick-add field

- capture-basic: A person captures a task from the quick-add field within two seconds of focusing it.

### Audit: capture storage

- raw-text-retention: NEVER the parser stores the raw text beyond the capture — the task is the record.
