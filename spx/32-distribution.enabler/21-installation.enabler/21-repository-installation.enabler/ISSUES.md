# Issues: Repository Installation

## The installation-architecture invariant contradicts agent-home delivery

`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md`
asserts "Every lifecycle placement destination resolves beneath the invocation
checkout." as a committed invariant, and its compliance rule binds lifecycle
placement to the invocation checkout. `spx/12-marketplace-state.adr.md` decides
that agent definitions installation delivers land in the selected agent home's
agent directory, with checkout materialization the owning plugin lifecycle
skill's explicit opt-in. The two committed decisions contradict each other about
where lifecycle placement lands while the architecture amendment waits for the
slice that changes the architecture.

**Resolution shape**: `PLAN.md` item 1 in this node — scope the invariant and
its compliance rule to the opt-in checkout-materialization path through
`/author` with the `adr-auditor` gate, landing with the implementation slice.
Until that slice ships, the architecture decision describes the shipped
checkout-materialization implementation only, and `spx/12-marketplace-state.adr.md`
governs where installation-delivered agent definitions land.

**Evidence.** Surfaced by the current-head integration review of the changeset
amending `spx/12-marketplace-state.adr.md` (PR #511).
