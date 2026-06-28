# Target Emission

PROVIDES per-coding-agent output emission with deterministic per-target translation
SO THAT the Claude Code and Codex marketplaces
CAN install plugin content from committed generated trees that match each coding agent's native conventions.

## Assertions

### Compliance

- ALWAYS: every `src/plugins/<plugin>/.../` source file produces exactly one corresponding output in `dist/claude/<plugin>/` and one in `dist/codex/<plugin>/` — a coverage gap means a plugin is missing from a coding-agent output tree ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `dist/<target>/<plugin>/` mirrors the `src/plugins/<plugin>/` subtree structure for both generated targets — output structure follows source structure ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `${CLAUDE_SKILL_DIR}/...` paths in source appear verbatim in `dist/claude/` output — Claude Code resolves the variable during skill execution ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: unescaped `${CLAUDE_SKILL_DIR}/...` execution paths in source appear as `${SKILL_DIR}/...` paths in `dist/codex/` output — Codex resolves bundled skill files through its skill-directory variable ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: source lines marked with the skill-directory rewrite escape emit `${CLAUDE_SKILL_DIR}` verbatim in both generated targets — authoring guidance can teach the canonical Claude Code source token while normal executable paths still translate per target ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: target-specific frontmatter fields (`disable-model-invocation` for Codex) are absent from a target that does not consume them, while portable skill capability fields such as `argument-hint` and `allowed-tools` appear in both generated runtime trees ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: a built output contains execution-time injection syntax that inlines sister-skill content — fan-out at build time replaces injection ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: an unescaped `dist/codex/` output references `${CLAUDE_SKILL_DIR}` — Codex output uses `${SKILL_DIR}` for executable skill-directory references ([test](tests/test_target_emission.compliance.l1.py))
