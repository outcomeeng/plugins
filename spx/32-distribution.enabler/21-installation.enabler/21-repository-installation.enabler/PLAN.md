# Plan: Repository Installation

## Implement agent-home delivery for Codex agent definitions

Governing decision: `spx/12-marketplace-state.adr.md`. Persistent installation places
each plugin's generated Codex agent definitions in the selected `CODEX_HOME` agents
directory beside the plugin content it installs; checkout placement is the owning
plugin lifecycle skill's explicit opt-in.

Pending implementation, in dependency order:

1. `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/21-installation-architecture.adr.md`
   — scope the checkout-destination architecture to the opt-in materialization path:
   the invariant "Every lifecycle placement destination resolves beneath the
   invocation checkout" and the compliance rule binding lifecycle placement to the
   invocation checkout describe the checkout-materialization opt-in only, distinct
   from the `CODEX_HOME` agent-home placement `spx/12-marketplace-state.adr.md`
   introduces. The invariant holds for the current implementation until the home
   path ships, so this amendment lands with the slice that changes the
   architecture, through `/author` with its `adr-auditor` gate.
2. `outcomeeng/distribution/installation.py` — place each installed plugin's generated
   Codex agent definitions into `$CODEX_HOME/agents/` during persistent installation,
   within the namespace each plugin owns, pruning that namespace's stale definitions.
   The retired manifest-tracked install model (removed by commit
   `63fea7b7bc65d1c4b520bb09e0fe98ab5d06ccba`) is not restored. The home is a shared
   directory, so the checkout's bare `<plugin>_` prefix is not ownership proof there:
   home placement must establish an ownership boundary that cannot claim a foreign
   agent whose filename happens to share a plugin prefix — a marketplace-scoped
   ownership record or content marker checked before any prune or overwrite, with a
   colliding foreign file reported and left untouched. Reconciliation covers the
   marketplace's whole ownership set, not only current catalog plugins: definitions
   the marketplace placed for a plugin since removed or renamed in
   `.agents/plugins/marketplace.json` are pruned by the same ownership record, so a
   catalog removal does not strand stale home definitions.
3. Home-placement declaration and L2 evidence — the implementation changeset adds
   the home-placement scenario to
   `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md`
   (persistent installation places a plugin's generated definitions in the selected
   `CODEX_HOME` agents directory beside the plugin content the same run installs,
   foreign definitions untouched), routed through `/verify`, and extends the
   isolated installation harness to observe home-directory placement. Until then
   the declaration lives as the `([compliance])` rule in
   `spx/12-marketplace-state.adr.md`.
4. Generated plugin lifecycle skills — the checkout-materialization verb becomes an
   explicit opt-in; the default repair path for a missing agent role refreshes the
   selected agent home and then reloads the harness plugin index or starts a new
   session, because a running session retains already-loaded plugin content. The same slice adds the opt-in gating evidence for this
   node's checkout-placement scenario; the scenario's trigger-neutral wording is
   evidenced today by the placement-mechanics test, while the trigger policy lives
   in `spx/12-marketplace-state.adr.md` until the gate ships.
5. The managed instruction-block template's Codex agent-init instruction — rewritten
   to the home-refresh-and-reload repair path with no commit guidance, recorded in
   `spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.
6. Smoke evidence that Codex discovers user-scope agents from `$CODEX_HOME/agents/`
   in tool-backed sessions, through the disposable-home harness.
