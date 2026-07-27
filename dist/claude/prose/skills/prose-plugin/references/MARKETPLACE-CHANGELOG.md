# Marketplace Changelog

Events that no single plugin owns: an agent harness gained or dropped, a plugin added, removed, or renamed, a floor that moves across plugins.

This file is identical in every installed Outcome Engineering plugin. It ships in all of them because a marketplace event has to stay readable whatever subset of plugins a repository installs — a plugin rename is unreadable from the renamed plugin, whose old identity no longer resolves.

Two other changelog lines run on their own clocks. What changed in a **plugin** is in that plugin's own `CHANGELOG.md`. What changed in the **methodology** is in `METHODOLOGY-CHANGELOG.md`, which ships with the spec-tree plugin that provides it.

The marketplace carries no version of its own — each plugin is versioned independently — so entries here are dated rather than numbered.

## 2026-07-18

### Added

- **`coding-agents` plugin.** Coordination between coding agents running in parallel worktrees: recipient discovery, bounded delegation with correlated handbacks, and Prowl pane operation.

## 2026-07-11

### Breaking

- **The `develop` plugin is renamed to `instructions`.** Every reference to `develop@outcomeeng` stops resolving. Re-install as `instructions@outcomeeng` and update any product-scoped `.claude/settings.json` or `.codex/config.toml` that names the old identity. Its skills — skill authoring, subagent authoring, and their audits — carry over unchanged.

## 2026-05-26

### Changed

- **Plugins ship from generated runtime trees.** Authored sources live under `src/plugins/`; the installed trees are generated from them. A plugin now carries exactly what its target harness can read.

## 2026-04-20

### Added

- **Codex harness support.** The marketplace publishes a second catalog alongside the Claude Code catalog, and shared plugins ship both manifests. Codex registration is user-scoped through `codex plugin marketplace add outcomeeng/plugins`, with per-product enablement committed in `.codex/config.toml`.

## 2026-01-05

### Added

- **The marketplace.** Initial catalog, Claude Code only.
