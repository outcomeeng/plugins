# Changelog — python plugin

Python engineering: coding, testing, architecture, and the matching concern audits.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.25.1

### Changed

- **`/python-architecture-standards` and `/author-python-architecture` instruct each `### Audit` rule to carry the tag `[audit:{rule-slug}]`, with a slug unique within the ADR.** An ADR written from either skill carries the tag the spec-tree ADR template writes and `/audit-adr` accepts. The example ADR rules in both skills and in the architecture references now carry `[audit:{rule-slug}]` with a distinct slug per rule, and `/author-python-code` checks audit-routed requirements against the `([audit:{rule-slug}])` form. Before this change, both skills instructed the pathless `[audit]` tag under `### Audit`, and their examples and the code-skill check used it.

## 0.25.0

### Breaking

- **Five skills take `{role}-{type}` names.** The installed name is the only selector, so it now states the skill's role and whole type. Invoke each skill by its new name; no alias answers to the old one, and behavior is unchanged.

  | Old name              | New name                      |
  | --------------------- | ----------------------------- |
  | `/code-python`        | `/author-python-code`         |
  | `/test-python`        | `/author-python-test`         |
  | `/architect-python`   | `/author-python-architecture` |
  | `/audit-python-tests` | `/audit-python-test`          |
  | `/python-standards`   | `/python-code-standards`      |

  `/audit-python-code`, `/audit-python-architecture`, `/python-test-standards`, and `/python-architecture-standards` keep their names. A plugin or instruction that selects a language skill through the `audit-{lang}-{code|test|architecture}` or `author-{lang}-{code|test|architecture}` template matches the new names.

## 0.24.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.23.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
