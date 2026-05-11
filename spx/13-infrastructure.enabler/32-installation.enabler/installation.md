# Installation

PROVIDES local plugin marketplace installation and update support for developer machines
SO THAT Codex and Claude Code users working from this repository
CAN refresh installed plugins without breaking active sessions or local tool state

## Assertions

### Scenarios

- Given a plugin's manifest has been published to two distinct versions on the marketplace branch within the last thirty days and the Codex plugin cache contains only the latest version directory, when the marketplace cache preservation step executes, then the older published version path resolves to a symlink pointing at the current version directory ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin's manifest published a version more than thirty days ago and that version path appears as a symlink in the Codex plugin cache, when the marketplace cache preservation step executes, then the out-of-window symlink is removed ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a plugin directory exists in the Codex plugin cache and no corresponding manifest exists in the working tree, when the marketplace cache preservation step executes, then the entire cache directory for that orphaned plugin is removed ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a working-tree plugin manifest declares a newer version than the Codex marketplace clone's published manifest for the same plugin, when validate_install runs, then the absence of the newer version in the Codex cache is reported as a warning that names the plugin and both versions, and the script exits zero ([test](tests/test_validate_install.scenario.l1.py))
