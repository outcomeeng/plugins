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
   `63fea7b7bc65d1c4b520bb09e0fe98ab5d06ccba`) is not restored. The home is a shared
   directory, so the checkout's bare `<plugin>_` prefix is not ownership proof there:
   home placement must establish an ownership boundary that cannot claim a foreign
   agent whose filename happens to share a plugin prefix — a marketplace-scoped
   ownership record or content marker checked before any prune or overwrite, with a
   colliding foreign file reported and left untouched. Reconciliation covers the
   marketplace's whole ownership set, not only current catalog plugins: definitions
   the marketplace placed for a plugin since removed or renamed in
   `.agents/plugins/marketplace.json` are pruned by the same ownership record, so a
   catalog removal does not strand stale home definitions. The same slice removes
   the automatic checkout `LIFECYCLE_PLACE` step from installation runs — checkout
   placement moves behind the owning lifecycle skill's opt-in — and updates the
   release documentation in `spx/local/merging.md` that describes the run, the
   third stale instruction surface beside the two templates the later items name.
   Because a checkout's product-scope definitions shadow the user-scope copies in
   the selected agent home, the same slice also ships the ownership-aware checkout
   migration: detect plugin-owned checkout definitions the repository did not opt
   into — definitions placed under the retired required-placement router guidance
   — and direct their removal, so no intermediate release leaves a stale committed
   copy shadowing the refreshed home copy.
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
   selected agent home and then reloads the harness plugin index or starts a new
   session, because a running session retains already-loaded plugin content. The
   checkout-shadow migration ships earlier, with the home-delivery slice above.
   The same slice
   rewrites the commit-directing Codex guidance in the authored lifecycle-skill
   template `src/templates/plugin/SKILL.md` ("durable checkout configuration …
   Commit them"), which renders into every plugin's `<plugin>-plugin` skill;
   with the managed instruction-block template in the next item, these are the
   two generated instruction surfaces carrying that guidance. The same slice adds the opt-in gating evidence for this
   node's checkout-placement scenario; the scenario's trigger-neutral wording is
   evidenced today by the placement-mechanics test, while the trigger policy lives
   in `spx/12-marketplace-state.adr.md` until the gate ships.
4. The managed instruction-block template's Codex agent-init instruction — rewritten
   to the home-refresh-and-reload repair path with no commit guidance, recorded in
   `spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.
5. Smoke evidence that Codex discovers user-scope agents from `$CODEX_HOME/agents/`
   in tool-backed sessions, through the disposable-home harness.
