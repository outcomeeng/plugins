---
id: 01a0b229-e718-7af0-8411-2e388a19f744
malleability: spec
---

# Herdr Environment

PROVIDES a source-owned, versioned abstraction over the public herdr command surface — worktree create, worktree open, agent start, stop, relaunch, inventory, read, bounded wait, one-line prompt, and keystroke — with correlated session identities
SO THAT orchestration, communication, and recovery workflows
CAN launch and operate positively identified agent sessions in herdr panes without constructing raw herdr commands or discovering command syntax at runtime

This capability is an agent adapter: the configured way the agent harness launches, observes, and communicates with an agent session that herdr hosts. It governs no agent and no agent session of its own.

## Assertions

### Mappings

- Every supported operation — open-worktree, create-worktree, start, stop, relaunch, inventory, read, wait, prompt, and key — maps one source-owned request shape through the source-owned operation registry to a checked response result: read maps to its `herdr agent read` argument vector plus one `herdr agent get` agent-evidence lookup for the same target, so its result carries the agent session or the named incomplete item, and every other operation maps to one herdr argument vector ([test](tests/test_herdr_environment.mapping.l1.py))
- Herdr agent evidence maps to the complete source-preserved name, agent kind, pane, and the server's own working, blocked, idle, done, and unknown states of each hosted agent session, or to a named unavailable or ambiguous result; an agent whose evidence lacks a projected field maps to a named incomplete item carrying its pane, every field its evidence carries, and the names of the missing fields, while every other agent in the same inventory maps in full ([test](tests/test_herdr_environment.mapping.l1.py))
- Start and relaunch map to the launched agent session's identity when that session is ready for input within the request's bound, to a named not-ready result, or to the named incomplete result when the agent's evidence lacks a field readiness needs; the bounded wait maps to the state reached, a named timeout, or that incomplete result; neither is an open-ended poll ([test](tests/test_herdr_environment.mapping.l1.py))
- An absent herdr server or an unsupported operation maps to the source-owned unavailable result and no fallback ([test](tests/test_herdr_environment.mapping.l1.py))
- A create-worktree request carrying a workspace, with an optional branch, base, and path, maps to one `herdr worktree create` argument vector and to a result carrying the created worktree's path, its workspace, and its root pane; a create-worktree or open-worktree request without a workspace maps to the source-owned invalid-request result before any herdr command runs ([test](tests/test_herdr_environment.mapping.l1.py))
- An open-worktree request carrying a workspace and a path maps to one `herdr worktree open` argument vector naming that workspace, so the opened worktree's workspace is the one the request names ([test](tests/test_herdr_environment.mapping.l1.py))
- A read or prompt addressed to the pane of an agent whose evidence is incomplete maps to the operation's own result, carrying the named incomplete item in place of the complete projection ([test](tests/test_herdr_environment.mapping.l1.py))
- Stop maps to one herdr argument vector that ends the agent session and leaves its pane open at the shell, so a relaunch into the same pane follows ([test](tests/test_herdr_environment.mapping.l1.py))

### Compliance

- ALWAYS: open-worktree, create-worktree, start, relaunch, stop, and key require explicit mutation authorization in the operation request before any herdr command runs ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: a wait-bearing request — wait, prompt with wait, start, or relaunch — is accepted without an explicit timeout, and the default runner never runs a command without a bound ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: create-worktree records a worktree-occupancy claim; the agent session `start` launches in the created worktree claims it ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: another shipped coding-agents script constructs a raw herdr argument vector or invokes herdr command help ([test](tests/test_herdr_environment.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct raw herdr commands, invoke herdr command help, or depend on an external environment-control skill ([audit])
- The environment surface carries the launch prompt, prompts, and keystrokes only and produces no pane-borne handback block ([audit])
