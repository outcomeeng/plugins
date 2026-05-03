# Target Emission

PROVIDES per-runtime output emission with deterministic per-target translation
SO THAT the Claude Code and Codex marketplaces
CAN install plugin content from committed runtime trees that match each runtime's native conventions.

## Assertions

### Compliance

- ALWAYS: every `src/plugins/<plugin>/.../` source file produces exactly one corresponding output in `dist/claude/<plugin>/` and one in `dist/codex/<plugin>/` — a coverage gap means a plugin is missing from a runtime ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `dist/<runtime>/<plugin>/` mirrors the `src/plugins/<plugin>/` subtree structure for both runtimes — output structure follows source structure ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `${CLAUDE_SKILL_DIR}/...` paths in source appear verbatim in `dist/claude/` output — Claude Code resolves the variable at runtime ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `${CLAUDE_SKILL_DIR}/...` paths in source appear as relative paths in `dist/codex/` output — Codex provides no equivalent variable ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: Claude-only frontmatter fields (`allowed-tools`, `disable-model-invocation`, `argument-hint`) appear in `dist/claude/` output and are absent from `dist/codex/` output — Codex's Agent Skills schema does not recognize them ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: a built output contains runtime-injection syntax that inlines sister-skill content — fan-out at build time replaces injection ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: a `dist/codex/` output references `${CLAUDE_SKILL_DIR}` — Codex has no equivalent environment variable and references must be rewritten ([test](tests/test_target_emission.compliance.l1.py))
