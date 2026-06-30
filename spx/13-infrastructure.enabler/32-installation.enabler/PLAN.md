# Installation Continuation Plan

## Cache Topology Health

PR #390 (`https://github.com/outcomeeng/plugins/pull/390`, head `5e8fa4354935e5356ed831430b82cd0ddf767794`) adds a final strict Codex local refresh after install validation. Build the next installation slice on top of that interface.

Observable path:

- Invocation: `uv run python -m outcomeeng.validation.install outcomeeng`
- Input state: Codex reports an installed `outcomeeng` plugin version, the configured local marketplace source publishes the same version, and `~/.codex/plugins/cache/outcomeeng/<plugin>/` contains version paths.
- Behavior: validation checks Codex cache topology as one invariant rather than separate checks for target existence, real-directory count, entry completeness, and symlink age.
- Required topology:
  - The target version is a complete real plugin root.
  - Every non-target version path is a symlink.
  - Every non-target symlink resolves directly to the target version directory.
  - Every present non-target real directory is an error.
- Inspection surface: validation errors name the plugin, target version, offending path, and actual symlink target or real directory state.

Acceptance evidence:

- Add test evidence for a cache that contains only a newer non-target real directory while the target version is absent.
- Add test evidence for a cache whose target version is real but compatibility symlinks point at an older real directory.
- Replace the existing Codex validation checks in `outcomeeng/validation/install.py` with one topology helper that produces those errors.
- Reuse the topology helper from `outcomeeng/distribution/codex_cache.py` strict mode after PR #390, so post-refresh strictness checks the full invariant, not only missing-current state.
- Run `just test spx/13-infrastructure.enabler/32-installation.enabler/tests/test_validate_install.scenario.l1.py spx/13-infrastructure.enabler/32-installation.enabler/tests/test_codex_plugin_cache.scenario.l1.py`.

Parallelization rule:

- This slice can proceed in parallel with PR #390 only if it targets the same final-refresh command-line interface (`--strict-current-cache`) and avoids editing the same lines until PR #390 merges.
- If PR #390 changes the strict-mode result shape, rebase this plan onto the merged interface before editing implementation.
