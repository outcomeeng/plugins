# Installation

PROVIDES local plugin marketplace installation and update support for developer machines
SO THAT Codex and Claude Code users working from this repository
CAN refresh installed plugins without breaking active sessions or local tool state

## Assertions

### Scenarios

- Given the Codex plugin cache contains an installed marketplace version, when the marketplace upgrade removes that version and installs a newer version of the same plugin, then the old version directory path becomes a symlink to the newer version and stale compatibility symlinks older than seven days are pruned ([test](tests/test_codex_plugin_cache.scenario.l1.py))
