# Build Orchestration

PROVIDES the build's runtime integration with the development workflow and marketplace catalogs
SO THAT plugin authors and marketplace consumers
CAN run the build deterministically and install from the committed runtime trees.

## Assertions

### Compliance

- ALWAYS: `just build-skills` invokes the build, regenerating `dist/claude/` and `dist/codex/` from `src/` — single canonical recipe ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: the lefthook pre-commit hook runs the build and fails the commit when `dist/` would change — stale dist is the failure mode this hook exists to prevent ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: `.claude-plugin/marketplace.json` references plugin sources under `dist/claude/` — Claude Code installs from the committed Claude runtime tree ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: `.agents/plugins/marketplace.json` references plugin sources under `dist/codex/` — Codex installs from the committed Codex runtime tree ([test](tests/test_build_orchestration.compliance.l1.py))
