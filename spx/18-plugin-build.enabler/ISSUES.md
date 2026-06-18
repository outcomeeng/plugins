# ISSUES — plugin-build / post-restructure follow-ups

Known issues left by the `src/plugins/` → `dist/` build restructure. Coordination note; not spec truth.

## 1. `spx/` spec references still cite the pre-restructure `plugins/` path

The restructure migrated `AGENTS.md` references to `src/plugins/` but left `spx/` specs and decision records citing `plugins/spec-tree/skills/...`. Spec/decision files under `spx/` still use the old `plugins/` path — enumerate the live set with `grep -rln 'plugins/spec-tree' spx/` (the bare `plugins/`, not the migrated `src/plugins/`); 37 files match, and several are spec-assertion subjects and decision-record text, not only backtick citations — for example `spx/21-spec-tree.enabler/17-auditing.adr.md`, `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/review-changes.md`, and `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`. Authored skills now live at `src/plugins/spec-tree/skills/...`; the generated output is `dist/{claude,codex}/...`. Migrate the prose references to the authored-source path. These are backtick citations, not Markdown links, so `just check` does not flag them — a deliberate repo-wide reference migration is needed, separate from any single node's work.
