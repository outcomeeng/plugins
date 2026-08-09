# Changelog — prose plugin

Prose craft: external prose writing and audit, internal team docs writing and audit.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.9.1

### Changed

- **Ambiguity resolution follows the caller's interactivity.** The interactive caller asks the user to select a kind; a dispatched audit honors a dispatch-declared kind only for text the detection procedure leaves ambiguous — ownership outranks a declared kind, and each declaration binds only the part it names — and undeclared ambiguity is reported in the verdict with the plausible kinds' shared rules audited.
- **internal-docs covers team documents wherever the team keeps them** — a workspace tool or a repository. The audience test reads the reader's context, not the storage platform.
- **The audit path runs at the craft model tier** — the `prose-auditor` agent and the five composed audit skills declare the craft model (Opus on Claude Code, gpt-5.5 on Codex) instead of the mechanical-auditor tier.

### Fixed

- The generated Codex `prose-auditor` configuration declares `sandbox_mode = "read-only"`, matching every sibling auditor.
- The `prose-auditor` description names its excluded targets — chat responses, operational prose, and repository-governed artifacts — so automatic dispatch matches the kind-detection boundary.

## 0.8.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.7.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
