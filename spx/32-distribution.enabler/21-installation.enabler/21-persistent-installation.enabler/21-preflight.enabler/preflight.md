# Persistent Installation Preflight

PROVIDES catalog-bounded selection and whole-run source and scope validation
SO THAT marketplace maintainers
CAN inspect a persistent installation plan before any state-changing operation

## Assertions

- ALWAYS: persistent selection is the catalog-bounded Claude Code inventory recorded for the invocation checkout at project or local scope or the catalog-bounded plugin keys in the selected Codex home's raw configuration, including disabled plugins and plugins with missing caches; product overrides never change that home-wide set.

- Given an existing noncanonical marketplace source for either agent, when persistent preflight runs, then it reports the observed and canonical sources and the need for explicit repair, and no agent performs a state-changing operation.

### Scenarios

- Given a nonempty selected subset that omits `spec-tree`, when persistent installation starts, then it reports the invalid selection and performs no state-changing operation. ([test](tests/test_preflight.scenario.l1.py))

- Given a user-scoped Claude Code `outcomeeng` marketplace registration, when persistent installation starts, then it reports the colliding settings path and performs no state-changing operation. ([test](tests/test_preflight.scenario.l1.py))

- Given a persistent marketplace inspection that fails, when persistent installation runs, then it reports a failure naming that operation and attempts no plan operation. ([test](tests/test_preflight.scenario.l1.py))

- Given a checkout declaring the canonical marketplace source and an agent home whose live marketplace listing lacks the marketplace, when persistent installation plans, then the plan adds the marketplace for that agent instead of refreshing it. ([test](tests/test_preflight.scenario.l1.py))

- Given a Claude Code listing entry at project scope that names no project path, when persistent installation plans, then it reports the listing defect and issues no command. ([test](tests/test_preflight.scenario.l1.py))

- Given an invocation checkout whose own Claude Code settings cannot be read, when persistent preflight runs, then it reports that settings path and issues no state-changing command. ([test](tests/test_preflight.scenario.l1.py))

- Given Claude Code's marketplace registry carrying `outcomeeng` from a noncanonical source, when persistent installation plans, then it reports the observed and canonical sources and the need for explicit repair and issues no state-changing command. ([test](tests/test_preflight.scenario.l1.py))

### Mappings

- Native plugin-listing entries map to marketplace membership through their declared marketplace identifiers; Claude Code entries additionally map through the invocation checkout's project or local scope. Listing membership alone never determines Codex persistent selection. ([test](tests/test_preflight.mapping.l1.py))
