# Changelog — coding-agents plugin

Coding-agent environments and coordination: Prowl pane operation, recipient discovery, bounded delegation, and cross-worktree coordination.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.6.1

### Fixed

- **Production requests use source-generated handback commands.** Callers provide semantic completion text, and `/operate-prowl` returns one structured block whose command ends at `run`, carries checked submission criteria, and cannot gain a stray trailing argument during prompt assembly.

## 0.6.0

### Breaking

- **`/message-agents` requests require `recipientPath`.** Supply the recipient's absolute worktree, repository, or working-directory path. A previous `toPane` value remains an optional identity assertion and is no longer sufficient by itself.

### Added

- **Path-based Prowl target resolution.** `/operate-prowl` maps an operator-supplied work path to complete matching agent-pane metadata and candidate-specific send request templates.

## 0.5.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.4.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
