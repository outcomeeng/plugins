# Live interview — transport spike

A standalone prototype of a real-time, bidirectional interview loop for the
`spec-tree` `interviewing` skill, modelled on impeccable's `live` mode but
reimplemented in **Python 3.11 stdlib only** (the portability floor shipped
skill scripts must meet — no Node, no third-party packages).

This is a spike, deliberately **outside** `src/plugins/`: nothing here ships,
nothing touches `dist/` or `just check`. It exists to de-risk the transport and
the conflict model before any spec node is authored, and to carry the tests
that the eventual `interviewing` outcome node will turn into `[test]` evidence.

## What it demonstrates

- The agent receives each user interaction in **real time** via long-poll.
- The browser receives each agent-side change in real time via **SSE**.
- A single monotonic `rev` reconciles concurrent edits from both sides.
- The subject is a **spec tree**: nodes can be renamed, added, removed, and
  drag-dropped in the browser, alongside answering interview questions.
- A clean process lifecycle: `/shutdown` stops the server and exits the host.

## Files

| File             | Role                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------- |
| `state.py`       | Pure, transport-free state + conflict core. The `rev`/journal spine. Unit-testable.    |
| `server.py`      | `ThreadingHTTPServer` hosting `/state`, `/event`, `/reply`, `/poll`, `/events` (SSE).  |
| `shell.html`     | Vanilla-JS browser UI: questions + editable tree; POSTs interactions, consumes SSE.    |
| `boot.py`        | **Swappable** launch layer (script model). Starts the server, publishes its URL/token. |
| `poll_client.py` | **Swappable** agent transport. One-shot long-poll / `--reply` / `--shutdown`.          |
| `tests/`         | `unittest` suite: pure-core unit tests + real-HTTP integration tests.                  |

## Run the tests

```bash
cd prototypes/interviewing-live
python3 -m unittest discover -s tests -v
```

The integration tests boot a real server on an ephemeral port in a thread and
stop it; no process outlives a test.

## Drive it by hand

```bash
cd prototypes/interviewing-live
python3 boot.py --port 0          # prints {openUrl, token, ...}; blocks (run backgrounded)
# open the printed openUrl in a browser

# agent posts the current question:
python3 poll_client.py --reply '{"type":"set_questions","questions":{"planned":[],"current":{"id":"q1","text":"Which consumers?","options":["A","B"],"choice":null},"settled":[]}}'

# agent waits for the next interaction (returns when the user clicks/edits):
python3 poll_client.py --since 0

python3 poll_client.py --shutdown
```

An optional `--seed seed.json` accepts either a full state document or a bare
`{"tree": [...], "planned": [...]}` to start from `spx spec status --format json`.

## The agent loop (script model)

```text
boot.py                          -> server up, openUrl printed
loop:
  poll_client.py --since <rev>   -> blocks; returns the next interaction as JSON
  agent interprets the event, may push back via --reply (set_questions/set_tree)
  re-poll with the new rev
```

In Claude Code the poll runs as a background task and the harness reports its
completion; the poll request is short-lived (≤270s slices) and self-exiting, so
it is never a keep-alive. The server is the one long-lived process and is owned
by an explicit boot/shutdown lifecycle.

## Swappable launch layer (the MCP fold-in)

`boot.py` and `poll_client.py` are the only transport-specific pieces. An
MCP-model variant replaces both: Claude Code owns the server process via the
plugin's `mcpServers` config (no agent-spawned background process), and a
blocking `wait_for_interaction` MCP tool returns the same event JSON the poll
client prints today. `state.py`, `server.py`'s HTTP+SSE core, and `shell.html`
are unchanged across both models — which is why the launch decision can be
deferred until the core is proven.

## Folding into the `interviewing` spec node

The tests in `tests/` are written as the seed for `[test]`-lane evidence. When
this graduates from a spike to a node:

- `state.py` becomes the portable core under the skill's `scripts/`.
- the question lifecycle and tree-integrity assertions move into the node's spec.
- per CLAUDE.md, shipped script tests live in `outcomeeng_testing/`, not in a
  `tests/` dir inside the skill (which would ship to consumers).
- the domain-agnostic loop stays in `interviewing`; spec-tree node semantics
  (enabler/outcome rules, sparse ordering) come from the calling spec-tree skill.
