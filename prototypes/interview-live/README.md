# Browser interface prototype

A standalone Python 3 stdlib prototype of the browser surface governed by
`spx/16-interfaces.enabler/21-browser.enabler`. It renders the SPX projection,
streams agent updates into the browser, and sends browser interactions back to
the agent through the MCP transport.

The prototype lives outside `src/plugins/`. Product truth lives in the browser
node spec and ADRs; this README is only the operator guide for running and
inspecting the prototype.

## What it demonstrates

- Claude Code owns the surface process through `mcp_server.py`, matching the MCP
  transport in `spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md`.
- The agent receives browser actions through the blocking `wait_for_interaction`
  MCP tool and replies through `say` or `present`.
- The browser receives agent-side changes over server-sent events and posts user
  edits to the same localhost server.
- The left pane keeps chat and interview questions independently scrollable from
  the spec-tree pane.
- The tree renders SPX projection fields for state, category, and index. Node
  detail waits on a richer SPX CLI projection that carries opener text,
  assertions, and evidence links.
- The state core uses a monotonic `rev`, an append-only journal, and stale
  structural-operation rejection for a single user plus one agent.

## Files

| File                           | Role                                                                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `state.py`                     | Transport-free state core: revisions, journal, tree edits, chat, and conflict handling.                                                     |
| `server.py`                    | `ThreadingHTTPServer` for `/state`, `/event`, `/reply`, `/poll`, `/events`, and `/shutdown`.                                                |
| `mcp_server.py`                | MCP stdio transport that owns `LiveServer` and exposes `get_surface_url`, `wait_for_interaction`, `say`, `present`, and `shutdown_surface`. |
| `shell.html`                   | Vanilla HTML/CSS/JS browser UI with the vendored visual system, chat channel, editable tree, and SSE updates.                               |
| `projection.py`                | Pure adapter from `spx spec status --format json` to the prototype tree shape.                                                              |
| `spx_seed.py`                  | CLI helper that emits a `{tree, planned}` seed from the SPX projection.                                                                     |
| `boot.py` and `poll_client.py` | Development fallback for local inspection without an MCP runtime.                                                                           |
| `tests/`                       | `unittest` coverage for the state core, HTTP server, and projection adapter.                                                                |

## Prototype tests

```bash
cd prototypes/interview-live
python3 -m unittest discover -s tests -v
```

The integration tests bind an ephemeral localhost port and stop the server before
the test exits.

## Seed the real spec tree

```bash
cd prototypes/interview-live
spx spec status --format json | python3 spx_seed.py > real-tree-seed.json
```

`boot.py` and `mcp_server.py` also accept `--seed` with a full state document, a
bare `{tree, planned}` seed, or the SPX projection shape adapted by
`projection.py`.

## Run through MCP

Register the MCP server in project `.mcp.json` or in the future plugin
`mcpServers` entry:

```json
{
  "mcpServers": {
    "spec-tree-surface": {
      "command": "python3",
      "args": [
        "/abs/path/prototypes/interview-live/mcp_server.py",
        "--seed",
        "/abs/path/prototypes/interview-live/real-tree-seed.json"
      ]
    }
  }
}
```

Then use the MCP tools:

- `get_surface_url` returns the localhost URL to open in the browser.
- `present` pushes questions and/or a tree to the surface.
- `say` sends an agent chat message to the browser.
- `wait_for_interaction` blocks until the user clicks, edits, reorders, answers,
  or sends chat.
- `shutdown_surface` stops the localhost server.

## Development fallback

The script path works for local inspection without an MCP runtime:

```bash
cd prototypes/interview-live
python3 boot.py --port 0 --seed real-tree-seed.json
```

Open the printed `openUrl`, then use `poll_client.py --reply`,
`poll_client.py --since <rev>`, and `poll_client.py --shutdown` from another
terminal.

## Productization boundary

`mcp_server.py` and `shell.html` prove the MCP launch and browser interaction
shape. The complex, test-bearing state core belongs in the SPX CLI before this
becomes shipped plugin behavior. The shipped plugin keeps thin MCP launch glue
and static renderer assets, with fonts vendored as local `woff2` files.
