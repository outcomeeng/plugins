# Build Architecture

## Purpose

Governs the architecture of the build pipeline that transforms Claude Code-authored `src/` plugin sources into generated outputs at `dist/claude/` and `dist/codex/`.

## Context

**Business impact:** The marketplace authors plugin content for Claude Code first, then emits compatible Codex output from the same source tree. Authoring source twice doubles the maintenance burden and leaks coding-agent-specific mechanisms (Claude's `!` `cat ${CLAUDE_SKILL_DIR}/...` injection) into authoring decisions. Codex resolves bundled skill files through `${SKILL_DIR}`, so Codex path syntax must be emitted mechanically from the Claude Code-authored source token.

**Technical constraints:** All marketplace tooling is Python, managed via `uv` and `pyproject.toml`. Existing pre-commit infrastructure runs through `lefthook`. Marketplace catalogs (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`) accept arbitrary relative paths for plugin sources, so committed `dist/` trees serve as canonical install targets without install-time generation. Each coding agent's plugin manifest format differs slightly: Claude Code accepts an `allowed-tools` frontmatter field that Codex's Agent Skills schema does not recognize. Codex's multi-root skill discovery walks `$CWD/.agents/skills`, ancestors up to repo root, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, and `/etc/codex/skills`; during skill execution Codex sets `${SKILL_DIR}` to the active skill directory.

## Decision

The build is a Python module invoked via `just build-skills` and registered as a `lefthook` pre-commit hook. It uses Jinja2 with custom delimiters (`{!% %!}` and `{{! !}}`) to expand a single source tree under `src/` into committed outputs at `dist/claude/` and `dist/codex/`.

### Source layout

Plugin sources live under `src/plugins/<plugin>/` mirroring Claude Code plugin structure (`skills/`, `commands/`, `agents/`). Canonical shared content lives under `src/_shared/<scope>/<topic>/` and contains a body fragment plus any reference subtrees that travel with it.

### Output layout

Built outputs live under `dist/claude/<plugin>/` and `dist/codex/<plugin>/` mirroring the source plugin structure for each coding-agent target. Both generated trees are committed. `.claude-plugin/marketplace.json` sets `metadata.pluginRoot` to `./dist/claude`, while `.agents/plugins/marketplace.json` sets each plugin's `source.path` under `./dist/codex/`.

### Template directives

The build recognizes two directive types in source files:

- `{!% include 'path/to/file.md' %!}` — static text inlining for short shared fragments (constants, principles, sub-topics). The named file's body is inlined verbatim into the rendered output.
- `{!% require_skill 'plugin:skill-name' %!}` — emits identical coding-agent-neutral text in both targets directing the agent to invoke the named skill before proceeding. Serves as the marketplace's mechanism for sister-skill access without execution-time injection.

### Per-target translation

For each source file, the build emits two outputs whose differences are mechanical: `${CLAUDE_SKILL_DIR}/...` paths are preserved verbatim in the Claude output and rewritten to `${SKILL_DIR}/...` paths in the Codex output; Claude-only frontmatter fields (`allowed-tools`, `disable-model-invocation`, `argument-hint`) are preserved in the Claude output and stripped from the Codex output; `{!% include %!}` and `{!% require_skill %!}` directives are expanded to identical bodies in both outputs.

### Shared-content fan-out

When a consuming source includes a shared fragment, the build inlines the fragment's body into the rendered output and copies every file under the shared directory's subtree (`references/`, `levels/`, etc.) into the consumer's matching subdirectory at both `dist/claude/<plugin>/skills/<consumer>/...` and `dist/codex/<plugin>/skills/<consumer>/...`. Reference fan-out is implicit: the entire subtree of the included shared directory travels with the fragment.

### Shared content placement

Shared content (code standards, test standards, agent-prompt conventions, and similar) lives under `src/_shared/<scope>/<topic>/`. Consuming skills include the relevant fragment via `{!% include %!}`. The marketplace publishes no skills that exist solely to serve as inline targets for other skills.

### Build orchestration

`just build-skills` runs the build manually. The lefthook pre-commit hook invokes the same recipe and fails the commit when the build produces any change to `dist/`. CI runs `just build-skills && git diff --exit-code dist/` to verify in-sync output.

## Rationale

**Single source plus committed dist beats execution-time injection.** Codex uses `${SKILL_DIR}` rather than `${CLAUDE_SKILL_DIR}`, so any cross-skill content sharing must either duplicate at the source (manual sync, error-prone across 27 consuming files), bake at build time (canonical source plus fan-out), or be replaced by an "invoke this other skill" instruction. Build-time bake-out preserves a single Claude Code-authored source while emitting deterministic outputs both coding agents consume natively.

**Jinja2 over a custom regex preprocessor.** The build does fan-out, conditional frontmatter, path rewriting, and reference-tree copying across 58 source files. Custom-regex tooling grows into "Jinja2 but worse" once macros (e.g., uniformly rendering an "invoke these skills" block from a list) are needed. Jinja2 is mature, well-documented, and a small additional dependency in a Python toolchain that already uses `pyyaml` and similar text-processing libraries.

**Custom delimiters over standard Jinja2 syntax.** Standard `{% %}` and `{{ }}` collide with skill content that literally contains those character sequences (skills teaching templating, Mustache, or referencing template engines themselves). Custom delimiters (`{!% %!}` and `{{! !}}`) avoid collision with documented content patterns without requiring `{% raw %}` escape blocks throughout.

**HTML-comment directives rejected.** A `<!-- include: foo -->` syntax is readable as plain Markdown but cannot express conditionals, loops, macros, or variable interpolation cleanly. The build's per-target translation requires conditionals (different frontmatter per target), and the `require_skill` directive benefits from accepting an arbitrary list of skills. Jinja2 handles these uniformly; an HTML-comment regex preprocessor re-implements the same features ad hoc.

**Committed dist over CI-only generation.** Marketplace consumers install directly from the repo's HEAD. A CI-only build means consumers see source templates instead of resolved outputs unless every install also runs the build, which neither Claude Code's `claude plugin marketplace add` nor Codex's `codex plugin marketplace add` does. Committing dist makes installs a pure clone — reproducible, offline, and unambiguous.

**Build-time fan-out over execution-time inline targets.** Execution-time injection (`!` `cat ${CLAUDE_SKILL_DIR}/...`) inlines a multi-hundred-line file per invocation and multiplies token cost. Build-time fan-out concentrates the cost on one machine (the build), produces no execution-time injection in either output, and obviates skills whose only role is serving as inline targets. Built outputs carry no `<codex_fallback>` workaround text.

## Trade-offs accepted

| Trade-off                                                                        | Mitigation / reasoning                                                                                                                                                    |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Authoring requires running `just build-skills` to materialize dist before commit | Lefthook pre-commit hook automates this; `just build-skills` is fast on the source tree                                                                                   |
| Editing `src/_shared/<topic>/` propagates to multiple consuming skills           | This is the intended behavior; the build is the operational form of "edit one place, update everywhere"                                                                   |
| Reading `src/plugins/.../SKILL.md` requires understanding build directives       | Directive surface is small (`include`, `require_skill`, and target variables); rendered `dist/claude/.../SKILL.md` is the canonical reference for what the agent receives |
| Running CI build to verify in-sync produces an ongoing CI cost                   | The build runs in seconds; verification is cheap relative to the wrong-state risk it eliminates                                                                           |
| `dist/` doubles the repository size on disk                                      | Plugin source is text-only; the disk impact is negligible compared to the determinism and offline-install benefits                                                        |

## Compliance

### Recognized by

The repository contains a `src/` tree as the only authored plugin source, plus `dist/claude/` and `dist/codex/` trees as committed build outputs. Marketplace JSONs reference plugin paths under `dist/`. `outcomeeng/distribution/build.py` is the sole writer of `dist/` content. Lefthook pre-commit configuration runs `just build-skills` and rejects commits that leave `dist/` out of sync with `src/`.

### MUST

- Use Jinja2 with custom delimiters (`{!% %!}` and `{{! !}}`) for template processing — collision-free syntax over standard Jinja2 delimiters in the presence of meta-skill content ([review])
- Place all canonical shared content under `src/_shared/<scope>/<topic>/` — single home for each shared fragment ([review])
- Emit committed outputs into both `dist/claude/` and `dist/codex/` for every plugin published in either marketplace catalog — Claude Code is the authoring source and Codex is generated compatibility output ([review])
- Run `just build-skills` from a lefthook pre-commit hook that fails the commit when `dist/` would change — stale dist is the failure mode this ADR exists to prevent ([review])
- Trace every committed `dist/` file to a `src/` ancestor through the build — no orphan dist content ([review])

### NEVER

- Edit `dist/claude/` or `dist/codex/` by hand — the build is the only writer; manual edits desynchronize the source-output contract ([review])
- Use `!` `cat ${CLAUDE_SKILL_DIR}/...` execution-time injection in built output — shared content reaches both coding-agent outputs via build-time fan-out ([review])
- Emit unescaped `${CLAUDE_SKILL_DIR}` references into `dist/codex/` outputs — Codex output uses `${SKILL_DIR}` for executable skill-directory references; source lines carrying the skill-directory rewrite-escape directive are the explicit exception, so authoring-guidance content can teach the canonical Claude Code source token in both generated targets ([review])
- Add separate ADRs for individual build concerns (template engine, source layout, output layout, orchestration) — these decisions are interdependent and belong in this single ADR ([review])
- Distribute downstream-repo content from `plugins/` — `distribute_skills.py` reads from `dist/claude/`, the canonical home of Claude Code plugin content ([review])
