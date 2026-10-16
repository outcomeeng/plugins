# Changelog — python plugin

Python engineering: coding, testing, architecture, and the matching concern audits.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

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

### Changed

- **`/author-python-architecture` references keep only product conventions.** The reference files drop general Python typing, security, testing, and domain-design teaching and keep the dependency-injection, Protocol, subprocess-boundary, test-infrastructure, and strict-typing rules an ADR states. The skill loads `spec-tree:verify`, `python:author-python-test`, and `spec-tree:author` by name when it needs them.

- **`/python-code-standards` states only the rules.** The skill drops its caller-conditioned overlay check and its pointer to `/audit-python-code`, and removes the general explanations of builtin shadowing and bare `except`. The `spx/local/python.md` overlay check applies in any repository, and the ruff and mypy rule codes carry the remaining rules unchanged.

## 0.24.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.23.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
