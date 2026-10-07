# Changelog — instructions plugin

Instruction authoring: skill and subagent creation, and the audits that gate them.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.20.1

### Changed

- **`/skill-standards` admits one split rerun after a dangerous-command guard block on a compound command.** A block on a command whose composition the parts cannot carry — a process substitution, a pipe between two operations, a background `&`, or a subshell — ends its command family. A skill may rely on Claude running the parts of a blocked compound command of `&&`, `||`, `;` or newline joins and shell expansions again one at a time, in their original order, with every string written literally; each value resolves first (a substitution's inner command runs on its own, a variable is the literal Claude assigned or the output of `printenv <name>`, a glob is the matching entries of a listing of its literal directory, a tilde, brace or arithmetic expansion is written out as its words), a secret value is never printed or written into a command, and a part the guard blocks on its own ends that part's family. The partition into one operation, a composition the parts cannot carry, and a compound command lives in `references/command-capabilities.md` `<guard_block_partition>`. A block on one operation written entirely in literals still admits no retry. The classifier-refusal retry keeps its own condition that a skill directs it. This reverses the 0.19.1 statement that a guard block admits no retry.
- **`/skill-standards` no longer invokes the eager-foundation exception for itself.** The skill renders under the 500-line limit the exception lifts, so `<eager_foundation_exception>` covers foundation skills only.
- **`/skill-standards` states two rules without naming who loads it or where a section sits.** The reference note and the repo-local overlay read no longer describe the skills that load the standard, and `<progressive_disclosure>` names `<eager_foundation_exception>` instead of pointing below it. The caller rule admits a description that states the skill's invocation contract, such as "Loaded by other skills, not invoked directly", because behavior never depends on who the caller is.

## 0.20.0

### Breaking

- **`/audit-skill` and `/audit-subagent` take a JSON argument.** Each takes one JSON object carrying the target path and the run-driver identity in place of a bare path; a bare path, an absent object, or a malformed run-driver identity returns a `BLOCKED` diagnostic before any run starts. The `skill-auditor` and `subagent-auditor` agents supply that object from the target they receive.

### Changed

- **The skill and subagent audits record their verdicts as sealed verification runs.** `/audit-skill` and `/audit-subagent` record their scope units and findings through `spx verification run`, and return the run token with the rendered projection, whose terminal status `approved` or `rejected` is the verdict; a `blocking` or a `debt` finding rejects the run, and a refused payload or finish returns a `BLOCKED` diagnostic. `/audit-skill` records one unit for the bundle and one per bundle file; `/audit-subagent` records one unit for the definition and one per governing declaration it read. The `skill-auditor` and `subagent-auditor` agents relay the token and projection unchanged, the auditor skeleton and `/create-skill`'s auditor template admit a sealed run as the verdict format, `/create-skill` accepts a skill only on a sealed `approved` run, and `/skill-standards` admits the `spx verification run` journal verbs in an audit skill's grants.

## 0.19.3

### Changed

- **Subagent authoring offers the Executor profile.** `/subagent-standards` lists Executor among the central profiles that require an explicit governing selection, and `/create-subagent` offers `profile: executor` with its complete configuration.
- **`/create-subagent` hands back what remains to verify.** It returns the configuration path, role, emitted definitions, and outstanding verification, and names no auditor or dispatch order of its caller.
- **Codex agents name current-generation models.** The plugin's Codex agent renderings and configuration examples carry each central profile's current-generation model in place of the retired generation.

## 0.19.2

### Changed

- **Scratch an agent creates stays in place.** `/skill-standards` `<path_boundary>` requires code that creates a scratch directory — a bundled script, a hook, a test fixture — to remove it on every exit path, and forbids a skill from instructing Claude to delete scratch it created through a shell command. The `create-skill` validation list and automation template follow the same split.
- **`create-skill`'s reusability and test-pattern references open with a table of contents**, so a partial read sees every section.

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
