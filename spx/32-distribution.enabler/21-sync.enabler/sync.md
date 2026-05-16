# Sync

PROVIDES the marketplace sync orchestration that refreshes installed plugins and validates their integrity when plugin distribution paths change since a reference commit
SO THAT marketplace maintainers and CI workflows
CAN refresh local Claude and Codex installations and verify the installed plugin set without re-running irrelevant tooling when no distribution paths changed

The `outcomeeng.distribution.sync` module accepts an optional base reference, detects whether plugin distribution paths (`plugins/`, `.claude-plugin/`, `.agents/plugins/`) changed since that reference, and on changes invokes the Claude marketplace update, Codex cache preservation, install validation, and installed-skill checks in order.

## Assertions

### Scenarios

- Given no plugin distribution changes since `base_ref`, when sync runs, then it exits 0 without invoking marketplace mutations ([test](tests/test_sync.scenario.l1.py))
- Given plugin distribution changes since `base_ref`, when sync runs, then it invokes — in order — the Claude marketplace update, Codex cache preservation, install validation, and installed-skill checks ([test](tests/test_sync.scenario.l1.py))

### Compliance

- ALWAYS: check availability of `claude`, `codex`, and `uv` before any orchestration step — missing tools fail fast with a diagnostic rather than partway through the sequence ([test](tests/test_sync.compliance.l1.py))
- NEVER: skip any validation step when plugin distribution paths changed — every change-driven run completes the full sequence or fails ([test](tests/test_sync.compliance.l1.py))
