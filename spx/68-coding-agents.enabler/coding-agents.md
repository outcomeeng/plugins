# Coding Agents

PROVIDES the coding-agent runtime boundaries that render, configure, and invoke agentic execution through native protocols
SO THAT plugin authors, marketplace maintainers, and product engineers
CAN use shared configured-agent semantics through Claude Code and Codex without treating either runtime as the canonical source language

## Assertions

### Mappings

- A configured verifier or reviewer invocation through Codex maps to an identity-preflight turn followed by the role task on the same agent id: the preflight returns the generated `OUTCOMEENG_CODEX_AGENT_NAME` marker, and a missing or unexpected marker blocks the gate before role work begins ([test](tests/test_codex_agent_identity.mapping.l1.py))

### Compliance

- ALWAYS: each coding-agent surface owns its native configured-agent grammar, rendering, invocation, and protocol — runtime-specific facts remain at the provided boundary ([audit])
- ALWAYS: coding-agent surfaces consume configured-agent task intent and execution policy from the agentic-execution domain — shared semantics remain consistent across runtime-native representations ([audit])
- NEVER: a coding-agent surface owns reusable agentic task semantics, model-selection policy, or another runtime's configuration contract — those concerns remain with their semantic or runtime owner ([audit])
