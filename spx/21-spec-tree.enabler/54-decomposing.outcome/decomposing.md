# Decomposing

WE BELIEVE THAT structured decomposition of nodes with too many assertions or independent concerns
WILL reduce cognitive load per node and enable parallel implementation
CONTRIBUTING TO faster development cycles and clearer spec-to-test mapping

The `/decomposing` skill applies decomposition heuristics: assertion count thresholds, concern independence analysis, and depth guidelines.

## Assertions

### Scenarios

- Given a node with more than 7 assertions, when decomposition is analyzed, then the skill recommends splitting into child nodes ([test](tests/test_decomposing.unit.py))
- Given a node with assertions covering two independent concerns, when decomposition is analyzed, then the skill recommends separate nodes for each concern ([test](tests/test_decomposing.unit.py))

### Compliance

- ALWAYS: check assertion count and concern independence before recommending decomposition — decomposition is not arbitrary splitting ([review])
- NEVER: decompose a node with fewer than 4 assertions unless the assertions cover genuinely independent concerns ([review])
