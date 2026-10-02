# Changelog — instructions plugin

Instruction authoring: skill and subagent creation, and the audits that gate them.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.19.2

### Changed

- **Scratch an agent creates stays in place.** `/skill-standards` `<path_boundary>` requires code that creates a scratch directory — a bundled script, a hook, a test fixture — to remove it on every exit path, and forbids a skill from instructing Claude to delete scratch it created through a shell command. The `create-skill` validation list and automation template follow the same split.

## 0.19.1

### Changed

- **`/skill-standards` admits one retrace-bound retry after an automated classifier's refusal.** A skill may direct one retry of a request the operator's instruction already authorized, only after Claude retraces the request, the classifier's reason, and the steps that shaped it, and only with the correction the retrace found. A permission prompt or a guard block still admits no retry.
- **Audit skills grant only the read-only Bash verb patterns their workflow runs**, never bare `Bash`, so the frontmatter rule matches the narrowest-grant rule in the command-capabilities reference.

### Fixed

- **The variable-scope hook example is a guarded command** with a kill switch, a floor, and a timeout, as the hook reference requires.

## 0.17.3

### Changed

- **Hook guidance names the agent-published session identity.** `skill-standards`'s `plugin-hooks.md` reference states that Claude Code publishes `$CLAUDE_CODE_SESSION_ID` to every Bash tool call — and that Pi's Claude-Code-compatible surface publishes the same variable alongside its own `$PI_SESSION_ID` — so a skill reads identity directly and never installs a hook to synthesize it. The `SessionStart` + `$CLAUDE_ENV_FILE` example now propagates a payload value the agent does not publish, and the per-agent identity table covers Claude Code, Pi, and Codex.

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
