# Changelog — spec-tree plugin

Spec Tree methodology skills and agents: `/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`, `/apply`, `/verify`, the audit family, and the merge lifecycle.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

This plugin delivers the methodology but is versioned separately from it. What changed in the **methodology** is in `METHODOLOGY-CHANGELOG.md` beside this file — a methodology release keeps its identity regardless of which plugin version delivers it.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.86.2

### Changed

- **`[review]` is no longer tolerated as a spelling of `[audit]`.** The foundation described it as the legacy spelling of the `[audit]` assertion tag. That description is gone: the assertion tags are `[test]`, `[eval]`, and `[audit]`, and review is an open-ended changeset gate that backs no assertion tag. An assertion still carrying `([review])` now reports an invalid tag under `/audit-specs`, and `/audit-tests` no longer lists it among the tags it skips. Migrate `([review])` to `([audit])` — the assertion text is unchanged, only the tag spelling.

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports the marketplace, plugin, and methodology changelog paths. Each is read from disk, without network access.
- **`METHODOLOGY-CHANGELOG.md` ships beside this file.** What changed in the **methodology** is recorded separately from what changed in this plugin, because a methodology release keeps its identity regardless of which plugin version delivers it.

This changelog begins here; earlier history predates the line.
