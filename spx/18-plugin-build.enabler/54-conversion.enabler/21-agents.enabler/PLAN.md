# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Pending implementation: `spx/12-marketplace-state.adr.md` declares that converted Codex
custom-agent files are written under the checkout's `.codex/agents/`. This node's compliance
assertion is scoped to what its linked test verifies — that agent conversion never writes generated
agents into the published Codex plugin manifest content. The node does not assert an install
destination: `tests/test_agents.compliance.l1.py` installs to a harness-chosen target root and never
exercises `DEFAULT_TARGET_ROOT`, which still resolves under the user home. The conversion writer and
test must be reconciled to write and verify only the checkout-scoped destination, dropping any
user-scope install path; that impl and test reconciliation travels with the production cutover of
`just sync-marketplace`, at which point the node declares the checkout-scoped install guarantee the
decision governs.
