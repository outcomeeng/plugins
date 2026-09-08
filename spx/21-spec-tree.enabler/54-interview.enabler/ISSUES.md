# Issues: Interview

Coordination note; not spec truth. Reconcile against `interview.md`, the consumed browser interface, and current intent before acting.

## No live interview review surface is wired to the browser interface

The live, bidirectional interview surface and its MCP transport belong to `spx/16-interfaces.enabler/21-browser.enabler/` (spec `browser.md`, decision `15-transport.adr.md`). The interview node consumes that browser interface for any live review surface rather than owning the transport. No such surface exists yet: the interview runs through the structured-question tool only. Wire a live-review surface to the browser interface once that node is built; its build steps live in that node's coordination notes.
