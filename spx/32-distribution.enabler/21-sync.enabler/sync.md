# Sync

PROVIDES marketplace sync orchestration bounded to the invocation checkout — detecting whether the checkout's plugin distribution content changed since a base reference and running the checkout's validation accordingly
SO THAT marketplace maintainers and CI workflows
CAN verify the checkout's plugin distribution set without mutating a developer's user-scope marketplace registrations, plugin caches, or agent directories

Sync accepts an optional base reference and detects whether the checkout's plugin distribution content changed since it, comparing the base reference against the working tree so uncommitted distribution edits are detected. Sync operates only on the invocation checkout: it verifies the checkout's plugin distribution and never reconciles a developer's user-scope marketplace registrations, refreshes their plugin caches, or repairs their agent directories, per `spx/12-marketplace-state.adr.md`.

## Assertions

### Scenarios

- Given uncommitted plugin distribution changes in the working tree since `base_ref`, when sync runs before commit, then it detects the distribution change because the change probe compares `base_ref` against the working tree rather than `HEAD` ([test](tests/test_sync.scenario.l1.py))

### Compliance

- ALWAYS: check availability of `claude`, `codex`, `ps`, and `uv` before any orchestration step — missing tools fail fast with a diagnostic rather than partway through the sequence ([test](tests/test_sync.compliance.l1.py))
- NEVER: skip any validation step when plugin distribution paths changed — every change-driven run completes the required validation or fails ([test](tests/test_sync.compliance.l1.py))
- NEVER: declare or invoke a sync step whose contract is `codex_cache_preserve`; Codex cache preservation exists only to protect user-scope state that `spx/12-marketplace-state.adr.md` removes from the toolchain's reach ([test](tests/test_sync.compliance.l1.py))
