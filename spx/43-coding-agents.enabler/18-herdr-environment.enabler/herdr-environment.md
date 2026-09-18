---
id: 01a0b229-e718-7af0-8411-2e388a19f744
malleability: spec
---

# Herdr Environment

PROVIDES a source-owned, versioned abstraction over the public herdr command surface — worktree open, agent start, stop, relaunch, inventory, read, bounded wait, one-line prompt, and keystroke — with correlated session identities
SO THAT orchestration, communication, and recovery workflows
CAN launch and operate positively identified agent sessions in herdr panes without constructing raw herdr commands or discovering command syntax at runtime

This capability is an agent adapter: the configured way the agent harness launches, observes, and communicates with an agent session that herdr hosts. It governs no agent and no agent session of its own.

## Assertions

### Mappings

- Every supported operation — open-worktree, start, stop, relaunch, inventory, read, wait, prompt, and key — maps one source-owned request shape through the source-owned operation registry to one herdr argument vector and checked response result ([test](tests/test_herdr_environment.mapping.l1.py))
- Herdr agent evidence maps to the complete source-preserved name, agent kind, pane, and the server's own working, blocked, idle, and done states of each hosted agent session, or to a named unavailable or ambiguous result ([test](tests/test_herdr_environment.mapping.l1.py))
- Start maps to the launched agent session's identity when that session is ready for input within the request's bound, or to a named not-ready result; the bounded wait maps to the state reached or a named timeout; neither is an open-ended poll ([test](tests/test_herdr_environment.mapping.l1.py))
- An absent herdr server or an unsupported operation maps to the source-owned unavailable result and no fallback ([test](tests/test_herdr_environment.mapping.l1.py))

### Compliance

- ALWAYS: open-worktree, start, relaunch, stop, and key require explicit mutation authorization in the operation request before any herdr command runs ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: a wait-bearing request — wait, prompt with wait, start, or relaunch — is accepted without an explicit timeout, and the default runner never runs a command without a bound ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: another shipped coding-agents script constructs a raw herdr argument vector or invokes herdr command help ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct raw herdr commands, invoke herdr command help, or depend on an external environment-control skill ([audit])
- The environment surface carries the launch prompt, prompts, and keystrokes only and produces no pane-borne handback block ([audit])
