# Plugin Build

PROVIDES single-source authoring of plugin files with deterministic per-runtime emission for Claude Code and Codex
SO THAT plugin authors and the marketplace
CAN maintain skills, commands, and agents as one canonical source while delivering runtime-specific outputs each agent runtime consumes.

## Assertions

### Compliance

- ALWAYS: every src plugin source file produces exactly one corresponding output in `dist/claude/` and one in `dist/codex/` — a coverage gap means a plugin is missing from a runtime ([test](tests/test_plugin_build.compliance.l1.py))
- NEVER: a built output contains runtime-injection syntax that inlines sister-skill content — fan-out at build time replaces injection ([test](tests/test_plugin_build.compliance.l1.py))
- NEVER: a `dist/codex/` output references `${CLAUDE_SKILL_DIR}` or other Claude Code-specific environment variables — Codex provides no equivalent and references must be rewritten ([test](tests/test_plugin_build.compliance.l1.py))
- NEVER: a `dist/` file lacks a corresponding `src/` ancestor traceable through the build — every committed runtime artifact is a build product ([test](tests/test_plugin_build.compliance.l1.py))

### Properties

- Build determinism: same `src/` content always produces byte-identical `dist/claude/` and `dist/codex/` outputs across machines and time ([test](tests/test_plugin_build.property.l1.py))
- Build idempotence: running the build twice in succession produces no changes on the second run ([test](tests/test_plugin_build.property.l1.py))
