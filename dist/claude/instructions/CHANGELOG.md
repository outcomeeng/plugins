# Changelog — instructions plugin

Instruction authoring: skill and subagent creation, and the audits that gate them.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.17.2

### Removed

- **The auditor-skeleton `<prose_variant>` exemption.** Every `audit-*` skill now uses `<audit_workflow>` as its procedure name; the prose auditor the exemption accommodated conforms to the skeleton directly. Removed from `skill-standards/references/auditor-skeleton.md` and from the `auditor_skeleton_violation` anti-pattern in `audit-skill` that restated it.

## 0.17.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.16.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line. This plugin was named `develop` until 2026-07-11; installations referencing `develop@outcomeeng` do not resolve.
