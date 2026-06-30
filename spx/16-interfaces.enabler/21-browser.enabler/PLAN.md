# Plan: browser interface

Coordination note for realizing `browser.md`. Reconcile against `browser.md`,
`13-rendering.adr.md`, `15-transport.adr.md`, `spx/12-shipped-scripting.adr.md`,
`spx/13-plugin-and-runtime-conventions.adr.md`, the prototype, and current intent
before acting. This is stale-prone coordination, not spec truth.

The browser interface is a local, MCP-backed authoring surface for Spec Tree
work. It renders the SPX projection, keeps chat and tree interaction live with
the agent, uses a vendored product-owned design system inspired by Levenate, and
grows toward write-back through SPX CLI capabilities. Levenate is reference
material only; this product owns its copied tokens, components, launch layer,
and renderer.

## Current runnable surface

- `prototypes/interview-live/` is the runnable prototype.
- `mcp_server.py` owns the MCP launch path and exposes the live browser URL,
  blocking interaction wait, agent messages, rendered updates, and shutdown.
- `shell.html` owns the static browser surface: chat, questions, drawer tree,
  editable projection rows, and server-sent updates.
- `projection.py` adapts `spx spec status --format json` to the prototype tree
  shape without re-parsing the spec tree.
- `boot.py` and `poll_client.py` are development fallback tools for inspecting
  the surface without an MCP runtime.

## Incomplete specification targets

- Specify and test SPX projection rendering for node state, category, index,
  depth, node-detail openers, grouped assertions, and evidence links.
- Specify and test drawer-based tree inspection, drag-drop reordering,
  click-to-comment, text selection, and expand/collapse.
- Specify and test HTML escaping for node and interview text inserted into the
  shell.
- Specify and test preservation of node state, category, index, depth, rename,
  add/remove, drag-drop reordering, and browser chat interactions over the live
  surface.

## Active path

1. **Projection detail.** Extend the SPX CLI projection, or add a detail
   projection, so the browser receives node titles from spec openers plus
   assertion groups and evidence links. The renderer consumes that projection;
   it does not parse spec files.
2. **Write-back.** Route rename, add, remove, and reorder events through SPX
   refactor/write capabilities. Reordering recomputes sparse integer order from
   the new sibling position instead of preserving stale order values.
3. **Commenting and selection.** Add inline notes and text selection on nodes,
   assertions, and evidence links. Notes belong to a deliberate methodology
   surface, not ad hoc browser-only state.
4. **Generated design tokens.** Add a product-owned token source for the browser
   interface and generate static `tokens.css`. Browser styles reference token
   variables rather than raw color, font, size, radius, shadow, or motion
   literals.
5. **State core placement.** Move complex, test-bearing state behavior into the
   SPX CLI when the prototype becomes shipped behavior. The plugin keeps thin
   MCP launch glue and static renderer assets.
6. **Plugin productization.** Create the shipped interfaces plugin with
   stdlib-only Python scripts, static renderer assets, MCP server registration,
   and vendored local `woff2` fonts.

## Evidence path

The node is declared. It has no co-located `[test]` evidence and is not listed
in `spx/EXCLUDE`. Add evidence when a shipped implementation path exists; use
`spx/EXCLUDE` only if the node becomes specified with tests before the
implementation path is present.
