---
description: Reflect, persist, and close session without creating a handoff file
allowed-tools:
  - Skill
---

<objective>
Close the current work session without creating a handoff file.

This is a convenience alias for the `/handing-off` skill with `--no-session`. It runs the full reflection and persistence protocol — anchoring nodes, five perspectives, persistence decisions, and commit gating — but skips session file creation.
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
