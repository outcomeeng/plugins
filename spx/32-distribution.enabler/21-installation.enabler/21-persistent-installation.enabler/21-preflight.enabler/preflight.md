# Persistent Installation Preflight

PROVIDES catalog-bounded selection and whole-run source and scope validation
SO THAT marketplace maintainers
CAN inspect a persistent installation plan before any state-changing operation

## Assertions

- ALWAYS: persistent selection is the catalog-bounded Claude Code project-installed inventory or the catalog-bounded plugin keys in the selected Codex home's raw configuration, including disabled plugins and plugins with missing caches; product overrides never change that home-wide set.

- Given an existing noncanonical marketplace source for either agent, when persistent preflight runs, then it reports the observed and canonical sources and the need for explicit repair, and no agent performs a state-changing operation.

- Given a nonempty selected subset that omits `spec-tree`, when persistent installation starts, then it reports the invalid selection and performs no state-changing operation. ([test](tests/test_preflight.scenario.l1.py))

- Given a user-scoped Claude Code `outcomeeng` marketplace registration, when persistent installation starts, then it reports the colliding settings path and performs no state-changing operation. ([test](tests/test_preflight.scenario.l1.py))

- Given a persistent marketplace inspection that fails, when persistent installation runs, then it reports a failure naming that operation and attempts no plan operation. ([test](tests/test_preflight.scenario.l1.py))

- Given a checkout declaring the canonical marketplace source and an agent home whose live marketplace listing lacks the marketplace, when persistent installation plans, then the plan adds the marketplace for that agent instead of refreshing it. ([test](tests/test_preflight.scenario.l1.py))
