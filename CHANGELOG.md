# Marketplace Changelog

Events that no single plugin owns: an agent harness gained or dropped, a plugin added, removed, or renamed, a floor that moves across plugins.

Two other changelog lines run on their own clocks. What changed in the **methodology** is in `src/plugins/spec-tree/METHODOLOGY-CHANGELOG.md`. What changed in a **plugin** is in that plugin's own `CHANGELOG.md`.

The marketplace carries no version of its own — each plugin is versioned independently — so entries here are dated rather than numbered.

## 2026-07-18

### Added

- **`coding-agents` plugin.** Coordination between coding agents running in parallel worktrees: recipient discovery, bounded delegation with correlated handbacks, and Prowl pane operation.

## 2026-07-11

### Breaking

- **The `develop` plugin is renamed to `instructions`.** Every reference to `develop@outcomeeng` stops resolving. Re-install as `instructions@outcomeeng` and update any product-scoped `.claude/settings.json` or `.codex/config.toml` that names the old identity. Its skills — skill authoring, subagent authoring, and their audits — carry over unchanged.

## 2026-05-26

### Changed

- **Plugins ship from generated runtime trees.** Authored sources live under `src/plugins/`; the installed trees under `dist/claude/` and `dist/codex/` are generated from them. Consumers install from the generated trees, so a plugin now carries exactly what its target harness can read.

## 2026-04-20

### Added

- **Codex harness support.** The marketplace publishes a second catalog at `.agents/plugins/marketplace.json` alongside the Claude Code catalog at `.claude-plugin/marketplace.json`. Shared plugins ship both manifests, and Codex registration is user-scoped through `codex plugin marketplace add outcomeeng/plugins`, with per-product enablement committed in `.codex/config.toml`.

## 2026-01-05

### Added

- **The marketplace.** Initial catalog, Claude Code only.
