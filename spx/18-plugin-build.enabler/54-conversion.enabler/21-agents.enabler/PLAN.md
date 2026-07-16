# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Pending implementation: this node's compliance assertion now declares that converted Codex
custom-agents install under the checkout's `.codex/agents/`; the user-scope `~/.codex/agents/`
destination is superseded per the ADR and removed from the spec. The conversion writer and
`tests/test_agents.compliance.l1.py` must be reconciled to write and verify only the
checkout-scoped destination, dropping any user-scope install path. That impl and test
reconciliation travels with the production cutover of `just sync-marketplace`, not with this
decision-declaration slice.
