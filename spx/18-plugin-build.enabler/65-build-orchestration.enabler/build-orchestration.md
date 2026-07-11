# Build Orchestration

PROVIDES the build's integration with the development workflow and marketplace catalogs
SO THAT plugin authors and marketplace consumers
CAN run the build deterministically and install from the committed generated trees.

## Assertions

### Scenarios

- Given `dist/` differs from the build output and `src/plugins/` carries matching uncommitted edits, when the dist-diff drift reporter runs, then it lists the drifting `dist/` paths, names the change as the expected pre-commit state to commit alongside `src/`, and exits non-zero — never a raw unified diff ([test](tests/test_build_orchestration.scenario.l1.py))
- Given `dist/` differs from the build output and `src/plugins/` has no uncommitted edits, when the dist-diff drift reporter runs, then it lists the drifting `dist/` paths, reports the drift with a `just build-skills` rebuild remediation, and exits non-zero ([test](tests/test_build_orchestration.scenario.l1.py))
- Given the formatter executable is unavailable, when the build formatter boundary runs, then it reports the missing formatter by command name without spawning a child process ([test](tests/test_build_orchestration.scenario.l1.py))
- Given the formatter executable reports failure, when the build formatter boundary runs, then it reports the formatter's diagnostic output through the build error ([test](tests/test_build_orchestration.scenario.l1.py))

### Compliance

- ALWAYS: `just build-skills` invokes the build, regenerating `dist/claude/` and `dist/codex/` from `src/` — single canonical recipe ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: `just codex-local` regenerates `dist/codex/`, prepares checkout-local plugin and custom-agent state, and launches Codex with that state, so a development session reads the checkout being built rather than a user-installed marketplace version ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: the lefthook pre-commit hook runs the build and fails the commit when `dist/` would change — stale dist is the failure mode this hook exists to prevent ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: the gate dist-diff step and the lefthook pre-commit drift check both invoke the actionable drift reporter rather than a raw `git diff --exit-code` — one drift-report shape across both surfaces ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: `.claude-plugin/marketplace.json` references plugin sources under `dist/claude/` — Claude Code installs from the committed Claude Code output tree ([test](tests/test_build_orchestration.compliance.l1.py))
- ALWAYS: `.agents/plugins/marketplace.json` references plugin sources under `dist/codex/` — Codex installs from the committed Codex output tree ([test](tests/test_build_orchestration.compliance.l1.py))
