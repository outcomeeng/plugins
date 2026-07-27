# Installation

PROVIDES marketplace installation workflows that execute agent CLIs from committed checkout declarations within caller-selected environments
SO THAT repository validation and explicit consumer setup
CAN install a consistent plugin set without depending on ambient user-scope marketplace state

## Assertions

### Compliance

- ALWAYS: repository installation derives each agent's complete plugin set from that agent's committed marketplace catalog. ([test](tests/test_installation.conformance.l1.py))
- ALWAYS: installation applies agent-CLI operations only to the invocation checkout and caller-selected agent homes. ([test](tests/test_installation.compliance.l1.py))
- ALWAYS: an agent-CLI failure identifies the exact agent and plugin operation and stops every subsequent installation operation. ([test](tests/test_installation.compliance.l1.py))
