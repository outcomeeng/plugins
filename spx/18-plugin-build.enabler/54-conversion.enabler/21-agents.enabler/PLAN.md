# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Pending implementation: `spx/12-marketplace-state.adr.md` declares that converted Codex
custom-agent files are written under the checkout's `.codex/agents/`. This node's compliance
assertion is scoped to what its linked test verifies — that agent conversion never writes generated
agents into the published Codex plugin manifest content, and that custom agents install through
local Codex configuration under `.codex/agents/`. The conversion writer's `DEFAULT_TARGET_ROOT`
still resolves under the user home, and `tests/test_agents.compliance.l1.py` does not yet exercise
the install destination. The writer and test must be reconciled to write and verify only the
checkout-scoped destination, dropping any user-scope install path; that impl and test reconciliation
travels with the production cutover of `just sync-marketplace`, at which point the assertion tightens
to the checkout-scoped guarantee the decision declares.
