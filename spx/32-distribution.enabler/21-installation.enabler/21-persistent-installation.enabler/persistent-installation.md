# Persistent Installation

PROVIDES home-selected marketplace refresh and ownership-bounded agent reconciliation
SO THAT marketplace maintainers
CAN refresh installed skill content and its native definitions while preserving activation and foreign files

## Assertions

- ALWAYS: selected Codex plugins' subagent definitions remain globally registered under the selected home's digest-bound ownership record regardless of product skill activation; disabling a plugin in a product neither removes its home definitions nor generates a product registry.

- ALWAYS: pending plugins retain their prior owned definitions while other selected published plugins refresh.

### Compliance

- NEVER: a publication-absence report counts a pending plugin as installed for the affected agent or removes it from another agent's successful installation report. ([test](tests/test_publication_report.compliance.l1.py))

- ALWAYS: persistent installation places each refreshed selected plugin's generated Codex agent definitions in the selected `CODEX_HOME/agents/` directory beside the skill content they invoke, leaving definitions outside the marketplace's recorded ownership unchanged ([test](tests/test_persistent_installation.compliance.l1.py))

- ALWAYS: marketplace reconciliation leaves exactly one current marketplace-owned definition for each authored Codex agent of a refreshed selected plugin and removes unchanged owned definitions for agents removed from refreshed plugins or plugins outside the catalog-bounded home selection ([test](tests/test_persistent_installation.compliance.l1.py))

- ALWAYS: a scope split — plugin-owned agent definitions in a checkout whose invoked skill content lives in the selected agent home — stops installation before mutation, reports every mismatched definition, and directs removal of byte-identical plugin copies while identifying changed or unrecognized copies as collisions for inspection ([test](tests/test_persistent_installation.compliance.l1.py))

- ALWAYS: reconciliation adopts a present destination whose bytes equal the plugin's current shipped definition but which no ownership entry records, so a run interrupted before its ownership-record write completes cleanly when re-run. ([test](tests/test_persistent_installation.compliance.l1.py))
