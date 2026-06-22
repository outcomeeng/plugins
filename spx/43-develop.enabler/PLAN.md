# PLAN — Retire command tooling; fold command capabilities into the skills cluster

**Status:** ready for a fresh session. Delete this file when the work lands.

## Why

`spx/13-plugin-and-runtime-conventions.adr.md` decides the skill is the marketplace's sole user-facing invocation artifact and "carries every command capability"; authoring a `commands/*.md` is forbidden, and no plugin ships one. So the develop plugin's command tooling — `create-commands`, `audit-commands`, and the `command-auditor` agent — authors and audits a forbidden artifact: a lower layer contradicting the ADR.

Skills already carry the command capabilities — `skill-standards` documents `argument-hint`, `allowed-tools`, `disable-model-invocation` (the user-only-command case), `!`-backtick dynamic context, and arguments — but `audit-skills` does not audit that surface: its `yaml_frontmatter` area checks only `name` and `description`. So a skill can wield command-power that nothing audits.

## Outcome

- `create-commands`, `audit-commands`, and the `command-auditor` agent are removed from the develop plugin, from `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and the README catalog.
- The still-live command-capability checks fold into the skills cluster: `audit-skills` gains evaluation areas for argument usage (`$ARGUMENTS`/positional and integration), `!`-dynamic-context safety, `allowed-tools`/tool-restriction security, and `argument-hint`; `create-skills` teaches authoring those capabilities. `skill-standards` stays the single source of the rules.
- No `/command-standards` is created — commands are not a supported artifact.

## Steps

1. `/understand`, then `/contextualize spx/43-develop.enabler/21-skills.enabler`.
2. Read `audit-commands` and `create-commands` to enumerate the capability checks and authoring guidance worth preserving: argument usage and integration, `!`-dynamic-context safety, `allowed-tools` tool-restriction security, `argument-hint`, `@` file references. Read `skill-standards/references/runtime-variables.md` for the exact skill-side variable / `$ARGUMENTS` mapping.
3. Fold those into `audit-skills` (new evaluation areas + anti-patterns) and `create-skills` (authoring guidance). Do not restate rules already in `skill-standards`; add any genuinely new shared rule there.
4. Remove `create-commands`, `audit-commands`, and the `command-auditor` agent. Drop them from both marketplace catalogs and the README catalog. Sweep references: `audit-commands`'s `require_skill 'create-commands'`, develop `develop.md` / `21-skills.enabler/skills.md` enumerations, and any cross-reference elsewhere (`grep -rn 'create-commands\|audit-commands\|command-auditor'`).
5. `just build-skills`, bump develop, gate `audit-skills` and `create-skills` with `develop:skill-auditor`, `just check`, `/merge`.

## Sequencing — THIS lands BEFORE the auditor-skeleton sweep

This work and the marketplace-wide auditor-skeleton structural sweep (its own session) both edit the `audit-skills` / `create-skills` surface. **Command removal + capability fold merges first.** Running the skeleton sweep's develop portion first forces a second edit of `audit-skills` / `create-skills` when this lands — touching the same files twice and rebasing one effort over the other. The skeleton session's develop portion waits on this; its spec-tree and language portions (which do not touch `audit-skills` / `create-skills`) are independent.

## Verification

- No `commands/` artifact and no `create-commands` / `audit-commands` / `command-auditor` remain anywhere; `just check` (`validate_plugins`) passes with both catalogs consistent and the README catalog regenerated (`just docs`).
- `audit-skills` audits the command-capability surface (argument usage, `!`-dynamic-context, tool-restriction security, `argument-hint`); `skill-standards` remains the sole rule source (no rule duplicated).
- `develop:skill-auditor` passes on `audit-skills` and `create-skills`.
