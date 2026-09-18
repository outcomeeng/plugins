---
malleability: spec
---

# Herdr Environment

PROVIDES a source-owned, versioned abstraction over the public herdr command surface — agent start, stop, relaunch, inventory, bounded wait, one-line prompt, and keystroke — with correlated session identities
SO THAT orchestration, communication, and recovery workflows
CAN launch and operate positively identified herdr agents without constructing raw herdr commands or discovering command syntax at runtime

## Assertions

### Mappings

- Every supported operation — start, stop, relaunch, inventory, wait, prompt, and key — maps one source-owned request shape through the source-owned operation registry to one herdr argument vector and checked response result
- Herdr agent evidence maps to complete source-preserved agent name, kind, pane, and the server's own working, blocked, idle, and done states, or to a named unavailable or ambiguous result
- Start maps to the launched session's identity and returns only when the agent is ready for input; the bounded wait maps to the state reached or a named timeout, never to an open-ended poll

### Compliance

- ALWAYS: key and focus require explicit mutation authorization in the operation request before any herdr command runs
- ALWAYS: an absent herdr server or an unsupported operation yields the source-owned unavailable result and no fallback
- NEVER: another shipped coding-agents script or skill constructs a raw herdr argument vector or invokes herdr command help
