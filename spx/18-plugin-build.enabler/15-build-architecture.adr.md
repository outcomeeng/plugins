# Build Architecture

The build is a Python module invoked via `just build-skills` and registered as a `lefthook` pre-commit hook, using Jinja2 with custom delimiters (`{!% %!}` and `{{! !}}`) to expand a single source tree under `src/` into committed outputs at `dist/claude/` and `dist/codex/`. Plugin sources live under `src/plugins/<plugin>/` mirroring Claude Code plugin structure; canonical shared content lives under `src/_shared/<scope>/<topic>/`. For each source file the build emits two outputs whose differences are mechanical: `${CLAUDE_SKILL_DIR}` paths are preserved in the Claude output and rewritten to `${SKILL_DIR}` in the Codex output, Claude-only frontmatter fields (`allowed-tools`, `disable-model-invocation`, `argument-hint`) are stripped from the Codex output, and `{!% include %!}` and `{!% require_skill %!}` directives expand to identical bodies in both. `outcomeeng/distribution/build.py` is the sole writer of `dist/`, and the lefthook hook fails any commit that leaves `dist/` out of sync with `src/`.

## Rationale

A single source plus committed `dist/` beats execution-time injection: Codex resolves bundled files through `${SKILL_DIR}` rather than `${CLAUDE_SKILL_DIR}`, so cross-skill sharing must either duplicate at the source, bake at build time, or be replaced by an "invoke this skill" instruction — build-time bake-out keeps one authored source while emitting deterministic outputs both coding agents consume natively. Jinja2 over a custom regex preprocessor because the build does fan-out, conditional frontmatter, path rewriting, and reference-tree copying that custom tooling grows into "Jinja2 but worse". Custom delimiters because standard `{% %}` collides with skill content that teaches templating. Committed `dist/` over CI-only generation because consumers install directly from HEAD and neither coding agent runs a build at install time. Build-time fan-out over execution-time `!`cat`` injection because injection inlines a multi-hundred-line file per invocation and multiplies token cost.

## Verification

### Testing

- ALWAYS: every committed `dist/` file traces to a `src/` ancestor through the build — no orphan dist content ([compliance])

### Audit

- ALWAYS: use Jinja2 with custom delimiters (`{!% %!}` and `{{! !}}`) for template processing — collision-free syntax in the presence of meta-skill content ([audit])
- ALWAYS: place all canonical shared content under `src/_shared/<scope>/<topic>/` — a single home for each shared fragment ([audit])
- ALWAYS: emit committed outputs into both `dist/claude/` and `dist/codex/` for every plugin published in either marketplace catalog ([audit])
- ALWAYS: run `just build-skills` from a lefthook pre-commit hook that fails the commit when `dist/` would change — stale dist is the failure mode this decision prevents ([audit])
- NEVER: edit `dist/claude/` or `dist/codex/` by hand — the build is the only writer; manual edits desynchronize the source-output contract ([audit])
- NEVER: use `!`cat ${CLAUDE_SKILL_DIR}/...`` execution-time injection in built output — shared content reaches both outputs via build-time fan-out ([audit])
- NEVER: emit unescaped `${CLAUDE_SKILL_DIR}` references into `dist/codex/` outputs — Codex output uses `${SKILL_DIR}`; source lines carrying the rewrite-escape directive are the explicit exception ([audit])
- NEVER: add separate ADRs for individual build concerns (template engine, source layout, output layout, orchestration) — these decisions are interdependent and belong in this single ADR ([audit])
- NEVER: distribute downstream-repo content from `plugins/` — `distribute_skills.py` reads from `dist/claude/`, the canonical home of Claude Code plugin content ([audit])
