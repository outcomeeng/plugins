---
allowed-tools: Skill
description: Load and claim a handoff session, then stop at the post-context checkpoint unless overridden
argument-hint: "[--list] [--auto-continue]"
---

<objective>
Forward to the picking-up skill to load and claim a handoff session, then stop at the post-context checkpoint unless `$ARGUMENTS` explicitly includes `--auto-continue`.
</objective>

<context>
**Arguments:** `$ARGUMENTS`
</context>

<process>
Call the Skill tool NOW with the arguments above:

```json
Skill tool → { "skill": "spec-tree:picking-up", "args": "$ARGUMENTS" }
```

Do NOT proceed manually. The skill contains the full pickup protocol.
</process>

<success_criteria>
The picking-up skill is invoked with the original arguments and takes over session management.
</success_criteria>
