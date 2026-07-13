# Supervision prototype instructions

This directory is a non-shipped experiment. It does not define production
behavior or evidence.

## Approved waiter exception

For this prototype only, `scripts/wait_for_panes.py` is the one approved
exception to the repository's general no-poll-loop process-hygiene rule. The
exception exists because Prowl exposes pane snapshots but no blocking pane-change
event.

The exception is valid only while every bound below holds:

- Exactly one waiter process runs per machine, enforced by a non-blocking file
  lock.
- The waiter runs in the foreground; it is never backgrounded or used as a
  keep-alive.
- Every `prowl` subprocess runs synchronously with a timeout and is reaped before
  the next subprocess starts.
- Working-pane content churn does not wake the supervising workflow.
- The waiter emits one meaningful fleet delta and exits. It has no internal
  restart loop; the supervising workflow starts a new process only after acting
  on that delta.
- The script remains at or below 50 physical lines.
- The script reads only Prowl's public JSON projections. It never reads harness
  transcripts and never mutates a pane.
- No second polling helper or shell polling loop is introduced.

The experiment intentionally carries no spec or automated test evidence. Manual
smoke checks may validate compilation, live projection parsing, and singleton
lock behavior.
