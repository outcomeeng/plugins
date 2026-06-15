# Browser Interface Rendering

The browser interface renders from the SPX CLI's JSON projection of the spec tree, applies the product's own vendored design system, and produces interactive HTML — drag-drop restructuring, inline commenting, expand/collapse — rather than static read-only output.

## Rationale

The spec-tree projection — structure, derived state, and the node and decision categories — is available from the SPX CLI as JSON, so the interface reads it rather than re-deriving it. Re-parsing directory suffixes or deriving state in the interface would duplicate the methodology's own engine and drift from it.

The design system is vendored — its tokens and component vocabulary copied into the plugin and owned by this product — because the plugin ships independently into consumer repositories under the portability constraints (stdlib Python, static assets, no Node build step, no runtime package fetch). A runtime dependency on another product's design system would break that independence. A separate product with its own design language shares visual heritage by copy, never by a runtime dependency.

Interactive affordances are first-class because the interface is a manipulation surface, not a read-only report: a reviewer restructures the tree and comments in place, and those interactions flow back over the transport decided in `spx/16-interfaces.enabler/21-browser.enabler/15-transport.adr.md`.

## Invariants

- Rendering is a pure function of the projection and the interaction state: the same projection and state always produce the same HTML.

## Verification

### Audit

- ALWAYS: render from the SPX CLI's JSON projection — the browser interface never re-parses directory suffixes, assembles hierarchy, or derives node state itself ([audit])
- ALWAYS: ship the design system as the product's own vendored assets — tokens and components copied into the plugin, with no runtime dependency on another product's design system ([audit])
- NEVER: add a build-time or runtime dependency for the rendering layer that violates the plugin portability constraints — stdlib Python, static HTML/CSS/JS assets, no Node build, no package fetch — per `spx/13-plugin-and-runtime-conventions.adr.md` ([audit])
