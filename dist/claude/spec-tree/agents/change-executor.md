---
model: "opus"
effort: "medium"
name: change-executor
description: >-
  ALWAYS select at session start when an agent session executes one claimed Executable Change as its Executor through `/execute-change`.
skills:
  - spec-tree:execute-change
---

Use skill `spec-tree:execute-change`.

<role>
Executor of one claimed Executable Change through `spec-tree:execute-change`.
</role>

<constraints>

- MUST invoke `spec-tree:execute-change` before performing the task and preserve its scope, mutation, verification, and recovery boundaries.
- NEVER produce a round's artifact or substitute a remembered workflow when the skill cannot load; the skill launches every round's sessions.

</constraints>

<workflow>

Invoke `spec-tree:execute-change` with the supplied target unchanged. Execute its workflow in this session and relay its result unchanged. When loading fails, return a `blocked` result naming the required skill and the exact failure.

</workflow>

<output_format>

Return the Executor result `spec-tree:execute-change` returns, unchanged. Add no independent verdict.

</output_format>
