# Plan: Repository Installation

## Implement agent-home delivery for Codex agent definitions

Governing decision: `spx/12-marketplace-state.adr.md`. A plugin's agent definitions
live in the same scope as the skill content they invoke: persistent installation
places each plugin's generated Codex agent definitions in the selected `CODEX_HOME`
agents directory beside the skills it installs, a checkout carries them only where
it also carries the invoked skill content, and a scope split is a reported fault.

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
   placement holds only where the checkout carries the plugin's invoked skill
   content — and updates the release documentation in `spx/local/merging.md` that
   describes the run, the third stale instruction surface beside the two templates
   the later items name. The same slice ships the decision's scope-split fault
   detection: plugin-owned definitions committed in a checkout whose invoked
   skills live in the selected agent home — including definitions placed under the
   retired required-placement router guidance — are reported as the fault with
   their directed repair, removal of the committed copies, never silently
   refreshed, pruned, or left shadowing the home copy.
2. Home-placement declaration and L2 evidence — the implementation changeset adds
   the home-placement scenario to
   `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md`
   (persistent installation places a plugin's generated definitions in the selected
   `CODEX_HOME` agents directory beside the plugin content the same run installs,
   foreign definitions untouched), routed through `/verify`, and extends the
   isolated installation harness to observe home-directory placement. Until then
   the declaration lives as the `([compliance])` rule in
   `spx/12-marketplace-state.adr.md`.
3. Generated plugin lifecycle skills — checkout materialization gates on
   co-location, reading the checkout itself: it runs only where the checkout
   carries the plugin's invoked skill content, and it reports the scope split
   otherwise. The default repair path for a missing agent role refreshes the
   selected agent home and then reloads the harness plugin index or starts a new
   session, because a running session retains already-loaded plugin content. The
   scope-split fault detection ships earlier, with the home-delivery slice above.
   The same slice
   rewrites the commit-directing Codex guidance in the authored lifecycle-skill
   template `src/templates/plugin/SKILL.md` ("durable checkout configuration …
   Commit them"), which renders into every plugin's `<plugin>-plugin` skill;
   with the managed instruction-block template in the next item, these are the
   two generated instruction surfaces carrying that guidance. The same slice adds
   the co-location gating evidence for this node's checkout-placement scenario;
   the scenario's trigger-neutral wording is evidenced today by the
   placement-mechanics test, while the trigger policy lives in
   `spx/12-marketplace-state.adr.md` until the gate ships.
4. The managed instruction-block template's Codex agent-init instruction — rewritten
   to the home-refresh-and-reload repair path with no commit guidance, recorded in
   `spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.
5. Smoke evidence that Codex discovers user-scope agents from `$CODEX_HOME/agents/`
   in tool-backed sessions, through the disposable-home harness.
