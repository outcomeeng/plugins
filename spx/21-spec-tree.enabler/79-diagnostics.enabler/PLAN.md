# Plan

Governing decision: `spx/15-marketplace-state.adr.md` (marketplace state ownership).

Pending re-declaration: make marketplace-install diagnosis product-scoped — derive expected
plugin state from the checkout's per-runtime project declarations, and remove `expected_plugins`
from the shipped diagnose manifest. Update
`spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md` accordingly.

Dependency (BLOCKING for the implementation slice): a published `@outcomeeng/spx` release must
first provide the revised diagnose manifest schema and marketplace-install classification.
Advance `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and the CI `SPX_VERSION`
pin in `.github/workflows/check.yml` to that published version before implementing. The
spec re-declaration itself carries no unpublished-dependency gate.
