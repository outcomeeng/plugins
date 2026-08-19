# Repository Installation

PROVIDES `just install-marketplace` for persistent installation and `just verify-marketplace-installation` for isolated end-to-end proof
SO THAT marketplace maintainers and the merge lifecycle
CAN refresh exactly the installed plugins in selected agent state and verify full, valid-subset, and invalid-subset behavior without changing persistent homes

## Assertions

### Scenarios

- Given an agent state with no installed `outcomeeng` plugin, when persistent installation runs, then it installs only `spec-tree` for that agent and warns that the operator probably wants additional plugins. ([test](tests/test_repository_installation.scenario.l3.py))
- Given a nonempty installed subset that omits `spec-tree`, when persistent installation starts, then it reports the invalid selection and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a checkout whose committed catalog declares a plugin the marketplace has not published, when persistent installation runs, then that plugin is reported as pending publication and every other plugin still installs. ([test](tests/test_repository_installation.scenario.l1.py))
- Given the same absent plugin, when isolated installation runs, then the absence is terminal at that plugin's install, because the marketplace an isolated run registers is the checkout itself. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a user-scoped Claude Code `outcomeeng` marketplace registration, when persistent installation starts, then it reports the colliding settings path and performs no state-changing operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given `just verify-marketplace-installation`, when the recipe runs, then it passes the repository-installation node's tests directory to the repository test command so pytest discovers every evidence file. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a generated subset omitting `spec-tree`, when isolated installation plans that selection, then it reports the invalid subset before an agent CLI mutates state. ([test](tests/test_repository_installation.scenario.l1.py))
- Given an installed plugin that owns Codex agent definitions, when that plugin's checkout materialization runs, then its generated definitions are placed in the invocation checkout's `.codex/agents/` namespace while definitions outside that plugin's ownership remain unchanged. ([test](tests/test_repository_installation.scenario.l3.py))
- Given unchanged committed catalogs and checkout content, when isolated installation, together with any checkout materialization the run exercises, runs twice against the same disposable homes, then the second run succeeds with the same installed and placed state. ([test](tests/test_repository_installation.scenario.l3.py))
- Given a persistent marketplace inspection that fails, when persistent installation runs, then it reports a failure naming that operation and attempts no plan operation. ([test](tests/test_repository_installation.scenario.l1.py))

### Mappings

- For each supported agent, a generated valid installed subset containing `spec-tree` maps through `just install-marketplace` to exactly those catalog plugins for that agent, with selected unpublished plugins reported as pending and the project's activation selection preserved. ([test](tests/test_repository_installation.mapping.l3.py))
- Each isolated verification selection — the complete committed catalogs and a generated valid subset containing `spec-tree` — maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI. ([test](tests/test_repository_installation.mapping.l3.py))
- Each marketplace, plugin, and lifecycle operation a repository-installation plan performs maps to a failure report naming that operation and its agent, with the attempted commands ending at that operation and no later operation performed. ([test](tests/test_repository_installation.mapping.l1.py))
- Each combination of installation mode and operation kind whose failure result contains the source-owned absent-marketplace marker maps to pending publication for a persistent plugin operation and to a terminal failure for every other combination. ([test](tests/test_repository_installation.mapping.l1.py))

### Compliance

- NEVER: repository installation reads or writes repository `.codex/config.toml` as Codex plugin installation or enablement state. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: a persistent installation run that starts with a committed plugin selection leaves that selection changed, including a run that fails after installing has already altered it. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: successful persistent installation creates a committed plugin selection when the checkout starts without one. ([test](tests/test_repository_installation.compliance.l3.py))
- NEVER: preserving the committed plugin selection reverts the marketplace source the same run reconciled — a checkout declaring a noncanonical source ends with the canonical source and its own selection. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: isolated verification reads or mutates a developer's persistent agent home, marketplace registration, plugin cache, or agent directory. ([test](tests/test_repository_installation.compliance.l3.py))
