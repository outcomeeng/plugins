# Plan: interview

Reconcile against `interview.md`, the consumed browser interface, and current intent before acting.

- The live, bidirectional interview surface and its MCP transport now live under `spx/16-interfaces.enabler/21-browser.enabler/` (spec `browser.md`, decision `15-transport.adr.md`). The interview node consumes that browser interface for any future live review surface rather than owning the transport.
- Wire a future interview live-review surface to the browser interface once that node is built.

Browser-interface build steps: `spx/16-interfaces.enabler/21-browser.enabler/PLAN.md`.
