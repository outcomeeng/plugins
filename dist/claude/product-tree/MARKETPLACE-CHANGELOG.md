# Marketplace Changelog

Events that no single plugin owns: an agent harness gained or dropped, a plugin added, removed, or renamed, a floor that moves across plugins.

This file ships with the `product-tree` plugin, which carries the methodology every other plugin operationalizes.

One other changelog line runs on its own clock: what changed in a **plugin** is in that plugin's own `CHANGELOG.md`.

The marketplace carries no version of its own — each plugin is versioned independently — so entries here are dated rather than numbered.

## 2026-10-24

### Breaking

- **The `spec-tree` plugin is renamed to `product-tree`.** Every reference to `spec-tree@outcomeeng` stops resolving. Re-install as `product-tree@outcomeeng`: update any project-scoped `.claude/settings.json` naming the old identity for Claude Code, and re-install into the selected `$CODEX_HOME` for Codex. The Claude Code catalog now maps the retired id to its successor in its `renames` map, and the README section "Upgrading from spec-tree" names the step for each place a consumer's setup can still name `spec-tree`: the installed plugin, project activation, the repository instruction blocks, and the Codex agent registry. Its skills carry over under the `product-tree:` namespace, and the language and craft plugins name that namespace from their releases of this date. The methodology the marketplace delivers is named Product Tree.

## 2026-07-18

### Added

- **`coding-agents` plugin.** Coordination between coding agents running in parallel worktrees: recipient discovery, bounded delegation with correlated handbacks, and Prowl pane operation.

## 2026-07-11

### Breaking

- **The `develop` plugin is renamed to `instructions`.** Every reference to `develop@outcomeeng` stops resolving. Re-install as `instructions@outcomeeng`: update any project-scoped `.claude/settings.json` naming the old identity for Claude Code, and re-install into the selected `$CODEX_HOME` for Codex. Its skills — skill authoring, subagent authoring, and their audits — carry over unchanged.

## 2026-05-26

### Changed

- **Plugins ship from generated runtime trees.** A plugin now carries exactly what its target harness can read, rather than one shared layout serving both.

## 2026-04-20

### Added

- **Codex harness support.** The marketplace publishes a second catalog alongside the Claude Code catalog, and shared plugins ship both manifests. Codex registration and installation belong to the selected `$CODEX_HOME`, through `codex plugin marketplace add outcomeeng/plugins` and `codex plugin add`. A repository's own `.codex/config.toml` carries no plugin installation or enablement semantics.

## 2026-01-05

### Added

- **The marketplace.** Initial catalog, Claude Code only.
