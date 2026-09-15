# Persistent Refresh

PROVIDES activation-preserving bootstrap, refresh, and interrupted-installation recovery
SO THAT marketplace maintainers
CAN make their selected published plugins available without widening selection or restoring obsolete configuration

## Assertions

- For each agent with empty persistent installation state, bootstrap registers and installs only `spec-tree` and warns that the operator can select additional plugins. Codex explicitly declares its home activation disabled; Claude Code preserves declared project activation and defaults absent activation to disabled.

- Given a trusted product enabling a home-disabled plugin, when that product loads, then the plugin's skills are active for that product; a product that supplies no override retains disabled activation, and a home-wide refresh preserves both products' configuration and the home's activation.

- Given configured home plugins whose marketplace snapshot or plugin cache is absent, when refresh runs or resumes after interruption, then all selected published plugins become available with the same activation and no additional selection, including when the marketplace revision is unchanged.

- For each supported agent, refreshing a valid selected subset preserves every pre-run activation entry, including disabled plugins and explicitly enabled home plugins, while updating every selected published plugin through native refresh operations.

- Given an unexpected selection or activation write during persistent execution, when verification detects it, then the run reports failure and retains the changed state for diagnosis without restoring an earlier settings snapshot or issuing compensating activation commands.

- ALWAYS: a pending-publication result names a selected plugin whose absence from the canonical source is established, preserves its prior owned definitions, and reports it separately from successfully refreshed plugins; other failures stop all later operations.

### Compliance

- NEVER: trusted-product Codex configuration changes catalog-selection planning or becomes an installation argument. ([test](tests/test_refresh.compliance.l1.py))

- Given Claude Code install records for catalog plugins in the invocation checkout and in other checkouts on the machine, when persistent installation runs, then each record receives one native plugin update at its scope from its project path, the run issues no install or enable for a plugin the invocation checkout records, and the report lists every refreshed record. ([test](tests/test_refresh.scenario.l1.py))

- Given a project-scope record in the invocation checkout and a local-scope record in a second checkout, both installed through the real Claude Code CLI into one disposable agent state, when the persistent recipe runs from the invocation checkout, then the native update executes for both records at their own scope from their own project path, the listing still reports both records, and neither checkout's activation entries change. ([test](tests/test_refresh.scenario.l3.py))

- Every Claude Code install record in a listing maps to exactly one native plugin update at its own scope from its own project path when its plugin is cataloged, its scope is project or local, its project path is an existing directory, and its project declares no noncanonical marketplace source in readable settings, read in Claude Code's own precedence order with the local document over the project document, and otherwise to one warning naming the record and why it is left unchanged, with no command for it; an entry from another marketplace maps to nothing. ([test](tests/test_refresh.mapping.l1.py))

- NEVER: a persistent plan reinstalls a plugin the invocation checkout already records — a reinstall moves no Claude Code install record, so refresh of a recorded plugin is the native update alone, and a native update failing outside the pending-publication wording stops the run. ([test](tests/test_refresh.compliance.l1.py))
