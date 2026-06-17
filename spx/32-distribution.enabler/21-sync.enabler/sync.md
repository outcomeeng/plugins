# Sync

PROVIDES the marketplace sync orchestration that refreshes installed plugins and validates their integrity when plugin distribution paths change since a reference commit
SO THAT marketplace maintainers and CI workflows
CAN refresh local Claude and Codex installations and verify the installed plugin set without re-running irrelevant tooling when no distribution paths changed

The `outcomeeng.distribution.sync` module accepts an optional base reference, detects whether plugin distribution paths (`src/`, `dist/`, `.claude-plugin/`, `.agents/plugins/`) changed since that reference, and on changes invokes the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, and installed-skill checks in order. The Codex local-source refresh verifies that Claude Code and Codex share the same local `outcomeeng` marketplace source, refreshes installed Codex plugins from `dist/codex`, and runs cache compatibility repair after the per-plugin refresh.

## Assertions

### Scenarios

- Given no plugin distribution changes since `base_ref`, when sync runs, then it exits 0 without invoking marketplace mutations ([test](tests/test_sync.scenario.l1.py))
- Given plugin distribution changes since `base_ref`, when sync runs, then it invokes — in order — the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, and installed-skill checks ([test](tests/test_sync.scenario.l1.py))
- Given uncommitted plugin distribution changes in the working tree since `base_ref`, when sync runs before commit, then it still invokes the full marketplace sync sequence because the change probe compares `base_ref` against the working tree rather than `HEAD` ([test](tests/test_sync.scenario.l1.py))

### Compliance

- ALWAYS: check availability of `claude`, `codex`, and `uv` before any orchestration step — missing tools fail fast with a diagnostic rather than partway through the sequence ([test](tests/test_sync.compliance.l1.py))
- NEVER: skip any validation step when plugin distribution paths changed — every change-driven run completes the full sequence or fails ([test](tests/test_sync.compliance.l1.py))
- NEVER: declare or invoke a sync step whose contract is `codex_cache_preserve`; Codex refresh is the local-source step governed by the installation ADR ([test](tests/test_sync.scenario.l1.py))
