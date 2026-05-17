# Installation

PROVIDES local plugin marketplace installation and update support for developer machines
SO THAT Codex and Claude Code users working from this repository
CAN refresh installed plugins without breaking active sessions or local tool state

## Assertions

### Scenarios

- Given a plugin's manifest has been published to two distinct versions on the marketplace branch within the last ten days and the Codex plugin cache contains only the latest version directory, when the marketplace cache preservation step executes, then the older published version path resolves to a symlink pointing at the current version directory ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin's manifest published a version more than ten days ago and that version path appears as a symlink in the Codex plugin cache, when the marketplace cache preservation step executes, then the out-of-window symlink is removed ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin directory exists in the Codex plugin cache and no corresponding manifest exists in the working tree, when the marketplace cache preservation step executes, then the entire cache directory for that orphaned plugin is removed ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin's manifest is committed at two distinct versions within the configured time window in the marketplace repository's git history, when the preservation step's published-versions provider runs against that repository, then it returns both versions including the current working-tree version regardless of whether older commits are reachable through follow-rename ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a real (non-symlink) directory exists at a plugin version path that falls outside the preservation window, when the preservation step runs, then the directory is left in place — preservation manages symlinks only and never removes real version directories ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin's manifest is present in the working tree but the plugin's cache directory does not exist (the plugin is not installed in this user's Codex), when the preservation step runs, then the plugin is skipped silently — preservation cannot act on a plugin Codex has never installed, and the operator does not need a diagnostic about a non-issue ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin's cache directory exists but contains no real version directory (an unexpected state — Codex installs the current version as a real directory), when the preservation step runs, then the plugin is reported in the result's skipped set so the operator's diagnostic surfaces the unexpected condition ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given the CLI is invoked as `python -m outcomeeng.distribution.codex_cache <marketplace>` from within the marketplace repository working tree, when the CLI runs, then the resulting symlink set on disk reflects each working-tree plugin's manifest history within the configured window — the working tree is the source the CLI consults regardless of the invoking shell's earlier `cd` history ([test](tests/test_codex_plugin_cache.scenario.l2.py))
- Given a working-tree plugin manifest declares a newer version than the Codex marketplace clone's published manifest for the same plugin, when validate_install runs, then the absence of the newer version in the Codex cache is reported as a warning that names the plugin and both versions, and the script exits zero ([test](tests/test_validate_install.scenario.l1.py))
- Given a plugin directory exists in either the Claude Code or Codex plugin cache and no manifest exists for that plugin in the working tree, when validate_install runs, then the orphan is reported as a warning that names the plugin, and the script exits zero ([test](tests/test_validate_install.scenario.l1.py))

### Properties

- Pre-state independence: same git history of the working-tree manifests and same working-tree plugin set always produce the same post-run cache state, regardless of the cache directory contents observed before the preservation step runs ([test](tests/test_codex_plugin_cache.property.l1.py))

### Compliance

- ALWAYS: marketplace sync and direct-publish wrappers refresh installed plugins only when the published range changes plugin distribution files under `plugins/`, `.claude-plugin/`, or `.agents/plugins`; spec-only and escape-hatch-only commits do not refresh marketplace caches ([review])
- NEVER: derive the preservation set from a pre-upgrade cache snapshot — the set is always computed from current repository state (git history of the working-tree manifest for Codex, cache directory listing for Claude) and the working-tree's current published version, never from observed cache state ([review])
