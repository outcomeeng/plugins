# Browser

PROVIDES a local, MCP-backed browser authoring surface that renders a spec-tree projection and live interview state into HTML
SO THAT humans and agents
CAN read, comment on, and restructure the tree directly in a browser while staying in a live conversation loop

## Assertions

### Compliance

- ALWAYS: apply the product's own vendored design system — the tokens and component vocabulary this product owns, independent of any other product's design system — per `spx/16-interfaces.enabler/21-browser.enabler/13-rendering.adr.md` ([audit])
- ALWAYS: exchange browser interactions and agent-side updates over the MCP transport — per `spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md` ([audit])
