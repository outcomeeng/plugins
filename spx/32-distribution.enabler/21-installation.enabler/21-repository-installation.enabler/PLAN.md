# Plan: Repository Installation

## Implement agent-home delivery for Codex agent definitions

Governing decision: `spx/12-marketplace-state.adr.md`. A plugin's agent definitions
live in the same scope as the skill content they invoke: persistent installation
places each plugin's generated Codex agent definitions in the selected `CODEX_HOME`
agents directory beside the skills it installs, a checkout carries them only where
it also carries the invoked skill content, and a scope split is a reported fault.

Pending implementation, in dependency order:

1. The co-location delivery slice. The plugin's shipped placement entry point
   (`scripts/place_agents.py` in each plugin's generated tree) is repointed from
   the invocation checkout to co-located delivery: it derives its destination
   from where the plugin's skill content lives, placing home-installed plugins'
   generated Codex agent definitions into `$CODEX_HOME/agents/`, within the
   namespace each plugin owns, pruning that namespace's stale definitions. The
   operation ships inside the plugin, so an ordinary consumer without this
   repository's toolchain receives agents from the plugin itself;
   `outcomeeng/distribution/installation.py` drives the same shipped entry point
   in bulk during the maintainers' persistent installation. The retired
   manifest-tracked install model (removed by commit
   `63fea7b7bc65d1c4b520bb09e0fe98ab5d06ccba`) is not restored. The home is a shared
   directory, so the checkout's bare `<plugin>_` prefix is not ownership proof there:
   home placement must establish an ownership boundary that cannot claim a foreign
   agent whose filename happens to share a plugin prefix — a marketplace-scoped
   ownership record or content marker checked before any prune or overwrite, with a
   colliding foreign file reported and left untouched. Cross-plugin cleanup is a distinct
   marketplace-scope reconciliation, separate from the plugin's
   namespace-bounded placement so both of the governing decision's rules hold:
   a plugin's placement verb creates, replaces, and prunes only within its own
   namespace, while the reconciliation pass acts under the marketplace's
   recorded ownership — the authority the decision grants agent-home placement
   — over the whole ownership set. The reconciler identifies stale definitions
   against the refreshed marketplace registration's current plugin set in the
   selected home — catalog state the home itself carries after a marketplace
   refresh, needing neither repository catalog access nor an installed-plugin
   heuristic — so definitions the marketplace placed for a plugin since removed
   or renamed in `.agents/plugins/marketplace.json` are pruned on the next
   shipped-operation run. No shipped surface can intercept the agent CLI's own
   marketplace or plugin refresh commands, and `spx/15-hook-safety.pdr.md` bars
   subprocess-bearing hooks, so the reconciliation rides every entry-point
   invocation instead of a refresh event: any plugin's placement run, any
   missing-role repair, and the maintainers' bulk installation each run their
   namespace-bounded placement and then the marketplace-scope reconciliation
   pass. A removed plugin's definitions therefore persist only until the next
   such invocation, inert and bounded by the ownership record, never
   indefinitely. The same slice removes
   the automatic checkout `LIFECYCLE_PLACE` step from installation runs — checkout
   materialization holds only where the checkout carries the plugin's invoked
   skill content — and updates the release documentation in `spx/local/merging.md` that
   describes the run, the third stale instruction surface beside the two templates
   the later items name. Repointing the entry point also retires the checkout
   output the repository declares generated: the same slice updates the
   `.codex/agents/**` relation in `spx/local/generated-sources.toml` and the
   `place-agents` / `place-agents-check` Justfile recipes that invoke the
   script with `--checkout .` and gate CI on checkout output, and it aligns
   `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md`
   — whose placement compliance rules bound pruning by slug prefix alone —
   with the decision's marketplace-scoped ownership-record,
   foreign-collision, and scope-split detection assertions and their evidence,
   so the placement node cannot stay passing on prefix-only behavior the
   shared home forbids or on placement that refreshes around a shadowing
   checkout definition. The
   same slice ships the decision's scope-split fault
   detection as a preflight beside the home ownership and collision
   validation: both run before any marketplace or plugin mutation in a run, so
   no refresh advances the home skills while a committed definition still
   shadows them, and no run advances skills whose agent placement it will then
   reject over a foreign collision. Plugin-owned definitions committed
   in a checkout whose invoked skills live in the selected agent home —
   including definitions placed under the retired required-placement router
   guidance — are reported as the fault with their directed repair, removal of
   the committed copies, never silently refreshed, pruned, or left shadowing
   the home copy. Legacy checkout copies predate any ownership marker, so the
   preflight classifies them by content, never by filename prefix alone: a
   file byte-identical to a definition the plugin ships is plugin-placed and
   receives the removal repair, while a file matching no shipped content —
   edited, renamed, or developer-authored — is reported as an ambiguous
   collision for operator review with the shadowing consequence named, never
   prescribed for removal; in both cases the run stops rather than refreshing
   around the split. This repository's own 14 committed `.codex/agents/*.toml`
   files are the first detected instance: their removal lands inside this
   slice, after home delivery is in place, because removing them earlier would
   leave Codex sessions without those roles while nothing yet populates
   `$CODEX_HOME/agents/`. Detection is per invocation checkout by design: a
   foreign checkout's committed copy shadows only that repository's own
   sessions and surfaces through this same preflight when any shipped
   operation runs there, so every affected repository self-detects on its next
   operation, and no shipped operation inspects a checkout it was not invoked
   in.
2. Home-placement declaration and L2 evidence — the implementation changeset adds
   the home-placement scenario to
   `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md`
   (persistent installation places a plugin's generated definitions in the selected
   `CODEX_HOME` agents directory beside the plugin content the same run installs,
   foreign definitions untouched), routed through `/verify`, and extends the
   isolated installation harness to observe home-directory placement. Until then
   the declaration lives as the `([compliance])` rule in
   `spx/12-marketplace-state.adr.md`.
3. Generated plugin lifecycle skills — each plugin's `<plugin>-plugin` skill
   becomes the consumer invocation of the entry point item 1 repoints: its
   placement verb executes the shipped operation, deriving the destination from
   co-location, so an ordinary consumer session populates `$CODEX_HOME/agents/`
   by running the plugin's own skill. A home write is a mutation outside the
   invocation checkout, so the verb names the absolute agent-home destination
   and proceeds only under the confirmation the external-write policy in
   `spx/43-instructions.enabler/21-skills.enabler/skills.md` requires — the
   harness approval prompt for the out-of-checkout write is that confirmation,
   never suppressed by a tool grant. Checkout materialization runs only where
   the checkout carries the plugin's invoked skill content, and the verb reports
   the scope split otherwise. The default repair path for a missing agent role
   refreshes the selected agent home — running the plugin's placement verb where
   the definitions are absent — and then reloads the harness plugin index or
   starts a new session, because a running session retains already-loaded plugin
   content. The entry-point repointing and the scope-split fault detection ship
   earlier, with the delivery slice above. The same slice
   rewrites the commit-directing Codex guidance in the authored lifecycle-skill
   template `src/templates/plugin/SKILL.md` ("durable checkout configuration …
   Commit them"), which renders into every plugin's `<plugin>-plugin` skill;
   with the managed instruction-block template in the next item, these are the
   two generated instruction surfaces carrying that guidance. The same slice adds
   the co-location gating evidence for this node's checkout-materialization
   scenario;
   the scenario's trigger-neutral wording is evidenced today by the
   placement-mechanics test, while the trigger policy lives in
   `spx/12-marketplace-state.adr.md` until the gate ships.
4. The managed instruction-block template's Codex agent-init instruction — rewritten
   to the home-refresh-and-reload repair path with no commit guidance, recorded in
   `spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`. The
   rewritten guidance also carries the scope-split recognition into every
   consumer session: a rendered router that finds committed plugin-owned agent
   definitions whose invoked skills are home-installed names them as the
   decision's scope-split fault and directs the repair at instruction-load
   time, so a repository whose shadow arose from a refresh elsewhere surfaces
   the fault on its next session rather than waiting for a placement run
   there. The same
   slice declares that behavior in the owning spec: `spx/21-spec-tree.enabler/43-instruction-block.enabler/instruction-block.md`
   gains the assertion, with its evidence, that the rendered router's agent-repair
   guidance names the home-refresh-and-reload path and carries no
   commit-directing guidance, so the node cannot stay passing while a rendered
   router contradicts `spx/12-marketplace-state.adr.md`.
5. Smoke evidence that Codex discovers user-scope agents from `$CODEX_HOME/agents/`
   in tool-backed sessions, through the disposable-home harness.
