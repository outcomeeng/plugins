# Installation

PROVIDES local plugin marketplace installation and update support for developer machines
SO THAT Codex and Claude Code users working from this repository
CAN refresh installed plugins without breaking active sessions or local tool state

## Assertions

### Scenarios

- Given a plugin's manifest has been published to two distinct versions on the marketplace branch within the last ten days and the Codex plugin cache contains only the latest version directory, when the marketplace cache preservation step executes, then the older published version path resolves to a symlink pointing at the current version directory ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin's manifest published a version more than ten days ago and that version path appears as a symlink in the Codex plugin cache, when the marketplace cache preservation step executes, then the out-of-window symlink is removed ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin directory exists in the Codex plugin cache and no corresponding manifest exists in the working tree, when the marketplace cache preservation step executes, then the entire cache directory for that orphaned plugin is removed ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin manifest exists in the working tree and no directory exists for that plugin in the local Codex plugin cache, when the marketplace cache preservation step executes, then no warning is emitted and the script exits zero ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a working-tree plugin manifest declares a newer version than the Codex marketplace clone's published manifest for the same plugin, when validate_install runs, then the absence of the newer version in the Codex cache is reported as a warning that names the plugin and both versions, and the script exits zero ([test](tests/test_validate_install.scenario.l1.py))
- Given a plugin directory exists in either the Claude Code or Codex plugin cache and no manifest exists for that plugin in the working tree, when validate_install runs, then the orphan is reported as a warning that names the plugin, and the script exits zero ([test](tests/test_validate_install.scenario.l1.py))
- Given a plugin's cache holds the version directories `0.9.0`, `0.10.0`, `0.17.6`, `0.17.10`, and `0.17.12`, when the cache listing is assembled, then the entries appear in numeric order — `0.9.0`, `0.10.0`, `0.17.6`, `0.17.10`, `0.17.12` — rather than the lexicographic order that would place `0.10.0` first and `0.9.0` last ([test](tests/test_validate_install.scenario.l1.py))

### Compliance

- ALWAYS: marketplace sync and direct-publish wrappers refresh installed plugins only when the published range changes plugin distribution files under `src/`, `dist/`, `.claude-plugin/`, or `.agents/plugins`; spec-only and coordination-note-only commits do not refresh marketplace caches ([review])
