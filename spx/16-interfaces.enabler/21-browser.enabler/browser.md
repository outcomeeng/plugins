# Browser

PROVIDES an interactive browser surface that renders a spec-tree projection and live interview state into HTML
SO THAT humans and agents
CAN read, comment on, and restructure the tree directly in a browser

## Assertions

### Scenarios

- Given a spec-tree JSON projection from the SPX CLI, when the prototype browser surface renders, then it shows the tree with each node's state, category, index, and depth ([test](tests/test_browser.scenario.l1.py))
- Given rendered content, when a user acts on it, then the prototype surface supports rename, add/remove, drag-drop reordering, and browser chat interactions over the live surface ([test](tests/test_browser.scenario.l1.py))
- Given node, question, or chat text inserted into the HTML, when the surface renders it, then the text is escaped so raw markup never reaches the document ([test](tests/test_browser.scenario.l1.py))
- Given the current SPX projection lacks node-detail fields, when planning the next browser slice, then the browser node tracks opener text, assertion groups, evidence links, and commentable text selection as remaining projection and interaction gaps ([test](tests/test_browser.scenario.l1.py))

### Compliance

- ALWAYS: apply the product's own vendored design system — the tokens and component vocabulary this product owns, independent of any other product's design system — per `spx/16-interfaces.enabler/21-browser.enabler/13-rendering.adr.md` ([audit])
- ALWAYS: exchange browser interactions and agent-side updates over the MCP transport — per `spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md` ([audit])
