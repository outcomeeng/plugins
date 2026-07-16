# Plan

Governing decision: `spx/15-marketplace-state.adr.md` (marketplace state ownership).

Pending narrowing: this node's compliance assertion names `~/.codex/agents/` (user-scope) as
a valid install destination for converted Codex custom-agents. Under the ADR, converted
agents live under the checkout's `.codex/agents/`, and the user-scope destination is
superseded. Narrow the `~/.codex/agents/` clause to the checkout-scoped `.codex/agents/` in
the same cutover that removes user-scope installation (the production cutover of
`just sync-marketplace`). The spec re-declaration travels with that impl removal, not with the
decision-declaration slice.
