# Plan: interview

Reconcile against `interview.md`, the consumed browser interface, and current intent before acting.

- The live, bidirectional interview surface and its MCP transport now live under `spx/16-interfaces.enabler/21-browser.enabler/` (spec `browser.md`, decision `15-transport.adr.md`). The interview node consumes that browser interface for its preview/live surface rather than owning the transport.
- Wire the interview skill's preview/live surface to the browser interface: replace the generate-once static Preview Protocol in `src/plugins/spec-tree/skills/interview/` with consumption of the browser interface once that node is built.
- Open governance gap: the shipped static Preview Protocol (`src/plugins/spec-tree/skills/interview/references/preview-template.md` and the `SKILL.md` Preview Protocol) is not governed by any assertion in `interview.md`. Govern it or supersede it with the browser interface — per `spx/15-spec-coverage.adr.md`, shipped skill behavior carries evidence.

Browser-interface build steps: `spx/16-interfaces.enabler/21-browser.enabler/PLAN.md`.
