---
allowed-tools: Skill
description: Load a handoff document to continue previous work
argument-hint: [--list]
---

<objective>
Forward to the picking-up skill to load and claim a handoff session, then continue work from the previous agent's context.
</objective>

<context>
**Arguments:** `$ARGUMENTS`
</context>

<process>
Call the Skill tool NOW with the arguments above:

```json
Skill tool → { "skill": "spec-tree:picking-up" }
```

Do NOT proceed manually. The skill contains the full pickup protocol.
</process>

<success_criteria>
The picking-up skill is invoked and takes over session management.
</success_criteria>
