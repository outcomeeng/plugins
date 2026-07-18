# Coding Agents

PROVIDES coding-agent boundaries that render, configure, and invoke agentic execution through native protocols
SO THAT plugin authors, marketplace maintainers, and product engineers
CAN use shared configured-agent semantics through Claude Code and Codex without treating either agent harness as the canonical source language

## Assertions

### Compliance

- ALWAYS: each coding-agent surface owns its native configured-agent grammar, rendering, invocation, and protocol — agent-harness-specific facts remain at the provided boundary ([audit])
- ALWAYS: coding-agent surfaces consume configured-agent task intent and execution policy from the agentic-execution domain — shared semantics remain consistent across native representations ([audit])
- ALWAYS: a configured verifier or reviewer invocation through Codex proves the generated agent identity before role work by using an identity-only first turn, accepting only the exact generated `OUTCOMEENG_CODEX_AGENT_NAME` marker, and submitting the role task to the same full agent id; a missing or unexpected marker blocks the gate ([audit])
- ALWAYS: a configured verifier or reviewer invocation through Claude Code uses native foreground configured-agent selection and returns the role result without the Codex identity preflight ([audit])
- NEVER: a coding-agent surface owns reusable agentic task semantics, model-selection policy, or another agent harness's configuration contract — those concerns remain with their semantic or native-surface owner ([audit])
