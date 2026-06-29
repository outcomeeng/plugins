# Browser

PROVIDES an interactive browser surface that renders a spec-tree projection and live interview state into HTML
SO THAT humans and agents
CAN read, comment on, and restructure the tree directly in a browser

## Assertions

### Scenarios

- Given a spec-tree JSON projection from the SPX CLI, when the browser surface renders, then it shows the tree with each node's state, category, index, and depth alongside a node-detail view of the opener, assertions grouped by type, and evidence links ([test](tests/test_browser.scenario.l1.py))
- Given rendered content, when a user acts on it, then the surface supports drag-drop reordering, click-to-comment, and expand/collapse ([test](tests/test_browser.scenario.l1.py))
- Given node or interview text inserted into the HTML, when the surface renders it, then the text is escaped so raw markup never reaches the document ([test](tests/test_browser.scenario.l1.py))
- Given the current prototype surface renders the SPX projection, when it receives the CLI JSON shape, then it preserves node state, category, index, depth, rename, add/remove, drag-drop reordering, and browser chat interactions over the live surface ([test](tests/test_browser.scenario.l1.py))

### Compliance

- ALWAYS: apply the product's own vendored design system — the tokens and component vocabulary this product owns, independent of any other product's design system — per `spx/16-interfaces.enabler/21-browser.enabler/13-rendering.adr.md` ([audit])
- ALWAYS: exchange browser interactions and agent-side updates over the MCP transport — per `spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md` ([audit])
