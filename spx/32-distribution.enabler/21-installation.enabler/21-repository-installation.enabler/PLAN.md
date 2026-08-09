# Plan: Repository Installation

## Implement agent-home delivery for Codex agent definitions

Governing decision: `spx/12-marketplace-state.adr.md`. Persistent installation places
each plugin's generated Codex agent definitions in the selected `CODEX_HOME` agents
directory beside the plugin content it installs; checkout placement is the owning
plugin lifecycle skill's explicit opt-in.

Pending implementation, in dependency order:

1. `outcomeeng/distribution/installation.py` — place each installed plugin's generated
   Codex agent definitions into `$CODEX_HOME/agents/` during persistent installation,
   within the namespace each plugin owns, pruning that namespace's stale definitions.
   The retired manifest-tracked install model (removed by commit
   `63fea7b7bc65d1c4b520bb09e0fe98ab5d06ccba`) is not restored; placement reuses the
   namespace-prefix model the lifecycle placement already uses.
2. Home-placement declaration and L2 evidence — the implementation changeset adds
   the home-placement scenario to
   `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md`
   (persistent installation places a plugin's generated definitions in the selected
   `CODEX_HOME` agents directory beside the plugin content the same run installs,
   foreign definitions untouched), routed through `/verify`, and extends the
   isolated installation harness to observe home-directory placement. Until then
   the declaration lives as the `([compliance])` rule in
   `spx/12-marketplace-state.adr.md`.
3. Generated plugin lifecycle skills — the checkout-materialization verb becomes an
   explicit opt-in; the default repair path for a missing agent role refreshes the
   selected agent home. The same slice adds the opt-in gating evidence for this
   node's checkout-placement scenario; the scenario's trigger-neutral wording is
   evidenced today by the placement-mechanics test, while the trigger policy lives
   in `spx/12-marketplace-state.adr.md` until the gate ships.
4. The managed instruction-block template's Codex agent-init instruction — rewritten
   to the home-refresh repair path with no commit guidance, recorded in
   `spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.
5. Smoke evidence that Codex discovers user-scope agents from `$CODEX_HOME/agents/`
   in tool-backed sessions, through the disposable-home harness.
