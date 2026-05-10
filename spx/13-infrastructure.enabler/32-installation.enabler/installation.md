# Installation

PROVIDES local plugin marketplace installation and update support for developer machines
SO THAT Codex and Claude Code users working from this repository
CAN refresh installed plugins without breaking active sessions or local tool state

## Assertions

### Scenarios

- Given the Codex plugin cache contains an installed marketplace version, when the marketplace upgrade removes that version and installs a newer version of the same plugin, then the old version directory path becomes a symlink to the newer version and stale compatibility symlinks older than seven days are pruned ([test](tests/test_codex_plugin_cache.scenario.l1.py))
- Given a working-tree plugin manifest declares a newer version than the Codex marketplace clone's published manifest for the same plugin, when validate_install runs, then the absence of the newer version in the Codex cache is reported as a warning that names the plugin and both versions, and the script exits zero ([test](tests/test_validate_install.scenario.l1.py))
