# Plugin Build

PROVIDES single-source authoring of plugin files with deterministic per-runtime emission for Claude Code and Codex
SO THAT plugin authors and the marketplace
CAN maintain skills, commands, and agents as one canonical source while delivering runtime-specific outputs each agent runtime consumes.

## Assertions

### Compliance

- ALWAYS: every committed file under `dist/` traces to a `src/` ancestor through the build — every committed runtime artifact is a build product ([test](tests/test_plugin_build.compliance.l1.py))

### Properties

- Build determinism: same `src/` content always produces byte-identical `dist/claude/` and `dist/codex/` outputs across machines and time ([test](tests/test_plugin_build.property.l1.py))
- Build idempotence: running the build twice in succession produces no changes on the second run ([test](tests/test_plugin_build.property.l1.py))
