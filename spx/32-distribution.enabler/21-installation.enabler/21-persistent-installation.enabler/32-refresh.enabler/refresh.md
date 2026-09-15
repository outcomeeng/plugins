# Persistent Refresh

PROVIDES activation-preserving bootstrap, refresh, and interrupted-installation recovery
SO THAT marketplace maintainers
CAN make their selected published plugins available without widening selection or restoring obsolete configuration

## Assertions

- Given an empty selected Codex home, when persistent installation runs, then only `spec-tree` is registered and cached, its home activation is explicitly disabled, and the run warns that the operator can select additional plugins.

- Given empty Claude Code project installation state, when bootstrap runs, then only `spec-tree` is installed, declared project activation is preserved, and absent activation defaults to disabled with a warning.

- Given a trusted product enabling a home-disabled plugin, when that product loads, then the plugin's skills are active for that product; a product that supplies no override retains disabled activation, and a home-wide refresh preserves both products' configuration and the home's activation.

- Given configured home plugins whose marketplace snapshot or plugin cache is absent, when refresh runs or resumes after interruption, then all selected published plugins become available with the same activation and no additional selection, including when the marketplace revision is unchanged.

- For each supported agent, refreshing a valid selected subset preserves every pre-run activation entry, including disabled plugins and explicitly enabled home plugins, while updating every selected published plugin through native refresh operations.

- Given an unexpected selection or activation write during persistent execution, when verification detects it, then the run reports failure and retains the changed state for diagnosis without restoring an earlier settings snapshot or issuing compensating activation commands.

- ALWAYS: a pending-publication result names a selected plugin whose absence from the canonical source is established, preserves its prior owned definitions, and reports it separately from successfully refreshed plugins; other failures stop all later operations.
