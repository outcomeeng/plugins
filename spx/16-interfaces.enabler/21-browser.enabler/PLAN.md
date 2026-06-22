# Plan: browser interface

Coordination note for realizing `browser.md`. Reconcile against `browser.md`,
`13-rendering.adr.md`, `15-transport.adr.md`, `spx/12-shipped-scripting.adr.md`,
`spx/13-plugin-and-runtime-conventions.adr.md`, the prototype, and current intent
before acting. This is stale-prone coordination, not spec truth.

A working prototype now exists and has been driven end to end with a human in a
browser. The decisions in `15-transport.adr.md` and `13-rendering.adr.md` are
validated by it. This note records what the prototype proved, what is rejected,
what the operator wants, and the path from prototype to shipped plugin.

## Source

- Prototype: `prototypes/interview-live/` on branch `feat/browser-interface`
  (commits `7e442b27` MCP transport, `be27cd29` chat channel, `667060dc`
  scroll fix; original spike `10c9a062`, PR #112).
- Design reference: `levenate-vision.html` and `levenate-tree.html` in the
  `outcomeeng/levenate` repo — **reference only; Levenate is a separate product**
  that reuses the SPX CLI and this browser interaction. The design system is
  shared by **copy** (vendored tokens), never a runtime dependency.

## What the prototype proved (works)

- **MCP transport is the right call.** Claude Code owns the surface process
  through `mcpServers`; the agent receives every browser interaction through a
  blocking `wait_for_interaction` tool and pushes updates through `say` /
  `present`; the browser renders over SSE. Fully bidirectional, entirely on
  `127.0.0.1`, **no copy-paste and no application switch.** This supersedes the
  spike's agent-spawned-server + CLI-long-poll model, exactly as
  `15-transport.adr.md` decided. The MCP server hosts the HTTP+SSE server
  in-process and bridges to it over localhost, so the real-time logic stays in
  one place (`server.py`).
- **Render from the SPX projection.** `spx spec status --format json` →
  a thin adapter → the surface. The interface never re-derives the tree
  (`13-rendering.adr.md`). The projection carries `{id, kind, order, slug,
  state, children}` per node plus a `decisions` array.
- **The state core is solid.** `state.py` (monotonic `rev`, append-only journal,
  single-writer conflict reconciliation, tree integrity) carries 28 passing
  tests and absorbed the real 16-node tree, live edits, and chat without change.
- **The vendored design system fits the domain.** Levenate's OKLCH tokens
  include status colors that map 1:1 onto node states (`declared / specified /
  failing / passing`) and category colors for `adr / pdr / outcome`.
- **Editing and chat both flow back to the agent.** Rename, add, remove,
  drag-drop reorder, and a free-text chat channel all arrive via
  `wait_for_interaction`. The operator filed a layout bug *through the surface's
  chat* and it was fixed and replied to in the same loop — the tool already
  improves itself.

## Rejected (do not rebuild these)

- **Copy-paste / clipboard round-trips.** The interview skill's
  `preview-template.md` and `levenate-vision.html` already do comment →
  clipboard → paste-back. The operator does not want it: the agent must receive
  responses without the user switching applications. MCP is required precisely
  to remove the paste.
- **Hosted, dependency-heavy surfaces.** The agent-native visual-plan tool
  (OAuth, an `npx` package, a hosted website, and a renderer that pinned a CPU
  core) is the wrong shape. The surface must be local, stdlib-only, static
  assets, no public site, no runtime package fetch.
- **CLI long-poll as the shipped transport.** Fine for the spike; superseded by
  MCP per `15-transport.adr.md` (the runtime ADR forbids agent-spawned
  long-lived processes and polling waits).

## What the operator wants

The agent starts a local web server and an MCP server. The user looks at a
browser window and chats with the agent, clicks, decides, adds notes, and
selects text — all locally, no public website. MCP is non-negotiable because it
is what returns the user's responses to the agent in real time. Scope here is
**authoring, refactoring, and maintaining a product's spec tree** — the in-scope
agent–user interaction affordance for this product, shipped to every consumer.
Richer product-building surfaces are Levenate's concern, not this node's.

## Prototype → shipped plugin (the path)

1. **Persist edits back to the tree (write-back) — the biggest gap.** Renames,
   adds, removes, and reorders currently live only in the surface's in-memory
   state. To be an authoring tool they must serialize to the `spx/` files and
   commit to git. Reorders must recompute sparse-integer `order` from the new
   position (the spike leaves `order` untouched). This is AST-driven
   refactor/rebalance — route it through the spec-tree refactor capability / the
   SPX CLI, not bespoke file writing in the surface.
2. **Real node titles, not slug-casing.** The adapter currently title-cases the
   slug (`hdl` → "Hdl", and a rename revealed "Python Code Quantity"). Titles
   must come from each node's spec opener. Either widen the SPX projection to
   carry the title, or fetch node detail per node.
3. **The detail pane.** `levenate-tree.html`'s right side (breadcrumb, opener,
   assertions grouped by lane with `[test]`/`[eval]`/`[audit]` chips) needs node
   detail beyond the structural projection — a per-node detail projection or a
   node-detail fetch over the same transport.
4. **Notes and text-selection.** Add the `commentable` pattern (inline notes on
   any node/assertion) and text selection. Consider the per-node `context/`
   folder Levenate proposes (research/notes, distinct from spec, decisions, and
   `PLAN.md`/`ISSUES.md`) as a candidate methodology extension to trial here.
5. **State core → SPX CLI.** Per `spx/12-shipped-scripting.adr.md`, the
   complex, test-bearing `state.py` does not ship as a heavy plugin script: once
   the interface proves itself (it now has), extract its complexity into the SPX
   CLI, tested there and consumed as a trusted component; the plugin keeps only
   thin launch + HTML-emitting glue under its `scripts/`.
6. **Productize into an `interfaces` plugin.** No such plugin exists yet. Ship
   the MCP launch glue and renderer as stdlib-only Python under the plugin's
   `scripts/`, register the server in the plugin's `mcpServers`, and **vendor the
   fonts as static `woff2`** — the prototype loads Google Fonts from a CDN, which
   the portability constraints forbid (`13-rendering.adr.md`,
   `13-plugin-and-runtime-conventions.adr.md`).
7. **Evidence.** Graduate the prototype's `state.py` tests into the node's
   `[test]` lane, decide the evidence home for `browser.md`'s rendering/affordance
   assertions, and remove the `spx/EXCLUDE` entry when implementation lands.

## Known constraints / gotchas

- **MCP loads at Claude Code startup.** Changes to `state.py` / `mcp_server.py`
  require a Claude reload (`/mcp` reconnect or restart) to take effect; only
  `shell.html` updates on a browser refresh (it is served per request,
  `Cache-Control: no-store`). The shipped plugin registers its server once via
  `mcpServers`; this dev-loop friction is inherent and worth documenting for
  contributors.
- **`wait_for_interaction` is the agent's only inbox.** It blocks with a ~270s
  deadline that returns a `{"type":"timeout"}` sentinel to re-call; nothing
  reaches the agent without it.
- **Single-writer reconciliation** (one user + one agent, monotonic `rev`,
  last-writer-wins with stale-structural-op rejection) is sufficient for this
  surface; do not reach for a CRDT here.
