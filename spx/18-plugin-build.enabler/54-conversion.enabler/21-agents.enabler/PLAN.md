# Plan

Governing decisions: `spx/12-marketplace-state.adr.md` (marketplace state ownership) and
`spx/18-plugin-build.enabler/15-build-architecture.adr.md` (build architecture).

## Defect this plan closes

A Codex consumer of the marketplace receives skills and zero agents. `.codex-plugin/plugin.json`
declares `"skills": "./skills/"` and no agents, and the Codex runtime reads custom agents only from
`.codex/agents/*.toml`. Plugin installation already copies each plugin's `agents/` directory into the
consumer's plugin cache — verified: `~/.codex/plugins/cache/outcomeeng/spec-tree/<version>/agents/`
holds the agent markdown today — but nothing converts or places it, so `applier`,
`changes-reviewer`, and every auditor are absent and any methodology step that dispatches one fails
under Codex. Nothing in the tree governs the last mile, and the converted agents were declared
gitignored, which also leaves every hosted Codex and web Claude environment without agents because
those environments resolve committed files only.

## Target model

1. **The build emits the Codex-native artifact.** `dist/codex/<plugin>/agents/` carries
   `<plugin>_<agent>.toml`, and the agent markdown is dropped from the Codex tree.
   `dist/claude/<plugin>/agents/*.md` is Claude's native surface; custom-agent TOML is Codex's, so
   each generated tree carries only what its agent reads. Conversion is a pure function of the agent
   source, so it runs once at build time under the existing `dist/` drift gate and every consumer
   receives byte-identical agents.

2. **Naming mirrors the Claude namespace.** Codex has no namespace, so the plugin name becomes the
   slug prefix with `_` as the joiner: Claude `spec-tree:adr-auditor` renders as Codex
   `spec-tree_adr-auditor.toml`. One authored identity, two native joiners, no third invented token.
   A Codex policy whitelists the plugin-name prefixes and denies arbitrary subagent spawning; the
   prefix set is the marketplace catalog, so it derives from `.agents/plugins/marketplace.json`
   rather than being hand-maintained. Duplicate slugs can then collide only within one plugin, which
   the converter's existing duplicate-filename guard already fails the build on.

3. **Delivery rides the existing install path.** Plugin installation already carries `agents/` to the
   consumer's plugin cache, so the built TOML reaches every consumer with no new transport.

4. **The last mile places the TOML into the checkout.** `<repo>/.codex/agents/` is committed content
   so hosted Codex and web Claude — which have no plugin cache — resolve the agents from committed
   files. The SPX CLI installs and keeps that directory current in this and any consumer repo, prunes
   stale generated entries, and offers a `--check` mode the local gate and CI read for drift. This
   repository consumes that mechanism rather than special-casing itself, so the consumer path is
   exercised by the product that ships it.

5. **`agents.py` is the interim writer** until the CLI capability is published and the version floor
   advances per the `@outcomeeng/spx` dependency rule. It also installs to `CODEX_HOME` on explicit
   invocation, so the methodology's agents are available in the spx repository while that capability
   is built there.

6. **User-scope carve-out.** `spx/12-marketplace-state.adr.md`'s never-mutate-user-scope invariant
   binds marketplace *synchronization* — the implicit path. An explicitly developer-invoked install
   naming the developer's own home is a distinct authorized operation, never a default and never
   implied by sync.

## Declarations this supersedes

- `spx/12-marketplace-state.adr.md`: converted Codex custom-agent files install under the checkout's
  *gitignored* `.codex/agents/` directory.
- This node: `NEVER: agent conversion writes generated agents into published Codex plugin manifest
  content`. Generated TOML becomes published plugin *tree* content; what stays out of publication is
  the manifest declaration itself.
- `spx/18-plugin-build.enabler/54-conversion.enabler/conversion.md`: conversion outputs stay scoped to
  local installation orchestration and are not published as plugin content.

## Execution order

1. Revise `spx/12-marketplace-state.adr.md` and
   `spx/18-plugin-build.enabler/15-build-architecture.adr.md` to the target model.
2. Align this node and `spx/18-plugin-build.enabler/54-conversion.enabler/conversion.md`; align
   `spx/13-infrastructure.enabler/32-installation.enabler` for coherence over the committed set.
3. Build: emit `<plugin>_<agent>.toml` into `dist/codex/<plugin>/agents/`; drop the markdown from the
   Codex tree.
4. `agents.py`: place the built TOML into `<repo>/.codex/agents/`, support an explicit `CODEX_HOME`
   target, prune stale generated entries; un-gitignore and commit `.codex/agents/`.
5. Establish evidence through `/verify` and the selected test specialist.
6. File `/issue` into the `@outcomeeng/spx` queue for the CLI place, refresh, prune, and `--check`
   capability; retire `agents.py` once it ships and the floor advances.

The checkout-bounded sync cutover in `spx/32-distribution.enabler/21-sync.enabler` folds in: the
build produces the agents, so sync no longer installs them, and the `codex_cache` and user-scope
machinery is removed. `spx/local/merging.md` lines 89-92 describe the superseded gitignored agent
install and are corrected with it.
