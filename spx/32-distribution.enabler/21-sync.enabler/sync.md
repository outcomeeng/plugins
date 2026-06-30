# Sync

PROVIDES the marketplace sync orchestration that reconciles runtime marketplace configuration, refreshes installed plugins, and validates their integrity when plugin distribution paths or repaired runtime configuration require it
SO THAT marketplace maintainers and CI workflows
CAN refresh local Claude and Codex installations and verify the installed plugin set without leaving runtime configuration drift to manual repair

The `outcomeeng.distribution.sync` module accepts an optional base reference, reconciles the Claude Code and Codex `outcomeeng` marketplace registrations to the default-branch worktree root as the canonical local source, detects whether plugin distribution paths (`src/`, `dist/`, `.claude-plugin/`, `.agents/plugins/`) changed since that reference, and invokes the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, a final Codex local-source refresh, and installed-skill checks when distribution files changed or source reconciliation repaired runtime configuration. The Codex local-source refresh installs generated Codex plugins from `dist/codex` and runs cache compatibility repair after the per-plugin refresh. The final Codex local-source refresh repairs cache drift caused by Codex CLI reads that occur during install validation and runs in strict current-cache mode so an incomplete final current cache entry fails sync before installed-skill checks.

## Assertions

### Scenarios

- Given no plugin distribution changes since `base_ref` and source reconciliation reports no runtime configuration repair, when sync runs, then it exits 0 after source reconciliation without invoking marketplace refresh mutations ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref` and source reconciliation repairs runtime configuration, when sync runs, then it invokes — in order — the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, final Codex local-source refresh, and installed-skill checks ([test](tests/test_sync.scenario.l1.py))
- Given multiple linked worktrees and exactly one checkout attached to the default branch, when sync resolves the canonical marketplace source, then it selects the default-branch worktree rather than a feature worktree ([test](tests/test_sync.scenario.l1.py))
- Given plugin distribution changes since `base_ref`, when sync runs, then it reconciles source configuration and invokes — in order — the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, final Codex local-source refresh, and installed-skill checks ([test](tests/test_sync.scenario.l1.py))
- Given uncommitted plugin distribution changes in the working tree since `base_ref`, when sync runs before commit, then it still invokes the full marketplace sync sequence because the change probe compares `base_ref` against the working tree rather than `HEAD` ([test](tests/test_sync.scenario.l1.py))

### Compliance

- ALWAYS: check availability of `claude`, `codex`, and `uv` before any orchestration step — missing tools fail fast with a diagnostic rather than partway through the sequence ([test](tests/test_sync.compliance.l1.py))
- ALWAYS: reconcile runtime marketplace source configuration before consulting the distribution-change probe — configuration drift is repaired even when plugin files did not change ([test](tests/test_sync.scenario.l1.py))
- NEVER: skip any validation step when plugin distribution paths changed — every change-driven run completes the full sequence or fails ([test](tests/test_sync.compliance.l1.py))
- NEVER: declare or invoke a sync step whose contract is `codex_cache_preserve`; Codex refresh is the local-source step governed by the installation ADR ([test](tests/test_sync.scenario.l1.py))
