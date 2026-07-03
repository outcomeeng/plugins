# Sync

PROVIDES the marketplace sync orchestration that reconciles runtime marketplace configuration, refreshes installed plugins, and validates their integrity when plugin distribution paths or repaired runtime configuration require it
SO THAT marketplace maintainers and CI workflows
CAN refresh local Claude and Codex installations and verify the installed plugin set without leaving runtime configuration drift to manual repair

Sync accepts an optional base reference, reconciles Claude Code and Codex `outcomeeng` marketplace registrations to the default-branch worktree root as the canonical local source, detects whether plugin distribution content or Codex agent converter code changed since that reference, and runs marketplace refresh, Codex agent installation, install validation, installed-skill checks, and final Codex local-source refresh when distribution content or converter code changed or source reconciliation repaired runtime configuration.

The final Codex local-source refresh repairs cache drift caused by Codex CLI reads during install validation and installed-skill checks, and runs in strict current-cache mode so an incomplete final current cache entry fails sync.

## Assertions

### Scenarios

- Given no plugin distribution changes since `base_ref`, source reconciliation reports no runtime configuration repair, and the Codex cache topology is healthy, when sync runs, then it exits 0 after source reconciliation and topology inspection without invoking marketplace refresh mutations ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref`, source reconciliation reports no runtime configuration repair, and the Codex cache topology is invalid, when sync runs, then it invokes the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, installed-skill checks, and final Codex local-source refresh ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref`, source reconciliation reports no runtime configuration repair, the Codex cache topology is invalid, and another sync owns the active repair, when sync runs, then it records pending state and exits 0 without invoking marketplace refresh mutations ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref`, source reconciliation reports no runtime configuration repair, the Codex cache topology is invalid, and the active repair lock is stale because its owner process is absent, when sync runs, then it replaces the stale lock and invokes the full marketplace refresh sequence ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref`, source reconciliation reports no runtime configuration repair, and the Codex cache topology check cannot read installed Codex plugin versions, when sync runs, then it exits non-zero before invoking marketplace refresh mutations ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref` and source reconciliation repairs runtime configuration, when sync runs, then it invokes — in order — the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, installed-skill checks, and final Codex local-source refresh ([test](tests/test_sync.scenario.l1.py))
- Given multiple linked worktrees and exactly one checkout attached to the default branch, when sync resolves the canonical marketplace source, then it selects the default-branch worktree rather than a feature worktree ([test](tests/test_sync.scenario.l1.py))
- Given plugin distribution or Codex agent converter changes since `base_ref`, when sync runs, then it reconciles source configuration and invokes — in order — the Claude marketplace update, Codex local-source refresh, Codex agent installation, install validation, installed-skill checks, and final Codex local-source refresh ([test](tests/test_sync.scenario.l1.py))
- Given plugin distribution changes since `base_ref` and rendered Claude agents exist, when sync runs, then it installs converted Codex custom-agent files before installed-plugin validation runs ([test](tests/test_sync.scenario.l1.py))
- Given no plugin distribution changes since `base_ref`, source reconciliation repairs runtime configuration, and another sync owns the active refresh, when sync runs, then it exits non-zero without invoking marketplace refresh mutations because configuration repair cannot skip required validation ([test](tests/test_sync.scenario.l1.py))
- Given plugin distribution changes since `base_ref` and another sync owns the active refresh, when sync runs, then it exits non-zero without invoking marketplace refresh mutations because change-driven sync cannot skip required validation ([test](tests/test_sync.scenario.l1.py))
- Given uncommitted plugin distribution changes in the working tree since `base_ref`, when sync runs before commit, then it still invokes the full marketplace sync sequence because the change probe compares `base_ref` against the working tree rather than `HEAD` ([test](tests/test_sync.scenario.l1.py))

### Compliance

- ALWAYS: check availability of `claude`, `codex`, and `uv` before any orchestration step — missing tools fail fast with a diagnostic rather than partway through the sequence ([test](tests/test_sync.compliance.l1.py))
- ALWAYS: reconcile runtime marketplace source configuration before consulting the distribution-change probe — configuration drift is repaired even when plugin files did not change ([test](tests/test_sync.compliance.l1.py))
- NEVER: skip any validation step when plugin distribution paths changed — every change-driven run completes the full sequence or fails ([test](tests/test_sync.compliance.l1.py))
- NEVER: declare or invoke a sync step whose contract is `codex_cache_preserve`; Codex refresh is the local-source step governed by `spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md` ([test](tests/test_sync.compliance.l1.py))
