# ISSUES — plugin-build / post-restructure follow-ups

Known issues left by the `src/plugins/` → `dist/` build restructure. Escape hatch; not spec truth.

## 1. `just build-skills` can emit a partial `dist/` with exit 0

A `just build-skills` run dropped three `dist/claude/` outputs whose `src/plugins/` sources exist — `hdl/skills/reviewing-systemverilog/SKILL.md`, its `references/systemverilog-idioms.md`, and `typescript/skills/coding-typescript/SKILL.md` — exiting 0 with an empty log; the matching `dist/codex/` outputs were kept. An immediate re-run re-emitted all three, and the next pre-commit rebuild was clean. `outcomeeng/distribution/build.py` documents itself as deterministic, so a partial emit that still succeeds is a reliability defect: it can leave a partial `dist/` that `dist-diff` only catches when a later clean build runs. Investigate the claude-vs-codex emission path for a race or a silent per-skill skip.

## 2. `spx/` spec references still cite the pre-restructure `plugins/` path

The restructure migrated `AGENTS.md` references to `src/plugins/` but left `spx/` specs and decision records citing `plugins/spec-tree/skills/...`. 21 spec/decision files under `spx/` still use the old `plugins/` path — including `spx/15-agent-pr-authority.pdr.md`, `spx/16-evidence-execution-lanes.adr.md`, `spx/15-audit-verdict-format.pdr.md`, and the reviewing node specs. Authored skills now live at `src/plugins/spec-tree/skills/...`; the shipped runtime is `dist/{claude,codex}/...`. Migrate the prose references to the authored-source path. These are backtick citations, not Markdown links, so `just check` does not flag them — a deliberate repo-wide reference migration is needed, separate from any single node's work.
