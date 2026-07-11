# ISSUES — plugin-build / post-restructure follow-ups

Known issues left by the `src/plugins/` → `dist/` build restructure. Coordination note; not spec truth.

## 1. `spx/` spec references still cite the pre-restructure `plugins/` path

The restructure migrated `AGENTS.md` references to `src/plugins/` but left `spx/` specs and decision records citing `plugins/spec-tree/skills/...`. Spec/decision files under `spx/` still use the old `plugins/` path — enumerate the live set with `grep -rln 'plugins/spec-tree' spx/` (the bare `plugins/`, not the migrated `src/plugins/`). Several matches are spec-assertion subjects and decision-record text, not only backtick citations — for example `spx/21-spec-tree.enabler/17-audit.adr.md`, `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`, and `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`. Authored skills now live at `src/plugins/spec-tree/skills/...`; the generated output is `dist/{claude,codex}/...`. Migrate the prose references to the authored-source path. These are backtick citations, not Markdown links, so `just check` does not flag them — a deliberate repo-wide reference migration is needed, separate from any single node's work.

## 2. Codex rendering for Claude-authored argument syntax

Source skills are authored in Claude Code's supported `SKILL.md` syntax. `src/plugins/instructions/skills/skill-standards/references/command-capabilities.md` permits `$ARGUMENTS` for whole-string instruction capture and keeps `arguments` / `$name` for stable positional tokens. That source policy resolves the former skill-auditor contradiction that treated bare `$ARGUMENTS` as command-only syntax.

The remaining concern belongs to generated Codex output: when authored source uses a Claude-supported form that Codex does not consume directly, the build renderer must adapt Codex runtime output without weakening the authored source.

Audit checklist:

- Enumerate every authored skill argument form: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, declared `$name`, and `arguments`.
- Compare each generated Codex skill surface against the Codex runtime's consumed argument syntax.
- Classify each surface as works as rendered, requires build adaptation, or requires source-policy clarification.
- Preserve `$ARGUMENTS` in authored source when a skill accepts free-form multi-word instructions or forwards instructions between lifecycle skills.
- Preserve `arguments` / `$name` in authored source when a stable token boundary improves reliability for agent invocation or convenience for user invocation.
- Implement any required adaptation in the build renderer and regenerate committed runtime output.

Required handling: run the audit as a plugin-build/runtime-parameterization follow-up before editing the build. Gate any implementation with the focused runtime-parameterization tests, `just build-skills`, `just check-skills`, `just docs-check`, and the repository's merge lifecycle. Surfaced by the argument-syntax review during `feat/guide-filename-runtime-token` (2026-06-26).
