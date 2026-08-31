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
- Given unchanged committed catalogs and checkout content, when isolated installation runs twice against the same disposable homes, then the first run places every shipped Codex agent definition in the disposable home's agent directory beside the skills it invokes, and the second run succeeds with the same installed and home-placed state. ([test](tests/test_repository_installation.scenario.l3.py))
- Given a persistent marketplace inspection that fails, when persistent installation runs, then it reports a failure naming that operation and attempts no plan operation. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a checkout declaring the canonical marketplace source and an agent home whose live marketplace listing lacks the marketplace, when persistent installation plans, then the plan adds the marketplace for that agent instead of refreshing it. ([test](tests/test_repository_installation.scenario.l1.py))
- Given a disposable `CODEX_HOME` that isolated installation populated and provisioned from the selected Codex home's existing login state, when the agent CLI confirms the copied login state and a fresh non-interactive Codex session in that home is asked for its available agent roles as structured output, then the returned role set contains every canonical role name the installation placed under that home's `agents/` directory. ([test](tests/test_repository_installation.scenario.l3.py))

### Mappings

- For each supported agent, a generated valid installed subset containing `spec-tree` maps through `just install-marketplace` to exactly those catalog plugins for that agent, with selected unpublished plugins reported as pending and the project's activation selection preserved. ([test](tests/test_repository_installation.mapping.l3.py))
- Each isolated verification selection — the complete committed catalogs and a generated valid subset containing `spec-tree` — maps to registration of the invocation checkout and exactly that selection reported as installed and enabled by the corresponding real agent CLI. ([test](tests/test_repository_installation.mapping.l3.py))
- For each supported agent, an explicitly selected valid isolated subset maps to a plan containing exactly its members in catalog order. ([test](tests/test_repository_installation.mapping.l1.py))
- Each marketplace, plugin, and lifecycle operation a repository-installation plan performs maps to a failure report naming that operation and its agent, with the attempted commands ending at that operation and no later operation performed. ([test](tests/test_repository_installation.mapping.l1.py))
- Each combination of installation mode and operation kind whose failure result contains the source-owned absent-marketplace marker maps to pending publication for a persistent plugin operation and to a terminal failure for every other combination. ([test](tests/test_repository_installation.mapping.l1.py))

### Compliance

- ALWAYS: persistent installation places every plugin's generated Codex agent definitions in the selected `CODEX_HOME/agents/` directory beside the skill content they invoke, leaving definitions outside the marketplace's recorded ownership unchanged ([test](tests/test_repository_installation.compliance.l1.py))
- ALWAYS: marketplace reconciliation leaves exactly one current marketplace-owned definition for every authored Codex agent in the selected agent home and removes marketplace-owned definitions for agents or plugins absent from the current committed catalog ([test](tests/test_repository_installation.compliance.l1.py))
- ALWAYS: a scope split — plugin-owned agent definitions in a checkout whose invoked skill content lives in the selected agent home — stops installation before mutation, reports every mismatched definition, and directs removal of byte-identical plugin copies while identifying changed or unrecognized copies as collisions for inspection ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: repository installation reads or writes repository `.codex/config.toml` as Codex plugin installation or enablement state. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: a persistent installation run leaves the checkout's committed plugin selection changed, including a run that fails after installing has already altered it. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: preserving the committed plugin selection reverts the marketplace source the same run reconciled — a checkout declaring a noncanonical source ends with the canonical source and its own selection. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: isolated verification mutates a developer's persistent agent home, marketplace registration, plugin cache, agent directory, or login state; its only persistent-state read is the selected Codex login state copied into the disposable home for the role-discovery probe. ([test](tests/test_repository_installation.compliance.l3.py))
- ALWAYS: reconciliation adopts a present destination whose bytes equal the plugin's current shipped definition but which no ownership entry records, so a run interrupted before its ownership-record write completes cleanly when re-run. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: the fresh-session role-discovery probe continues without selected Codex login state; direct invocation with no selected login state raises a loud error before any agent process runs. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: the fresh-session role-discovery probe returns an observation after any credential-bearing login-state scalar appears in a command argument or captured stream. ([test](tests/test_repository_installation.compliance.l1.py))
- NEVER: the fresh-session role-discovery probe changes the selected Codex login state or exposes a credential-bearing scalar through command arguments, reports, logs, or captured streams; the L3 evidence reports an explicit skip before probe invocation when selected login state is unavailable. ([test](tests/test_repository_installation.compliance.l3.py))
