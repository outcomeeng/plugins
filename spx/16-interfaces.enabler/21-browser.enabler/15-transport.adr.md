# Browser Interface Transport

The browser interface exchanges agent-side updates and user interactions over a Model Context Protocol server that Claude Code owns through the plugin's `mcpServers` configuration. The agent receives each browser-side interaction by calling a blocking `wait_for_interaction` tool and pushes rendered updates back through MCP tool calls; the browser renders agent-side changes over server-sent events and posts its interactions to the same server.

## Rationale

`spx/13-plugin-and-runtime-conventions.adr.md` forbids shipped plugin code from spawning subprocesses that outlive a single tool call or implementing polling waits. A script-model transport — an agent-spawned long-lived HTTP server plus an agent-driven long-poll loop — violates both constraints. Inverting process ownership to Claude Code through `mcpServers` removes the agent-spawned process, and a blocking `wait_for_interaction` tool replaces the long-poll: the agent awaits one interaction per call while the runtime, not a poll loop, holds the wait.

The decision binds the launch layer only. The transport-free state core — the monotonic revision counter, the append-only journal, the interaction lifecycle, and spec-tree integrity — and the browser shell are transport-agnostic, so the same core serves any launch model. Isolating transport in a replaceable launch layer is what lets the core be proven independently of the launch model.

## Invariants

- The state core is transport-free: identical state transitions result regardless of which launch layer drives them.
- A single monotonic revision reconciles concurrent edits from agent and browser; the revision advances only on an accepted event.

## Verification

### Audit

- ALWAYS: Claude Code owns the browser-interface server process through the plugin's `mcpServers` configuration — the agent never spawns the server as a background process ([audit])
- ALWAYS: the agent receives each browser-side interaction through a blocking `wait_for_interaction` tool call, not an agent-driven poll ([audit])
- ALWAYS: the transport-free state core and the browser shell stay transport-agnostic — only the launch layer changes between transports ([audit])
- NEVER: the shipped browser-interface transport implements a polling wait or spawns a subprocess outliving a single tool call — per `spx/13-plugin-and-runtime-conventions.adr.md` ([audit])
