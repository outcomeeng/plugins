# Repository Installation

PROVIDES `just install-marketplace` for persistent installation and `just verify-marketplace-installation` for isolated end-to-end proof
SO THAT marketplace maintainers and the merge lifecycle
CAN refresh every committed plugin in selected agent state and verify the same operation without changing persistent homes

## Assertions

### Scenarios

- Given canonical project configuration and an active `CODEX_HOME`, when `just install-marketplace` runs, then Claude Code refreshes project-scoped `outcomeeng/plugins`, Codex refreshes `outcomeeng/plugins` in that selected home, and every committed catalog plugin is installed and enabled. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a user-scoped Claude Code `outcomeeng` marketplace registration, when persistent installation starts, then it reports the colliding settings path and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given `just verify-marketplace-installation`, when the recipe runs, then it executes the repository-installation L2 evidence in disposable homes through the repository test command. ([test](tests/test_repository_installation.compliance.l1.py))
- Given every plugin in the Claude Code and Codex marketplace catalogs, when the isolated installation harness installs the catalog, then each agent registers the invocation checkout and every catalog plugin is observable as installed and enabled through the corresponding real agent CLI. ([test](tests/test_repository_installation.scenario.l2.py))
- Given an installed plugin that owns Codex agent definitions, when its lifecycle installation runs, then its generated definitions are placed in the invocation checkout's `.codex/agents/` namespace while definitions outside that plugin's ownership remain unchanged. ([test](tests/test_repository_installation.scenario.l2.py))
- Given an agent marketplace, plugin, or lifecycle operation that fails, when repository installation runs, then it reports the failing agent and plugin operation and performs no later operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given unchanged committed catalogs and checkout content, when isolated installation runs twice against the same disposable homes, then the second run succeeds with the same installed and placed state. ([test](tests/test_repository_installation.scenario.l2.py))

### Compliance

- NEVER: repository installation reads or writes repository `.codex/config.toml` as Codex plugin installation or enablement state. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: isolated verification reads or mutates a developer's persistent agent home, marketplace registration, plugin cache, or agent directory. ([test](tests/test_repository_installation.compliance.l1.py))
