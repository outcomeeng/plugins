# Installation

PROVIDES catalog-derived installation plans, explicit state boundaries, and ownership-bounded native agent placement
SO THAT marketplace maintainers and isolated verification
CAN inspect installation operations and preserve unrelated files while reconciling skill content with its native definitions

Installation follows `spx/32-distribution.enabler/21-installation.enabler/12-installation-state.pdr.md` and `spx/32-distribution.enabler/21-installation.enabler/15-installation-architecture.adr.md`. Agent delivery preserves the shared guarantees in `spx/12-agent-delivery.pdr.md`.

## Assertions

### Scenarios

- Given `just verify-marketplace-installation`, when the recipe runs, then it passes `spx/32-distribution.enabler/21-installation.enabler` to the repository test command so pytest discovers the common evidence and every installation descendant. ([test](tests/test_installation_contracts.scenario.l1.py))

### Mappings

- Each marketplace, plugin, and lifecycle operation an installation plan performs maps to a failure report naming that operation and its agent, with attempted commands ending at that operation and no later operation performed, except an established pending-publication absence in persistent mode. ([test](tests/test_installation_contracts.mapping.l1.py))
- For each supported agent and selected installation mode, the selected plugin set maps to catalog order; an empty persistent selection maps to only `spec-tree`, and isolated full-catalog selection maps to every committed member. ([test](tests/test_installation.mapping.l1.py))

### Compliance

- ALWAYS: persistent installation targets Claude Code project scope in the invocation checkout for marketplace, inspection, and bootstrap operations, each recorded plugin's own project or local scope and project path for its native update, and the selected `CODEX_HOME`, while isolated verification targets only caller-selected disposable homes; an agent-CLI failure reports its exact agent and operation and stops subsequent operations except established pending publication in persistent mode. ([test](tests/test_installation.compliance.l1.py))
- ALWAYS: a plugin lifecycle places and prunes only its own recorded definitions, adopts identical unrecorded content without rewriting it, and preserves definition and ownership-file identity on an unchanged repeat. ([test](tests/test_installation_contracts.compliance.l1.py))
- NEVER: placement overwrites or prunes foreign, modified, symlinked, or otherwise invalid destinations; changes after preflight stop mutation. ([test](tests/test_installation_contracts.compliance.l1.py))
- ALWAYS: scope-split preflight reports every mismatched definition even when ownership or the selected agent directory is invalid, distinguishing byte-identical directed removals from changed or renamed collisions. ([test](tests/test_installation_contracts.compliance.l1.py))
