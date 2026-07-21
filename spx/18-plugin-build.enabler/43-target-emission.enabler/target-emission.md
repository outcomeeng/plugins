# Target Emission

PROVIDES per-coding-agent output emission with deterministic per-target translation
SO THAT the Claude Code and Codex marketplaces
CAN install plugin content from committed generated trees that match each coding agent's native conventions.

## Assertions

### Compliance

- ALWAYS: every `src/plugins/<plugin>/.../` source file produces at least one corresponding output in `dist/claude/<plugin>/` and at least one in `dist/codex/<plugin>/` — a source that emits into no target tree is a coverage gap, while a fan-out source emits once per plugin it renders for ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `dist/<target>/<plugin>/` mirrors the `src/plugins/<plugin>/` subtree structure except where the target's agent-capability registry directs an artifact elsewhere — structure follows source unless a target reads that artifact class from a different location ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: a target's native agent format, agent filename shape, and flat-versus-namespaced agent namespace resolve from a source-owned per-target agent-capability registry — adding a target adds a registry entry rather than editing emission logic ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: a generated target tree carries an agent artifact in a format that target cannot read — each target receives its own native agent artifact and no foreign one ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: `${CLAUDE_SKILL_DIR}/...` paths in source appear verbatim in `dist/claude/` output — Claude Code resolves the variable during skill execution ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: unescaped `${CLAUDE_SKILL_DIR}/...` execution paths in source appear as `${SKILL_DIR}/...` paths in `dist/codex/` output — Codex resolves bundled skill files through its skill-directory variable ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: source lines marked with the skill-directory rewrite escape emit `${CLAUDE_SKILL_DIR}` verbatim in both generated targets — authoring guidance can teach the canonical Claude Code source token while normal executable paths still translate per target ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: target-specific frontmatter fields (`disable-model-invocation` for Codex) are absent from a target that does not consume them, while portable skill capability fields such as `argument-hint` and `allowed-tools` appear in both generated runtime trees ([test](tests/test_target_emission.compliance.l1.py))
- ALWAYS: an include inside a per-target conditional emits its shared-topic sibling files only into the matching generated target, including when the conditional include is nested inside another shared fragment ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: a built output contains execution-time injection syntax that inlines sister-skill content — fan-out at build time replaces injection ([test](tests/test_target_emission.compliance.l1.py))
- NEVER: an unescaped `dist/codex/` output references `${CLAUDE_SKILL_DIR}` — Codex output uses `${SKILL_DIR}` for executable skill-directory references ([test](tests/test_target_emission.compliance.l1.py))
