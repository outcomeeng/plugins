# Plan: browser interface

Anchors the work to realize the browser interface. Reconcile against `browser.md`, `13-rendering.adr.md`, `15-transport.adr.md`, `spx/12-shipped-scripting.adr.md`, the prototypes, and current intent before acting.

- Vendor the product's own design system — copy the OKLCH token set and component vocabulary from the `levenate-vision.html` / `levenate-tree.html` prototypes into the `interfaces` plugin as static assets; keep it independent of the Levenate product.
- Build the rendering layer — render the SPX CLI's JSON projection (and live interaction state) into interactive HTML with drag-drop reordering, click-to-comment, and expand/collapse. Reference fidelity: the two `levenate-*.html` prototypes.
- Keep shipped plugin scripting simple per `spx/12-shipped-scripting.adr.md`: the MCP launch glue and HTML-emitting glue ship as standalone Python scripts in the `interfaces` plugin's `scripts/`.
- The state-management core (`prototypes/interview-live/state.py` — monotonic rev, journal, interaction lifecycle, tree integrity) is complex, test-bearing, and unproven. Per `spx/12-shipped-scripting.adr.md` it does NOT ship as a heavy plugin script: it stays a prototype until the browser interface proves itself, then its complexity extracts into the SPX CLI (tested there, consumed as a trusted third-party component). The browser interface then consumes that capability over the SPX JSON projection rather than carrying the core in-plugin.
- Under `/test`, decide the evidence home for `browser.md`'s rendering/affordance assertions once the rendering glue exists, and remove the EXCLUDE entry when implementation lands.

Source spike: `prototypes/interview-live/` (commit `10c9a062`, PR #112). Design prototypes: `levenate-vision.html` and `levenate-tree.html` in the `outcomeeng/levenate` repository (reference only — Levenate is a separate product).
