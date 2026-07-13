# Agent supervision prototype

A non-shipped prototype for actively supervising coding agents across Prowl
panes. It detects shared external blockers, restores the conditions for work,
notifies affected operating agents, and confirms that they continue without
taking ownership of their workflows.

## Contents

- `AGENTS.md` — the prototype-local authorization and hard safety bounds for
  the foreground waiter exception.
- `SKILL.md` — the agentic supervision loop.
- `scripts/wait_for_panes.py` — one foreground, machine-wide pane-change
  waiter. The script is limited to 50 lines.

## Waiter

The bounded polling exception and its rationale are defined in `AGENTS.md`.

```bash
python3 prototypes/supervise-agents/scripts/wait_for_panes.py
```

The waiter acquires `/tmp/outcomeeng-pane-wait.lock`, snapshots Prowl's agent
roster, task status, and rendered pane content, and blocks until a meaningful
change occurs. Content churn from a pane that remains `working` does not wake
the orchestrator. A roster change, task-status transition, or content change in
a non-working pane does.

It emits one JSON object and exits:

```json
{
  "event": "pane-change",
  "allTerminal": false,
  "panes": ["<readable-pane-uuid>"],
  "removed": ["<removed-pane-uuid>"]
}
```

The orchestration agent reads only `panes` with `prowl read --wait-stable`;
`removed` records IDs that disappeared and are no longer readable. It acts and
starts the waiter again. `done` is the prototype's sole terminal status. If
every pane is `done` when the waiter starts, it stays blocked until the fleet
changes rather than creating an empty return/restart loop.

Each `prowl` call has a 15-second timeout. Lock contention, command failure,
malformed JSON, and schema errors terminate the waiter instead of creating an
internal restart loop.

## Boundaries

- Prototype only: nothing under this directory is built into `dist/`.
- Requires the `prowl` CLI on `PATH`.
- Reads Prowl's public JSON projections only.
- Does not read transcript JSONL or transcript directories.
- Does not mutate panes; the skill decides whether and what to send.
- The operating agent owns its workflow state and retry decisions.
- No automated spec or test evidence is claimed during the prototype phase.
