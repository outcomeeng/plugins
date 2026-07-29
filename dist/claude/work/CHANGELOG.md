# Changelog — work plugin

Work deliverables: Excalidraw diagrams and PowerPoint deck cleanup.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.8.0

### Changed

- **A methodology-changelog request is directed to `spx.config.yaml`.** No installed plugin carries a methodology changelog, and the lifecycle skill no longer offers one. A repository declares the methodology version it follows in its own `spx.config.yaml`; `help` directs the reader to that declaration and the source it names.

## 0.7.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
