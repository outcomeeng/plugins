# Coding Agents

PROVIDES the coding-agent runtime boundaries that render, configure, and invoke agentic execution through native protocols
SO THAT plugin authors, marketplace maintainers, and product engineers
CAN use shared configured-agent semantics through Claude Code and Codex without treating either runtime as the canonical source language

## Assertions

### Compliance

- ALWAYS: each coding-agent surface owns its native configured-agent grammar, rendering, invocation, and protocol — runtime-specific facts remain at the provided boundary ([audit])
- ALWAYS: coding-agent surfaces consume configured-agent task intent and execution policy from the agentic-execution domain — shared semantics remain consistent across runtime-native representations ([audit])
- ALWAYS: a coding-agent surface whose native spawn does not bind a generated agent's identity proves that identity before submitting role work and routes the role task only to the proven agent — an absent or mismatched identity blocks the invocation, so a verifier or reviewer never runs on an unverified agent ([audit])
- NEVER: a coding-agent surface owns reusable agentic task semantics, model-selection policy, or another runtime's configuration contract — those concerns remain with their semantic or runtime owner ([audit])
