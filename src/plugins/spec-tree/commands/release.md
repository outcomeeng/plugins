---
description: Reflect, persist, and close session without creating a handoff file (archives in-scope sessions; does NOT return them to the todo queue)
allowed-tools:
  - Skill
---

<objective>
Close the current work session without creating a handoff file. All in-scope sessions are archived.

This is a convenience alias for the `/handing-off` skill with `--no-session`. It runs the full reflection and persistence protocol — anchoring nodes, six perspectives, persistence decisions, and commit gating — but skips session file creation. Every in-scope session is archived.

**This is not a "return to queue" operation.** `/release` does not put the claimed session back in `.spx/sessions/todo/` for another agent. If the user wants to put a wrongly-claimed session back on the shared queue, that is a separate manual operation (move the session file from `.spx/sessions/doing/` back to `.spx/sessions/todo/`).
</objective>

<process>
Call the Skill tool now:

```json
Skill tool → { "skill": "spec-tree:handing-off", "args": "--no-session $ARGUMENTS" }
```

Do not invoke `/handoff` as an intermediate command.
</process>

<success_criteria>

- `/handing-off` is invoked with `--no-session`
- No session file is created by command-local logic
- Durable persistence and commit gating come from the skill

</success_criteria>
